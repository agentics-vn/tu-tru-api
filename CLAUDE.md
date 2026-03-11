# CLAUDE.md — Bat Tu Date Selection API

## Project Context
REST API that scans a date range and returns auspicious dates (ngày tốt) based on:
1. User's Bat Tu birth chart (personal astrology)
2. Intent (Khai Truong, Cuoi Hoi, Dong Tho, etc.)
3. Traditional Vietnamese almanac rules (hung ngay, truc, sao)

## Tech Stack
- **Runtime:** Node.js 20+ (or Python 3.11+ — dev's choice, be consistent)
- **Framework:** Express.js (Node) or FastAPI (Python)
- **DB:** SQLite for local dev, PostgreSQL for production
- **Cache:** Redis (required — Layer 1 results cached by month)
- **Auth:** API Key via `X-API-Key` header, hashed in DB

## Project Structure
```
bat-tu-api/
├── CLAUDE.md
├── docs/
│   ├── algorithm.md      ← ALL calculation logic lives here
│   ├── api-spec.md       ← Request/response contract
│   └── seed/             ← Static data files (seed DB from these)
│       ├── truc.json
│       ├── hung-ngay.json
│       ├── sao-ngay.json
│       └── ngu-hanh.json
├── src/
│   ├── api/
│   │   ├── routes/chon-ngay.js
│   │   └── middleware/auth.js
│   ├── engine/
│   │   ├── battu.js        ← computeBatTu()
│   │   ├── layer1.js       ← filterLayer1()
│   │   ├── layer2.js       ← filterLayer2()
│   │   ├── layer3.js       ← scoreDays()
│   │   └── reason-builder.js
│   ├── lib/
│   │   ├── can-chi.js      ← getCanChiDay(), getCanChiYear()
│   │   ├── lunar.js        ← toLunar() wrapper
│   │   └── ngu-hanh.js     ← element lookups
│   ├── db/
│   │   ├── index.js
│   │   └── seed.js
│   └── cache/redis.js
└── tests/
    ├── unit/
    └── integration/
```

## Coding Rules
- All Vietnamese text in strings must be UTF-8. Never use ASCII transliteration in DB or responses.
- Every filter function must be **pure** (no side effects, same input → same output). This is critical for the safety guarantee in test TC-10.
- The safety invariant: **a day with severity=3 in dates_to_avoid MUST NEVER appear in recommended_dates.** Add a final guard check before building the response.
- Use `docs/algorithm.md` as the single source of truth for all calculations. Do not invent rules.
- Use `docs/seed/*.json` to seed static tables. Do not hardcode lookup data in application code.

## Lunar Calendar Library
Use **`chinese-lunar-calendar`** npm package for solar→lunar conversion. Do NOT roll your own.
```bash
npm install chinese-lunar-calendar
```
Wrapper: `src/lib/lunar.js` should expose `toLunar(dateString)` returning `{ year, month, day, isLeap }`.

## Key Commands
```bash
npm run dev          # start with nodemon
npm run seed         # seed all static tables from docs/seed/*.json
npm test             # run all tests
npm run test:unit    # unit tests only
npm run test:tc      # run the 10 critical test cases from docs/test-cases.md
```

## Environment Variables (.env)
```
DATABASE_URL=postgresql://user:pass@localhost:5432/battu
REDIS_URL=redis://localhost:6379
NODE_ENV=development
PORT=3000
```

## Critical Constraints
- Max date range per request: 90 days
- Max response time: 1 second (p95)
- Redis TTL for Layer 1 cache: 86400 seconds (1 day), keyed by `layer1:{YYYY-MM}`
- Rate limit: 100 req/day per API key (BASIC plan), tracked in Redis
- `top_n` default: 3, max: 10

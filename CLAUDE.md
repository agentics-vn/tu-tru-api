# CLAUDE.md — Bat Tu Date Selection API

## Project Context
REST API that scans a date range and returns auspicious dates (ngày tốt) based on:
1. User's Bat Tu birth chart (personal astrology)
2. Intent (Khai Truong, Cuoi Hoi, Dong Tho, etc.)
3. Traditional Vietnamese almanac rules (hung ngay, truc, sao)

## Tech Stack
- **Runtime:** Python 3.11+
- **Framework:** FastAPI
- **Lunar calendar:** `sxtwl` (C extension for solar↔lunar conversion)

## Project Structure
```
bat-tu-api/
├── CLAUDE.md
├── docs/
│   ├── algorithm.md      ← ALL calculation logic lives here
│   ├── api-spec.md       ← Request/response contract
│   └── seed/             ← Static data files (loaded at startup)
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
└── tests/
    ├── unit/
    └── integration/
```

## Coding Rules
- All Vietnamese text in strings must be UTF-8. Never use ASCII transliteration in responses.
- Every filter function must be **pure** (no side effects, same input → same output). This is critical for the safety guarantee in test TC-10.
- The safety invariant: **a day with severity=3 in dates_to_avoid MUST NEVER appear in recommended_dates.** Add a final guard check before building the response.
- Use `docs/algorithm.md` as the single source of truth for all calculations. Do not invent rules.
- Use `docs/seed/*.json` as static data sources. Do not hardcode lookup data in application code.

## Key Commands
```bash
uvicorn src.app:app --reload --port 3000   # start dev server
pytest                                      # run all tests
pytest tests/unit                           # unit tests only
```

## Environment Variables (.env)
```
PORT=3000
```

## Critical Constraints
- Max date range per request: 90 days
- Max response time: 1 second (p95)
- `top_n` default: 3, max: 10

## gstack
- For all web browsing, use the `/browse` skill from gstack. Never use `mcp__claude-in-chrome__*` tools.
- Available skills:
  - `/plan-ceo-review`
  - `/plan-eng-review`
  - `/review`
  - `/ship`
  - `/browse`
  - `/qa`
  - `/setup-browser-cookies`
  - `/retro`

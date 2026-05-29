# Direction C fixtures

Golden JSON responses for NLTT regression. Regenerate after API changes:

```bash
PYTHONPATH=src .venv/bin/python scripts/generate_direction_c_fixtures.py
```

| File | Endpoint |
|------|----------|
| `day-detail-generic.json` | `GET /v1/day-detail?mode=generic` |
| `day-detail-personalized-*.json` | Personalized day-detail samples |
| `chon-ngay-happy.json` / `chon-ngay-empty.json` | `POST /v1/chon-ngay` |
| `day-luan-context.json` | `GET /v1/day-detail/luan-context` |
| `day-compare.json` | `GET /v1/day-compare` |
| `la-so-full.json` | `GET /v1/la-so` |
| `la-so-luu-nien-2026.json` | `GET /v1/la-so/luu-nien` |
| `phong-thuy-year-2026.json` | `GET /v1/phong-thuy?year=2026` |

# Financial Therapy Coach (MVP)

A runnable MVP inspired by your planning document:
- KMSI-R style onboarding and money script scoring
- Personalized coaching responses based on dominant script
- A deterministic "what-if" affordability simulation
- Consent-gated subscription cancellation draft generation
- Frontend fallback routing so non-API paths do not return accidental "Not Found"

## Run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```

Open http://localhost:8000

## Test

```bash
pytest -q
```

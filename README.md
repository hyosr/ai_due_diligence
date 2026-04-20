# AI Due Diligence – AI SaaS Credibility Assessment (MVP)

## Run

```bash
python -m venv .venv
source .venv/bin/activate   # Linux/macOS
.venv\Scripts\activate    # Windows

pip install -r requirements.txt
uvicorn app.main:app --reload
```

API docs:
- http://127.0.0.1:8000/docs

UI:
-http://127.0.0.1:8000/ui 

## Main flow
1. `POST /intake/company` (company name + website + optional URLs)
2. `POST /assessment/run/{company_id}` (extract signals + score)
3. `GET /report/markdown/{assessment_id}` (download markdown)
4. `GET /report/pdf/{assessment_id}` (download pdf)

## Notes
- This is a robust MVP and easy to extend.
- For production: add Celery/Redis, retries, rate-limiting, and secure storage for uploaded docs.
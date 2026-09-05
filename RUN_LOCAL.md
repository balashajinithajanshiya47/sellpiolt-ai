# SellPilot AI — Quick Local Run

## 1. Terminal A: backend

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
set BACKEND_URL=http://localhost:8000
uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

## 2. Terminal B: Streamlit

```bash
venv\Scripts\activate
streamlit run app.py
```

## 3. Optional Groq setup

Copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml` and add your real `GROQ_API_KEY`.

For Streamlit Cloud, add the key under the app's Secrets instead of committing a secrets file.

## 4. Razorpay

Razorpay belongs on the FastAPI backend. Put the test key ID and test secret in Render Environment Variables (or local environment variables). Do not put the secret in GitHub or Streamlit code.

## 5. Health check

Open:

```text
http://localhost:8000/health
```

Expected basic response includes:

```json
{
  "status": "ok"
}
```

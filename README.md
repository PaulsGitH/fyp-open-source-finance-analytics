##FYP Open Source Finance Analytics

#Purpose
Semester 1 hello world scaffold for an open source financial analytics system.
Includes a FastAPI backend, a Streamlit frontend, and a sample CSV for basic metrics.

#Run locally
1. Create and activate a Python virtual environment
2. pip install -r requirements.txt
3. In one terminal: uvicorn backend.main:app --reload --port 8000
4. In another terminal: streamlit run app/streamlit_app.py

#Run with Docker
docker compose up --build

#Next steps
Replace the rule based categoriser with a Hugging Face model in Semester 2.
Add database support and additional analytics when required.

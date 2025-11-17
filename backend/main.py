from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .schemas import SummaryRequest, SummaryResponse
from .categoriser import count_labels

app = FastAPI(title="FYP Finance API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/summary", response_model=SummaryResponse)
def summary(payload: SummaryRequest):
    amounts = [t.amount for t in payload.transactions]
    income = sum(a for a in amounts if a > 0)
    expenses = -sum(a for a in amounts if a < 0)
    net = income - expenses
    labels = count_labels([t.description for t in payload.transactions])
    return SummaryResponse(income=income, expenses=expenses, net=net)

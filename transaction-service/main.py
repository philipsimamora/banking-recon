from fastapi import FastAPI
from database import Base, engine
from routers import transactions

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Transaction Service", version="1.0.0")
app.include_router(transactions.router)

@app.get("/health")
def health():
    return {"service": "transaction-service", "status": "ok"}
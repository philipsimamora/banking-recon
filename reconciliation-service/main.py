from fastapi import FastAPI
from routers import reconciliation

app = FastAPI(title="Reconciliation Service", version="1.0.0")
app.include_router(reconciliation.router)

@app.get("/health")
def health():
    return {"service": "reconciliation-service", "status": "ok"}
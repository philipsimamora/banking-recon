from fastapi import FastAPI
from database import Base, engine
from routers import statements

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Statement Service", version="1.0.0")
app.include_router(statements.router)

@app.get("/health")
def health():
    return {"service": "statement-service", "status": "ok"}
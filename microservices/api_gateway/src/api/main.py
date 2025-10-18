from fastapi import FastAPI

app = FastAPI(
    title="Investment Portfolio API",
    description="API для управления инвестиционным портфелем",
    version="0.1.0",
)


@app.get("/", tags=["Root"])
def read_root():
    return {"status": "healthy", "message": "Welcome to Investment Portfolio API!"}

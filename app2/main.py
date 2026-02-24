from fastapi import FastAPI
from src.core.kafka import start_consumer

app = FastAPI(title="Consumer")




# ===================== app2 자동 실행 =====================
@app.on_event("startup")
def startup_event():
  start_consumer()

# ================== 기본화면(사용하지 않음) ==================
@app.get("/")
def read_root():
  return {"Hello": "World"}
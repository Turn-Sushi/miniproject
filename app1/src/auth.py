from fastapi import APIRouter
from src.settings import settings
from src.db import findOne, add_key
from pydantic import EmailStr, BaseModel, Field
from kafka import KafkaProducer
import redis
import json
from src.logger import log

router = APIRouter(tags=["회원관리"], prefix="/auth")

pd = KafkaProducer(
  bootstrap_servers=settings.kafka_server,
  value_serializer=lambda v: json.dumps(v).encode("utf-8")
)

class EmailModel(BaseModel):
  email: EmailStr = Field(..., title="이메일 주소", description="사용자 식별을 위한 이메일 주소 입니다.")

@router.post("/email")
def producer(model: EmailModel):
  pd.send(settings.kafka_topic, dict(model))
  pd.flush()
  return {"status": True}

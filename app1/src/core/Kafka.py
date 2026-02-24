from kafka import KafkaProducer
from src.settings import settings
import json

# ================= 외부 서비스 연결 =================

pd = KafkaProducer(
  bootstrap_servers=settings.kafka_server,
  value_serializer=lambda v: json.dumps(v).encode("utf-8")
)
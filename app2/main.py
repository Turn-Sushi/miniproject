from fastapi import FastAPI
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from kafka import KafkaConsumer
from src.settings import settings
import threading
import asyncio
import json
import random
import string
import redis

# ================= redis 및 ConnectionConfig 설정 =================

app = FastAPI(title="Consumer")

client = redis.Redis(
  host=settings.redis_host,
  port=settings.redis_port,
  db=settings.redis_db
)

conf = ConnectionConfig(
  MAIL_USERNAME = settings.mail_username,
  MAIL_PASSWORD = settings.mail_password,
  MAIL_FROM = settings.mail_from,
  MAIL_PORT = settings.mail_port,
  MAIL_SERVER = settings.mail_server,
  MAIL_FROM_NAME = settings.mail_from_name,
  MAIL_STARTTLS = settings.mail_starttls,
  MAIL_SSL_TLS = settings.mail_ssl_tls,
  USE_CREDENTIALS = settings.use_credentials,
  VALIDATE_CERTS = settings.validate_certs
)

# ================= 로그인 인증코드 발급 =================
async def simple_send(email: str, loginId: str):
  id = ''.join(random.choices(string.digits, k=6))
  client.setex(f"login:{loginId}", 180, json.dumps({
    "email": email,
    "id": id
  }))
  
  html = f"""
    <h1>Login Service</h1>
    <p>{id}</p>
  """

  message = MessageSchema(
    subject="일회용 인증 코드 발급",
    recipients=[ email ],
    body=html,
    subtype=MessageType.html
  )

  fm = FastMail(conf)
  await fm.send_message(message)

# ================= 카프카서버에서 값 받아옴 =================
def consumer():
  cs = KafkaConsumer(
    settings.kafka_topic, 
    bootstrap_servers=settings.kafka_server, 
    enable_auto_commit=True,
    value_deserializer=lambda v: json.loads(v.decode("utf-8"))
  )
  for msg in cs:
    data = msg.value
    if data.get("event") == "generate_code":
      asyncio.run(simple_send(data["email"], data["loginId"]))

# ===================== app2 자동 실행 =====================
@app.on_event("startup")
def startConsumer():
  thread = threading.Thread(target=consumer, daemon=True)
  thread.start()

# ================== 기본화면(사용하지 않음) ==================
@app.get("/")
def read_root():
  return {"Hello": "World"}
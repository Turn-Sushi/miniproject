from kafka import KafkaConsumer
from fastapi_mail import FastMail, MessageSchema, MessageType
from src.settings import settings
from src.core.redis import client
from src.core.mail_config import conf
import threading
import asyncio
import json
import random
import string


# ================= 로그인 인증코드 발급 =================
async def simple_send(email: str, loginId: str):
  id = ''.join(random.choices(string.digits, k=6))

  client.setex(
    f"login:{loginId}",
    180,
    json.dumps({
      "email": email,
      "id": id
    })
  )

  print(email, id)

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


# ================= Consumer Thread 시작 =================
def start_consumer():
  thread = threading.Thread(target=consumer, daemon=True)
  thread.start()
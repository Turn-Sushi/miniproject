from fastapi.middleware.cors import CORSMiddleware
from db import findOne, save
from fastapi import FastAPI, Depends, HTTPException, status, Response
from kafka import KafkaProducer
from settings import settings
from pydantic import EmailStr, BaseModel
import json
import redis
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError, ExpiredSignatureError
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials


app = FastAPI(title="Producer")

origins = [ "http://localhost:5173" ]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBearer()

class EmailModel(BaseModel):
  email: EmailStr

class CodeModel(BaseModel):
  id: str

class userInfo(BaseModel):
  name : str
  email : EmailStr
  gender : str

def set_token(email: str):
  try:
    sql = f"select `user_no` from mini.user where `email` = '{email}'"
    data = findOne(sql)
    if data:
      iat = datetime.now(timezone.utc)
      exp = iat + (timedelta(minutes=settings.access_token_expire_minutes))
      data = {
        "iss": "Team3",
        "sub": str(data["user_no"]),
        "iat": iat,
        "exp": exp
      }
      return jwt.encode(data, settings.secret_key, algorithm=settings.algorithm)
  except JWTError as e:
    print(f"JWT ERROR : {e}")
  return None

def get_payload(credentials: HTTPAuthorizationCredentials = Depends(security)):
  if credentials.scheme == "Bearer":
    try:
      payload = jwt.decode(credentials.credentials, settings.secret_key, algorithms=settings.algorithm)
      exp = payload.get("exp")

      now = datetime.now(timezone.utc).timestamp()
      minutes, remaining_seconds = divmod(int(exp - now), 60)
      return payload
    except ExpiredSignatureError as e:
      raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token expired",
      )
    except JWTError as e:
      raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid token",
      )
  return None

pd = KafkaProducer(
  bootstrap_servers=settings.kafka_server,
  value_serializer=lambda v: json.dumps(v).encode("utf-8")
)

client = redis.Redis(
  host=settings.redis_host,
  port=settings.redis_port,
  db=settings.redis_db,
  decode_responses=True
)

@app.post("/emailCheck")
def emailCheck(data: EmailModel):
    print(data.email)
    sql = f"SELECT COUNT(*) AS cnt FROM mini.user WHERE email = '{data.email}'"
    result = findOne(sql)
    count = result['cnt']
    if count > 0 :
      return {"status" : False, "msg": "가입된 이메일이 존재합니다."}
    return {"status" : True, "msg": "사용 가능한 이메일 입니다."}

@app.post("/signup")
def signup(data: userInfo):
    print(data)
    checkSql = f"SELECT COUNT(*) AS cnt FROM mini.user WHERE email = '{data.email}'"
    result = findOne(checkSql)
    count = result['cnt']
    if count > 0 :
      return {"status" : False, "msg": "가입된 이메일이 존재합니다."}
    
    insertSql = f"""
        INSERT INTO mini.user (name, email, gender)
        VALUES ('{data.name}', '{data.email}',  '{data.gender}')
    """
    save(insertSql)
    return {"status" : True, "msg" : "회원가입 성공"}

@app.post("/login")
def producer(model: EmailModel):
  print(model.email)
  sql = f"select `user_no`, `name` from mini.user where `email` = '{model.email}'"
  data = findOne(sql)
  if data:
    pd.send(settings.kafka_topic, dict(model))
    pd.flush()
    return {"status": True}
  return {"status": False}

@app.post("/code")
def code(model: CodeModel):
  print(model.id)
  result = client.get(model.id)
  if result:
    access_token = set_token(result)
    if access_token:
      client.delete(model.id)
      return {"status": True, "access_token": access_token}
  return {"status": False}

@app.post("/me")
def me(payload = Depends(get_payload)):
  if payload:
    return {"status": True}
  return {"status": False}

@app.get("/")
def read_root():
  return {"Hello": "World"}
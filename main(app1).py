from fastapi.middleware.cors import CORSMiddleware
from db import findOne, save
from fastapi import FastAPI, Depends, HTTPException, status, Response, Request
from kafka import KafkaProducer
from settings import settings
from pydantic import EmailStr, BaseModel
import json
import redis
import uuid
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


class EmailModel(BaseModel):
  email: EmailStr

class CodeModel(BaseModel):
  loginId: str
  id: str

class userInfo(BaseModel):
  name : str
  email : EmailStr
  gender : str

class boardInfo(BaseModel) :
    title : str
    content : str
    # writer : str

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

def get_payload(request: Request):
  token = request.cookies.get("access_token")

  if not token:
      raise HTTPException(
          status_code=status.HTTP_401_UNAUTHORIZED,
          detail="Not authenticated"
      )

  try:
      payload = jwt.decode(
          token,
          settings.secret_key,
          algorithms=[settings.algorithm]
      )
      return payload

  except ExpiredSignatureError:
      raise HTTPException(
          status_code=status.HTTP_401_UNAUTHORIZED,
          detail="Token expired"
      )

  except JWTError:
      raise HTTPException(
          status_code=status.HTTP_401_UNAUTHORIZED,
          detail="Invalid token"
      )

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

# [회원가입] : 이메일 중복 체크
@app.post("/emailCheck")
def emailCheck(data: EmailModel):
    print(data.email)
    sql = f"SELECT COUNT(*) AS cnt FROM mini.user WHERE email = '{data.email}'"
    result = findOne(sql)
    count = result['cnt']
    if count > 0 :
      return {"status" : False, "msg": "가입된 이메일이 존재합니다."}
    return {"status" : True, "msg": "사용 가능한 이메일 입니다."}

# [회원가입]
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

# [로그인] : UUID + Redis 저장
@app.post("/login")
def producer(model: EmailModel , modelC: CodeModel):
  print(model.email)
  sql = f"select `user_no`, `name` from mini.user where `email` = '{model.email}'"
  data = findOne(sql)
  if not data:
      return {"status": False}
  
  loginId = str(uuid.uuid4())
  print(loginId)

  # code = str(random.randint(100000, 999999))

  client.set(
      f"login:{loginId}",
      json.dumps({
          "email": model.email,
          "id": modelC.id
      }),
      ex=180
  )

  pd.send(settings.kafka_topic, {
        "event": "login_request",
        "email": model.email,
        "loginId": modelC.loginId
    })
  pd.flush()

  # print("인증코드:", code)

  return {
      "status": True,
      "loginId": loginId
  }

# [로그인] : UUID 기반 검증 + JWT 발급
@app.post("/code")
def code(model: CodeModel, response: Response):

  key = f"login:{model.loginId}"
  data = client.get(key)

  if not data:
        return {"status": False, "msg": "만료 또는 잘못된 요청"}
  
  data = json.loads(data)

  if data["id"] != model.id:
    print(model.id)
    return {"status": False, "msg": "인증코드 불일치"}
  
  access_token = set_token(data["email"])

  if not access_token:
      return {"status": False}
  
  client.delete(key)

  response.set_cookie(
      key="access_token",
      value=access_token,
      httponly=True,
      secure=False,
      samesite="Lax",
      max_age=60 * settings.access_token_expire_minutes
  )

  pd.send(settings.kafka_topic, {
        "event": "login_success",
        "email": data["email"]
    })
  pd.flush()

  return {"status": True}

# [로그인] : JWT → DB 기록
@app.post("/me")
def me(payload = Depends(get_payload)):
  if not payload:
    return {"status" : False}
  user_no = payload.get("sub")
  sql = f"""
  INSERT INTO mini.login (`user_no`)
  VALUES ({user_no});
  """
  save(sql)
  if payload:
    print(user_no)
    return {"status": True, "user" : user_no}
  return {"status": False}

# [게시글 작성]
@app.post("/boardadd")
def board_add(data: boardInfo) :
    sqlSelect = f"""
    SELECT u.user_no, b.user_no 
    FROM user board.user_no AS b
    INNER JOIN user.user_no AS u
    ON(u.user_no = b.user_no)
    WHERE email = '{data.writer}'
    """
    userSelect = findOne(sqlSelect)

    if userSelect :
        find = userSelect['user_no']
        sqlInsert = f"""
                        INSERT INTO board (title, cnt, user_no)
                        VALUES ('{data.title}', '{data.content}', {find})
                    """
        print(find)
        if save(sqlInsert) :
            return {"status" : True, "msg" : "게시글 등록 성공"}
    return {"status" : False, "msg" : "게시물 등록 실패"}


@app.get("/")
def read_root():
  return {"Hello": "World"}
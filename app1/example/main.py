from fastapi.middleware.cors import CORSMiddleware
from db import findOne, findAll ,save
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
import math


app = FastAPI(title="Producer")

origins = [ "http://localhost:5173",
             "http://127.0.0.1:5173" ]
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
    writer : str
    
class BoardCreate(BaseModel):
    title: str
    content: str
    user_no: int

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

# [메인화면]
@app.get("/home")
def home(page: int = 1, size: int = 5, keyword: str = ""):
    offset = (page - 1) * size

    where = "WHERE b.delYn = 0"
    if keyword:
        where += f" AND b.title LIKE '%{keyword}%'"

    sql = f"""
        SELECT b.board_no, b.title, u.name, b.regDate
        FROM mini.board b
        JOIN mini.user u ON b.user_no = u.user_no
        {where}
        ORDER BY b.board_no DESC
        LIMIT {size} OFFSET {offset}
    """

    data = findAll(sql)

    countSql = f"""
        SELECT COUNT(*) AS cnt
        FROM mini.board b
        {where}
    """

    total = findOne(countSql)["cnt"]
    totalPages = math.ceil(total / size) if total > 0 else 1

    return {
        "status": True,
        "data": data,
        "totalPages": totalPages
    }

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
@app.post("/login") # POST /login 엔드포인트 생성
def producer(model: EmailModel):  #EmailModel(email 필드 있는 Pydantic 모델)을 받음
  print(model.email)  # 이메일 확인
  sql = f"select `user_no`, `name` from mini.user where `email` = '{model.email}'"  # DB에서 해당 이메일 유저 조회
  data = findOne(sql) # 유저 한 명 가져오기
  if not data:  # 유저 없으면 로그인 실패
      return {"status": False}
  
  loginId = str(uuid.uuid4().hex)   # 랜덤 로그인 식별자 생성 -> 인증번호 요청을 구분하기 위한 키
  print(loginId)

  # Kafka에 메시지 전송 : "이 이메일로 인증번호 생성해"
  pd.send(settings.kafka_topic, { 
        "event": "generate_code",
        "email": model.email,
        "loginId": loginId
    })
  pd.flush()  # Kafka 메시지 즉시 전송

  return {"status": True, "loginId": loginId} # 프론트에 loginId 반환 -> 이후 인증번호 검증할 때 필요


# [로그인] : UUID 기반 인증번호 검증 + JWT 발급
@app.post("/code")  # 인증번호 확인 API
def code(model: CodeModel, response: Response): # CodeModel(loginId + id(인증번호)) 받음, Response 객체로 쿠키 설정 가능

  # Redis에서 해당 loginId 데이터 조회
  key = f"login:{model.loginId}"
  storedData = client.get(key)

# Redis TTL 끝났거나 존재 안 하면 실패
  if not storedData:
        return {"status": False, "msg": "인증 시간 만료"}
  
  # JSON 문자열 → 딕셔너리 변환
  data = json.loads(storedData)

  # 사용자가 입력한 인증번호 비교
  if data["id"] != model.id:
    return {"status": False, "msg": "인증번호 불일치"}
  
  # JWT 생성
  access_token = set_token(data["email"])

  if not access_token:
    return {"status": False}
  
  # JWT를 쿠키에 저장
  response.set_cookie(
      key="access_token",
      value=access_token,
      httponly=True,
      secure=False,
      samesite="Lax",
      max_age=60 * settings.access_token_expire_minutes
  )

  # Redis에서 인증 데이터 삭제
  client.delete(key)
  return {"status": True} # 로그인 성공
 

# [로그인] : JWT → DB 기록
@app.post("/me")
def me(payload = Depends(get_payload)): # get_payload는 JWT 디코딩 함수, payload 자동 주입
  print(payload)  # 디코딩 결과 확인

  # 토큰이 없거나 위조면 실패
  if not payload:
    return {"status" : False}
  
  # JWT 안에 저장한 user_no 꺼냄
  user_no = payload.get("sub")

  # 로그인 기록 테이블에 저장
  sql = f"""
  INSERT INTO mini.login (`user_no`)
  VALUES ({user_no});
  """

  # DB 저장
  save(sql)
  if payload:
    print(user_no)
    return {"status": True, "user" : user_no} # 로그인 성공 + user_no 반환
  return {"status": False}

# 전체 흐름
# [1] 이메일 입력
#         ↓
# /login
#         ↓
# UUID 생성 + Kafka 전송
#         ↓
# Consumer가 인증번호 생성 + Redis 저장
#         ↓
# 사용자 인증번호 입력
#         ↓
# /code
#         ↓
# Redis 비교
#         ↓
# JWT 발급 (쿠키 저장)
#         ↓
# /me
#         ↓
# JWT 검증 → 로그인 기록 저장




# [게시글 작성]
@app.post("/boardadd")
def board_add(data: boardInfo) :
    # 이거 처음에 user_no로 비교해줄라고 했는데 이렇게 바꾼 이유: 처음 글쓴 사람은 user_no 일치 못함 ㅋㅋ
    sqlSelect = f"""
        SELECT user_no
        FROM mini.user
        WHERE email = '{data.writer}'
        AND delYn = 0
      """
    userSelect = findOne(sqlSelect)

    if userSelect :
        find = userSelect['user_no']
        sqlInsert = f"""
                        INSERT INTO mini.board (title, cnt, user_no)
                        VALUES ('{data.title}', '{data.content}', {find})
                    """
        print(find)
        if save(sqlInsert) :
            return {"status" : True, "msg" : "게시글 등록 성공"}
    return {"status" : False, "msg" : "게시물 등록 실패"}

@app.get("/")
def read_root():
  return {"Hello": "World"}
from fastapi.middleware.cors import CORSMiddleware
from db import findOne, save, add_key
from fastapi import FastAPI, Depends, HTTPException, status, Response, Request, File, UploadFile, Form
from kafka import KafkaProducer
from settings import settings
from pydantic import EmailStr, BaseModel
import json
import redis
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError, ExpiredSignatureError
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import urllib.parse
import base64
import uuid
import shutil
from pathlib import Path
from typing import List
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="Producer")

# 업로드한 파일 위치를 정하기위해 선언
# 이녀석이 있어야 프로필 파일 사진이 보임.... 
# 단, docker containers에 올릴때는 확인 필요....
# compose.yml 파일 참조!!!
# volumes:
#   uploads:
#   mysql:
app.mount(
    "/uploads",
    StaticFiles(directory="uploads"),
    name="uploads"
)

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


# 사용자 상세(사용자 불러오기)
@app.post("/selUser")
def usrt_delYn(request: Request):
  selectUser = request.cookies.get("selectUser")
  if not selectUser:
    return {"status": False, "msg": "회원정보를 불러오는데 실패하였습니다."}
  
  selectUser = base64Decode(selectUser)
  decoded = urllib.parse.unquote(selectUser)
  data = json.loads(decoded)
  sql =f"""
      SELECT A.`user_no` AS userNo, A.`name`, A.`email`, A.`gender`, A.`regDate`, A.`modDate`, B.`pro_no` AS proNo, B.`origin`, B.`fileName`
      FROM `mini`.`user` AS A
      INNER JOIN `mini`.`user_pr` AS B
        ON A.`pro_no` = B.`pro_no`
        AND A.`user_no` = B.`user_no`
      WHERE A.`email` = '{data["email"]}' AND A.`user_no` = '{data["user_no"]}';
    """
  if data: 
    data = findOne(sql)
  return {"status":data}

# 사용자 탈퇴(사용자 삭제)
@app.post("/userDelYn")
def usrt_delYn(request: Request):
  userInfo = request.cookies.get("userInfo")
  if not userInfo:
    return {"status": False, "msg": "탈퇴에 실패하였습니다."}
  
  userInfo = base64Decode(userInfo)
  decoded = urllib.parse.unquote(userInfo)
  data = json.loads(decoded)
  sql =f"""
      UPDATE mini.`user` 
      SET `delYn` = '{data["delYn"]}' 
      WHERE `user_no` = '{data["user_no"]}'
    """
  if data: 
    save(sql)
  return {"status":data, "msg": "탈퇴 되었습니다.\n감사합니다. 안녕히 가십시오."}

# 사용자 수정(사용자 정보 수정)
@app.post("/userUpdate")
def usrt_delYn(request: Request):
  userUp = request.cookies.get("userUp")
  if not userUp:
    return {"status": False, "msg": "수정에 실패하였습니다."}
  
  userUp = base64Decode(userUp)
  decoded = urllib.parse.unquote(userUp)
  data = json.loads(decoded)
  sql =f"""
      UPDATE mini.`user` SET
        `pro_no` = '{data["proNo"]}',
        `name` = '{data["name"]}',
        `email` = '{data["email"]}',
        `gender` = '{data["gender"]}'
      WHERE `user_no` = '{data["userNo"]}'
    """
  if data: 
    save(sql)
  return {"status":data, "msg": "수정이 완료되었습니다.\n감사합니다."}

# 프로필 업로드용으로 추가
UPLOAD_DIR = Path("uploads")
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}
MAX_FILE_SIZE = 10 * 1024

def checkDir():
  UPLOAD_DIR.mkdir(exist_ok=True)

# 파일 업로드 영역
def saveFile(file, userNo):
  checkDir()
  origin = file.filename
  ext = origin.split(".")[-1].lower()
  newName = f"{uuid.uuid4().hex}.{ext}"
  sql = f"""
        INSERT into mini.`user_pr` (`user_no`, `origin`, `ext`, `fileName`, `cntType`) 
        VALUE ('{userNo}', '{origin}', '{ext}', '{newName}', '{file.content_type}')
      """
  
  result = add_key(sql)
  if result[0]:
    path = UPLOAD_DIR / newName
    with path.open("wb") as f:
      shutil.copyfileobj(file.file, f)
    return result[1]
  return 0

# 최종 업로드
@app.post("/uploadFile")
def upload(files: List[UploadFile] = File(), userNo: int = Form()):
  sql = f"""
        SELECT `pro_no`
        FROM mini.`user_pr`
        WHERE `user_no` = '{userNo}'
        ORDER BY modDate DESC
        LIMIT 1;
      """
  arr = []
  for file in files:
    result = saveFile(file, userNo)
    if not result:
      return {"status": False, "msg": "프로필 등록에 실패하였습니다."}
    arr.append(result)
  # 파일 업로드 후 userNo를 이용하여 proNo를 불러와서 전달
  proNo = findOne(sql)
  return {"status": True, "result": arr, "proNo": proNo["pro_no"]}

# 사용자 화면에 전부 사용중
def base64Decode(data):
  encoded = urllib.parse.unquote(data)
  return base64.b64decode(encoded).decode("utf-8")
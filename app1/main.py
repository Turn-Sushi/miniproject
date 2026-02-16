from fastapi.middleware.cors import CORSMiddleware 
from fastapi.staticfiles import StaticFiles
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi import FastAPI, Depends, HTTPException, status, Response, Request, File, UploadFile, Form
from pydantic import EmailStr, BaseModel 
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError, ExpiredSignatureError
from kafka import KafkaProducer
from src.db import findOne, findAll, save, add_key
from src.settings import settings
from src import auth
from pathlib import Path
from typing import List
import urllib.parse
import base64
import json 
import redis
import uuid
import math
import shutil


# ================= CORS 설정 =================

app = FastAPI(title="Producer")

# 업로드한 파일 위치를 정하기위해 선언
# 이녀석이 있어야 프로필 파일 사진이 보임.... 
# 단, docker containers에 올릴때는 확인 필요....
# compose.yml 파일 참조!!!
# volumes:
#   uploads:
app.mount(
  "/uploads",
  StaticFiles(directory="uploads"),
  name="uploads"
)

origins = [ settings.react_url ]

app.add_middleware(
  CORSMiddleware,
  allow_origins=origins,
  allow_credentials=True,
  allow_methods=["*"],
  allow_headers=["*"],
)

app.include_router(auth.router)

security = HTTPBearer()

# ================= JWT 유틸리티 =================
# def set_token(email: str):
#   # f-string 방식으로 변경
#   # 게시판 사용하는 곳 확인 필요....
#   sql = f"SELECT `user_no` FROM mini.user WHERE `email` = '{email}'"
#   data = findOne(sql)

#   if not data: return None

#   iat = datetime.now(timezone.utc)
#   exp = iat + timedelta(minutes=settings.access_token_expire_minutes)
    
#   payload = {
#     "iss": "Team3",
#     "sub": str(data["user_no"]),
#     "iat": iat,
#     "exp": exp
#   }
#   return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)

def get_payloads(credentials: HTTPAuthorizationCredentials = Depends(security)):
  try:
    payload = jwt.decode(credentials.credentials, settings.secret_key, algorithms=[settings.algorithm])
    return payload
  except ExpiredSignatureError:
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
  except JWTError:
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")


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
    payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
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


# ================= 외부 서비스 연결 =================
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

# ================= 데이터 모델 (Pydantic) =================
class EmailModel(BaseModel):
  email: EmailStr

class CodeModel(BaseModel):
  loginId: str
  id: str

class UserInfo(BaseModel):
  name: str
  email: EmailStr
  gender: str

class CommentModel(BaseModel):
  board_no: int
  cnt: str

class BoardInfo(BaseModel):
  title : str
  content : str
  writer : str

class BoardCreate(BaseModel):
  title: str
  content: str
  user_no: int

# ================= API 엔드포인트 =================

# 1. 회원 관련 ====================================================================
# ================= [회원가입] : 이메일 중복 체크 =================
@app.post("/emailCheck")
def emailCheck(data: EmailModel):
  print(data.email)
  sql = f"SELECT COUNT(*) AS cnt FROM mini.`user` WHERE `email` = '{data.email}'"
  result = findOne(sql)
  count = result['cnt']
  if count > 0 :
    return {"status" : False, "msg": "가입된 이메일이 존재합니다."}
  return {"status" : True, "msg": "사용 가능한 이메일 입니다."}

# ======================== [회원가입] ========================
@app.post("/signup")
def signup(data: UserInfo):
  print(data)
  checkSql = f"SELECT COUNT(*) AS cnt FROM mini.`user` WHERE `email` = '{data.email}'"
  result = findOne(checkSql)
  count = result['cnt']
  if count > 0 :
    return {"status" : False, "msg": "가입된 이메일이 존재합니다."}
  
  insertSql = f"""
              INSERT INTO mini.`user` (`name`, `email`, `gender`)
              VALUES ('{data.name}', '{data.email}',  '{data.gender}')
            """
  save(insertSql)
  return {"status" : True, "msg" : "회원가입 성공"}


# ================= 회원 정보 상세(회원 정보 불러오기) =================
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

# ================= 회원 탈퇴(회원 삭제) =================
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

# ================= 회원 정보 수정 =================
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

# ================= 프로필 최종 업로드 =================
# 프로필 업로드시 필요한 부분
UPLOAD_DIR = Path("uploads")
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}
MAX_FILE_SIZE = 10 * 1024

def checkDir():
  UPLOAD_DIR.mkdir(exist_ok=True)

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

# 프로필 업로드
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

# 회원 정보 화면중 상세, 수정, 탈퇴에 사용중
def base64Decode(data):
  encoded = urllib.parse.unquote(data)
  return base64.b64decode(encoded).decode("utf-8")

# 2. 로그인 관련 ====================================================================
# ================= [로그인] : UUID + Redis 저장 =================
@app.post("/login")
def producer(model: EmailModel):
  print(model.email)
  sql = f"select `user_no`, `name` from mini.`user` where `email` = '{model.email}'"
  data = findOne(sql)
  if not data:
    return {"status": False}
  
  loginId = str(uuid.uuid4().hex)
  print(loginId)

  pd.send(settings.kafka_topic, {
    "event": "generate_code",
    "email": model.email,
    "loginId": loginId
  })
  pd.flush()

  return {"status": True, "loginId": loginId}


# ================= [로그인] : UUID 기반 검증 + JWT 발급 =================
@app.post("/code")
def code(model: CodeModel, response: Response):

  key = f"login:{model.loginId}"
  storedData = client.get(key)

  if not storedData:
        return {"status": False, "msg": "인증 시간 만료"}
  
  data = json.loads(storedData)

  if data["id"] != model.id:
    return {"status": False, "msg": "인증번호 불일치"}
  
  access_token = set_token(data["email"])

  if not access_token:
    return {"status": False}
  
  response.set_cookie(
    key="access_token",
    value=access_token,
    httponly=True,
    secure=False,
    samesite="Lax",
    max_age=60 * settings.access_token_expire_minutes
  )

  client.delete(key)
  return {"status": True}


# ================= [로그인] : JWT → DB 기록 =================
@app.post("/me")
def me(payload = Depends(get_payload)):
  print(payload)
  if not payload:
    return {"status" : False}
  user_no = payload.get("sub")
  sql = f"""
        INSERT INTO mini.`login` (`user_no`)
        VALUES ({user_no});
      """
  save(sql)
  if payload:
    print(user_no)
    return {"status": True, "user" : user_no}
  return {"status": False}

# # 1. 회원 관련
# @app.post("/signup")
# def signup(data: UserInfo):
#   sql = f"INSERT INTO mini.`user` (`name`, `email`, `gender`) VALUES ('{data.name}', '{data.email}', '{data.gender}')"
#   save(sql)
#   return {"status": True, "msg": "회원가입 성공"}

# @app.post("/login")
# def login(data: EmailModel):
#   sql = f"SELECT `user_no` FROM mini.`user` WHERE email = '{data.email}'"
#   user = findOne(sql)
#   if not user: return {"status": False, "msg": "유저를 찾을 수 없습니다."}

#   pd.send(settings.kafka_topic, dict(data))
#   pd.flush()
#   return {"status": True}

# 3. 게시판 관련
# @app.get("/board")
# def board_list():
#   sql = """
#         SELECT b.`board_no`, b.`title`, u.`name`, b.`regDate` 
#         FROM mini.`board` AS b 
#         JOIN mini.`user` AS u ON b.`user_no` = u.`user_no` 
#         WHERE b.`delYn` = 0 ORDER BY b.`board_no` DESC
#       """
#   return {"status": True, "data": findAll(sql)}

# 3. 게시판 관련 ====================================================================
# ================= 메인화면(게시판 목록) =================
@app.get("/home")
def home(page: int = 1, size: int = 5, keyword: str = ""):
    offset = (page - 1) * size

    where = "WHERE b.`delYn` = 0"
    if keyword:
        where += f" AND b.`title` LIKE '%{keyword}%'"

    sql = f"""
          SELECT b.`board_no`, b.`title`, u.`name`, b.`regDate`
          FROM mini.`board` AS b
          JOIN mini.`user` AS u ON b.`user_no` = u.`user_no`
          {where}
          ORDER BY b.`board_no` DESC
          LIMIT {size} OFFSET {offset}
        """

    data = findAll(sql)

    countSql = f"""
        SELECT COUNT(*) AS cnt
        FROM mini.`board` b
        {where}
    """

    total = findOne(countSql)["cnt"]
    totalPages = math.ceil(total / size) if total > 0 else 1

    return {
        "status": True,
        "data": data,
        "totalPages": totalPages
    }
    
# ================= 게시글 작성 =================
@app.post("/boardadd")
def board_add(data: BoardInfo) :
    # 이거 처음에 user_no로 비교해줄라고 했는데 이렇게 바꾼 이유: 처음 글쓴 사람은 user_no 일치 못함 ㅋㅋ
    sqlSelect = f"""
                SELECT `user_no`
                FROM mini.`user`
                WHERE `email` = '{data.writer}'
                AND `delYn` = 0
              """
    userSelect = findOne(sqlSelect)

    if userSelect :
        find = userSelect['user_no']
        sqlInsert = f"""
                    INSERT INTO mini.board (`title`, `cnt`, `user_no`)
                    VALUES ('{data.title}', '{data.content}', {find})
                  """
        print(find)
        if save(sqlInsert) :
            return {"status" : True, "msg" : "게시글 등록 성공"}
    return {"status" : False, "msg" : "게시물 등록 실패"}

# ================= 게시글 상세 조회 =================
@app.get("/board/{no}")
def get_board(no: int):
  sql = f"""
    SELECT b.`board_no`, b.`title`, b.`cnt`, u.`name`, b.`regDate`
    FROM mini.`board` AS b
    JOIN mini.`user` AS u ON b.`user_no` = u.`user_no`
    WHERE b.`board_no` = {no} AND b.`delYn` = 0
  """
  data = findOne(sql)
  if not data:
      return {"status": False, "msg": "게시글이 없습니다."}
  return {"status": True, "data": data}

# ================= 댓글 목록 조회 =================
# 프로필에 등록된 fileName과 origin을 불러오기 위해 JOIN 부분과 불러오는 컬럼 추가
@app.get("/comment")
def list_comments(board_no: int):
  sql = f"""
    SELECT c.`cnt_no`, c.`board_no`, c.`user_no`, c.`cnt`, c.`delYn`, u.`name`, c.`regDate`, p.`fileName`, p.`origin`
    FROM mini.`board_cnt` AS c
    JOIN mini.`user` AS u ON c.`user_no` = u.`user_no`
    JOIN mini.`user_pr` AS p ON c.`user_no` = p.`user_no`
    WHERE c.`board_no` = {board_no}
    ORDER BY c.`cnt_no` ASC
  """
  data = findAll(sql)
  return {"status": True, "data": data}

# ================= 댓글 삭제 =================
@app.delete("/comment/{id}")
def delete_comment(id: int, payload=Depends(get_payloads)):
  check_sql = f"SELECT `user_no` FROM mini.`board_cnt` WHERE `cnt_no` = {id} AND delYn = 0"
  comment = findOne(check_sql)
  if not comment or str(comment["user_no"]) != str(payload["sub"]):
    raise HTTPException(403, "권한이 없거나 댓글이 없습니다.")
    
  sql = f"UPDATE mini.`board_cnt` SET `delYn` = 1 WHERE `cnt_no` = {id}"
  save(sql)
  return {"status": True}

# ================= 댓글 수정 =================
@app.put("/comment/{id}")
def update_comment(id: int, data: dict, payload=Depends(get_payloads)):
  new_cnt = data.get("cnt", "").strip()
  if not new_cnt:
    return {"status": False, "msg": "댓글 내용이 비어있습니다."}

  check_sql = f"SELECT `user_no` FROM mini.`board_cnt` WHERE `cnt_no` = {id} AND delYn = 0"
  comment = findOne(check_sql)
  if not comment or str(comment["user_no"]) != str(payload["sub"]):
    raise HTTPException(403, "권한이 없거나 댓글이 없습니다.")

  sql = f"UPDATE mini.`board_cnt` SET `cnt` = '{new_cnt}' WHERE `cnt_no` = {id}"
  save(sql)
  return {"status": True}
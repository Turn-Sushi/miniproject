from fastapi import FastAPI, Depends, HTTPException, status 
from fastapi.middleware.cors import CORSMiddleware 
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials 
from pydantic import EmailStr, BaseModel 
from datetime import datetime, timedelta, timezone
import json 
import redis 
from jose import jwt, JWTError, ExpiredSignatureError
from db import findOne, findAll, save
from kafka import KafkaProducer
from settings import settings

app = FastAPI(title="Mini Project API")

# ================= CORS 설정 =================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:80", "http://localhost:5173", "http://localhost"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBearer()

# ================= JWT 유틸리티 =================
def set_token(email: str):
    # f-string 방식으로 변경
    sql = f"SELECT user_no FROM mini.user WHERE email = '{email}'"
    data = findOne(sql)

    if not data: return None

    iat = datetime.now(timezone.utc)
    exp = iat + timedelta(minutes=settings.access_token_expire_minutes)
    
    payload = {
        "iss": "Team3",
        "sub": str(data["user_no"]),
        "iat": iat,
        "exp": exp
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)

def get_payload(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, settings.secret_key, algorithms=[settings.algorithm])
        return payload
    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

# ================= 외부 서비스 연결 =================
producer = KafkaProducer(
    bootstrap_servers=settings.kafka_server,
    value_serializer=lambda v: json.dumps(v).encode("utf-8")
)

redis_client = redis.Redis(
    host=settings.redis_host, port=settings.redis_port, 
    db=settings.redis_db, decode_responses=True
)

# ================= 데이터 모델 (Pydantic) =================
class EmailModel(BaseModel):
    email: EmailStr

class CodeModel(BaseModel):
    id: str

class UserInfo(BaseModel):
    name: str
    email: EmailStr
    gender: str

class BoardModel(BaseModel):
    title: str
    cont: str

class CommentModel(BaseModel):
    board_no: int
    cnt: str

# ================= API 엔드포인트 =================

# 1. 회원 관련
@app.post("/signup")
def signup(data: UserInfo):
    sql = f"INSERT INTO mini.user (name, email, gender) VALUES ('{data.name}', '{data.email}', '{data.gender}')"
    save(sql)
    return {"status": True, "msg": "회원가입 성공"}

@app.post("/login")
def login(data: EmailModel):
    sql = f"SELECT user_no FROM mini.user WHERE email = '{data.email}'"
    user = findOne(sql)
    if not user: return {"status": False, "msg": "유저를 찾을 수 없습니다."}
    
    producer.send(settings.kafka_topic, dict(data))
    producer.flush()
    return {"status": True}

# 2. 게시판 관련
@app.get("/board")
def board_list():
    sql = """
        SELECT b.board_no, b.title, u.name, b.regDate 
        FROM mini.board b 
        JOIN mini.user u ON b.user_no = u.user_no 
        WHERE b.delYn = 0 ORDER BY b.board_no DESC
    """
    return {"status": True, "data": findAll(sql)}
# ================= 게시글 상세 조회 =================
@app.get("/board/{no}")
def get_board(no: int):
    sql = f"""
        SELECT b.board_no, b.title, b.cnt, u.name, b.regDate
        FROM mini.board b
        JOIN mini.user u ON b.user_no = u.user_no
        WHERE b.board_no = {no} AND b.delYn = 0
    """
    data = findOne(sql)
    if not data:
        return {"status": False, "msg": "게시글이 없습니다."}
    return {"status": True, "data": data}

# ================= 댓글 목록 조회 =================
@app.get("/comment")
def list_comments(board_no: int):
    sql = f"""
        SELECT c.cnt_no, c.board_no, c.user_no, c.cnt, c.delYn, u.name, c.regDate
        FROM mini.board_cnt c
        JOIN mini.user u ON c.user_no = u.user_no
        WHERE c.board_no = {board_no}
        ORDER BY c.cnt_no ASC
    """
    data = findAll(sql)
    return {"status": True, "data": data}

# ================= 댓글 삭제 =================
@app.delete("/comment/{id}")
def delete_comment(id: int, payload=Depends(get_payload)):
    check_sql = f"SELECT user_no FROM mini.board_cnt WHERE cnt_no = {id} AND delYn = 0"
    comment = findOne(check_sql)
    if not comment or str(comment["user_no"]) != str(payload["sub"]):
        raise HTTPException(403, "권한이 없거나 댓글이 없습니다.")
    
    sql = f"UPDATE mini.board_cnt SET delYn = 1 WHERE cnt_no = {id}"
    save(sql)
    return {"status": True}

# ================= 댓글 수정 =================
@app.put("/comment/{id}")
def update_comment(id: int, data: dict, payload=Depends(get_payload)):
    new_cnt = data.get("cnt", "").strip()
    if not new_cnt:
        return {"status": False, "msg": "댓글 내용이 비어있습니다."}

    check_sql = f"SELECT user_no FROM mini.board_cnt WHERE cnt_no = {id} AND delYn = 0"
    comment = findOne(check_sql)
    if not comment or str(comment["user_no"]) != str(payload["sub"]):
        raise HTTPException(403, "권한이 없거나 댓글이 없습니다.")

    sql = f"UPDATE mini.board_cnt SET cnt = '{new_cnt}' WHERE cnt_no = {id}"
    save(sql)
    return {"status": True}

from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import EmailStr, BaseModel
from db import findOne, findAll, save
from kafka import KafkaProducer
from settings import settings
from jose import jwt, JWTError, ExpiredSignatureError
from datetime import datetime, timedelta, timezone
import json
import redis

app = FastAPI(title="Mini Project API")

# ================= CORS =================
origins = [
            "http://localhost:80",
            "http://localhost:5173",
            "http://localhost",
          ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ================= JWT =================
security = HTTPBearer()

def set_token(email: str):
    sql = f"SELECT user_no FROM mini.user WHERE email = '{email}'"
    data = findOne(sql)

    if not data:
        return None

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
        payload = jwt.decode(
            credentials.credentials,
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


# ================= Kafka & Redis =================
producer = KafkaProducer(
    bootstrap_servers=settings.kafka_server,
    value_serializer=lambda v: json.dumps(v).encode("utf-8")
)

redis_client = redis.Redis(
    host=settings.redis_host,
    port=settings.redis_port,
    db=settings.redis_db,
    decode_responses=True
)

# ================= 회원 =================

class EmailModel(BaseModel):
    email: EmailStr

class CodeModel(BaseModel):
    id: str

class UserInfo(BaseModel):
    name: str
    email: EmailStr
    gender: str


@app.post("/emailCheck")
def email_check(data: EmailModel):
    sql = f"SELECT COUNT(*) AS cnt FROM mini.user WHERE email = '{data.email}'"
    result = findOne(sql)

    if result["cnt"] > 0:
        return {"status": False, "msg": "이미 가입된 이메일입니다."}

    return {"status": True, "msg": "사용 가능한 이메일입니다."}


@app.post("/signup")
def signup(data: UserInfo):
    sql = f"""
        INSERT INTO mini.user (name, email, gender)
        VALUES ('{data.name}', '{data.email}', '{data.gender}')
    """
    save(sql)
    return {"status": True, "msg": "회원가입 성공"}


@app.post("/login")
def login(data: EmailModel):
    sql = f"SELECT user_no FROM mini.user WHERE email = '{data.email}'"
    user = findOne(sql)

    if not user:
        return {"status": False}

    producer.send(settings.kafka_topic, dict(data))
    producer.flush()

    return {"status": True}


@app.post("/code")
def code(data: CodeModel):
    result = redis_client.get(data.id)

    if not result:
        return {"status": False}

    token = set_token(result)

    if token:
        redis_client.delete(data.id)
        return {"status": True, "access_token": token}

    return {"status": False}


@app.get("/me")
def me(payload=Depends(get_payload)):
    return {"status": True, "user_no": payload["sub"]}


# ================= 게시판 =================

class BoardCreate(BaseModel):
    title: str
    cont: str

@app.get("/board")
def board_list():
    sql = """
        SELECT b.board_no, b.title, u.name, b.regDate
        FROM mini.board b
        JOIN mini.user u ON b.user_no = u.user_no
        WHERE b.delYn = 0
        ORDER BY b.board_no DESC
    """
    rows = findAll(sql)
    return {"status": True, "data": rows}


@app.post("/board")
def create_board(data: BoardCreate, payload=Depends(get_payload)):
    user_no = payload["sub"]
    sql = f"""
        INSERT INTO mini.board (title, cont, user_no, delYn)
        VALUES ('{data.title}', '{data.cont}', {user_no}, 0)
    """
    save(sql)
    return {"status": True}

@app.put("/board/{no}")
def update_board(no: int, data: BoardCreate, payload=Depends(get_payload)):
    user_no = payload["sub"]
    post = findOne(f"""
        SELECT user_no FROM mini.board
        WHERE board_no = {no} AND delYn = 0
      """)
    if not post:
        raise HTTPException(404, "게시글이 없습니다.")
    if str(post["user_no"]) != str(user_no):
        raise HTTPException(403, "작성자가 아닙니다.")
    sql = f"""
        UPDATE mini.board
        SET title = '{data.title}',
            cont = '{data.cont}'
        WHERE board_no = {no}
    """
    save(sql)
    return {"status": True}

@app.delete("/board/{no}")
def delete_board(no: int, payload=Depends(get_payload)):
    user_no = payload["sub"]
    post = findOne(f"""
        SELECT user_no FROM mini.board
        WHERE board_no = {no} AND delYn = 0
    """)
    if not post:
        raise HTTPException(404, "게시글이 없습니다.")
    if str(post["user_no"]) != str(user_no):
        raise HTTPException(403, "작성자가 아닙니다.")
    sql = f"""
        UPDATE mini.board SET delYn = 1 WHERE board_no = {no}
      """
    save(sql)
    return {"status": True}


# ================= 댓글 =================
class CommentCreate(BaseModel):
    board_no: int
    cnt: str

@app.get("/comment")
def get_comments(board_no: int):
    sql = f"""
        SELECT bc.cnt_no, bc.board_no, bc.user_no,
               bc.cnt, bc.regDate, u.name
        FROM mini.board_cnt bc
        JOIN mini.user u ON bc.user_no = u.user_no
        WHERE bc.board_no = {board_no}
          AND bc.delYn = 0
        ORDER BY bc.cnt_no ASC
      """
    rows = findAll(sql)
    return {"status": True, "data": rows}

@app.post("/comment")
def create_comment(data: CommentCreate, payload=Depends(get_payload)):
    user_no = payload["sub"]
    sql = f"""
        INSERT INTO mini.board_cnt (board_no, user_no, cnt, delYn)
        VALUES ({data.board_no}, {user_no}, '{data.cnt}', 0)
      """
    save(sql)
    return {"status": True}

@app.put("/comment/{no}")
def update_comment(no: int, data: CommentCreate, payload=Depends(get_payload)):
    user_no = payload["sub"]
    comment = findOne(f"""
        SELECT user_no FROM mini.board_cnt
        WHERE cnt_no = {no} AND delYn = 0
    """)
    if not comment:
        raise HTTPException(404, "댓글이 없습니다.")
    if str(comment["user_no"]) != str(user_no):
        raise HTTPException(403, "작성자가 아닙니다.")
    sql = f"""
        UPDATE mini.board_cnt
        SET cnt = '{data.cnt}'
        WHERE cnt_no = {no}
    """
    save(sql)
    return {"status": True}

@app.delete("/comment/{no}")
def delete_comment(no: int, payload=Depends(get_payload)):
    user_no = payload["sub"]
    comment = findOne(f"""
        SELECT user_no FROM mini.board_cnt
        WHERE cnt_no = {no} AND delYn = 0
    """)
    if not comment:
        raise HTTPException(404, "댓글이 없습니다.")

    if str(comment["user_no"]) != str(user_no):
        raise HTTPException(403, "작성자가 아닙니다.")

    sql = f"""
        UPDATE mini.board_cnt SET delYn = 1 WHERE cnt_no = {no}
    """
    save(sql)
    return {"status": True}

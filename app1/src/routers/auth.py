from fastapi import APIRouter, Response, Depends
from src.models.baseModel import EmailModel, CodeModel
from src.core.db import findOne, save
from src.core.kafka import pd
from src.core.redis import client
from src.core.jwt import set_token, get_payload2
from src.settings import settings
import uuid
import json

router = APIRouter()

# ================= [로그인] : UUID + Redis 저장 =================
@router.post("/login")
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
@router.post("/code")
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
@router.post("/me")
def me(result = Depends(get_payload2)):
  if result["status"]:
    user_no = result["payload"].get("sub")
    
    sql = f"""
          SELECT u.`user_no`, IFNULL(up.`fileName`, '') AS fileName
          FROM  mini.`user` AS u 
          LEFT OUTER JOIN mini.`user_pr` AS up
            ON (u.`pro_no` = up.`pro_no`)
          WHERE  u.`user_no` = '{user_no}'
        """
    data = findOne(sql)
    if data:
      sql = f"""
            INSERT INTO mini.`login` (`user_no`)
            VALUES ({user_no});
          """
      save(sql)
      return {"status": True, "user" : user_no, "fileName": data['fileName']}
  return result
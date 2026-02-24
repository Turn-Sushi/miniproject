from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError, ExpiredSignatureError
from fastapi import HTTPException, status, Request
from src.core.db import findOne
from src.settings import settings

# ================= JWT 유틸리티 =================

def set_token(email: str):
  try:
    sql = f"""
      SELECT u.`user_no`, IFNULL(up.`fileName`, '') AS fileName
        FROM  mini.`user` AS u 
        LEFT OUTER JOIN mini.`user_pr` AS up
          ON (u.`pro_no` = up.`pro_no`)
        WHERE  u.`email` = '{email}'
    """
    data = findOne(sql)
    if data:
      iat = datetime.now(timezone.utc)
      exp = iat + (timedelta(minutes=settings.access_token_expire_minutes))
      data = {
        "iss": "Team3",
        "sub": str(data["user_no"]),
        "pro": str(data["fileName"]),
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
    raise HTTPException(status_code=401, detail="Token expired")

  except JWTError:
    raise HTTPException(status_code=401, detail="Invalid token")
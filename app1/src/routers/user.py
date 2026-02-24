from fastapi import APIRouter, Depends, Response, Request, File, UploadFile, Form
from typing import List
from pathlib import Path
import uuid
import shutil
import base64
import urllib.parse
import json

from src.core.db import findOne, save, add_key
from src.models.baseModel import EmailModel, UserInfo
from src.core.jwt import get_payload

router = APIRouter()

# ================= 프로필 업로드 설정 =================

UPLOAD_DIR = Path("uploads")
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}
MAX_FILE_SIZE = 10 * 1024


# ================= 디렉토리 체크 =================
def checkDir():
  UPLOAD_DIR.mkdir(exist_ok=True)


# ================= 파일 저장 =================
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


# ================= base64 디코드 =================
def base64Decode(data):
  encoded = urllib.parse.unquote(data)
  return base64.b64decode(encoded).decode("utf-8")


# ================= [회원가입] : 이메일 중복 체크 =================
@router.post("/emailCheck")
def emailCheck(data: EmailModel):
  sql = f"SELECT COUNT(*) AS cnt FROM mini.`user` WHERE `email` = '{data.email}'"
  result = findOne(sql)
  count = result['cnt']
  if count > 0 :
    return {"status" : False, "msg": "가입된 이메일이 존재합니다."}
  return {"status" : True, "msg": "사용 가능한 이메일 입니다."}


# ======================== 회원가입 ========================
@router.post("/signup")
def signup(data: UserInfo):
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


# ================= 회원 정보 상세 =================
@router.post("/selUser")
def usrt_view(payload = Depends(get_payload)):
  user_no = payload.get("sub")

  sql = f"""
        SELECT u.`user_no` AS userNo, u.`name`, u.`email`, u.`gender`, 
          DATE_FORMAT(u.`regDate`, '%Y-%m-%d %H:%i:%s') as regDate, 
          DATE_FORMAT(u.`modDate`, '%Y-%m-%d %H:%i:%s') as modDate, 
          up.`pro_no` AS proNo, 
          up.`origin`, up.`fileName`
        FROM `mini`.`user` AS u
        LEFT JOIN `mini`.`user_pr` AS up 
          ON (u.`pro_no` = up.`pro_no`)
        WHERE u.`user_no` = '{user_no}';
      """

  data = findOne(sql)

  if data:
    return {"status": data}
  else:
    return {"status": False, "msg": "회원 정보를 찾을 수 없습니다."}


# ================= 회원 탈퇴 =================
@router.post("/userDelYn")
def usrt_delYn(payload = Depends(get_payload), response: Response = None):
  if not payload:
    return {"status": False, "msg": "탈퇴에 실패하였습니다."}
  
  user_no = payload.get("sub")
  
  sql = f"""
        UPDATE mini.`user` 
        SET `delYn` = 1 
        WHERE `user_no` = {user_no}
      """
  save(sql)
  response.delete_cookie(key="access_token")

  return {"status":True, "msg": "탈퇴 되었습니다.\n감사합니다. 안녕히 가십시오."}


# ================= 회원 정보 수정 =================
@router.post("/userUpdate")
def usrt_update(request: Request):
  userUp = request.cookies.get("userUp")

  if not userUp:
    return {"status": False, "msg": "수정에 실패하였습니다."}
  
  userUp = base64Decode(userUp)
  decoded = urllib.parse.unquote(userUp)
  data = json.loads(decoded)

  sql = f"""
        UPDATE mini.`user` SET
          `pro_no` = '{data["proNo"]}',
          `name` = '{data["name"]}',
          `email` = '{data["email"]}',
          `gender` = '{data["gender"]}'
        WHERE `user_no` = '{data["userNo"]}'
      """

  if data: 
    save(sql)
    return {"status": True, "msg": "수정이 완료되었습니다.\n감사합니다."}
  return {"status": False, "msg": "수정에 실패하였습니다."}


# ================= 프로필 업로드 =================
@router.post("/uploadFile")
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
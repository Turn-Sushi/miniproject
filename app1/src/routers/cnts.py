from fastapi import APIRouter, Depends, HTTPException
from src.models.baseModel import CommentModel
from src.core.jwt import get_payload
from src.core.db import save, findAll, findOne

router = APIRouter()

# ================= 댓글 목록 조회 =================
# 프로필에 등록된 fileName과 origin을 불러오기 위해 JOIN 부분과 불러오는 컬럼 추가
@router.get("/comment")
def list_comments(board_no: int):
  sql = f"""
        SELECT c.`cnt_no`, c.`board_no`, c.`user_no`, c.`cnt`, c.`delYn`, 
          u.`name`, c.`regDate`, c.`modDate`, p.`fileName`, p.`origin`
        FROM mini.`board_cnt` AS c
        JOIN mini.`user` AS u 
          ON c.`user_no` = u.`user_no`
        LEFT JOIN (
          SELECT *
          FROM (
            SELECT *,
              ROW_NUMBER() OVER (PARTITION BY user_no ORDER BY modDate DESC) AS rn
            FROM mini.`user_pr`
          ) t
          WHERE t.rn = 1
        ) p ON c.`user_no` = p.`user_no`
        WHERE c.`board_no` = {board_no}
        ORDER BY c.`cnt_no` ASC;
      """
  data = findAll(sql)
  return {"status": True, "data": data}


# ================= 댓글 등록 =================
# 댓글 작성을 위한 API 엔드포인트 추가
@router.post("/comment")
def add_comment(data: CommentModel, payload = Depends(get_payload)):
    user_no = payload.get("sub")
    
    # 디버깅을 위한 출력
    print(f"댓글 작성 시도: 유저 {user_no}, 게시글 {data.board_no}")

    sql = f"""
          INSERT INTO mini.`board_cnt` (`board_no`, `user_no`, `cnt`)
          VALUES ('{data.board_no}', '{user_no}', '{data.cnt}')
        """
    
    try:
      # DB에 저장 시도
      save(sql) 
      return {"status": True, "msg": "댓글이 등록되었습니다."}
    except Exception as e:
      # 만약 에러가 난다면 여기서 원인을 출력해줍니다.
      print(f"DEBUG: SQL 실행 실패! 원인: {e}")
      return {"status": False, "msg": str(e)}


# ================= 댓글 삭제 =================
@router.delete("/comment/{id}")
def delete_comment(id: int, payload=Depends(get_payload)):
  check_sql = f"SELECT `user_no` FROM mini.`board_cnt` WHERE `cnt_no` = {id} AND `delYn` = 0"
  comment = findOne(check_sql)
  if not comment or str(comment["user_no"]) != str(payload["sub"]):
    raise HTTPException(403, "권한이 없거나 댓글이 없습니다.")

  sql = f"UPDATE mini.`board_cnt` SET `delYn` = 1 WHERE `cnt_no` = {id}"
  save(sql)
  return {"status": True}


# ================= 댓글 수정 =================
@router.put("/comment/{id}")
def update_comment(id: int, data: dict, payload=Depends(get_payload)):
  new_cnt = data.get("cnt", "").strip()
  if not new_cnt:
    return {"status": False, "msg": "댓글 내용이 비어있습니다."}

  check_sql = f"SELECT `user_no` FROM mini.`board_cnt` WHERE `cnt_no` = {id} AND `delYn` = 0"
  comment = findOne(check_sql)
  if not comment or str(comment["user_no"]) != str(payload["sub"]):
    raise HTTPException(403, "권한이 없거나 댓글이 없습니다.")

  sql = f"UPDATE mini.`board_cnt` SET `cnt` = '{new_cnt}' WHERE `cnt_no` = {id}"
  save(sql)
  return {"status": True}
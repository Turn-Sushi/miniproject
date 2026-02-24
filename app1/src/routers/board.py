from fastapi import APIRouter, Depends
from src.models.baseModel import BoardCreate
from src.core.db import findAll, findOne, save
from src.core.jwt import get_payload
import math

router = APIRouter()

# ================= 메인화면(게시판 목록) =================
@router.get("/home")
def home(page: int = 1, size: int = 5, keyword: str = ""):
    offset = (page - 1) * size

    where = "WHERE b.`delYn` = 0"
    if keyword:
        where += f" AND b.`title` LIKE '%{keyword}%'"

    sql = f"""
          SELECT b.`board_no`, b.`title`, u.`name`, DATE_FORMAT(b.`regDate`, '%Y-%m-%d ') as regDate, b.`delYn`
          FROM mini.`board` AS b
          JOIN mini.`user` AS u ON b.`user_no` = u.`user_no`
          {where}
          ORDER BY b.`board_no` DESC
          LIMIT {size} OFFSET {offset}
        """
# DATE_FORMAT(b.`regDate`, '%Y-%m-%d %H:%i:%s') as regDate
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
@router.post("/boardadd")
def board_add(data: BoardCreate, payload = Depends(get_payload)) :
    # 이거 처음에 user_no로 비교해줄라고 했는데 이렇게 바꾼 이유: 처음 글쓴 사람은 user_no 일치 못함 ㅋㅋ
    user_no = payload.get("sub")

    if user_no :
        sqlInsert = f"""
                    INSERT INTO mini.`board` (`title`, `cnt`, `user_no`)
                    VALUES ('{data.title}', '{data.content}', {user_no})
                  """
        if save(sqlInsert) :
            return {"status" : True, "msg" : "게시글 등록 성공"}
    return {"status" : False, "msg" : "게시물 등록 실패"}


# ================= 게시글 상세 조회 =================
@router.get("/board/{no}")
def get_board(no: int):
  sql = f"""
    SELECT b.`board_no`, b.`title`, b.`cnt`, u.`name`, DATE_FORMAT(b.`regDate`, '%Y-%m-%d %H:%i:%s') as regDate, b.`user_no`
    FROM mini.`board` AS b
    JOIN mini.`user` AS u ON b.`user_no` = u.`user_no`
    WHERE b.`board_no` = {no} AND b.`delYn` = 0
  """
  data = findOne(sql)
  if not data:
      return {"status": False, "msg": "게시글이 없습니다."}
  return {"status": True, "data": data}


# ================= 게시글 수정 =================
@router.put("/board/{no}")
def update_board(no: int, data: dict, payload = Depends(get_payload)):
    # 1. 로그인한 유저 정보 가져오기
    login_user = payload.get("sub")
    # 2. 수정하려는 게시글의 실제 작성자 확인
    check_sql = f"SELECT `user_no` FROM mini.`board` WHERE `board_no` = {no} AND `delYn` = 0"
    board = findOne(check_sql)
    if not board:
        return {"status": False, "msg": "존재하지 않는 게시글입니다."}
    # 3. 작성자 본인인지 검증 (문자열 비교 방지를 위해 둘 다 str로 변환)
    if str(board['user_no']) != str(login_user):
        return {"status": False, "msg": "수정 권한이 없습니다. 본인 글만 수정 가능합니다."}

    # 1. 전달받은 데이터 추출
    title = data.get('title')
    cnt = data.get('cnt')
    
    # 디버깅 로그
    # print(f"DEBUG: 게시글 {no}번 수정 시도 - 제목: {title}")
    
    # 2. f-string을 이용한 SQL문 작성
    # 문자열 파라미터(title, cnt)는 반드시 '{변수}' 처럼 따옴표로 감싸야 합니다.
    sql = f"""
          UPDATE mini.`board` 
          SET `title` = '{title}', 
            `cnt` = '{cnt}' 
          WHERE `board_no` = {no}
        """

    try:
        save(sql) # 파라미터 없이 쿼리만 전달
        return {"status": True, "msg": "수정 성공"}
    except Exception as e:
        print(f"SQL Error: {e}")
        return {"status": False, "msg": "DB 수정 중 오류가 발생했습니다."}


# ================= 게시물 삭제 =================
@router.delete("/board/{no}")
def delete_board(no: int, payload = Depends(get_payload)):
  login_user = payload.get("sub")

  check_sql = f"SELECT `user_no` FROM mini.`board` WHERE `board_no` = {no} AND `delYn` = 0"
  board = findOne(check_sql)
  if not board:
      return {"status": False, "msg": "존재하지 않는 게시글입니다."}
  if str(board['user_no']) != str(login_user):
      return {"status": False, "msg": "수정 권한이 없습니다. 본인 글만 수정 가능합니다."}

  sql = f"""
        UPDATE mini.`board` SET `delYn` = 1 WHERE `board_no` = {no} 
      """
  save(sql)
  return {"status": True}
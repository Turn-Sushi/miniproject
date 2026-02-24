from pydantic import BaseModel, EmailStr

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

class BoardCreate(BaseModel):
  title: str
  content: str
  user_no: int = None
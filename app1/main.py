from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi import FastAPI
from src.settings import settings

from src.routers import user, auth, board, cnt

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

# ================= Router 등록 =================
app.include_router(user.router)
app.include_router(auth.router)
app.include_router(board.router)
app.include_router(cnt.router)
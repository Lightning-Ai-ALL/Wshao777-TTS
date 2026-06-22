from fastapi import FastAPI
from api.control_tower_api import router as control_tower_router

app = FastAPI(title="Lightning Control Tower")
app.include_router(control_tower_router)

# 其他既有路由...
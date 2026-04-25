"""
多Agent图书管理系统 - FastAPI主应用
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import settings
from app.database import init_db
from app.agents import coordinator
from app.routers import books, users, borrows, analytics
from app.api import agents


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时初始化数据库
    init_db()
    await coordinator.start()
    print(f"{settings.APP_NAME} v{settings.APP_VERSION} 已启动")
    try:
        yield
    finally:
        # 关闭时清理资源
        await coordinator.stop()
        print("系统关闭中...")


# 创建FastAPI应用
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="基于多Agent架构的智能图书管理系统",
    lifespan=lifespan
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(books.router, prefix="/api", tags=["图书管理"])
app.include_router(users.router, prefix="/api", tags=["用户管理"])
app.include_router(borrows.router, prefix="/api", tags=["借阅管理"])
app.include_router(analytics.router, prefix="/api", tags=["数据分析"])
app.include_router(agents.router, prefix="/api", tags=["多Agent系统"])


@app.get("/")
async def root():
    """根路径"""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "运行中",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy"}

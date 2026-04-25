"""
用户管理API路由
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from pydantic import BaseModel
import hashlib

from app.database import get_db
from app.models.user import User, UserRole
from app.models.borrow_record import BorrowRecord
from app.agents import coordinator

router = APIRouter(prefix="/users", tags=["用户管理"])


def _unwrap_agent_result(result: dict, default_status: int = 400) -> dict:
    """统一处理协调器结果，兼容业务错误与异常错误。"""
    if result.get("status") in {"error", "timeout", "failed"}:
        raise HTTPException(status_code=default_status, detail=result.get("error", "请求失败"))

    payload = result.get("result", {})
    if isinstance(payload, dict) and payload.get("status") == "error":
        raise HTTPException(status_code=default_status, detail=payload.get("error", "请求失败"))

    if isinstance(payload, dict) and "error" in payload:
        raise HTTPException(status_code=default_status, detail=payload["error"])

    return payload


class UserCreate(BaseModel):
    """创建用户请求"""
    username: str
    email: str
    password: str
    full_name: Optional[str] = None
    phone: Optional[str] = None


class UserUpdate(BaseModel):
    """更新用户请求"""
    email: Optional[str] = None
    full_name: Optional[str] = None
    phone: Optional[str] = None
    is_active: Optional[bool] = None


class UserResponse(BaseModel):
    """用户响应"""
    id: int
    username: str
    email: str
    full_name: Optional[str]
    phone: Optional[str]
    role: str
    is_active: bool
    total_borrowed: int
    current_borrowed: int
    
    class Config:
        from_attributes = True


@router.get("/", response_model=List[UserResponse])
async def get_users(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db)
):
    """获取用户列表"""
    users = db.query(User).offset((page - 1) * size).limit(size).all()
    return [user.to_dict() for user in users]


@router.post("/", response_model=UserResponse)
async def create_user(user_data: UserCreate, db: Session = Depends(get_db)):
    """创建新用户"""
    # 检查用户名是否已存在
    existing_user = db.query(User).filter(User.username == user_data.username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="用户名已存在")
    
    # 检查邮箱是否已存在
    existing_email = db.query(User).filter(User.email == user_data.email).first()
    if existing_email:
        raise HTTPException(status_code=400, detail="邮箱已被注册")
    
    # 创建新用户
    user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hashlib.sha256(user_data.password.encode("utf-8")).hexdigest(),
        full_name=user_data.full_name,
        phone=user_data.phone,
        role=UserRole.READER
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return user.to_dict()


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: int, db: Session = Depends(get_db)):
    """获取用户详情"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    return user.to_dict()


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int, 
    user_data: UserUpdate, 
    db: Session = Depends(get_db)
):
    """更新用户信息"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    # 更新字段
    update_data = user_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        if hasattr(user, field):
            setattr(user, field, value)
    
    db.commit()
    db.refresh(user)
    
    return user.to_dict()


@router.get("/{user_id}/borrow-history")
async def get_user_borrow_history(
    user_id: int,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """获取用户借阅历史"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    records = (
        db.query(BorrowRecord)
        .filter(BorrowRecord.user_id == user_id)
        .order_by(BorrowRecord.borrow_date.desc())
        .offset((page - 1) * size)
        .limit(size)
        .all()
    )

    return {
        "user_id": user_id,
        "total": db.query(BorrowRecord).filter(BorrowRecord.user_id == user_id).count(),
        "page": page,
        "size": size,
        "items": [
            {
                **record.to_dict(),
                "book_title": record.book.title if record.book else None,
                "book_author": record.book.author if record.book else None,
                "user_name": user.full_name or user.username,
            }
            for record in records
        ],
    }


@router.get("/{user_id}/recommendations")
async def get_user_recommendations(
    user_id: int,
    limit: int = Query(10, ge=1, le=50)
):
    """获取用户个性化推荐"""
    result = await coordinator.delegate_task(
        task_type="recommend",
        task_data={
            "user_id": user_id,
            "limit": limit
        },
        preferred_agent="RecommendAgent"
    )
    
    return _unwrap_agent_result(result)

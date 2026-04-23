"""
借阅管理API路由
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from pydantic import BaseModel

from app.database import get_db
from app.models.borrow_record import BorrowRecord, BorrowStatus
from app.agents import coordinator

router = APIRouter(prefix="/borrows", tags=["借阅管理"])


def _unwrap_agent_result(result: dict, default_status: int = 400) -> dict:
    """统一处理协调器结果，兼容业务错误与异常错误。"""
    if result.get("status") == "error":
        raise HTTPException(status_code=default_status, detail=result.get("error", "请求失败"))

    payload = result.get("result", {})
    if isinstance(payload, dict) and "error" in payload:
        raise HTTPException(status_code=default_status, detail=payload["error"])

    return payload


class BorrowCreateRequest(BaseModel):
    """借书请求"""
    user_id: int
    book_id: int
    notes: Optional[str] = None


class BorrowReturnRequest(BaseModel):
    """还书请求"""
    borrow_id: int
    notes: Optional[str] = None


class BorrowRenewRequest(BaseModel):
    """续借请求"""
    borrow_id: int


class BorrowResponse(BaseModel):
    """借阅记录响应"""
    id: int
    user_id: int
    book_id: int
    borrow_date: str
    due_date: str
    return_date: Optional[str]
    renew_count: int
    status: str
    fine_amount: float
    fine_paid: bool
    notes: Optional[str]
    
    class Config:
        from_attributes = True


@router.post("/", response_model=dict)
async def borrow_book(borrow_data: BorrowCreateRequest):
    """借书"""
    result = await coordinator.delegate_task(
        task_type="borrow_book",
        task_data={
            "user_id": borrow_data.user_id,
            "book_id": borrow_data.book_id,
            "notes": borrow_data.notes
        },
        preferred_agent="BookAgent"
    )

    return _unwrap_agent_result(result)


@router.put("/return", response_model=dict)
async def return_book(return_data: BorrowReturnRequest):
    """还书"""
    result = await coordinator.delegate_task(
        task_type="return_book",
        task_data={
            "borrow_id": return_data.borrow_id,
            "notes": return_data.notes
        },
        preferred_agent="BookAgent"
    )

    return _unwrap_agent_result(result)


@router.put("/renew", response_model=dict)
async def renew_book(renew_data: BorrowRenewRequest):
    """续借"""
    result = await coordinator.delegate_task(
        task_type="renew_book",
        task_data={
            "borrow_id": renew_data.borrow_id
        },
        preferred_agent="BookAgent"
    )

    return _unwrap_agent_result(result)


@router.get("/", response_model=List[dict])
async def list_borrows(
    user_id: Optional[int] = Query(None, description="按用户筛选"),
    status: Optional[str] = Query(None, description="状态筛选"),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """获取借阅记录列表（支持按用户筛选）"""
    query = db.query(BorrowRecord)

    if user_id is not None:
        query = query.filter(BorrowRecord.user_id == user_id)

    if status:
        query = query.filter(BorrowRecord.status == BorrowStatus(status))

    borrows = query.order_by(BorrowRecord.borrow_date.desc()).offset(
        (page - 1) * size
    ).limit(size).all()

    result = []
    for borrow in borrows:
        item = borrow.to_dict()
        item["user_name"] = borrow.user.full_name if borrow.user else None
        item["book_title"] = borrow.book.title if borrow.book else None
        result.append(item)

    return result


@router.get("/user/{user_id}", response_model=List[dict])
async def get_user_borrows(
    user_id: int,
    status: Optional[str] = Query(None, description="状态筛选"),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """获取用户借阅记录"""
    query = db.query(BorrowRecord).filter(BorrowRecord.user_id == user_id)
    
    if status:
        query = query.filter(BorrowRecord.status == BorrowStatus(status))
    
    borrows = query.order_by(BorrowRecord.borrow_date.desc()).offset(
        (page - 1) * size
    ).limit(size).all()
    
    result = []
    for borrow in borrows:
        item = borrow.to_dict()
        item["user_name"] = borrow.user.full_name if borrow.user else None
        item["book_title"] = borrow.book.title if borrow.book else None
        result.append(item)

    return result


@router.get("/overdue", response_model=List[dict])
async def get_overdue_books(db: Session = Depends(get_db)):
    """获取逾期图书列表"""
    overdue_records = db.query(BorrowRecord).filter(
        BorrowRecord.status == BorrowStatus.OVERDUE
    ).all()
    
    result = []
    for record in overdue_records:
        item = record.to_dict()
        item["user_name"] = record.user.full_name if record.user else None
        item["book_title"] = record.book.title if record.book else None
        result.append(item)

    return result


@router.post("/check-overdue")
async def check_overdue():
    """检查逾期图书"""
    result = await coordinator.delegate_task(
        task_type="check_overdue",
        task_data={},
        preferred_agent="BookAgent"
    )

    return _unwrap_agent_result(result)

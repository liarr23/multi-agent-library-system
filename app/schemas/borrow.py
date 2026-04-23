"""
借阅相关的Pydantic schemas
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class BorrowStatus(str, Enum):
    """借阅状态枚举"""
    BORROWED = "borrowed"
    RETURNED = "returned"
    OVERDUE = "overdue"
    RENEWED = "renewed"


class BorrowCreate(BaseModel):
    """创建借阅记录"""
    user_id: int = Field(..., description="用户ID")
    book_id: int = Field(..., description="图书ID")
    notes: Optional[str] = Field(None, max_length=500, description="备注")


class BorrowReturn(BaseModel):
    """归还图书"""
    borrow_id: int = Field(..., description="借阅记录ID")
    notes: Optional[str] = Field(None, max_length=500, description="备注")


class BorrowRenew(BaseModel):
    """续借图书"""
    borrow_id: int = Field(..., description="借阅记录ID")


class BorrowResponse(BaseModel):
    """借阅记录响应"""
    id: int
    user_id: int
    book_id: int
    borrow_date: datetime
    due_date: datetime
    return_date: Optional[datetime]
    renew_count: int
    status: BorrowStatus
    fine_amount: float
    fine_paid: bool
    notes: Optional[str]
    created_at: datetime
    
    # 关联的图书和用户信息
    book_title: Optional[str] = None
    book_author: Optional[str] = None
    user_name: Optional[str] = None
    
    class Config:
        from_attributes = True


class BorrowListResponse(BaseModel):
    """借阅列表响应"""
    total: int
    items: List[BorrowResponse]
    page: int
    size: int


class OverdueInfo(BaseModel):
    """逾期信息"""
    borrow_id: int
    book_title: str
    user_name: str
    due_date: datetime
    days_overdue: int
    fine_amount: float

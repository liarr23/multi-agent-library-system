"""
图书相关的Pydantic schemas
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class BookBase(BaseModel):
    """图书基础schema"""
    isbn: str = Field(..., min_length=10, max_length=20, description="ISBN号")
    title: str = Field(..., min_length=1, max_length=200, description="书名")
    author: str = Field(..., min_length=1, max_length=100, description="作者")
    publisher: Optional[str] = Field(None, max_length=100, description="出版社")
    publish_date: Optional[datetime] = Field(None, description="出版日期")
    category: Optional[str] = Field(None, max_length=50, description="分类")
    description: Optional[str] = Field(None, description="描述")
    price: float = Field(0.0, ge=0, description="价格")
    total_copies: int = Field(1, ge=1, description="总册数")


class BookCreate(BookBase):
    """创建图书的schema"""
    pass


class BookUpdate(BaseModel):
    """更新图书的schema"""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    author: Optional[str] = Field(None, min_length=1, max_length=100)
    publisher: Optional[str] = Field(None, max_length=100)
    publish_date: Optional[datetime] = None
    category: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = None
    price: Optional[float] = Field(None, ge=0)
    total_copies: Optional[int] = Field(None, ge=1)
    is_active: Optional[bool] = None


class BookResponse(BookBase):
    """图书响应schema"""
    id: int
    available_copies: int
    avg_rating: float
    rating_count: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class BookListResponse(BaseModel):
    """图书列表响应"""
    total: int
    items: List[BookResponse]
    page: int
    size: int

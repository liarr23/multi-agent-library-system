"""
图书数据模型
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database import Base


class Book(Base):
    """图书模型"""
    __tablename__ = "books"
    
    id = Column(Integer, primary_key=True, index=True)
    isbn = Column(String(20), unique=True, index=True, nullable=False)
    title = Column(String(200), nullable=False, index=True)
    author = Column(String(100), nullable=False, index=True)
    publisher = Column(String(100))
    publish_date = Column(DateTime)
    category = Column(String(50), index=True)
    description = Column(Text)
    price = Column(Float, default=0.0)
    
    # 库存信息
    total_copies = Column(Integer, default=1)
    available_copies = Column(Integer, default=1)
    
    # 评分信息
    avg_rating = Column(Float, default=0.0)
    rating_count = Column(Integer, default=0)
    
    # 状态
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
        # 关系
    borrow_records = relationship("BorrowRecord", back_populates="book")
    ratings = relationship("Rating", back_populates="book")
    
    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "isbn": self.isbn,
            "title": self.title,
            "author": self.author,
            "publisher": self.publisher,
            "publish_date": self.publish_date,
            "category": self.category,
            "description": self.description,
            "price": self.price,
            "total_copies": self.total_copies,
            "available_copies": self.available_copies,
            "avg_rating": self.avg_rating,
            "rating_count": self.rating_count,
            "is_active": self.is_active,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }

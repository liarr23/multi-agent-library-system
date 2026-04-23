"""
评分数据模型
"""
from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database import Base


class Rating(Base):
    """评分模型"""
    __tablename__ = "ratings"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # 外键关联
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    book_id = Column(Integer, ForeignKey("books.id"), nullable=False, index=True)
    
    # 评分信息
    score = Column(Float, nullable=False)  # 1-5分
    comment = Column(Text)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # 关系
    user = relationship("User", back_populates="ratings")
    book = relationship("Book", back_populates="ratings")
    
    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "book_id": self.book_id,
            "score": self.score,
            "comment": self.comment,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

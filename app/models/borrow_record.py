"""
借阅记录数据模型
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, Boolean, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.database import Base


class BorrowStatus(str, enum.Enum):
    """借阅状态枚举"""
    BORROWED = "borrowed"      # 已借出
    RETURNED = "returned"      # 已归还
    OVERDUE = "overdue"        # 逾期
    RENEWED = "renewed"        # 已续借


class BorrowRecord(Base):
    """借阅记录模型"""
    __tablename__ = "borrow_records"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # 外键关联
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    book_id = Column(Integer, ForeignKey("books.id"), nullable=False, index=True)
    
    # 借阅信息
    borrow_date = Column(DateTime, default=datetime.now, nullable=False)
    due_date = Column(DateTime, nullable=False)
    return_date = Column(DateTime)
    
    # 续借信息
    renew_count = Column(Integer, default=0)
    last_renew_date = Column(DateTime)
    
    # 状态
    status = Column(SQLEnum(BorrowStatus), default=BorrowStatus.BORROWED)
    
    # 罚款信息
    fine_amount = Column(Float, default=0.0)
    fine_paid = Column(Boolean, default=False)
    
    # 备注
    notes = Column(String(500))
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # 关系
    user = relationship("User", back_populates="borrow_records")
    book = relationship("Book", back_populates="borrow_records")
    
    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "book_id": self.book_id,
            "borrow_date": self.borrow_date.isoformat() if self.borrow_date else None,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "return_date": self.return_date.isoformat() if self.return_date else None,
            "renew_count": self.renew_count,
            "status": self.status.value,
            "fine_amount": self.fine_amount,
            "fine_paid": self.fine_paid,
            "notes": self.notes
        }

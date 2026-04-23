"""
用户数据模型
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.database import Base


class UserRole(str, enum.Enum):
    """用户角色枚举"""
    READER = "reader"  # 普通读者
    ADMIN = "admin"    # 管理员


class User(Base):
    """用户模型"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(200), nullable=False)
    full_name = Column(String(100))
    phone = Column(String(20))
    
    # 角色和状态
    role = Column(SQLEnum(UserRole), default=UserRole.READER)
    is_active = Column(Boolean, default=True)
    
    # 统计信息
    total_borrowed = Column(Integer, default=0)
    current_borrowed = Column(Integer, default=0)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # 关系
    borrow_records = relationship("BorrowRecord", back_populates="user")
    ratings = relationship("Rating", back_populates="user")
    
    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "full_name": self.full_name,
            "phone": self.phone,
            "role": self.role.value,
            "is_active": self.is_active,
            "total_borrowed": self.total_borrowed,
            "current_borrowed": self.current_borrowed
        }

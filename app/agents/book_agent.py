"""
图书管理Agent - 处理图书CRUD和借阅归还逻辑
"""
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.agents.base_agent import BaseAgent, AgentMessage
from app.models.book import Book
from app.models.user import User
from app.models.borrow_record import BorrowRecord, BorrowStatus
from app.config import settings


class BookAgent(BaseAgent):
    """图书管理Agent"""
    
    def __init__(self):
                super().__init__(
            name="BookAgent",
            description="负责图书管理、借阅归还、库存管理等核心业务"
        )
    
    async def process_message(self, message: AgentMessage) -> Any:
        """处理消息"""
        content = message.content
        task_type = content.get("task_type")
        task_data = content.get("data")
        
        # 更新处理状态
        await self._update_status()
        
        self.log_action(f"处理任务: {task_type}", task_data)
        
        try:
            if task_type == "book_search":
                return await self.search_books(task_data)
            elif task_type == "book_create":
                return await self.create_book(task_data)
            elif task_type == "book_update":
                return await self.update_book(task_data)
            elif task_type == "book_delete":
                return await self.delete_book(task_data)
            elif task_type == "book_detail":
                return await self.get_book_detail(task_data)
            elif task_type == "borrow_book":
                return await self.borrow_book(task_data)
            elif task_type == "return_book":
                return await self.return_book(task_data)
            elif task_type == "renew_book":
                return await self.renew_book(task_data)
            elif task_type == "check_overdue":
                return await self.check_overdue_books()
            else:
                return {"error": f"未知任务类型: {task_type}"}
        except Exception as e:
            return await self.handle_error(e, f"处理任务 {task_type}")
    
    async def search_books(self, params: Dict) -> Dict:
        """搜索图书"""
        db = self.get_db_session()
        try:
            query = db.query(Book).filter(Book.is_active == True)
            
            # 关键词搜索
            keyword = params.get("keyword")
            if keyword:
                query = query.filter(
                    or_(
                        Book.title.ilike(f"%{keyword}%"),
                        Book.author.ilike(f"%{keyword}%"),
                        Book.isbn.ilike(f"%{keyword}%")
                    )
                )
            
            # 分类筛选
            category = params.get("category")
            if category:
                query = query.filter(Book.category == category)
            
                        # 分页
            page = params.get("page", 1)
            size = params.get("size", 20)
            total = query.count()
            books = query.offset((page - 1) * size).limit(size).all()
            
            return {
                "total": total,
                "items": [book.to_dict() for book in books],
                "page": page,
                "size": size
            }
        finally:
            db.close()
    
    async def create_book(self, params: Dict) -> Dict:
        """创建图书"""
        db = self.get_db_session()
        try:
            # 检查ISBN是否已存在
            existing = db.query(Book).filter(Book.isbn == params["isbn"]).first()
            if existing:
                return {"error": "ISBN已存在", "existing_book": existing.to_dict()}
            
            # 处理日期格式
            publish_date = params.get("publish_date")
            if publish_date and isinstance(publish_date, str):
                try:
                    from datetime import datetime as dt
                    publish_date = dt.strptime(publish_date, "%Y-%m-%d")
                except ValueError:
                    try:
                        publish_date = dt.strptime(publish_date, "%Y-%m-%dT%H:%M:%S")
                    except ValueError:
                        publish_date = None
            
            book = Book(
                isbn=params["isbn"],
                title=params["title"],
                author=params["author"],
                publisher=params.get("publisher"),
                publish_date=publish_date,
                category=params.get("category"),
                description=params.get("description"),
                price=params.get("price", 0.0),
                total_copies=params.get("total_copies", 1),
                available_copies=params.get("total_copies", 1)
            )
            
            db.add(book)
            db.commit()
            db.refresh(book)
            
            self.log_action("创建图书成功", book.to_dict())
            return {"status": "success", "book": book.to_dict()}
        finally:
            db.close()
    
    async def update_book(self, params: Dict) -> Dict:
        """更新图书信息"""
        db = self.get_db_session()
        try:
            book_id = params.pop("book_id")
            book = db.query(Book).filter(Book.id == book_id).first()
            
            if not book:
                return {"error": "图书不存在"}
            
            # 更新字段
            for key, value in params.items():
                if hasattr(book, key) and key not in ["id", "created_at"]:
                    setattr(book, key, value)
            
            book.updated_at = datetime.now()
            db.commit()
            db.refresh(book)
            
            self.log_action("更新图书成功", book.to_dict())
            return {"status": "success", "book": book.to_dict()}
        finally:
            db.close()
    
    async def delete_book(self, params: Dict) -> Dict:
        """删除图书（软删除）"""
        db = self.get_db_session()
        try:
            book_id = params["book_id"]
            book = db.query(Book).filter(Book.id == book_id).first()
            
            if not book:
                return {"error": "图书不存在"}
            
            # 检查是否有未归还的借阅
            active_borrows = db.query(BorrowRecord).filter(
                and_(
                    BorrowRecord.book_id == book_id,
                    BorrowRecord.status.in_([BorrowStatus.BORROWED, BorrowStatus.RENEWED])
                )
            ).count()
            
            if active_borrows > 0:
                return {"error": "该图书有未归还的借阅记录，无法删除"}
            
            # 软删除
            book.is_active = False
            book.updated_at = datetime.now()
            db.commit()
            
            self.log_action("删除图书成功", {"book_id": book_id})
            return {"status": "success", "message": "图书已删除"}
        finally:
            db.close()
    
    async def get_book_detail(self, params: Dict) -> Dict:
        """获取图书详情"""
        db = self.get_db_session()
        try:
            book_id = params["book_id"]
            book = db.query(Book).filter(Book.id == book_id).first()
            
            if not book:
                return {"error": "图书不存在"}
            
            # 获取最近的借阅记录
            recent_borrows = db.query(BorrowRecord).filter(
                BorrowRecord.book_id == book_id
            ).order_by(BorrowRecord.borrow_date.desc()).limit(5).all()
            
            result = book.to_dict()
            result["recent_borrows"] = [br.to_dict() for br in recent_borrows]
            
            return result
        finally:
            db.close()
    
    async def borrow_book(self, params: Dict) -> Dict:
        """借书"""
        db = self.get_db_session()
        try:
            user_id = params["user_id"]
            book_id = params["book_id"]
            
            # 检查用户
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return {"error": "用户不存在"}

            if not user.is_active:
                return {"error": "用户已被停用，无法借阅"}
            
            # 检查借阅数量限制
            if user.current_borrowed >= settings.MAX_BORROW_COUNT:
                return {"error": f"已达到最大借阅数量 ({settings.MAX_BORROW_COUNT}本)"}
            
            # 检查图书
            book = db.query(Book).filter(Book.id == book_id).first()
            if not book:
                return {"error": "图书不存在"}

            if not book.is_active:
                return {"error": "图书已下架，无法借阅"}
            
            if book.available_copies <= 0:
                return {"error": "图书已全部借出"}
            
            # 检查是否已有未归还的借阅
            existing_borrow = db.query(BorrowRecord).filter(
                and_(
                    BorrowRecord.user_id == user_id,
                    BorrowRecord.book_id == book_id,
                    BorrowRecord.status.in_([BorrowStatus.BORROWED, BorrowStatus.RENEWED])
                )
            ).first()
            
            if existing_borrow:
                return {"error": "您已借阅此图书，请先归还"}
            
            # 创建借阅记录
            borrow_record = BorrowRecord(
                user_id=user_id,
                book_id=book_id,
                due_date=datetime.now() + timedelta(days=settings.MAX_BORROW_DAYS),
                status=BorrowStatus.BORROWED,
                notes=params.get("notes")
            )
            
            # 更新库存和用户统计
            book.available_copies -= 1
            user.current_borrowed += 1
            user.total_borrowed += 1
            
            db.add(borrow_record)
            db.commit()
            db.refresh(borrow_record)
            
            self.log_action("借书成功", {
                "user_id": user_id,
                "book_id": book_id,
                "due_date": borrow_record.due_date.isoformat()
            })
            
            return {
                "status": "success",
                "borrow_record": borrow_record.to_dict(),
                "book": book.to_dict(),
                "message": f"借阅成功，请于 {borrow_record.due_date.strftime('%Y-%m-%d')} 前归还"
            }
        finally:
            db.close()
    
    async def return_book(self, params: Dict) -> Dict:
        """还书"""
        db = self.get_db_session()
        try:
            borrow_id = params["borrow_id"]
            
            borrow_record = db.query(BorrowRecord).filter(BorrowRecord.id == borrow_id).first()
            if not borrow_record:
                return {"error": "借阅记录不存在"}
            
            if borrow_record.status == BorrowStatus.RETURNED:
                return {"error": "该图书已归还"}
            
            # 计算罚款
            fine_amount = 0.0
            if datetime.now() > borrow_record.due_date:
                days_overdue = (datetime.now() - borrow_record.due_date).days
                fine_amount = days_overdue * settings.FINE_PER_DAY
            
            # 更新借阅记录
            borrow_record.status = BorrowStatus.RETURNED
            borrow_record.return_date = datetime.now()
            borrow_record.fine_amount = fine_amount
            
            # 更新库存和用户统计
            book = db.query(Book).filter(Book.id == borrow_record.book_id).first()
            book.available_copies += 1
            
            user = db.query(User).filter(User.id == borrow_record.user_id).first()
            user.current_borrowed -= 1
            
            db.commit()
            db.refresh(borrow_record)
            
            result = {
                "status": "success",
                "borrow_record": borrow_record.to_dict(),
                "message": "归还成功"
            }
            
            if fine_amount > 0:
                result["fine"] = {
                    "amount": fine_amount,
                    "days_overdue": days_overdue,
                    "message": f"逾期{days_overdue}天，罚款{fine_amount}元"
                }
            
            self.log_action("还书成功", result)
            return result
        finally:
            db.close()
    
    async def renew_book(self, params: Dict) -> Dict:
        """续借"""
        db = self.get_db_session()
        try:
            borrow_id = params["borrow_id"]
            
            borrow_record = db.query(BorrowRecord).filter(BorrowRecord.id == borrow_id).first()
            if not borrow_record:
                return {"error": "借阅记录不存在"}
            
            if borrow_record.status == BorrowStatus.RETURNED:
                return {"error": "该图书已归还，无法续借"}
            
            # 检查续借次数限制
            if borrow_record.renew_count >= 2:
                return {"error": "已达最大续借次数（2次）"}
            
            # 检查是否逾期
            if datetime.now() > borrow_record.due_date:
                return {"error": "图书已逾期，请先归还"}
            
            # 续借
            borrow_record.due_date = borrow_record.due_date + timedelta(days=settings.MAX_BORROW_DAYS)
            borrow_record.renew_count += 1
            borrow_record.last_renew_date = datetime.now()
            borrow_record.status = BorrowStatus.RENEWED
            
            db.commit()
            db.refresh(borrow_record)
            
            self.log_action("续借成功", {
                "borrow_id": borrow_id,
                "new_due_date": borrow_record.due_date.isoformat()
            })
            
            return {
                "status": "success",
                "borrow_record": borrow_record.to_dict(),
                "message": f"续借成功，新的归还日期为 {borrow_record.due_date.strftime('%Y-%m-%d')}"
            }
        finally:
            db.close()
    
    async def check_overdue_books(self) -> Dict:
        """检查逾期图书"""
        db = self.get_db_session()
        try:
            overdue_records = db.query(BorrowRecord).filter(
                and_(
                    BorrowRecord.status.in_([BorrowStatus.BORROWED, BorrowStatus.RENEWED]),
                    BorrowRecord.due_date < datetime.now()
                )
            ).all()
            
            # 更新状态为逾期
            for record in overdue_records:
                record.status = BorrowStatus.OVERDUE
                days_overdue = (datetime.now() - record.due_date).days
                record.fine_amount = days_overdue * settings.FINE_PER_DAY
            
            db.commit()
            
            # 获取详细信息
            overdue_details = []
            for record in overdue_records:
                book = db.query(Book).filter(Book.id == record.book_id).first()
                user = db.query(User).filter(User.id == record.user_id).first()
                
                overdue_details.append({
                    "borrow_id": record.id,
                    "book_title": book.title if book else "未知",
                    "user_name": user.full_name if user else "未知",
                    "due_date": record.due_date.isoformat(),
                    "days_overdue": (datetime.now() - record.due_date).days,
                    "fine_amount": record.fine_amount
                })
            
            self.log_action("检查逾期完成", {"count": len(overdue_details)})
            
            return {
                "status": "success",
                "overdue_count": len(overdue_details),
                "overdue_details": overdue_details
            }
        finally:
            db.close()

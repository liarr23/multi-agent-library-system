"""
数据分析Agent - 负责借阅统计、热门分析、趋势预测和报表生成
"""
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, desc

from app.agents.base_agent import BaseAgent, AgentMessage
from app.models.book import Book
from app.models.user import User
from app.models.borrow_record import BorrowRecord, BorrowStatus
from app.models.rating import Rating


class AnalyticsAgent(BaseAgent):
    """数据分析Agent"""

    def __init__(self):
        super().__init__(
            name="AnalyticsAgent",
            description="负责系统概览、借阅统计、热门分析、趋势预测和报表生成"
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
            if task_type == "analytics_overview":
                return await self.get_system_overview(task_data)
            elif task_type == "analytics_popular":
                return await self.get_popular_books(task_data)
            elif task_type == "analytics_trends":
                return await self.get_borrow_trends(task_data)
            elif task_type == "generate_report":
                return await self.generate_analytics_report(task_data)
            elif task_type == "user_activity":
                return await self.get_user_activity(task_data)
            elif task_type == "category_stats":
                return await self.get_category_statistics(task_data)
            else:
                return {"error": f"未知任务类型: {task_type}"}
        except Exception as e:
            return await self.handle_error(e, f"处理任务 {task_type}")
    
    async def get_system_overview(self, params: Dict) -> Dict:
        """获取系统概览统计"""
        db = self.get_db_session()
        try:
            # 图书统计
            total_books = db.query(Book).filter(Book.is_active == True).count()
            total_copies = db.query(func.sum(Book.total_copies)).filter(
                Book.is_active == True
            ).scalar() or 0
            available_copies = db.query(func.sum(Book.available_copies)).filter(
                Book.is_active == True
            ).scalar() or 0
            
            # 用户统计
            total_users = db.query(User).filter(User.is_active == True).count()
            active_users = db.query(User).filter(
                and_(
                    User.is_active == True,
                    User.current_borrowed > 0
                )
            ).count()
            
            # 借阅统计
            total_borrows = db.query(BorrowRecord).count()
            current_borrows = db.query(BorrowRecord).filter(
                BorrowRecord.status.in_([BorrowStatus.BORROWED, BorrowStatus.RENEWED])
            ).count()
            overdue_count = db.query(BorrowRecord).filter(
                BorrowRecord.status == BorrowStatus.OVERDUE
            ).count()
            
            # 评分统计
            total_ratings = db.query(Rating).count()
            avg_rating = db.query(func.avg(Rating.score)).scalar() or 0
            
            # 今日统计
            today = datetime.now().date()
            today_borrows = db.query(BorrowRecord).filter(
                func.date(BorrowRecord.borrow_date) == today
            ).count()
            today_returns = db.query(BorrowRecord).filter(
                and_(
                    BorrowRecord.return_date.isnot(None),
                    func.date(BorrowRecord.return_date) == today
                )
            ).count()
            
            return {
                "status": "success",
                "overview": {
                    "books": {
                        "total_titles": total_books,
                        "total_copies": total_copies,
                        "available_copies": available_copies,
                        "borrowed_copies": total_copies - available_copies
                    },
                    "users": {
                        "total_users": total_users,
                        "active_users": active_users
                    },
                    "borrows": {
                        "total_all_time": total_borrows,
                        "current_active": current_borrows,
                        "overdue": overdue_count,
                        "today_borrows": today_borrows,
                        "today_returns": today_returns
                    },
                    "ratings": {
                        "total_ratings": total_ratings,
                        "average_rating": round(avg_rating, 2)
                    }
                }
            }
        finally:
            db.close()
    
    async def get_popular_books(self, params: Dict) -> Dict:
        """获取热门图书"""
        db = self.get_db_session()
        try:
            days = params.get("days", 30)
            limit = params.get("limit", 10)
            
            start_date = datetime.now() - timedelta(days=days)
            
            # 按借阅次数排序
            popular_by_borrows = db.query(
                Book.id,
                Book.title,
                Book.author,
                Book.category,
                Book.avg_rating,
                func.count(BorrowRecord.id).label('borrow_count')
            ).join(
                BorrowRecord, Book.id == BorrowRecord.book_id
            ).filter(
                and_(
                    Book.is_active == True,
                    BorrowRecord.borrow_date >= start_date
                )
            ).group_by(Book.id).order_by(
                desc('borrow_count')
            ).limit(limit).all()
            
            # 按评分排序（需要至少5个评分）
            popular_by_rating = db.query(
                Book.id,
                Book.title,
                Book.author,
                Book.category,
                Book.avg_rating,
                Book.rating_count,
                func.count(Rating.id).label('recent_ratings')
            ).join(
                Rating, Book.id == Rating.book_id
            ).filter(
                and_(
                    Book.is_active == True,
                    Book.rating_count >= 5,
                    Rating.created_at >= start_date
                )
            ).group_by(Book.id).order_by(
                Book.avg_rating.desc()
            ).limit(limit).all()
            
            return {
                "status": "success",
                "period_days": days,
                "popular_by_borrows": [
                    {
                        "id": b.id,
                        "title": b.title,
                        "author": b.author,
                        "category": b.category,
                        "avg_rating": b.avg_rating,
                        "borrow_count": b.borrow_count
                    }
                    for b in popular_by_borrows
                ],
                "popular_by_rating": [
                    {
                        "id": b.id,
                        "title": b.title,
                        "author": b.author,
                        "category": b.category,
                        "avg_rating": b.avg_rating,
                        "rating_count": b.rating_count,
                        "recent_ratings": b.recent_ratings
                    }
                    for b in popular_by_rating
                ]
            }
        finally:
            db.close()
    
    async def get_borrow_trends(self, params: Dict) -> Dict:
        """获取借阅趋势"""
        db = self.get_db_session()
        try:
            days = params.get("days", 30)
            
            start_date = datetime.now() - timedelta(days=days)
            
            # 每日借阅数量
            daily_borrows = db.query(
                func.date(BorrowRecord.borrow_date).label('date'),
                func.count(BorrowRecord.id).label('count')
            ).filter(
                BorrowRecord.borrow_date >= start_date
            ).group_by(
                func.date(BorrowRecord.borrow_date)
            ).order_by('date').all()
            
            # 每日归还数量
            daily_returns = db.query(
                func.date(BorrowRecord.return_date).label('date'),
                func.count(BorrowRecord.id).label('count')
            ).filter(
                and_(
                    BorrowRecord.return_date.isnot(None),
                    BorrowRecord.return_date >= start_date
                )
            ).group_by(
                func.date(BorrowRecord.return_date)
            ).order_by('date').all()
            
            # 按分类统计
            category_trends = db.query(
                Book.category,
                func.count(BorrowRecord.id).label('borrow_count')
            ).join(
                BorrowRecord, Book.id == BorrowRecord.book_id
            ).filter(
                BorrowRecord.borrow_date >= start_date
            ).group_by(Book.category).order_by(
                desc('borrow_count')
            ).all()
            
            # 转换为字典格式
            trends = {
                "daily_borrows": {str(d.date): d.count for d in daily_borrows},
                "daily_returns": {str(d.date): d.count for d in daily_returns},
                "category_distribution": {c.category or "未分类": c.borrow_count for c in category_trends}
            }
            
            # 计算统计摘要
            total_borrows = sum(trends["daily_borrows"].values())
            avg_daily = total_borrows / days if days > 0 else 0
            
            return {
                "status": "success",
                "period_days": days,
                "trends": trends,
                "summary": {
                    "total_borrows": total_borrows,
                    "average_daily": round(avg_daily, 2),
                    "peak_day": max(trends["daily_borrows"].items(), key=lambda x: x[1]) if trends["daily_borrows"] else None
                }
            }
        finally:
            db.close()
    
    async def get_user_activity(self, params: Dict) -> Dict:
        """获取用户活跃度分析"""
        db = self.get_db_session()
        try:
            days = params.get("days", 30)
            limit = params.get("limit", 10)
            
            start_date = datetime.now() - timedelta(days=days)
            
            # 最活跃用户（按借阅数量）
            most_active = db.query(
                User.id,
                User.username,
                User.full_name,
                func.count(BorrowRecord.id).label('borrow_count')
            ).join(
                BorrowRecord, User.id == BorrowRecord.user_id
            ).filter(
                BorrowRecord.borrow_date >= start_date
            ).group_by(User.id).order_by(
                desc('borrow_count')
            ).limit(limit).all()
            
            # 用户活跃度分布
            activity_distribution = db.query(
                User.current_borrowed
            ).filter(User.is_active == True).all()
            
            # 计算活跃度分布
            distribution = {
                "no_borrow": 0,
                "1-3_books": 0,
                "4-6_books": 0,
                "7+_books": 0
            }
            
            for user in activity_distribution:
                if user.current_borrowed == 0:
                    distribution["no_borrow"] += 1
                elif user.current_borrowed <= 3:
                    distribution["1-3_books"] += 1
                elif user.current_borrowed <= 6:
                    distribution["4-6_books"] += 1
                else:
                    distribution["7+_books"] += 1
            
            return {
                "status": "success",
                "period_days": days,
                "most_active_users": [
                    {
                        "id": u.id,
                        "username": u.username,
                        "full_name": u.full_name,
                        "borrow_count": u.borrow_count
                    }
                    for u in most_active
                ],
                "activity_distribution": distribution
            }
        finally:
            db.close()
    
    async def get_category_statistics(self, params: Dict) -> Dict:
        """获取分类统计"""
        db = self.get_db_session()
        try:
            # 图书分类统计
            book_categories = db.query(
                Book.category,
                func.count(Book.id).label('book_count'),
                func.sum(Book.total_copies).label('total_copies'),
                func.sum(Book.available_copies).label('available_copies')
            ).filter(
                Book.is_active == True
            ).group_by(Book.category).all()
            
            # 借阅分类统计（最近30天）
            days = params.get("days", 30)
            start_date = datetime.now() - timedelta(days=days)
            
            borrow_categories = db.query(
                Book.category,
                func.count(BorrowRecord.id).label('borrow_count')
            ).join(
                BorrowRecord, Book.id == BorrowRecord.book_id
            ).filter(
                BorrowRecord.borrow_date >= start_date
            ).group_by(Book.category).all()
            
            # 构建结果
            categories = {}
            for cat in book_categories:
                category_name = cat.category or "未分类"
                categories[category_name] = {
                    "book_count": cat.book_count,
                    "total_copies": cat.total_copies or 0,
                    "available_copies": cat.available_copies or 0,
                    "borrow_count": 0
                }
            
            for cat in borrow_categories:
                category_name = cat.category or "未分类"
                if category_name in categories:
                    categories[category_name]["borrow_count"] = cat.borrow_count
            
            return {
                "status": "success",
                "categories": categories,
                "total_categories": len(categories)
            }
        finally:
            db.close()
    
    async def generate_analytics_report(self, params: Dict) -> Dict:
        """生成综合分析报告"""
        db = self.get_db_session()
        try:
            report_type = params.get("report_type") or params.get("type", "monthly")
            start_date = params.get("start_date")
            end_date = params.get("end_date")
            
            # 如果没有指定日期范围，默认最近30天
            if not start_date:
                start_date = datetime.now() - timedelta(days=30)
            if not end_date:
                end_date = datetime.now()
            
            # 收集各项数据
            overview = await self.get_system_overview({})
            popular = await self.get_popular_books({"days": 30})
            trends = await self.get_borrow_trends({"days": 30})
            categories = await self.get_category_statistics({})
            
            # 生成报告
            report = {
                "report_info": {
                    "type": report_type,
                    "generated_at": datetime.now().isoformat(),
                    "period": {
                        "start": start_date.isoformat() if isinstance(start_date, datetime) else start_date,
                        "end": end_date.isoformat() if isinstance(end_date, datetime) else end_date
                    }
                },
                "executive_summary": self._generate_executive_summary(
                    overview.get("overview", {}),
                    trends.get("summary", {})
                ),
                "detailed_analysis": {
                    "overview": overview.get("overview", {}),
                    "popular_books": popular.get("popular_by_borrows", [])[:5],
                    "trends": trends.get("trends", {}),
                    "category_distribution": categories.get("categories", {})
                },
                "recommendations": self._generate_recommendations(
                    overview.get("overview", {}),
                    trends.get("summary", {})
                )
            }
            
            self.log_action("生成分析报告", {
                "type": report_type,
                "period_days": 30
            })
            
            return {
                "status": "success",
                "report": report
            }
        finally:
            db.close()
    
    def _generate_executive_summary(self, overview: Dict, trends: Dict) -> Dict:
        """生成执行摘要"""
        books = overview.get("books", {})
        borrows = overview.get("borrows", {})
        
        return {
            "total_books": books.get("total_titles", 0),
            "total_copies": books.get("total_copies", 0),
            "current_borrows": borrows.get("current_active", 0),
            "overdue_rate": round(
                borrows.get("overdue", 0) / max(borrows.get("current_active", 1), 1) * 100, 2
            ),
            "daily_average_borrows": trends.get("average_daily", 0),
            "utilization_rate": round(
                (books.get("total_copies", 0) - books.get("available_copies", 0)) /
                max(books.get("total_copies", 1), 1) * 100, 2
            )
        }
    
    def _generate_recommendations(self, overview: Dict, trends: Dict) -> List[str]:
        """生成建议"""
        recommendations = []
        
        borrows = overview.get("borrows", {})
        books = overview.get("books", {})
        
        # 检查逾期率
        overdue_rate = borrows.get("overdue", 0) / max(borrows.get("current_active", 1), 1)
        if overdue_rate > 0.1:
            recommendations.append("逾期率较高，建议加强催还提醒")
        
        # 检查库存利用率
        utilization = (books.get("total_copies", 0) - books.get("available_copies", 0)) / max(books.get("total_copies", 1), 1)
        if utilization < 0.3:
            recommendations.append("图书利用率较低，可考虑减少采购或加强推广")
        elif utilization > 0.8:
            recommendations.append("图书利用率较高，建议增加热门图书副本")
        
        # 检查日均借阅
        if trends.get("average_daily", 0) < 5:
            recommendations.append("日均借阅量较低，可举办读书活动提升活跃度")
        
        return recommendations

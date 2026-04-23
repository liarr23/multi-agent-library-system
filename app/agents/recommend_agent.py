"""
智能推荐Agent - 基于用户行为和图书特征提供个性化推荐
"""
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
import numpy as np
from collections import defaultdict

from app.agents.base_agent import BaseAgent, AgentMessage
from app.models.book import Book
from app.models.user import User
from app.models.borrow_record import BorrowRecord, BorrowStatus
from app.models.rating import Rating
from app.config import settings


class RecommendAgent(BaseAgent):
    """智能推荐Agent"""

    def __init__(self):
        super().__init__(
            name="RecommendAgent",
            description="负责个性化推荐、用户画像分析、相似度计算"
        )
        # 用户画像缓存
        self._user_profiles: Dict[int, Dict] = {}
    
    async def process_message(self, message: AgentMessage) -> Any:
        """处理消息"""
        content = message.content
        task_type = content.get("task_type")
        task_data = content.get("data")
        
        # 更新处理状态
        await self._update_status()
        
        self.log_action(f"处理任务: {task_type}", task_data)
        
        try:
            if task_type == "recommend":
                return await self.get_recommendations(task_data)
            elif task_type == "update_user_profile":
                return await self.update_user_profile(task_data)
            elif task_type == "calculate_similarity":
                return await self.calculate_book_similarity(task_data)
            elif task_type == "get_similar_books":
                return await self.get_similar_books(task_data)
            else:
                return {"error": f"未知任务类型: {task_type}"}
        except Exception as e:
            return await self.handle_error(e, f"处理任务 {task_type}")
    
    async def get_recommendations(self, params: Dict) -> Dict:
        """获取个性化推荐"""
        user_id = params.get("user_id")
        limit = params.get("limit", settings.RECOMMENDATION_COUNT)
        
        if not user_id:
            return {"error": "需要提供用户ID"}
        
        db = self.get_db_session()
        try:
            # 获取用户画像
            user_profile = await self._build_user_profile(db, user_id)
            
            # 获取用户已借阅的图书ID
            borrowed_book_ids = self._get_borrowed_book_ids(db, user_id)
            
            # 获取推荐候选
            candidates = await self._get_recommendation_candidates(
                db, user_id, user_profile, borrowed_book_ids
            )
            
            # 计算推荐分数
            scored_books = []
            for book in candidates:
                score = self._calculate_recommendation_score(
                    book, user_profile, borrowed_book_ids
                )
                scored_books.append({
                    "book": book.to_dict(),
                    "score": score,
                    "reason": self._generate_recommendation_reason(book, user_profile)
                })
            
            # 按分数排序并返回
            scored_books.sort(key=lambda x: x["score"], reverse=True)
            recommendations = scored_books[:limit]
            
            self.log_action("生成推荐", {
                "user_id": user_id,
                "count": len(recommendations)
            })
            
            return {
                "status": "success",
                "user_id": user_id,
                "recommendations": recommendations,
                "user_profile_summary": {
                    "preferred_categories": user_profile.get("category_preferences", {}),
                    "preferred_authors": user_profile.get("author_preferences", {}),
                    "avg_rating": user_profile.get("avg_rating", 0)
                }
            }
        finally:
            db.close()
    
    async def _build_user_profile(self, db: Session, user_id: int) -> Dict:
        """构建用户画像"""
        # 检查缓存
        if user_id in self._user_profiles:
            cached = self._user_profiles[user_id]
            # 缓存24小时有效
            if (datetime.now() - cached.get("updated_at", datetime.min)).days < 1:
                return cached
        
        profile = {
            "user_id": user_id,
            "category_preferences": defaultdict(float),
            "author_preferences": defaultdict(float),
            "borrow_history": [],
            "rating_history": [],
            "avg_rating": 0,
            "updated_at": datetime.now()
        }
        
        # 获取借阅历史
        borrows = db.query(BorrowRecord).filter(
            BorrowRecord.user_id == user_id
        ).order_by(BorrowRecord.borrow_date.desc()).limit(50).all()
        
        for borrow in borrows:
            book = db.query(Book).filter(Book.id == borrow.book_id).first()
            if book:
                profile["borrow_history"].append({
                    "book_id": book.id,
                    "category": book.category,
                    "author": book.author,
                    "borrow_date": borrow.borrow_date
                })
                
                # 增加分类偏好权重（越近的借阅权重越高）
                if book.category:
                    days_ago = (datetime.now() - borrow.borrow_date).days
                    weight = max(0.1, 1.0 - days_ago / 365)
                    profile["category_preferences"][book.category] += weight
                
                # 增加作者偏好权重
                if book.author:
                    days_ago = (datetime.now() - borrow.borrow_date).days
                    weight = max(0.1, 1.0 - days_ago / 365)
                    profile["author_preferences"][book.author] += weight
        
        # 获取评分历史
        ratings = db.query(Rating).filter(
            Rating.user_id == user_id
        ).all()
        
        if ratings:
            profile["avg_rating"] = sum(r.score for r in ratings) / len(ratings)
            for rating in ratings:
                book = db.query(Book).filter(Book.id == rating.book_id).first()
                if book:
                    profile["rating_history"].append({
                        "book_id": book.id,
                        "category": book.category,
                        "author": book.author,
                        "score": rating.score
                    })
        
        # 缓存用户画像
        self._user_profiles[user_id] = profile
        return profile
    
    def _get_borrowed_book_ids(self, db: Session, user_id: int) -> set:
        """获取用户已借阅的图书ID"""
        borrows = db.query(BorrowRecord).filter(
            BorrowRecord.user_id == user_id
        ).all()
        return {b.book_id for b in borrows}
    
    async def _get_recommendation_candidates(
        self, db: Session, user_id: int, profile: Dict, borrowed_ids: set
    ) -> List[Book]:
        """获取推荐候选图书"""
        # 基础查询：活跃且有库存的图书
        query = db.query(Book).filter(
            and_(
                Book.is_active == True,
                Book.available_copies > 0,
                ~Book.id.in_(borrowed_ids) if borrowed_ids else True
            )
        )
        
        # 优先选择用户偏好的分类
        preferred_categories = list(profile.get("category_preferences", {}).keys())
        if preferred_categories:
            # 70%来自偏好分类，30%来自其他
            category_books = query.filter(
                Book.category.in_(preferred_categories)
            ).limit(int(settings.RECOMMENDATION_COUNT * 1.5)).all()
            
            other_books = query.filter(
                ~Book.category.in_(preferred_categories) if preferred_categories else True
            ).limit(int(settings.RECOMMENDATION_COUNT * 0.5)).all()
            
            candidates = category_books + other_books
        else:
            # 新用户：推荐热门图书
            candidates = query.order_by(
                Book.avg_rating.desc(),
                Book.rating_count.desc()
            ).limit(settings.RECOMMENDATION_COUNT * 2).all()
        
        return candidates
    
    def _calculate_recommendation_score(
        self, book: Book, profile: Dict, borrowed_ids: set
    ) -> float:
        """计算推荐分数"""
        score = 0.0
        
        # 1. 图书评分权重 (30%)
        if book.avg_rating and book.rating_count:
            # 考虑评分和评分数量
            rating_score = book.avg_rating * min(1.0, book.rating_count / 10)
            score += rating_score * 0.3
        
        # 2. 分类匹配权重 (35%)
        if book.category and book.category in profile.get("category_preferences", {}):
            category_weight = profile["category_preferences"][book.category]
            score += category_weight * 0.35
        
        # 3. 作者匹配权重 (25%)
        if book.author and book.author in profile.get("author_preferences", {}):
            author_weight = profile["author_preferences"][book.author]
            score += author_weight * 0.25
        
        # 4. 新书加成 (10%)
        if book.publish_date:
            days_since_published = (datetime.now() - book.publish_date).days
            if days_since_published < 90:  # 3个月内新书
                recency_bonus = max(0, 1.0 - days_since_published / 90)
                score += recency_bonus * 0.1
        
        return round(score, 4)
    
    def _generate_recommendation_reason(self, book: Book, profile: Dict) -> str:
        """生成推荐理由"""
        reasons = []
        
        # 分类匹配
        if book.category and book.category in profile.get("category_preferences", {}):
            reasons.append(f"您喜欢{book.category}类图书")
        
        # 作者匹配
        if book.author and book.author in profile.get("author_preferences", {}):
            reasons.append(f"您曾借阅过{book.author}的作品")
        
        # 高评分
        if book.avg_rating and book.avg_rating >= 4.0:
            reasons.append(f"评分高达{book.avg_rating:.1f}分")
        
        # 新书
        if book.publish_date and (datetime.now() - book.publish_date).days < 90:
            reasons.append("新书上架")
        
        return "，".join(reasons) if reasons else "为您精选推荐"
    
    async def update_user_profile(self, params: Dict) -> Dict:
        """更新用户画像"""
        user_id = params.get("user_id")
        if not user_id:
            return {"error": "需要提供用户ID"}
        
        db = self.get_db_session()
        try:
            # 清除缓存，强制重新构建
            if user_id in self._user_profiles:
                del self._user_profiles[user_id]
            
            # 重新构建用户画像
            profile = await self._build_user_profile(db, user_id)
            
            return {
                "status": "success",
                "user_id": user_id,
                "message": "用户画像已更新",
                "profile_summary": {
                    "preferred_categories": dict(profile.get("category_preferences", {})),
                    "preferred_authors": dict(profile.get("author_preferences", {})),
                    "borrow_count": len(profile.get("borrow_history", [])),
                    "rating_count": len(profile.get("rating_history", []))
                }
            }
        finally:
            db.close()
    
    async def calculate_book_similarity(self, params: Dict) -> Dict:
        """计算图书相似度"""
        book_id = params.get("book_id")
        if not book_id:
            return {"error": "需要提供图书ID"}
        
        db = self.get_db_session()
        try:
            target_book = db.query(Book).filter(Book.id == book_id).first()
            if not target_book:
                return {"error": "图书不存在"}
            
            # 获取所有图书
            all_books = db.query(Book).filter(
                and_(Book.is_active == True, Book.id != book_id)
            ).all()
            
            # 计算相似度
            similarities = []
            for book in all_books:
                similarity = self._calculate_book_similarity(target_book, book)
                if similarity > settings.SIMILARITY_THRESHOLD:
                    similarities.append({
                        "book": book.to_dict(),
                        "similarity": similarity
                    })
            
            # 按相似度排序
            similarities.sort(key=lambda x: x["similarity"], reverse=True)
            
            return {
                "status": "success",
                "target_book": target_book.to_dict(),
                "similar_books": similarities[:10]
            }
        finally:
            db.close()
    
    def _calculate_book_similarity(self, book1: Book, book2: Book) -> float:
        """计算两本图书的相似度"""
        similarity = 0.0
        
        # 分类相同
        if book1.category and book2.category and book1.category == book2.category:
            similarity += 0.4
        
        # 作者相同
        if book1.author and book2.author and book1.author == book2.author:
            similarity += 0.4
        
        # 评分接近
        if book1.avg_rating and book2.avg_rating:
            rating_diff = abs(book1.avg_rating - book2.avg_rating)
            similarity += max(0, 0.2 - rating_diff * 0.1)
        
        return round(similarity, 4)
    
    async def get_similar_books(self, params: Dict) -> Dict:
        """获取相似图书"""
        return await self.calculate_book_similarity(params)

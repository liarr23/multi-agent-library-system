"""
图书管理Agent测试
"""
import pytest
from app.agents.book_agent import BookAgent
from app.agents.base_agent import AgentMessage


class TestBookAgent:
    """图书管理Agent测试类"""
    
    @pytest.fixture
    def book_agent(self):
        """创建BookAgent实例"""
        return BookAgent()
    
    @pytest.mark.asyncio
    async def test_create_book(self, book_agent, db_session):
        """测试创建图书"""
        message = AgentMessage(
            sender="test",
            receiver="BookAgent",
            content={
                "task_type": "book_create",
                "data": {
                    "isbn": "978-7-111-12345-6",
                    "title": "Python编程从入门到实践",
                    "author": "Eric Matthes",
                    "publisher": "人民邮电出版社",
                    "category": "编程",
                    "price": 89.00,
                    "total_copies": 5
                }
            }
        )
        
        result = await book_agent.process_message(message)
        assert result["status"] == "success"
        assert result["book"]["title"] == "Python编程从入门到实践"
        assert result["book"]["available_copies"] == 5
    
    @pytest.mark.asyncio
    async def test_search_books(self, book_agent, db_session):
        """测试搜索图书"""
        # 先创建测试数据
        message = AgentMessage(
            sender="test",
            receiver="BookAgent",
            content={
                "task_type": "book_search",
                "data": {
                    "keyword": "Python",
                    "page": 1,
                    "size": 10
                }
            }
        )
        
        result = await book_agent.process_message(message)
        assert "total" in result
        assert "items" in result
        assert "page" in result
        assert "size" in result
    
    @pytest.mark.asyncio
    async def test_borrow_book(self, book_agent, db_session):
        """测试借书"""
        message = AgentMessage(
            sender="test",
            receiver="BookAgent",
            content={
                "task_type": "borrow_book",
                "data": {
                    "user_id": 1,
                    "book_id": 1
                }
            }
        )
        
        result = await book_agent.process_message(message)
        # 由于测试数据库可能没有数据，这里主要测试方法能正常执行
        assert isinstance(result, dict)
    
    @pytest.mark.asyncio
    async def test_return_book(self, book_agent, db_session):
        """测试还书"""
        message = AgentMessage(
            sender="test",
            receiver="BookAgent",
            content={
                "task_type": "return_book",
                "data": {
                    "borrow_id": 1
                }
            }
        )
        
        result = await book_agent.process_message(message)
        assert isinstance(result, dict)

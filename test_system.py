"""
多Agent图书管理系统测试脚本
"""
import asyncio
import sys
import io

# 设置UTF-8编码
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from app.agents import coordinator
from app.database import init_db, SessionLocal
from app.models.user import User
from app.models.book import Book
from app.models.borrow_record import BorrowRecord, BorrowStatus
from datetime import datetime, timedelta

async def test_system():
    print("=" * 60)
    print("多Agent图书管理系统 - 功能测试")
    print("=" * 60)
    
    # 初始化数据库
    init_db()
    print("✅ 数据库初始化完成")
    
    # 创建测试数据
    db = SessionLocal()
    try:
                        # 检查是否已有用户
        existing_user = db.query(User).filter(User.username == "liar").first()
        if not existing_user:
            import hashlib
            # 使用简单的哈希代替bcrypt
            password_hash = hashlib.sha256("password123".encode()).hexdigest()
            
            user = User(
                username="liar",
                email="liar@example.com",
                full_name="Liar",
                phone="13800138000",
                role="reader",
                hashed_password=password_hash
            )
            db.add(user)
            db.commit()
            print("✅ 创建测试用户成功")
        else:
            print("✅ 测试用户已存在")
        
        # 检查是否已有图书
        book_count = db.query(Book).count()
        if book_count == 0:
            books = [
                Book(
                    isbn="978-7-115-42802-3",
                    title="Python编程从入门到实践",
                    author="Eric Matthes",
                    publisher="人民邮电出版社",
                    category="编程",
                    description="本书针对所有层次Python读者而作，非常适合初学者入门。",
                    price=89.0,
                    total_copies=5,
                    available_copies=5
                ),
                Book(
                    isbn="978-7-113-25678-1",
                    title="算法导论",
                    author="Thomas H. Cormen",
                    publisher="机械工业出版社",
                    category="计算机科学",
                    description="本书全面介绍了计算机算法，是算法领域的经典教材。",
                    price=128.0,
                    total_copies=3,
                    available_copies=3
                ),
                Book(
                    isbn="978-7-302-45678-2",
                    title="深入理解计算机系统",
                    author="Randal E. Bryant",
                    publisher="机械工业出版社",
                    category="计算机科学",
                    description="本书从程序员的视角详细阐述计算机系统的本质概念。",
                    price=139.0,
                    total_copies=4,
                    available_copies=4
                ),
                Book(
                    isbn="978-7-121-45678-3",
                    title="机器学习",
                    author="周志华",
                    publisher="清华大学出版社",
                    category="人工智能",
                    description="本书全面介绍了机器学习的基本概念和算法。",
                    price=88.0,
                    total_copies=2,
                    available_copies=2
                ),
                Book(
                    isbn="978-7-111-45678-4",
                    title="数据库系统概论",
                    author="王珊",
                    publisher="高等教育出版社",
                    category="数据库",
                    description="本书系统地介绍了数据库系统的基本概念和原理。",
                    price=39.0,
                    total_copies=6,
                    available_copies=6
                )
            ]
            
            for book in books:
                db.add(book)
            db.commit()
            print("✅ 创建测试图书成功")
        else:
            print(f"✅ 数据库中已有 {book_count} 本图书")
    except Exception as e:
        print(f"❌ 创建测试数据失败: {e}")
        db.rollback()
    finally:
        db.close()
    
    print("\n" + "=" * 60)
    print("测试协调器功能")
    print("=" * 60)
    
    # 测试1: 搜索图书
    print("\n1. 测试图书搜索功能...")
    try:
        result = await coordinator.delegate_task(
            task_type="book_search",
            task_data={"keyword": "Python", "page": 1, "size": 10}
        )
        if result["status"] == "success":
            data = result["result"]
            print(f"✅ 搜索到 {data['total']} 本相关图书")
            for book in data["items"]:
                print(f"   - {book['title']} by {book['author']}")
        else:
            print(f"❌ 搜索失败: {result}")
    except Exception as e:
        print(f"❌ 搜索异常: {e}")
    
    # 测试2: 获取图书详情
    print("\n2. 测试获取图书详情...")
    try:
        result = await coordinator.delegate_task(
            task_type="book_detail",
            task_data={"book_id": 1}
        )
        if result["status"] == "success":
            book = result["result"]
            print(f"✅ 获取图书详情成功: {book['title']}")
            print(f"   作者: {book['author']}")
            print(f"   ISBN: {book['isbn']}")
            print(f"   库存: {book['available_copies']}/{book['total_copies']}")
        else:
            print(f"❌ 获取详情失败: {result}")
    except Exception as e:
        print(f"❌ 获取详情异常: {e}")
    
        # 测试3: 借阅图书
    print("\n3. 测试借阅图书功能...")
    try:
        result = await coordinator.delegate_task(
            task_type="borrow_book",
            task_data={
                "user_id": 1,
                "book_id": 1,
                "days": 14
            }
        )
        if result["status"] == "success":
            borrow_info = result["result"]
            print(f"✅ 借阅成功")
            if "borrow_record" in borrow_info:
                print(f"   借阅ID: {borrow_info['borrow_record']['id']}")
                print(f"   应还日期: {borrow_info['borrow_record']['due_date']}")
            print(f"   消息: {borrow_info.get('message', '')}")
        else:
            print(f"❌ 借阅失败: {result}")
    except Exception as e:
        print(f"❌ 借阅异常: {e}")
    
    # 测试4: 推荐图书
    print("\n4. 测试图书推荐功能...")
    try:
        result = await coordinator.delegate_task(
            task_type="recommend",
            task_data={
                "user_id": 1,
                "recommend_type": "popular",
                "limit": 3
            }
                )
        if result["status"] == "success":
            recommendations = result["result"].get("recommendations", [])
            print(f"✅ 获取推荐成功，共 {len(recommendations)} 本")
            for i, rec in enumerate(recommendations, 1):
                book = rec.get("book", {})
                reason = rec.get("reason", "")
                print(f"   {i}. {book.get('title', '未知')} - {reason}")
        else:
            print(f"❌ 推荐失败: {result}")
    except Exception as e:
        print(f"❌ 推荐异常: {e}")
    
        # 测试5: 数据分析
    print("\n5. 测试数据分析功能...")
    try:
        result = await coordinator.delegate_task(
            task_type="analytics_overview",
            task_data={}
        )
        if result["status"] == "success":
            analytics = result["result"]
            print(f"✅ 数据分析成功")
            print(f"   总图书数: {analytics.get('total_books', 0)}")
            print(f"   总用户数: {analytics.get('total_users', 0)}")
            print(f"   总借阅次数: {analytics.get('total_borrows', 0)}")
            print(f"   当前借出: {analytics.get('current_borrows', 0)}")
        else:
            print(f"❌ 数据分析失败: {result}")
    except Exception as e:
        print(f"❌ 数据分析异常: {e}")
    
    # 测试6: 归还图书
    print("\n6. 测试归还图书功能...")
    try:
        # 先查找未归还的借阅记录
        db = SessionLocal()
        borrow_record = db.query(BorrowRecord).filter(
            BorrowRecord.user_id == 1,
            BorrowRecord.book_id == 1,
            BorrowRecord.status.in_([BorrowStatus.BORROWED, BorrowStatus.RENEWED])
        ).first()
        db.close()
        
        if borrow_record:
            result = await coordinator.delegate_task(
                task_type="return_book",
                task_data={
                    "borrow_id": borrow_record.id,
                    "user_id": 1
                }
            )
            if result["status"] == "success":
                return_info = result["result"]
                print(f"✅ 归还成功")
                print(f"   罚款金额: {return_info.get('fine_amount', 0)} 元")
            else:
                print(f"❌ 归还失败: {result}")
        else:
            print("⚠️  没有找到未归还的借阅记录")
    except Exception as e:
        print(f"❌ 归还异常: {e}")
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_system())
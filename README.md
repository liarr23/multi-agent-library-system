# 多Agent图书管理系统

基于多Agent架构的智能图书管理系统，使用FastAPI构建，支持个性化推荐、借阅管理和数据分析。

## 系统架构

```
┌─────────────────────────────────────────────────────────────────┐
│                        客户端 (Web/Mobile)                       │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    FastAPI REST API 层                           │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│  │  Books   │  │  Users   │  │ Borrows  │  │Analytics │       │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘       │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Agent 协调器 (Coordinator)                    │
│         负责任务分发、Agent间通信、结果汇总                        │
└─────────────────────────────────────────────────────────────────┘
                                │
        ┌───────────────────────┼───────────────────────┐
        ▼                       ▼                       ▼
┌──────────────┐      ┌──────────────┐      ┌──────────────┐
│  BookAgent   │      │RecommendAgent│      │AnalyticsAgent│
│  图书管理     │      │  智能推荐     │      │  数据分析     │
│  借阅归还     │      │  用户画像     │      │  报表生成     │
└──────────────┘      └──────────────┘      └──────────────┘
        │                       │                       │
        └───────────────────────┼───────────────────────┘
                                ▼
                    ┌──────────────────────┐
                    │    SQLite 数据库      │
                    └──────────────────────┘
```

## 功能特性

### 1. 图书管理 (BookAgent)
- 图书CRUD操作（创建、查询、更新、删除）
- 借书/还书/续借功能
- 库存管理
- 逾期检查

### 2. 智能推荐 (RecommendAgent)
- 基于用户历史的个性化推荐
- 用户画像分析
- 图书相似度计算
- 推荐理由生成

### 3. 数据分析 (AnalyticsAgent)
- 系统概览统计
- 热门图书排行
- 借阅趋势分析
- 分类统计
- 用户活跃度分析

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 启动服务

```bash
python run.py
```

服务默认运行在 `http://localhost:8000`

### 3. 访问API文档

启动后访问 `http://localhost:8000/docs` 查看Swagger文档

## API接口

### 图书管理

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/books/` | 获取图书列表 |
| POST | `/api/books/` | 创建新图书 |
| GET | `/api/books/{id}` | 获取图书详情 |
| PUT | `/api/books/{id}` | 更新图书信息 |
| DELETE | `/api/books/{id}` | 删除图书 |
| GET | `/api/books/{id}/similar` | 获取相似图书 |

### 借阅管理

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/borrows/` | 借书 |
| PUT | `/api/borrows/return` | 还书 |
| PUT | `/api/borrows/renew` | 续借 |
| GET | `/api/borrows/user/{user_id}` | 获取用户借阅记录 |
| GET | `/api/borrows/overdue` | 获取逾期图书列表 |

### 数据分析

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/analytics/overview` | 获取系统概览 |
| GET | `/api/analytics/popular` | 获取热门图书 |
| GET | `/api/analytics/trends` | 获取借阅趋势 |
| GET | `/api/analytics/category-stats` | 获取分类统计 |
| POST | `/api/analytics/report` | 生成分析报表 |

## 项目结构

```
multi-agent-library-system/
├── app/
│   ├── agents/           # Agent模块
│   │   ├── base_agent.py     # Agent基类
│   │   ├── coordinator.py    # Agent协调器
│   │   ├── book_agent.py     # 图书管理Agent
│   │   ├── recommend_agent.py # 智能推荐Agent
│   │   └── analytics_agent.py # 数据分析Agent
│   ├── models/           # SQLAlchemy模型
│   │   ├── book.py           # 图书模型
│   │   ├── user.py           # 用户模型
│   │   ├── borrow_record.py  # 借阅记录模型
│   │   └── rating.py         # 评分模型
│   ├── routers/          # API路由
│   │   ├── books.py          # 图书相关接口
│   │   ├── users.py          # 用户相关接口
│   │   ├── borrows.py        # 借阅相关接口
│   │   └── analytics.py      # 数据分析接口
│   ├── schemas/          # Pydantic schemas
│   │   ├── book.py           # 图书相关schema
│   │   └── borrow.py         # 借阅相关schema
│   ├── config.py         # 配置文件
│   ├── database.py       # 数据库配置
│   └── main.py           # FastAPI主应用
├── tests/                # 测试文件
├── requirements.txt      # 依赖列表
├── run.py               # 启动脚本
└── README.md            # 项目说明
```

## 数据库模型

### Book (图书)
- ISBN、书名、作者、出版社
- 分类、描述、价格
- 总册数、可用册数
- 平均评分、评分数量

### User (用户)
- 用户名、邮箱、密码
- 姓名、电话、角色
- 累计借阅次数、当前借阅数

### BorrowRecord (借阅记录)
- 用户ID、图书ID
- 借阅日期、应还日期、实际归还日期
- 续借次数、状态
- 罚款金额、是否已支付

### Rating (评分)
- 用户ID、图书ID
- 评分、评论内容

## Agent通信机制

系统使用协调器模式实现Agent间通信：

1. **消息格式**: 所有消息使用`AgentMessage`类封装
2. **任务分发**: 协调器根据任务类型自动选择合适的Agent
3. **结果汇总**: 协调器收集Agent返回结果并统一返回

```python
# 示例：通过协调器委托任务
result = await coordinator.delegate_task(
    task_type="book_search",
    task_data={"keyword": "Python"},
    preferred_agent="BookAgent"  # 可选，指定Agent
)
```

## 开发说明

### 添加新的Agent

1. 继承`BaseAgent`类
2. 实现`process_message`方法
3. 在`app/agents/__init__.py`中注册

### 添加新的API接口

1. 在`app/routers/`下创建路由文件
2. 在`app/main.py`中注册路由
3. 通过协调器调用对应的Agent

## 测试

```bash
pytest tests/ -v
```

## 许可证

MIT License

# 📚 多Agent图书管理系统

基于多Agent架构的智能图书管理系统，采用FastAPI构建，支持个性化推荐、借阅管理和数据分析。

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104.1-green.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 🏗️ 系统架构

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           客户端 (Web/Mobile)                            │
└─────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         FastAPI REST API 层                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐ │
│  │  Books   │  │  Users   │  │ Borrows  │  │Analytics │  │  Agents  │ │
│  │  图书接口 │  │  用户接口 │  │ 借阅接口  │  │ 分析接口  │  │ Agent接口 │ │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘  └──────────┘ │
└─────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      Agent 协调器 (Coordinator)                          │
│              负责任务分发、Agent间通信、消息路由、结果汇总                  │
└─────────────────────────────────────────────────────────────────────────┘
                                      │
            ┌─────────────────────────┼─────────────────────────┐
            ▼                         ▼                         ▼
    ┌──────────────┐         ┌──────────────┐         ┌──────────────┐
    │  BookAgent   │         │RecommendAgent│         │AnalyticsAgent│
    │   图书管理    │         │   智能推荐    │         │   数据分析    │
    │   借阅归还    │         │   用户画像    │         │   报表生成    │
    │   库存管理    │         │   相似计算    │         │   趋势分析    │
    └──────────────┘         └──────────────┘         └──────────────┘
            │                         │                         │
            └─────────────────────────┼─────────────────────────┘
                                      ▼
                          ┌──────────────────────┐
                          │     SQLite 数据库     │
                          │     (library.db)      │
                          └──────────────────────┘
```

---

## ✨ 功能特性

### 📖 图书管理 (BookAgent)
- 图书CRUD操作（创建、查询、更新、删除）
- 借书/还书/续借功能
- 库存管理与可用性检查
- 逾期自动检测与罚款计算
- 相似图书推荐

### 🎯 智能推荐 (RecommendAgent)
- 基于用户历史的个性化推荐
- 用户画像分析（阅读偏好、活跃度）
- 图书相似度计算（基于分类、作者、评分）
- 推荐理由生成

### 📊 数据分析 (AnalyticsAgent)
- 系统概览统计（图书总数、用户数、借阅量）
- 热门图书排行（按借阅次数、评分）
- 借阅趋势分析（日/周/月统计）
- 分类统计与分布
- 用户活跃度分析
- 可视化报表生成

---

## 🚀 快速开始

### 环境要求

- Python 3.8+
- pip

### 1. 克隆项目

```bash
git clone <repository-url>
cd multi-agent-library-system
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 启动服务

**方式一：使用启动脚本**
```bash
python run.py
```

**方式二：使用uvicorn直接启动**
```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**方式三：一键启动前后端**
```bash
python start_all.py
```

### 4. 访问系统

| 服务 | 地址 |
|------|------|
| API服务 | http://localhost:8000 |
| Swagger文档 | http://localhost:8000/docs |
| ReDoc文档 | http://localhost:8000/redoc |
| 健康检查 | http://localhost:8000/health |

---

## 📡 API接口

### 图书管理

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/books/` | 获取图书列表（支持搜索和分页） |
| POST | `/api/books/` | 创建新图书 |
| GET | `/api/books/{book_id}` | 获取图书详情 |
| PUT | `/api/books/{book_id}` | 更新图书信息 |
| DELETE | `/api/books/{book_id}` | 删除图书 |
| GET | `/api/books/{book_id}/similar` | 获取相似图书 |

### 用户管理

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/users/` | 获取用户列表 |
| POST | `/api/users/` | 创建新用户 |
| GET | `/api/users/{user_id}` | 获取用户详情 |
| GET | `/api/users/{user_id}/borrow-history` | 获取借阅历史 |
| GET | `/api/users/{user_id}/recommendations` | 获取个性化推荐 |

### 借阅管理

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/borrows/` | 借阅图书 |
| POST | `/api/borrows/return` | 归还图书 |
| POST | `/api/borrows/renew` | 续借图书 |
| GET | `/api/borrows/user/{user_id}` | 获取用户借阅记录 |
| GET | `/api/borrows/overdue` | 获取逾期图书列表 |
| POST | `/api/borrows/check-overdue` | 检查逾期图书 |

### 数据分析

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/analytics/overview` | 获取系统概览 |
| GET | `/api/analytics/popular` | 获取热门图书 |
| GET | `/api/analytics/trends` | 获取借阅趋势 |
| GET | `/api/analytics/category-stats` | 获取分类统计 |
| POST | `/api/analytics/report` | 生成分析报告 |
| GET | `/api/analytics/user-activity` | 获取用户活跃度 |

### 多Agent系统

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/agents/status` | 获取所有Agent状态 |
| POST | `/api/agents/start` | 启动所有Agent |
| POST | `/api/agents/stop` | 停止所有Agent |
| GET | `/api/agents/messages` | 获取消息历史 |
| GET | `/api/agents/tasks` | 获取任务列表 |
| POST | `/api/agents/test/search` | 测试图书搜索Agent |
| POST | `/api/agents/test/recommend` | 测试推荐Agent |
| POST | `/api/agents/test/analytics` | 测试分析Agent |

---

## 📁 项目结构

```
multi-agent-library-system/
├── app/                          # 应用核心代码
│   ├── agents/                   # Agent模块
│   │   ├── __init__.py          # 模块初始化，注册Agent
│   │   ├── base_agent.py        # Agent基类（消息处理、状态管理）
│   │   ├── coordinator.py       # Agent协调器（任务分发、消息路由）
│   │   ├── book_agent.py        # 图书管理Agent
│   │   ├── recommend_agent.py   # 智能推荐Agent
│   │   └── analytics_agent.py   # 数据分析Agent
│   ├── api/                      # API路由
│   │   └── agents.py            # 多Agent系统API
│   ├── models/                   # SQLAlchemy数据模型
│   │   ├── book.py              # 图书模型
│   │   ├── user.py              # 用户模型
│   │   ├── borrow_record.py     # 借阅记录模型
│   │   └── rating.py            # 评分模型
│   ├── routers/                  # 业务路由
│   │   ├── books.py             # 图书相关接口
│   │   ├── users.py             # 用户相关接口
│   │   ├── borrows.py           # 借阅相关接口
│   │   └── analytics.py         # 数据分析接口
│   ├── schemas/                  # Pydantic数据验证
│   │   ├── book.py              # 图书相关schema
│   │   └── borrow.py            # 借阅相关schema
│   ├── config.py                 # 应用配置
│   ├── database.py               # 数据库配置与初始化
│   └── main.py                   # FastAPI主应用入口
├── data/                         # 数据文件
├── frontend/                     # 前端代码
│   └── server.py                # 前端服务
├── tests/                        # 测试文件
│   ├── test_api.py              # API测试
│   ├── test_analytics.py        # 分析功能测试
│   └── test_system.py           # 系统集成测试
├── library.db                    # SQLite数据库文件
├── requirements.txt              # Python依赖
├── run.py                        # 启动脚本
├── start_all.py                  # 一键启动脚本（前后端）
├── 使用说明.md                    # 详细使用说明
├── 启动服务.bat                   # Windows启动脚本
├── 测试API.bat                    # Windows测试脚本
└── README.md                     # 项目说明文档
```

---

## 🗄️ 数据库模型

### Book (图书)
| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| isbn | String | ISBN编号 |
| title | String | 书名 |
| author | String | 作者 |
| publisher | String | 出版社 |
| category | String | 分类 |
| description | Text | 描述 |
| price | Float | 价格 |
| total_copies | Integer | 总册数 |
| available_copies | Integer | 可用册数 |
| average_rating | Float | 平均评分 |
| rating_count | Integer | 评分数量 |

### User (用户)
| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| username | String | 用户名 |
| email | String | 邮箱 |
| password_hash | String | 密码哈希 |
| full_name | String | 姓名 |
| phone | String | 电话 |
| role | String | 角色(student/teacher/admin) |
| total_borrowed | Integer | 累计借阅次数 |
| current_borrowed | Integer | 当前借阅数 |

### BorrowRecord (借阅记录)
| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| user_id | Integer | 用户ID |
| book_id | Integer | 图书ID |
| borrow_date | DateTime | 借阅日期 |
| due_date | DateTime | 应还日期 |
| return_date | DateTime | 实际归还日期 |
| renew_count | Integer | 续借次数 |
| status | String | 状态(borrowed/returned/overdue) |
| fine_amount | Float | 罚款金额 |
| fine_paid | Boolean | 是否已支付 |

### Rating (评分)
| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| user_id | Integer | 用户ID |
| book_id | Integer | 图书ID |
| rating | Float | 评分(1-5) |
| comment | Text | 评论内容 |

---

## 🤖 Agent通信机制

系统使用协调器模式实现Agent间通信：

### 消息格式
```python
AgentMessage(
    id="msg_123",
    sender="BookAgent",
    receiver="RecommendAgent",
    content={"task_type": "recommend", "data": {...}},
    timestamp=datetime.now(),
    message_type="request"
)
```

### 任务分发
```python
# 通过协调器委托任务
result = await coordinator.delegate_task(
    task_type="book_search",
    task_data={"keyword": "Python"},
    preferred_agent="BookAgent"  # 可选，指定Agent
)
```

### Agent注册
```python
# 在 app/agents/__init__.py 中注册
coordinator.register_agent("BookAgent", BookAgent())
coordinator.register_agent("RecommendAgent", RecommendAgent())
coordinator.register_agent("AnalyticsAgent", AnalyticsAgent())
```

---

## 🧪 测试

### 运行所有测试
```bash
pytest tests/ -v
```

### 运行特定测试
```bash
# API测试
pytest tests/test_api.py -v

# 分析功能测试
pytest tests/test_analytics.py -v

# 系统集成测试
pytest tests/test_system.py -v
```

### 使用测试脚本
```bash
# Windows
测试API.bat

# 或直接运行
python test_api.py
```

---

## ⚙️ 配置

配置文件位于 `app/config.py`，支持环境变量覆盖：

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| APP_NAME | 多Agent图书管理系统 | 应用名称 |
| APP_VERSION | 1.0.0 | 应用版本 |
| DEBUG | True | 调试模式 |
| DATABASE_URL | sqlite:///./library.db | 数据库连接 |
| MAX_CONCURRENT_AGENTS | 5 | 最大并发Agent数 |
| AGENT_TIMEOUT | 30 | Agent超时时间(秒) |
| MAX_BORROW_DAYS | 30 | 最大借阅天数 |
| MAX_BORROW_COUNT | 10 | 最大借阅数量 |
| FINE_PER_DAY | 0.5 | 每天罚款金额 |
| RECOMMENDATION_COUNT | 10 | 推荐数量 |
| SIMILARITY_THRESHOLD | 0.3 | 相似度阈值 |

---

## 🔧 开发指南

### 添加新的Agent

1. 继承 `BaseAgent` 类
2. 实现 `process_message` 方法
3. 在 `app/agents/__init__.py` 中注册

```python
from app.agents.base_agent import BaseAgent

class MyAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="MyAgent",
            description="我的自定义Agent"
        )
    
    async def process_message(self, message):
        # 处理消息逻辑
        return {"result": "success"}
```

### 添加新的API接口

1. 在 `app/routers/` 下创建路由文件
2. 在 `app/main.py` 中注册路由
3. 通过协调器调用对应的Agent

```python
from fastapi import APIRouter

router = APIRouter(prefix="/my", tags=["我的接口"])

@router.get("/test")
async def my_test():
    return {"message": "Hello"}
```

---

## 📝 使用示例

### 借阅图书
```bash
curl -X POST "http://localhost:8000/api/borrows/" \
  -H "Content-Type: application/json" \
  -d '{"user_id": 1, "book_id": 1}'
```

### 获取个性化推荐
```bash
curl "http://localhost:8000/api/users/1/recommendations"
```

### 生成分析报告
```bash
curl -X POST "http://localhost:8000/api/analytics/report" \
  -H "Content-Type: application/json" \
  -d '{"report_type": "monthly"}'
```

---

## 🐛 故障排除

### 端口被占用
```bash
# 检查端口占用
netstat -ano | findstr :8000

# 修改端口
# 编辑 run.py 中的 port 参数
```

### 数据库问题
```bash
# 删除数据库文件重新初始化
rm library.db
python -c "from app.database import init_db; init_db()"
```

### 依赖问题
```bash
pip install -r requirements.txt --upgrade
```

---

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

---

## 🤝 贡献

欢迎提交Issue和Pull Request！

---

## 📧 联系方式

如有问题或建议，请提交Issue。

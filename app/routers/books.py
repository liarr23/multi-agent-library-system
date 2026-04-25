"""
图书管理API路由
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.schemas.book import BookCreate, BookUpdate, BookResponse, BookListResponse
from app.agents import coordinator

router = APIRouter(prefix="/books", tags=["图书管理"])


def _unwrap_agent_result(result: dict, default_status: int = 400) -> dict:
    """统一处理协调器结果，兼容业务错误与异常错误。"""
    if result.get("status") in {"error", "timeout", "failed"}:
        raise HTTPException(status_code=default_status, detail=result.get("error", "请求失败"))

    payload = result.get("result", {})
    if isinstance(payload, dict) and payload.get("status") == "error":
        raise HTTPException(status_code=default_status, detail=payload.get("error", "请求失败"))

    if isinstance(payload, dict) and "error" in payload:
        raise HTTPException(status_code=default_status, detail=payload["error"])

    return payload


@router.get("/", response_model=BookListResponse)
async def get_books(
    keyword: Optional[str] = Query(None, description="搜索关键词"),
    category: Optional[str] = Query(None, description="分类筛选"),
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db)
):
    """获取图书列表"""
    result = await coordinator.delegate_task(
        task_type="book_search",
        task_data={
            "keyword": keyword,
            "category": category,
            "page": page,
            "size": size
        }
    )

    return _unwrap_agent_result(result)


@router.post("/", response_model=BookResponse)
async def create_book(book_data: BookCreate):
    """创建新图书"""
    result = await coordinator.delegate_task(
        task_type="book_create",
        task_data=book_data.dict()
    )

    payload = _unwrap_agent_result(result)
    return payload.get("book", payload)


@router.get("/{book_id}", response_model=BookResponse)
async def get_book(book_id: int):
    """获取图书详情"""
    result = await coordinator.delegate_task(
        task_type="book_detail",
        task_data={"book_id": book_id}
    )

    return _unwrap_agent_result(result, default_status=404)


@router.put("/{book_id}", response_model=BookResponse)
async def update_book(book_id: int, book_data: BookUpdate):
    """更新图书信息"""
    update_data = book_data.dict(exclude_unset=True)
    update_data["book_id"] = book_id
    
    result = await coordinator.delegate_task(
        task_type="book_update",
        task_data=update_data
    )

    payload = _unwrap_agent_result(result)
    return payload.get("book", payload)


@router.delete("/{book_id}")
async def delete_book(book_id: int):
    """删除图书"""
    result = await coordinator.delegate_task(
        task_type="book_delete",
        task_data={"book_id": book_id}
    )

    return _unwrap_agent_result(result)


@router.get("/{book_id}/similar")
async def get_similar_books(book_id: int):
    """获取相似图书"""
    result = await coordinator.delegate_task(
        task_type="get_similar_books",
        task_data={"book_id": book_id},
        preferred_agent="RecommendAgent"
    )

    return _unwrap_agent_result(result)

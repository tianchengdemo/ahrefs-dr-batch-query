# -*- coding: utf-8 -*-
"""
Ahrefs DR 批量查询工具 - FastAPI 服务
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional
import uvicorn
from datetime import datetime
import uuid

from ahrefs import AhrefsClient
from hubstudio import HubStudioClient
from config import (
    HUBSTUDIO_API_BASE, APP_ID, APP_SECRET, CONTAINER_CODE,
    SOCKS5_PROXY, AHREFS_COOKIE
)

# 创建 FastAPI 应用
app = FastAPI(
    title="Ahrefs DR Batch Query API",
    description="通过 HubStudio 和 CDP 协议自动获取 Cookie，批量查询域名 DR 和 AR",
    version="2.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 任务存储（生产环境应使用 Redis）
tasks_storage = {}


# ============================================================
# Pydantic 模型
# ============================================================

class QueryRequest(BaseModel):
    """单个域名查询请求"""
    domain: str = Field(..., description="域名", example="example.com")
    country: Optional[str] = Field("us", description="国家代码", example="us")


class BatchQueryRequest(BaseModel):
    """批量查询请求"""
    domains: List[str] = Field(..., description="域名列表", example=["example.com", "google.com"])
    country: Optional[str] = Field("us", description="国家代码", example="us")


class TaskResponse(BaseModel):
    """任务响应"""
    task_id: str = Field(..., description="任务 ID")
    status: str = Field(..., description="任务状态: pending, processing, completed, failed")
    message: str = Field(..., description="状态消息")


class QueryResult(BaseModel):
    """查询结果"""
    domain: str
    domain_rating: Optional[float]
    ahrefs_rank: Optional[int]
    dr_delta: Optional[float] = None
    ar_delta: Optional[int] = None
    error: Optional[str] = None


class TaskResult(BaseModel):
    """任务结果"""
    task_id: str
    status: str
    created_at: str
    completed_at: Optional[str] = None
    results: Optional[List[QueryResult]] = None
    error: Optional[str] = None


# ============================================================
# 辅助函数
# ============================================================

def get_ahrefs_client():
    """获取 Ahrefs 客户端"""
    cookie = None
    proxy_url = SOCKS5_PROXY

    # 尝试从 HubStudio 获取 Cookie
    if CONTAINER_CODE and APP_ID and APP_SECRET:
        try:
            hub = HubStudioClient()

            # 启动浏览器并通过 CDP 获取 Cookie
            browser_info = hub.start_browser(
                CONTAINER_CODE,
                enable_cdp=True,
                open_url="https://app.ahrefs.com"
            )
            debugging_port = browser_info.get("debuggingPort")

            if debugging_port:
                import time
                time.sleep(5)  # 等待页面加载

                cookies = hub.get_cookies_via_cdp(debugging_port, "ahrefs.com")
                if cookies:
                    cookie = hub.build_cookie_header(cookies)
                else:
                    cookies = hub.export_cookies(CONTAINER_CODE)
                    if cookies:
                        cookie = hub.build_cookie_header(cookies)

            if not proxy_url:
                proxy_url = hub.get_proxy_for_env(CONTAINER_CODE)

        except Exception as e:
            print(f"[API] HubStudio 获取失败: {e}")

    # 回退到配置文件
    if not cookie:
        cookie = AHREFS_COOKIE

    if not cookie:
        raise HTTPException(status_code=500, detail="未配置 Cookie")

    return AhrefsClient(cookie_header=cookie, proxy_url=proxy_url)


def process_query_task(task_id: str, domains: List[str], country: str):
    """处理查询任务（后台任务）"""
    try:
        tasks_storage[task_id]["status"] = "processing"

        # 获取客户端
        client = get_ahrefs_client()

        # 批量查询
        results = client.batch_get_domain_rating(domains, country=country)

        # 更新任务状态
        tasks_storage[task_id]["status"] = "completed"
        tasks_storage[task_id]["completed_at"] = datetime.now().isoformat()
        tasks_storage[task_id]["results"] = results

    except Exception as e:
        tasks_storage[task_id]["status"] = "failed"
        tasks_storage[task_id]["error"] = str(e)
        tasks_storage[task_id]["completed_at"] = datetime.now().isoformat()


# ============================================================
# API 端点
# ============================================================

@app.get("/", tags=["Root"])
async def root():
    """API 根路径"""
    return {
        "name": "Ahrefs DR Batch Query API",
        "version": "2.1.0",
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }


@app.post("/api/query", response_model=TaskResponse, tags=["Query"])
async def query_domain(request: QueryRequest, background_tasks: BackgroundTasks):
    """
    查询单个域名的 DR 和 AR

    - **domain**: 域名（如 example.com）
    - **country**: 国家代码（默认 us）

    返回任务 ID，使用 /api/result/{task_id} 获取结果
    """
    task_id = str(uuid.uuid4())

    # 创建任务
    tasks_storage[task_id] = {
        "task_id": task_id,
        "status": "pending",
        "created_at": datetime.now().isoformat(),
        "domains": [request.domain],
        "country": request.country
    }

    # 添加后台任务
    background_tasks.add_task(
        process_query_task,
        task_id,
        [request.domain],
        request.country
    )

    return TaskResponse(
        task_id=task_id,
        status="pending",
        message="任务已创建，正在处理中"
    )


@app.post("/api/batch", response_model=TaskResponse, tags=["Query"])
async def batch_query(request: BatchQueryRequest, background_tasks: BackgroundTasks):
    """
    批量查询多个域名的 DR 和 AR

    - **domains**: 域名列表
    - **country**: 国家代码（默认 us）

    返回任务 ID，使用 /api/result/{task_id} 获取结果
    """
    task_id = str(uuid.uuid4())

    # 创建任务
    tasks_storage[task_id] = {
        "task_id": task_id,
        "status": "pending",
        "created_at": datetime.now().isoformat(),
        "domains": request.domains,
        "country": request.country
    }

    # 添加后台任务
    background_tasks.add_task(
        process_query_task,
        task_id,
        request.domains,
        request.country
    )

    return TaskResponse(
        task_id=task_id,
        status="pending",
        message=f"任务已创建，正在处理 {len(request.domains)} 个域名"
    )


@app.get("/api/result/{task_id}", response_model=TaskResult, tags=["Query"])
async def get_result(task_id: str):
    """
    获取任务结果

    - **task_id**: 任务 ID

    返回任务状态和查询结果
    """
    if task_id not in tasks_storage:
        raise HTTPException(status_code=404, detail="任务不存在")

    task = tasks_storage[task_id]

    return TaskResult(
        task_id=task["task_id"],
        status=task["status"],
        created_at=task["created_at"],
        completed_at=task.get("completed_at"),
        results=task.get("results"),
        error=task.get("error")
    )


@app.get("/api/tasks", tags=["Query"])
async def list_tasks():
    """
    列出所有任务

    返回任务列表
    """
    return {
        "total": len(tasks_storage),
        "tasks": [
            {
                "task_id": task["task_id"],
                "status": task["status"],
                "created_at": task["created_at"],
                "domains_count": len(task["domains"])
            }
            for task in tasks_storage.values()
        ]
    }


# ============================================================
# 启动服务
# ============================================================

if __name__ == "__main__":
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

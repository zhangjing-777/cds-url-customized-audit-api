from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse
from pathlib import Path
from typing import Optional
from ..core.content_manager import content_manager
from ..config import settings

router = APIRouter(prefix="/content", tags=["content"])

@router.get("/list/{site_name}")
def list_content(
    site_name: str,
    limit: Optional[int] = Query(None, description="限制返回的记录数量，不设置则返回所有", ge=1, le=100)
):
    """
    列出指定网站的所有爬取记录
    
    参数说明:
    - site_name: 网站名称，支持: gys, travelsky, travelskyir
    - limit: 可选，限制返回数量，范围1-100
    
    返回:
    - success: 布尔值
    - data: 爬取记录列表，按时间倒序排列
        - date: 爬取时间目录名 (格式: YYYY-MM-DD_HH_MM_SS)
        - path: 完整路径
        - pages: 页面数量
        - page_list: 页面详情列表
    
    示例:
    GET /content/list/gys?limit=10
    
    响应示例:
    {
        "success": true,
        "data": [
            {
                "date": "2024-01-01_10_30_15",
                "path": "/path/to/data/2024-01-01_10_30_15",
                "pages": 5,
                "page_list": [
                    {"name": "home", "url": "http://example.com"},
                    {"name": "about", "url": "http://example.com/about"}
                ]
            }
        ]
    }
    """
    if site_name not in ["gys", "travelsky", "travelskyir"]:
        raise HTTPException(status_code=400, detail="无效的网站名称，支持: gys, travelsky, travelskyir")
    
    result = content_manager.get_content_list(site_name)
    if result["success"] and limit:
        result["data"] = result["data"][:limit]
    
    return result

@router.get("/detail/{site_name}/{date}")
def get_content_detail(
    site_name: str, 
    date: str
):
    """
    查看指定日期的爬取内容详情
    
    参数说明:
    - site_name: 网站名称，支持: gys, travelsky, travelskyir
    - date: 爬取时间目录名，格式: YYYY-MM-DD_HH_MM_SS
    
    返回:
    - success: 布尔值
    - data: 内容详情
        - pages: 页面列表
            - name: 页面名称
            - files: 文件信息
                - txt: 文本文件列表
                - images: 图片文件列表
    
    示例:
    GET /content/detail/gys/2024-01-01_10_30_15
    
    响应示例:
    {
        "success": true,
        "data": {
            "pages": [
                {
                    "name": "home",
                    "files": {
                        "txt": ["home.txt"],
                        "images": ["logo.png", "banner.jpg"]
                    }
                }
            ]
        }
    }
    """
    if site_name not in ["gys", "travelsky", "travelskyir"]:
        raise HTTPException(status_code=400, detail="无效的网站名称")
    
    # 验证日期格式
    try:
        from datetime import datetime
        datetime.strptime(date, "%Y-%m-%d_%H_%M_%S")
    except ValueError:
        raise HTTPException(status_code=400, detail="日期格式错误，应为: YYYY-MM-DD_HH_MM_SS")
    
    return content_manager.get_content_detail(site_name, date)

@router.get("/file/{site_name}/{date}/{page_name}/{file_type}/{file_name}")
def get_file(
    site_name: str, 
    date: str, 
    page_name: str, 
    file_type: str, 
    file_name: str
):
    """
    下载或查看具体文件
    
    参数说明:
    - site_name: 网站名称，支持: gys, travelsky, travelskyir
    - date: 爬取时间目录名，格式: YYYY-MM-DD_HH_MM_SS
    - page_name: 页面名称
    - file_type: 文件类型，支持: txt, image
    - file_name: 文件名
    
    返回:
    - 直接返回文件内容，浏览器会根据文件类型进行处理
    
    示例:
    GET /content/file/gys/2024-01-01_10_30_15/home/txt/home.txt
    GET /content/file/gys/2024-01-01_10_30_15/home/image/logo.png
    
    注意: 
    - txt文件会直接在浏览器中显示
    - 图片文件会直接显示或下载
    """
    if site_name not in settings.data_paths:
        raise HTTPException(status_code=404, detail="网站不存在")
    
    if file_type not in ["txt", "image"]:
        raise HTTPException(status_code=400, detail="文件类型错误，支持: txt, image")
    
    file_path = Path(settings.data_paths[site_name]) / date / page_name / file_type / file_name
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="文件不存在")
    
    return FileResponse(file_path)

@router.delete("/{site_name}/{date}")
def delete_content(
    site_name: str, 
    date: str
):
    """
    删除指定日期的爬取内容
    
    参数说明:
    - site_name: 网站名称，支持: gys, travelsky, travelskyir
    - date: 爬取时间目录名，格式: YYYY-MM-DD_HH_MM_SS
    
    返回:
    - success: 布尔值
    - message: 成功或错误信息
    
    示例:
    DELETE /content/gys/2024-01-01_10_30_15
    
    警告: 此操作不可恢复，请谨慎使用
    """
    if site_name not in ["gys", "travelsky", "travelskyir"]:
        raise HTTPException(status_code=400, detail="无效的网站名称")
    
    return content_manager.delete_content(site_name, date)

@router.delete("/{site_name}")
def delete_all_content(
    site_name: str,
    confirm: bool = Query(False, description="确认删除所有内容，必须设置为true")
):
    """
    删除指定网站的所有爬取内容
    
    参数说明:
    - site_name: 网站名称，支持: gys, travelsky, travelskyir
    - confirm: 确认参数，必须设置为true才能执行删除
    
    返回:
    - success: 布尔值
    - message: 成功或错误信息
    
    示例:
    DELETE /content/gys?confirm=true
    
    警告: 此操作将删除该网站的所有历史数据，不可恢复！
    """
    if site_name not in ["gys", "travelsky", "travelskyir"]:
        raise HTTPException(status_code=400, detail="无效的网站名称")
    
    if not confirm:
        raise HTTPException(status_code=400, detail="必须设置confirm=true才能删除所有内容")
    
    return content_manager.delete_content(site_name)
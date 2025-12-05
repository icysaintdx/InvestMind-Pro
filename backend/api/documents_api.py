from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pathlib import Path
import os

router = APIRouter(prefix="/api/documents", tags=["Documents"])

# docs目录路径
DOCS_DIR = Path(__file__).parent.parent.parent / "docs"

@router.get("/list")
async def list_documents():
    """
    获取docs目录下所有.md文件列表
    """
    try:
        if not DOCS_DIR.exists():
            return JSONResponse(content={"files": [], "error": "docs目录不存在"})
        
        # 获取所有.md文件
        md_files = []
        for file in DOCS_DIR.glob("*.md"):
            if file.is_file():
                md_files.append(file.name)
        
        # 按文件名排序
        md_files.sort()
        
        return JSONResponse(content={
            "files": md_files,
            "count": len(md_files),
            "docs_path": str(DOCS_DIR)
        })
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"读取文档列表失败: {str(e)}")


@router.get("/read/{filename:path}")
async def read_document(filename: str):
    """
    读取指定文档的内容
    """
    try:
        # 安全检查：防止路径遍历攻击
        if ".." in filename or filename.startswith("/"):
            raise HTTPException(status_code=400, detail="非法的文件名")
        
        file_path = DOCS_DIR / filename
        
        # 检查文件是否存在
        if not file_path.exists():
            raise HTTPException(status_code=404, detail=f"文档不存在: {filename}")
        
        # 检查是否是.md文件
        if not filename.endswith(".md"):
            raise HTTPException(status_code=400, detail="只能读取Markdown文件")
        
        # 读取文件内容
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        return JSONResponse(content={
            "filename": filename,
            "content": content,
            "size": len(content)
        })
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"读取文档失败: {str(e)}")

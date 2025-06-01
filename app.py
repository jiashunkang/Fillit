from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
import tempfile
import os
from pathlib import Path
import uvicorn
import logging

# 导入现有模块
from reader import extract_text_from_pdf
from llmparser import parse_resume_with_langchain
from models import ResumeData

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Resume Parser API", version="1.0.0")

@app.post("/parse-resume", response_model=ResumeData)
async def parse_resume(file: UploadFile = File(...)):
    """
    上传PDF简历文件，返回结构化的JSON数据
    """
    try:
        # 验证文件类型
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(status_code=400, detail="只支持PDF文件")
        
        # 创建临时文件保存上传的PDF
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        try:
            # 步骤1: 使用reader.py提取PDF文本
            logger.info(f"开始提取PDF文本: {file.filename}")
            resume_text = extract_text_from_pdf(temp_file_path)
            
            if not resume_text.strip():
                raise HTTPException(status_code=400, detail="无法从PDF中提取文本内容")
            
            # 步骤2: 使用llmparser.py解析为结构化数据
            logger.info("开始使用LLM解析简历内容")
            parsed_resume = parse_resume_with_langchain(resume_text)
            
            logger.info("简历解析完成")
            return parsed_resume
            
        finally:
            # 清理临时文件
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
                
    except Exception as e:
        logger.error(f"解析简历时发生错误: {str(e)}")
        raise HTTPException(status_code=500, detail=f"解析失败: {str(e)}")

@app.get("/")
async def root():
    """
    健康检查接口
    """
    return {"message": "Resume Parser API is running"}

@app.get("/health")
async def health_check():
    """
    健康检查接口
    """
    return {"status": "healthy", "service": "resume-parser"}

if __name__ == "__main__":
    # 确保scratch目录存在
    Path("scratch").mkdir(parents=True, exist_ok=True)
    
    # 启动服务器
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=True
    )
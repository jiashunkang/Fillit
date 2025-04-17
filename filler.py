import asyncio

from gradio_client.utils import value_is_file
from models import PersonalInfo, Education, Experience, Project, ResumeData  # 导入自定义的 Pydantic 模型
from langchain.output_parsers import PydanticOutputParser
from playwright.async_api import (
	Browser,
	Page,
	Playwright,
	async_playwright,
)
import requests
import logging

logger = logging.getLogger(__name__)

# 创建 PydanticOutputParser 实例
parser = PydanticOutputParser(pydantic_object=ResumeData)

def parse_jsonstr(file_path:str)->ResumeData:
    """解析jsonstr"""
    with open(file_path, "r") as f:
        json_str = f.read()
    try:
        parsed_resume = parser.parse(json_str)
    except Exception as e:
        print(f"解析错误: {e}")
        return None
    return parsed_resume

async def fill_resume(resumeData:ResumeData,page:Page)->None:
    await page.goto("https://jobs.mihoyo.com/#/campus/resume/position/edit/5906", timeout=60000, wait_until="domcontentloaded")

    # Fill in Personal Info
    # await page.get_by_role("textbox", name="* 姓名").fill(value = resumeData.personal_info.name)
    await page.get_by_role("textbox", name="* 邮箱").fill(value = resumeData.personal_info.email)
    await page.get_by_role("textbox", name="* 手机号").fill(value = resumeData.personal_info.phone)
    await page.get_by_role("textbox", name="* 专业名称").fill(value = resumeData.education[0].degree)
    await page.get_by_role("textbox", name="* 学校名称").fill(value = resumeData.education[0].school)
    await page.get_by_role("button", name="plus 工作经历").click()
    await page.get_by_role("textbox", name="请填写开始时间").fill(value = "2023-09")
    await page.get_by_role("textbox", name="* 公司名称").fill(value = resumeData.experience[0].company)
    await page.get_by_role("textbox", name="* 职位名称").fill(value = resumeData.experience[0].role)
    await page.get_by_role("textbox", name="* 工作职责").fill(value = "\n".join(resumeData.experience[0].description))


async def fill_input_with_text(page:Page,xpath:str,text:str)->None:
    """在指定的xpath元素填入内容"""
    try:
        await page.locator(f"xpath={xpath}").fill(text)
        logger.info(f"Filled {xpath} with content: {text}")
    except Exception as e:
        logger.error(f"Error filling {xpath}: {str(e)}")

# async def main():
#     # 启动本机的chrome
#     async with async_playwright() as pw:	
#         browser = await pw.chromium.connect_over_cdp("http://localhost:9222")
#         default_context = browser.contexts[0]
#         page = default_context.pages[0]
#         await fill_resume(page)
    
#     print('Press Enter to close the browser...')
#     await asyncio.get_event_loop().run_in_executor(None, input)

async def main():
    # with open("./cv.txt", "r") as f:
    #     resume_str = f.read()
    #     resume_data = parser.parse(resume_str)
    # 启动本机的chrome
    async with async_playwright() as pw:	
        browser = await pw.chromium.connect_over_cdp("http://localhost:9222")
        default_context = browser.contexts[0]
        page = default_context.pages[0]
        await fill_input_with_text(page,"//div/div/div/section/div/div/div/div/div/div/div[2]/div/div/div/div/form/div[3]/div[2]/div/div/div/div/div[2]/div/div/input","张三")
    
    print('Press Enter to close the browser...')
    await asyncio.get_event_loop().run_in_executor(None, input)

if __name__ == "__main__":
    asyncio.run(main())
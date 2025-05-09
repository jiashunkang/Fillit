import json
from typing import List
from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.prompts.base import Message,UserMessage, AssistantMessage
from mybrowser import BrowserInstance
import asyncio
import logging

logging.disable(logging.INFO)

# 初始化 FastMCP server
mcp = FastMCP("browser")

browser_instance = None  # 全局浏览器实例
clickable_items = {}  # 页面可交互组件
page = None  # 页面实例

# 每次填写或点击前刷新一下可交互元素，确保xpath index能和页面同步，因为有时候点击按钮后会打乱原本DOM顺序
def refresh_clickable_items():
    global clickable_items
    try:
        with open("clickable_items.json", "r", encoding="utf-8") as f:
            clickable_items = json.load(f)
    except FileNotFoundError:
        clickable_items = {}
    except json.JSONDecodeError as e:
        clickable_items = {}

# 初始化默认去到某个简历网址
@mcp.tool()
async def initialize_page(url:str= "https://jobs.mihoyo.com/#/campus/resume/position/edit/5906"):
    """异步连接浏览器,并前往url的页面"""
    global browser_instance
    global page
    context = None
    if browser_instance is None:
        browser_instance = BrowserInstance()
        context = await browser_instance.connect()
    existing_page = await browser_instance.get_existing_page(url)
    # 优先查看当前浏览器有没有该页面
    if existing_page is not None:
        page = existing_page
        return
    if page is None:
        # 页面为空，创建新页面
        page = await context.new_page()
    print(f"当前页面URL: {page.url}")
    if page.url != url:
        await page.goto(url, wait_until="domcontentloaded", timeout=30000)  # 等待页面加载完成
        await asyncio.sleep(3)  # 等待页面加载完成

async def close_browser():
    """关闭浏览器实例"""
    if browser_instance:
        await browser_instance.close()

@mcp.tool()
async def get_webpage_input() -> str:
    """获取网页所有输入框信息,返回网页元素的index,tag,description"""
    global browser_instance
    global clickable_items
    global page

    # 刷新页面上可交互元素
    clickable_items = await browser_instance.return_clickable_item(page)
    results = []
    
    for elem in clickable_items["input_elements"]:
        index = elem.get("index")
        tag = elem.get("tag")
        # xpath = elem.get("xpath")
        desc = elem.get("description", [])

        # 处理 description：如果是字符串，转为列表；否则拼接成字符串
        if isinstance(desc, str):
            desc_str = desc
        else:
            desc_str = " | ".join(filter(None, desc))  # 过滤空字符串后拼接

        results.append({
            "index": index,
            "tag": tag,
            # "xpath": xpath,
            "description": desc_str
        })
    return json.dumps(results, ensure_ascii=False)

@mcp.tool()
async def get_webpage_button() -> str:
    """获取网页所有按钮信息,返回网页元素的index,tag,description"""
    global browser_instance
    global clickable_items
    global page

    # 刷新页面上可交互元素
    clickable_items = await browser_instance.return_clickable_item(page)
    results = []
    
    for elem in clickable_items["clickable_elements"]:
        if elem.get("tag") == "button":
            index = elem.get("index")
            tag = elem.get("tag")
            # xpath = elem.get("xpath")
            desc = elem.get("description", [])

            # 处理 description：如果是字符串，转为列表；否则拼接成字符串
            if isinstance(desc, str):
                desc_str = desc
            else:
                desc_str = " | ".join(filter(None, desc))  # 过滤空字符串后拼接

            results.append({
                "index": index,
                "tag": tag,
                # "xpath": xpath,
                "description": desc_str
            })
    return json.dumps(results, ensure_ascii=False)

@mcp.tool()
async def fill_index_with_content(index: int, content: str) -> str:
    """输入content到指定的index元素"""
    refresh_clickable_items()
    xpath = None
    for elem in clickable_items["input_elements"]:
        if int(elem.get("index")) == index:
            xpath = elem.get("xpath")
            break
    if xpath is None:
        return f"Element with index {index} not found."
    # 填content到指定xpath
    global browser_instance
    global page
    result = await browser_instance.fill(page, xpath, content)
    if result:
        await page.locator(selector=f"xpath={xpath}").press("Enter")
        return f"Filled"
    else:
        return f"Failed to fill"
       
@mcp.tool()
async def click_index(index: int) -> str:
    """点击指定index的元素,注意当点击按钮有添加栏目作用的时候，需要重新获取DOM信息"""
    xpath = None
    for elem in clickable_items["clickable_elements"]:
        if int(elem.get("index")) == index:
            xpath = elem.get("xpath")
            break
    if xpath is None:
        return f"Element with index {index} not found."
    # 点击指定xpath元素
    global browser_instance
    global page
    if await browser_instance.click(page, xpath):
        return f"Clicked"
    else:
        return f"Failed to click"

@mcp.tool()
async def get_resume_content() -> str:
    """获取简历内容"""
    with open("cv.txt", "r", encoding="utf-8") as f:
        # 去除换行符和空格
        resume_content = f.read().replace("\n", "").replace(" ", "")
    return json.dumps(resume_content, ensure_ascii=False)

@mcp.prompt()
def fill_resume_start(url: str) -> List[Message]:
    """Initiates a debugging help session."""
    return [
        UserMessage(f"你是一个操作浏览器的Agent，请读取我的简历，并填写到网页url为\"{url}\"的简历输入框。当点击了按钮导致添加了栏目，你需要重新读取变化后的DOM元素。我希望你在最初先决定好添加几次栏目，最后再统一填写，只需要调用一次读取DOM元素的函数。"),
        AssistantMessage("我会先评估简历内容，确定需要添加多少实习经历和项目经历，然后获取网页按钮信息，一次性添加所需栏目，最后统一填写内容。由于网络浏览器限制，如果有输入错误或无关的的输入框我会跳过")
    ]

async def main():
    global browser_instance
    await initialize_browser()
    result = await get_webpage_input()
    print(result)
    # print(result)
    # result = await get_webpage_button()
    # print(result)
    # result = await fill_index_with_content(12, "测试内容")
    await browser_instance.close()
    

if __name__ == "__main__":
    # asyncio.run(main())
    mcp.run(transport='stdio')
import asyncio
import logging
from typing import Dict, List, Optional, Any, Union

from playwright.async_api import Browser,BrowserContext, Page, Playwright, async_playwright
from browser_use.dom.views import DOMBaseNode, DOMElementNode, DOMState, DOMTextNode
from browser_use import DomService
import json
from jsutils import get_nearest_text_from_label_span_div

logger = logging.getLogger(__name__)

class BrowserInstance:
    def __init__(self):
        self.playwright:Playwright = None
        self.browser:Browser = None
        self.default_context = None
        self.page:Page = None
        self.dom_service = None
        self.return_clickable_items_cache: Dict[str, Dict[str, List[Dict[str, Any]]]] = {}
        
    async def connect(self, cdp_url: str = "http://localhost:9222"):
        """建立与Chrome DevTools Protocol的连接"""
        self.playwright = await async_playwright().start()
        self.browser:Browser = await self.playwright.chromium.connect_over_cdp(cdp_url)
        self.default_context:BrowserContext = self.browser.contexts[0]
        self.page = await self.default_context.new_page()
        logger.info(f"Connected to browser at {cdp_url}")
        return self.default_context
    
    async def get_dom_service(self, page: Page):
        """获取页面的DOM服务"""
        if not self.dom_service:
            self.dom_service = DomService(page)
        return self.dom_service
    
    async def fill(self, page: Page, xpath: str, content: str) -> bool:
        """在指定的xpath元素填入内容"""
        try:
            await page.locator(f"xpath={xpath}").fill(content)
            logger.info(f"Filled {xpath} with content: {content}")
            return True
        except Exception as e:
            logger.error(f"Error filling {xpath}: {str(e)}")
            return False
    
    async def click(self, page: Page, xpath: str) -> bool:
        """点击指定的xpath元素"""
        try:
            await  page.locator(f"xpath={xpath}").click()
            logger.info(f"Clicked element at {xpath}")
            return True
        except Exception as e:
            logger.error(f"Error clicking {xpath}: {str(e)}")
            return False
    
    async def return_clickable_item(self, page: Page) -> Dict[str, List[Dict[str, Any]]]:
        """
        返回页面上所有可点击和可输入元素的信息
        用于LLM判断点击或输入操作
        """
        dom_service = await self.get_dom_service(page)
        dom_state: DOMState = await dom_service.get_clickable_elements(highlight_elements=False,viewport_expansion=-1)
        
        clickable_items = []
        input_items = []
        i = -1
        for element in dom_state.selector_map.values():
            i += 1
            element_info = {
                "index": i,
                "tag": element.tag_name,
                "xpath": element.xpath,
                "description": []
            }
            
            # 获取最近的文本内容作为该元素Description信息
            result = await get_nearest_text_from_label_span_div(page, element.xpath)
            # text = result["closest"]["text"]
            if result and "closest" in result and "text" in result["closest"]:
                element_info["description"].append(result["closest"]["text"])
            else:
                element_info["description"] = ""
            
            # 添加placeholder,id,title信息到Description
            if 'placeholder' in element.attributes:
                element_info["description"].append(element.attributes['placeholder'])
            if 'id' in element.attributes:
                element_info["description"].append("#"+element.attributes['id'])
            if 'title' in element.attributes:
                element_info["description"].append(element.attributes['title'])
                
            # 区分可输入和可点击，减少LLM的token消耗
            if element.tag_name in ['input', 'textarea', 'select']:
                input_items.append(element_info)
            else:
                clickable_items.append(element_info)
        
        # 缓存本地json文件供之后读取
        with open("clickable_items.json", "w", encoding="utf-8") as f:
            json.dump({
                "clickable_elements": clickable_items,
                "input_elements": input_items
            }, f, ensure_ascii=False)

        return {
            "clickable_elements": clickable_items,
            "input_elements": input_items
        }
    
    async def close(self):
        """关闭浏览器连接"""
        if self.playwright:
            await self.playwright.stop()
            logger.info("Browser connection closed")


async def example_usage():
    """示例用法"""
    browser_instance = BrowserInstance()
    
    try:
        # 连接到浏览器
        context = await browser_instance.connect()
        page = await context.new_page()
        await page.goto("https://jobs.mihoyo.com/#/campus/resume/position/edit/5906",wait_until='domcontentloaded')
        await asyncio.sleep(3)  # 等待页面加载完成
        # 获取所有可点击元素
        clickable_items = await browser_instance.return_clickable_item(page)
        print("Clickable elements:")
        for i, item in enumerate(clickable_items["clickable_elements"]):
            print(f"Element {item['index']}: {item['tag']} - Closest text: {item.get('description', '')}")
        
        print("\nInput elements:")
        for i, item in enumerate(clickable_items["input_elements"]):
            print(f"Element {item['index']}: {item['tag']} - Des: {" ".join(item.get('description', ''))}")
        
        print('Press Enter to close the browser...')
        await asyncio.get_event_loop().run_in_executor(None, input)
    
    finally:
        # 关闭浏览器连接
        await browser_instance.close()


if __name__ == "__main__":
    asyncio.run(example_usage())
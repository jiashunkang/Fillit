import asyncio

from browser_use.dom.views import DOMBaseNode, DOMElementNode, DOMState, DOMTextNode
from pydantic_core.core_schema import is_instance_schema
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
from browser_use import DomService
from jsutils import get_nearest_text_from_label_span_div

logger = logging.getLogger(__name__)

async def main():
    # 启动本机的chrome
    async with async_playwright() as pw:	
        browser = await pw.chromium.connect_over_cdp("http://localhost:9222")
        default_context = browser.contexts[0]
        page = await default_context.new_page()
        await page.goto("https://jobs.mihoyo.com/#/campus/resume/position/edit/5906", timeout=60000, wait_until="domcontentloaded")
        await asyncio.sleep(2)
        dom_service = DomService(page)
        dom_state:DOMState = await dom_service.get_clickable_elements(highlight_elements=True,viewport_expansion=-1)
        i = -1
        for element in dom_state.selector_map.values():
            i += 1
            # if element.tag_name in ['input','textarea','select']:
            if element.tag_name in ['button']:
                print(f"Element {i}:")
                print(f"Tag: {element.tag_name}")
                print(f"XPath: {element.xpath}")
                # print(f"Attributes: {element.attributes}")
                # Find its children and if it is span then print its text content
                # if element.children:
                #     for child in element.children:
                #         if isinstance(child,DOMTextNode):
                            # print(f"Child: {child.text}")
                            # print(f"Child XPath: {child.xpath}")
                            # print(f"Child Attributes: {child.attributes}")

                result = await get_nearest_text_from_label_span_div(page,element.xpath)
                text = result["closest"]["text"]
                if text:
                    print(f"Text: {text}")     
                if 'id' in element.attributes:
                    print(f"ID: {element.attributes['id']}")
                if 'placeholder' in element.attributes:
                    print(f"PH: {element.attributes['placeholder']}")
            
    
    print('Press Enter to close the browser...')
    await asyncio.get_event_loop().run_in_executor(None, input)

if __name__ == "__main__":
    asyncio.run(main())
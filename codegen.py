import asyncio
from playwright.async_api import async_playwright

async def main():
    
    async with async_playwright() as p:
        # 连接已经开启的chrome
        browser = await p.chromium.connect_over_cdp("http://localhost:9222")
        default_context = browser.contexts[0]
        page = default_context.pages[0]

        # # Make sure to run headed.
        # browser = await p.chromium.launch(headless=False)

        # # Setup context however you like.
        # context = await browser.new_context() # Pass any options
        # await context.route('**/*', lambda route: route.continue_())

        # # Pause the page, and start recording manually.
        # page = await context.new_page()
        await page.pause()

asyncio.run(main())
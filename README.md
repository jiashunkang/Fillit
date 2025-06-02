# Fillit

**Fillit** is an AI agent that can automatically fill out your resume on various websites, aiming to reduce the tedious manual effort required to re-enter resume information repeatedly.  
It is built on top of [FastMCP](https://github.com/jlowin/fastmcp) and [Browser Use](https://github.com/browser-use/browser-use). The project functions as an MCP (Multi-Command Protocol) server, providing tools for AI to interact with web page content. **Claude Desktop** is required to invoke these MCP tools.

> ⚠️ This project is still under active development and may contain bugs.

---

## Installation

### Chrome

Only **Google Chrome** is supported, as we rely on the Chrome DevTools Protocol (CDP) to communicate with a running browser instance. This allows bypassing manual authentication steps.

---

### Install UV (Universal Virtual Environment)

On **Windows**, open PowerShell and run:

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

You can verify the installation by running `uv --version`.

---

## Project Requirements

<!-- ### 1. Claude Desktop

Download and install the latest version of Claude Desktop from the official website:

👉 [https://claude.ai/download](https://claude.ai/download)

---

### 2. Set up Claude Configuration

1. Open **Claude Desktop**
2. Navigate to `File > Settings > Developer > Edit Config`
3. You will be redirected to a folder like:
   ```
   C:\Users\<YourUsername>\AppData\Roaming\Claude
   ```
4. Open the file `claude_desktop_config.json` and paste the following content (update the `"directory"` path to where your Fillit project is located):

```json
{
  "mcpServers": {
    "fillit": {
      "command": "uv",
      "args": [
        "--directory",
        "C:\\Users\\<YourUsername>\\Desktop\\Fillit",
        "run",
        "mcpserver.py"
      ]
    }
  }
}
``` -->
### 1. Project Dependencies
```
# Install dependencies
uv sync
```

```
# Activate venv
.venv\Scripts\activate
```

Remember to select venv as python interpreter  in VS Code

### How to start
First step is to start a chrome browser at port 9222.It will generate user data in  in `ChromeUserData` which is separate from your previous Chrome.

```bash
# Start chrome that enables cdp connection
python start_chrome.py
```

Then start the MCP Client (This is a Gradio App runs on port 7860)
```bash
# Start chrome that enables cdp connection
python webui.py
```

In the Gradio App, only Deepseek and Azure OpenAI works now. Leave all the settings blank so that default settings in .env will be applied. Then click `Set LLM` and then click `Connect`, and finally you can chat with the LLM to let it call mcp tools and fill resume.

### Recommend Prompt
```markdown
你是一个专业的浏览器自动化Agent，具备以下MCP工具来操作网页：

**可用工具说明：**
- `initialize_page(url)`: 打开浏览器并导航到指定网页
- `get_resume_content()`: 读取用户的简历内容
- `get_webpage_button()`: 获取当前页面所有可点击按钮的信息（包括"添加实习经历"、"添加项目经历"等按钮）
- `get_webpage_input()`: 获取当前页面所有输入框的信息（包括姓名、学校、公司等输入框）
- `click_index(index)`: 点击指定索引号的按钮
- `fill_index_with_content(index, content)`: 在指定索引号的输入框中填入内容

**任务目标：**
请帮我自动填写简历到 https://jobs.mihoyo.com/#/campus/resume/position/edit/6018

**执行步骤（请严格按此顺序）：**

1. **初始化和分析阶段**
   - 使用 `initialize_page()` 打开目标网页
   - 使用 `get_resume_content()` 读取我的简历内容
   - 分析简历，统计实习经历数量和项目经历数量

2. **DOM结构添加阶段**
   - 使用 `get_webpage_button()` 获取页面按钮信息
   - 根据简历分析结果，找到"添加实习经历"和"添加项目经历"按钮
   - 一次性点击足够次数的添加按钮（例如：如果有3个实习经历，就点击3次"添加实习经历"按钮）
   - ⚠️ **重要**：每次点击后页面DOM会变化，所以要一次性添加完所有需要的栏目

3. **内容填写阶段**
   - 使用 `get_webpage_input()` 重新获取更新后的输入框信息
   - 按照简历内容，使用 `fill_index_with_content()` 逐一填写所有输入框
   - 填写顺序建议：个人信息 → 教育经历 → 实习经历 → 项目经历 → 技能等

**注意事项：**
- 如果某些输入框因为格式限制无法填写，请跳过并继续下一个
- 在点击添加按钮改变DOM结构后，必须重新调用 `get_webpage_input()` 获取最新的输入框信息
- 使用工具时请准确传递index参数，确保操作正确的元素
- 填写内容时请根据输入框的描述信息匹配合适的简历内容

**开始执行任务吧！**
```


## For Developers

### Project Structure
Following are the files that have real function in the project. (Others are just test scripts)

| File              | Description                                                             |
|-------------------|-------------------------------------------------------------------------|
| `mcpserver.py`    | Main MCP server logic and tool definitions                              |
| `mybrowser.py`    | Wrapper for the browser interface (based on Browser Use)                |
| `jsutils.py`      | Utility functions to extract text and attributes from the DOM           |
| `start_chrome.py` | Script to launch a Chrome instance with CDP enabled                     |
| `webui.py` | MCP Client， Gradio App                    |
---

### Run MCP Inspector (For Debugging)

To inspect and debug MCP tools:
- Prerequiste Node.js
- Open powershell as admin

```powershell
cd path\to\Fillit
.venv\Scripts\activate
mcp dev mcpserver.py
```

This will launch an interactive MCP tool inspector.


### Reference
This project adapt the MCP Client from the tutorial below

https://www.gradio.app/guides/building-an-mcp-client-with-gradio#part-2-building-the-mcp-client-with-gradio


### Misc 
Update on 2025/05/10:

I cannot start this project from default user data which is usually in `C:\Users\<YourUsername>\AppData\Local\Google\Chrome\User Data\`
 because Chrome does not support this anymore for security reasons. 

 Further information can be found in `https://developer.chrome.com/blog/remote-debugging-port`

 However, I have updated the script. Now, `start_chrome.py` start from the customized user data directory in `ChromeUserData`. Users can choose to reload their data after launching Chrome by `start_chrome.py` and login to certain job website and store authorizations so that later the AI agent can fill resumes.
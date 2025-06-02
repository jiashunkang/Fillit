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
```prompt
你是一个操作浏览器的Agent，请读取我的简历，并填写到网页url为{}的简历输入框。
你需要先评估简历内容，确定需要添加多少实习经历和项目经历，然后获取网页按钮信息，一次性添加所需栏目，最后获取网页输入框信息，统一填写内容。如果有输入错误或无关的的输入框请跳过。
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
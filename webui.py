import asyncio
import os
import json
from typing import List, Dict, Any, Union, Optional, Type
from contextlib import AsyncExitStack
from enum import Enum

import gradio as gr
from gradio.components.chatbot import ChatMessage
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from dotenv import load_dotenv
from langchain_core.callbacks import CallbackManagerForToolRun
from pydantic import Field, BaseModel, create_model

# LangChain imports for multiple LLM support
from langchain_openai import ChatOpenAI, AzureChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import HumanMessage, AIMessage, SystemMessage
from langchain.tools import BaseTool
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain.prompts import ChatPromptTemplate

# Import resume parsing modules
from models import ResumeData
from reader import extract_text_from_pdf
from llmparser import parse_resume_with_langchain
from langchain.output_parsers import PydanticOutputParser

load_dotenv()

class LLMProvider(Enum):
    OPENAI = "OpenAI"
    AZURE_OPENAI = "Azure OpenAI"
    ANTHROPIC = "Anthropic" 
    GOOGLE = "Google"
    DEEPSEEK = "DeepSeek"

class MCPTool(BaseTool):
    """Wrapper for MCP tools to work with LangChain"""
    name: str = Field(description="Tool name")
    description: str = Field(description="Tool description") 
    session: Any = Field(description="MCP session", exclude=True)
    mcp_input_schema: dict = Field(description="MCP input schema", exclude=True)

    def __init__(self, name: str, description: str, input_schema: dict, session):
        # 创建动态参数模型
        args_schema = self._create_args_schema(input_schema)
        
        super().__init__(
            name=name,
            description=description,
            session=session,
            mcp_input_schema=input_schema,
            args_schema=args_schema
        )

    def _create_args_schema(self, input_schema: dict) -> Type[BaseModel]:
        """将MCP输入schema转换为Pydantic模型"""
        if not input_schema or "properties" not in input_schema:
            # 如果没有参数定义，返回空模型
            return create_model("EmptyArgs")
        
        fields = {}
        properties = input_schema.get("properties", {})
        required = input_schema.get("required", [])
        
        for param_name, param_info in properties.items():
            param_type = param_info.get("type", "string")
            param_desc = param_info.get("description", "")
            param_default = param_info.get("default", ...)
            
            # 转换类型
            if param_type == "string":
                python_type = str
            elif param_type == "integer":
                python_type = int
            elif param_type == "number":
                python_type = float
            elif param_type == "boolean":
                python_type = bool
            else:
                python_type = str
            
            # 设置字段
            if param_name in required and param_default is ...:
                fields[param_name] = (python_type, Field(description=param_desc))
            else:
                default_value = param_default if param_default is not ... else None
                fields[param_name] = (Optional[python_type], Field(default=default_value, description=param_desc))
        
        return create_model("MCPToolArgs", **fields)

    def _run(
        self, 
        run_manager: Optional[CallbackManagerForToolRun] = None,
        **kwargs: Any
    ) -> str:
        """Use the tool synchronously."""
        try:
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(self._arun(run_manager=run_manager, **kwargs))
        except Exception as e:
            return f"Error running tool: {str(e)}"

    async def _arun(
        self,
        run_manager: Optional[CallbackManagerForToolRun] = None,
        **kwargs: Any
    ) -> str:
        """Use the tool asynchronously."""
        try:
            # 过滤掉None值的参数
            filtered_kwargs = {k: v for k, v in kwargs.items() if v is not None}
            
            print(f"Calling MCP tool '{self.name}' with args: {filtered_kwargs}")
            
            result = await self.session.call_tool(self.name, filtered_kwargs)
            if hasattr(result, 'content'):
                if isinstance(result.content, list):
                    return '\n'.join([str(item) for item in result.content])
                return str(result.content)
            return str(result)
        except Exception as e:
            return f"Error executing MCP tool '{self.name}': {str(e)}"

class MCPClientWrapper:
    def __init__(self):
        self.session = None
        self.exit_stack = None
        self.llm = None
        self.tools = []
        self.mcp_tools = []
        self.provider = LLMProvider.OPENAI
    
    def set_llm_provider(self, provider: str, model: str = None, api_key: str = None, base_url: str = None, 
                        azure_endpoint: str = None, api_version: str = None) -> str:
        """动态设置LLM提供商"""
        try:
            self.provider = LLMProvider(provider)
            
            if self.provider == LLMProvider.OPENAI:
                self.llm = ChatOpenAI(
                    model=model or "gpt-4o",
                    api_key=api_key or os.getenv("OPENAI_API_KEY"),
                    base_url=base_url,
                    temperature=0.1
                )
            elif self.provider == LLMProvider.AZURE_OPENAI:
                self.llm = AzureChatOpenAI(
                    deployment_name=model or os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4o"),
                    api_key=api_key or os.getenv("AZURE_OPENAI_API_KEY"),
                    azure_endpoint=azure_endpoint or os.getenv("AZURE_OPENAI_ENDPOINT"),
                    api_version=api_version or os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview"),
                    temperature=0.1
                )
            elif self.provider == LLMProvider.ANTHROPIC:
                self.llm = ChatAnthropic(
                    model=model or "claude-3-5-sonnet-20241022",
                    api_key=api_key or os.getenv("ANTHROPIC_API_KEY"),
                    temperature=0.1
                )
            elif self.provider == LLMProvider.GOOGLE:
                self.llm = ChatGoogleGenerativeAI(
                    model=model or "gemini-pro",
                    google_api_key=api_key or os.getenv("GOOGLE_API_KEY"),
                    temperature=0.1
                )
            elif self.provider == LLMProvider.DEEPSEEK:
                self.llm = ChatOpenAI(
                    model=model or "Pro/deepseek-ai/DeepSeek-V3",
                    api_key=api_key or os.getenv("DEEPSEEK_API_KEY"),
                    base_url=base_url or "https://api.siliconflow.cn/v1",
                    temperature=0.1
                )
            
            return f"Successfully switched to {provider} with model {model or 'default'}"
        except Exception as e:
            return f"Error setting LLM provider: {str(e)}"
    
    def connect(self, server_path: str) -> str:
        return loop.run_until_complete(self._connect(server_path))
    
    async def _connect(self, server_path: str) -> str:
        if self.exit_stack:
            await self.exit_stack.aclose()
        
        self.exit_stack = AsyncExitStack()
        
        is_python = server_path.endswith('.py')
        command = "python" if is_python else "node"
        
        server_params = StdioServerParameters(
            command=command,
            args=[server_path],
            env={"PYTHONIOENCODING": "utf-8", "PYTHONUNBUFFERED": "1"}
        )
        
        stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
        self.stdio, self.write = stdio_transport
        
        self.session = await self.exit_stack.enter_async_context(ClientSession(self.stdio, self.write))
        await self.session.initialize()
        
        response = await self.session.list_tools()
        
        # 创建LangChain工具
        self.mcp_tools = []
        for tool in response.tools:
            mcp_tool = MCPTool(
                name=tool.name,
                description=tool.description or f"MCP tool: {tool.name}",
                input_schema=tool.inputSchema or {},
                session=self.session
            )
            self.mcp_tools.append(mcp_tool)
            print(f"Registered tool: {mcp_tool.name}")
            print(f"  Description: {mcp_tool.description}")
            print(f"  Input schema: {tool.inputSchema}")
            print(f"  Args schema: {mcp_tool.args_schema}")
        
        tool_names = [tool.name for tool in self.mcp_tools]
        return f"Connected to MCP server. Available tools: {', '.join(tool_names)}"
    
    def process_message(self, message: str, history: List[Union[Dict[str, Any], ChatMessage]]) -> tuple:
        if not self.session or not self.llm:
            error_msg = "Please connect to an MCP server and set an LLM provider first."
            return history + [
                {"role": "user", "content": message}, 
                {"role": "assistant", "content": error_msg}
            ], gr.Textbox(value="")
        
        new_messages = loop.run_until_complete(self._process_query(message, history))
        return history + [{"role": "user", "content": message}] + new_messages, gr.Textbox(value="")
    
    async def _process_query(self, message: str, history: List[Union[Dict[str, Any], ChatMessage]]):
        # 构建消息历史
        messages = []
        for msg in history:
            if isinstance(msg, ChatMessage):
                role, content = msg.role, msg.content
            else:
                role, content = msg.get("role"), msg.get("content")
            
            if role == "user":
                messages.append(HumanMessage(content=content))
            elif role == "assistant":
                messages.append(AIMessage(content=content))
            elif role == "system":
                messages.append(SystemMessage(content=content))
        
        messages.append(HumanMessage(content=message))
        
        result_messages = []
        
        try:
            # 如果有工具可用，使用工具
            if self.mcp_tools:
                # 创建提示模板
                prompt = ChatPromptTemplate.from_messages([
                    ("system", "You are a helpful assistant that can use tools to answer questions. When calling tools, make sure to provide all required parameters."),
                    ("human", "{input}"),
                    ("placeholder", "{agent_scratchpad}"),
                ])
                
                # 创建代理
                agent = create_openai_tools_agent(self.llm, self.mcp_tools, prompt)
                agent_executor = AgentExecutor(
                    agent=agent, 
                    tools=self.mcp_tools, 
                    verbose=True,
                    max_iterations=10,
                    handle_parsing_errors=True
                )
                
                # 执行查询
                response = await agent_executor.ainvoke({"input": message})
                
                result_messages.append({
                    "role": "assistant",
                    "content": response["output"]
                })
            else:
                # 直接调用LLM
                response = await self.llm.ainvoke(messages)
                result_messages.append({
                    "role": "assistant",
                    "content": response.content
                })
                
        except Exception as e:
            result_messages.append({
                "role": "assistant",
                "content": f"Error processing request: {str(e)}"
            })
        
        return result_messages

# Resume parsing functions
parser = PydanticOutputParser(pydantic_object=ResumeData)

def handle_pdf_upload(pdf_file):
    """处理PDF上传，解析简历数据"""
    if pdf_file is None:
        return ["请上传PDF文件"] + [gr.update()] * 31
    
    try:
        # PDF提取文字
        resume_str = extract_text_from_pdf(pdf_file.name)
        if resume_str is None:
            return ["解析错误: 无法提取文本"] + [gr.update()] * 31
        
        # 解析简历
        parsed_resume = parse_resume_with_langchain(resume_str)
        
        # 更新个人信息
        personal_updates = [
            parsed_resume.personal_info.name,
            parsed_resume.personal_info.email,
            parsed_resume.personal_info.phone,
            parsed_resume.personal_info.address
        ]

        # 教育经历更新（最多5个）
        edu_updates = []
        for i in range(5):
            if i < len(parsed_resume.education):
                edu = parsed_resume.education[i]
                edu_updates += [
                    gr.update(value=edu.school, visible=True),
                    gr.update(value=edu.degree, visible=True),
                    gr.update(value=edu.year, visible=True),
                    gr.update(visible=True),
                ]
            else:
                edu_updates += [gr.update(visible=False)] * 4

        # 工作经历更新（最多5个）
        exp_updates = []
        for i in range(5):
            if i < len(parsed_resume.experience):
                exp = parsed_resume.experience[i]
                exp_updates += [
                    gr.update(value=exp.company, visible=True),
                    gr.update(value=exp.role, visible=True),
                    gr.update(value=exp.duration, visible=True),
                    gr.update(value="\n".join(exp.description) if exp.description else "", visible=True),
                    gr.update(visible=True),
                ]
            else:
                exp_updates += [gr.update(visible=False)] * 5

        # 项目经历更新（最多5个）
        proj_updates = []
        for i in range(5):
            if i < len(parsed_resume.projects):
                proj = parsed_resume.projects[i]
                proj_updates += [
                    gr.update(value=proj.name, visible=True),
                    gr.update(value=proj.description, visible=True),
                    gr.update(value=proj.duration, visible=True),
                    gr.update(value="\n".join(proj.bullet_points) if proj.bullet_points else "", visible=True),
                    gr.update(visible=True),
                ]
            else:
                proj_updates += [gr.update(visible=False)] * 5

        return ["解析成功", parsed_resume] + personal_updates + edu_updates + exp_updates + proj_updates + [", ".join(parsed_resume.skills)]
    
    except Exception as e:
        return [f"解析错误: {str(e)}"] + [gr.update()] * 31

loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
client = MCPClientWrapper()

def create_mcp_interface():
    """创建MCP客户端界面"""
    with gr.Column():
        gr.Markdown("# 🤖 Multi-LLM MCP Assistant")
        gr.Markdown("Connect to MCP servers and switch between different LLM providers")
        
        # LLM Provider Selection
        with gr.Row():
            with gr.Column(scale=2):
                provider_dropdown = gr.Dropdown(
                    choices=[p.value for p in LLMProvider],
                    label="LLM Provider",
                    value=LLMProvider.AZURE_OPENAI.value
                )
            with gr.Column(scale=2):
                model_input = gr.Textbox(
                    label="Model/Deployment Name",
                    placeholder="e.g., gpt-4o, claude-3-5-sonnet-20241022",
                    value="gpt-4o"
                )
        
        # 添加Azure OpenAI特定字段
        with gr.Row(visible=True) as azure_row:
            with gr.Column(scale=2):
                azure_endpoint_input = gr.Textbox(
                    label="Azure Endpoint",
                    placeholder="https://your-resource.openai.azure.com/",
                    value=""
                )
            with gr.Column(scale=2):
                api_version_input = gr.Textbox(
                    label="API Version",
                    placeholder="2024-02-15-preview",
                    value="2025-03-01-preview"
                )
        
        with gr.Row():
            with gr.Column(scale=2):
                api_key_input = gr.Textbox(
                    label="API Key (optional)",
                    placeholder="Leave empty to use env vars",
                    type="password"
                )
            with gr.Column(scale=2):
                base_url_input = gr.Textbox(
                    label="Base URL (optional)",
                    placeholder="Custom API endpoint"
                )
            with gr.Column(scale=1):
                set_llm_btn = gr.Button("Set LLM")
        
        llm_status = gr.Textbox(label="LLM Status", interactive=False)
        
        # MCP Server Connection
        with gr.Row(equal_height=True):
            with gr.Column(scale=4):
                server_path = gr.Textbox(
                    label="Server Script Path",
                    placeholder="Enter path to server script (e.g., weather.py)",
                    value="mcpserver.py"
                )
            with gr.Column(scale=1):
                connect_btn = gr.Button("Connect")
        
        status = gr.Textbox(label="MCP Connection Status", interactive=False)
        
        chatbot = gr.Chatbot(
            value=[], 
            height=500,
            type="messages",
            show_copy_button=True,
            avatar_images=("👤", "🤖")
        )
        
        with gr.Row(equal_height=True):
            msg = gr.Textbox(
                label="Your Question",
                placeholder="Ask a question...",
                scale=4
            )
            clear_btn = gr.Button("Clear Chat", scale=1)
        
        # 添加事件处理来显示/隐藏Azure字段
        def toggle_azure_fields(provider):
            if provider == "Azure OpenAI":
                return gr.Row(visible=True)
            else:
                return gr.Row(visible=False)
        
        provider_dropdown.change(
            toggle_azure_fields,
            inputs=provider_dropdown,
            outputs=azure_row
        )
        
        # 修改LLM设置函数调用
        def set_llm_with_azure(provider, model, api_key, base_url, azure_endpoint, api_version):
            return client.set_llm_provider(
                provider=provider,
                model=model,
                api_key=api_key,
                base_url=base_url,
                azure_endpoint=azure_endpoint,
                api_version=api_version
            )
        
        # 事件绑定
        set_llm_btn.click(
            set_llm_with_azure,
            inputs=[provider_dropdown, model_input, api_key_input, base_url_input, 
                   azure_endpoint_input, api_version_input],
            outputs=llm_status
        )
        connect_btn.click(client.connect, inputs=server_path, outputs=status)
        msg.submit(client.process_message, [msg, chatbot], [chatbot, msg])
        clear_btn.click(lambda: [], None, chatbot)

def create_resume_interface():
    """创建简历解析界面"""
    with gr.Column():
        gr.Markdown("# 📄 Resume Parser & Editor")
        
        # 文件上传
        with gr.Row():
            pdf_input = gr.File(label="上传PDF简历", file_types=[".pdf"])
            upload_button = gr.Button("解析简历")
        
        # 错误信息和简历数据
        error_text = gr.Textbox(label="状态信息", visible=True)
        resume_data = gr.JSON(label="解析数据", visible=True)
        
        # 个人信息
        with gr.Column():
            gr.Markdown("### 🧑 个人信息")
            name = gr.Textbox(label="姓名")
            email = gr.Textbox(label="邮箱")
            phone = gr.Textbox(label="电话")
            address = gr.Textbox(label="地址")

        # 教育经历（最多5个）
        edu_components = []
        with gr.Column():
            gr.Markdown("### 🎓 教育经历")
            for i in range(5):
                with gr.Group(visible=False) as group:
                    edu_components.extend([
                        gr.Textbox(visible=False, interactive=True, label=f"学校 {i+1}", show_label=True),
                        gr.Textbox(visible=False, interactive=True, label=f"专业 {i+1}", show_label=True),
                        gr.Textbox(visible=False, interactive=True, label=f"年份 {i+1}", show_label=True),
                        group
                    ])

        # 工作经历（最多5个）
        exp_components = []
        with gr.Column():
            gr.Markdown("### 💼 工作经历")
            for i in range(5):
                with gr.Group(visible=False) as group:
                    exp_components.extend([
                        gr.Textbox(visible=False, interactive=True, label=f"公司 {i+1}", show_label=True),
                        gr.Textbox(visible=False, interactive=True, label=f"职位 {i+1}", show_label=True),
                        gr.Textbox(visible=False, interactive=True, label=f"时长 {i+1}", show_label=True),
                        gr.Textbox(visible=False, interactive=True, label=f"工作描述 {i+1}", show_label=True, lines=3),
                        group
                    ])

        # 项目经历（最多5个）
        proj_components = []
        with gr.Column():
            gr.Markdown("### 🏆 项目经历")
            for i in range(5):
                with gr.Group(visible=False) as group:
                    proj_components.extend([
                        gr.Textbox(visible=False, interactive=True, label=f"项目名称 {i+1}", show_label=True),
                        gr.Textbox(visible=False, interactive=True, label=f"项目描述 {i+1}", show_label=True, lines=2),
                        gr.Textbox(visible=False, interactive=True, label=f"时间 {i+1}", show_label=True),
                        gr.Textbox(visible=False, interactive=True, label=f"项目要点 {i+1}", show_label=True, lines=3),
                        group
                    ])

        skills = gr.Textbox(label="技能列表")

        # 绑定事件
        upload_button.click(
            handle_pdf_upload,
            inputs=[pdf_input],
            outputs=[
                error_text,
                resume_data,
                name, email, phone, address,
                *edu_components,
                *exp_components,
                *proj_components,
                skills
            ]
        )

def main_interface():
    """主界面，包含两个页面的标签页"""
    with gr.Blocks(title="Multi-Function Assistant") as demo:
        with gr.Tabs():
            with gr.TabItem("🤖 MCP Assistant"):
                create_mcp_interface()
            
            with gr.TabItem("📄 Resume Parser"):
                create_resume_interface()
        
    return demo

if __name__ == "__main__":
    # 初始化默认LLM
    client.set_llm_provider(LLMProvider.AZURE_OPENAI.value)
    
    interface = main_interface()
    interface.launch(debug=True)
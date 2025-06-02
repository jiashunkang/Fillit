import os
from openai import OpenAI
import json
import os
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.output_parsers import PydanticOutputParser
from models import ResumeData  # 导入 自定义的Pydantic模型
import time

client = OpenAI(api_key="sk-runqvqjtjnoyurszseqqbdupuciqzsopahjhculttowxyvud", base_url="https://api.siliconflow.cn/v1")
llm = ChatOpenAI(model_name="Pro/deepseek-ai/DeepSeek-V3-1226",
                 api_key="sk-runqvqjtjnoyurszseqqbdupuciqzsopahjhculttowxyvud",
                 base_url = "https://api.siliconflow.cn/v1",
                 max_completion_tokens=4096)
# 使用 PydanticOutputParser 解析 LLM 输出
parser = PydanticOutputParser(pydantic_object=ResumeData)

# 定义 Prompt
prompt_template = PromptTemplate(
    template="""
    你是一个专业的 NLP 解析器。请将以下简历文本解析为结构化 JSON。
    
    文本:
    {resume_text}

    请严格按照这个 JSON 结构输出:
    {format_instructions}
    """,
    input_variables=["resume_text"],
    partial_variables={"format_instructions": parser.get_format_instructions()},
)

def parse_resume_with_langchain(resume_text: str) -> ResumeData:
    """ 调用 LLM 并解析为 Pydantic 结构 """
    formatted_prompt = prompt_template.format(resume_text=resume_text)
    response = llm.invoke(formatted_prompt)
    # print(response)
    # Store json to file, set local time as file name
    with open(f"./scratch/{int(time.time()*1000)}.txt", "w") as f:
        f.write(response.content.replace("```json", "").replace("```", "").strip())
    return parser.parse(response.content.replace("```json", "").replace("```", "").strip())  # 自动转换为 Pydantic 对象

# # 解析简历文本
# with open("./scratch/CV_CNI.txt", "r") as f:
#     resume_str = f.read()
# # parsed_data = parse_resume_with_llm(resume_str)
# parsed_resume = parse_resume_with_langchain(resume_str)

# # 输出解析结果
# print(parsed_resume.model_dump_json(indent=2))
# print(json.dumps(parsed_data, indent=2, ensure_ascii=False))  # 预览解析后的 JSON

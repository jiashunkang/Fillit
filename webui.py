import gradio as gr
import json
from models import ResumeData
from reader import extract_text_from_pdf
from llmparser import parse_resume_with_langchain
from langchain.output_parsers import PydanticOutputParser

resume_state = gr.State()
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

def handle_pdf_upload(pdf_file: gr.File):
    """处理PDF上传，解析简历数据"""
    if pdf_file is None:
        return ["请上传PDF文件"] + [gr.update()] * 31  # 根据组件总数调整
    # pdf提取文字
    resume_str = extract_text_from_pdf(pdf_file.name)
    if resume_str is None:
        return ["解析错误: 无法提取文本"] + [gr.update()] * 31  # 根据组件总数调整
    # 解析简历
    parsed_resume = parse_resume_with_langchain(resume_str)
    # with open("./scratch/CV_CNI.txt", "r") as f:
    #     resume_text = f.read()

    # parsed_resume = parse_resume_with_langchain(resume_text)
    # parsed_resume = parse_jsonstr("./cv.txt")

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
                gr.update(value="\n".join(exp.description), visible=True),
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
                gr.update(value="\n".join(proj.bullet_points), visible=True),
                # gr.update(value=", ".join(proj.skills), visible=True),
                gr.update(visible=True),
            ]
        else:
            proj_updates += [gr.update(visible=False)] * 5

    return ["", parsed_resume] + personal_updates + edu_updates + exp_updates + proj_updates + [", ".join(parsed_resume.skills)]

# 预定义组件
with gr.Blocks() as demo:
    gr.Markdown("# 📄 Resume Parser & Editor")
    
    # 文件上传
    with gr.Row():
        pdf_input = gr.File(label="上传PDF简历", file_types=[".pdf"])
        upload_button = gr.Button("解析简历")
    
    # 错误信息和简历数据
    error_text = gr.Textbox(label="错误信息", visible=True)
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
    with gr.Column() as education_container:
        gr.Markdown("### 🎓 教育经历")
        for _ in range(5):
            with gr.Group(visible=False) as group:
                edu_components.extend([
                    gr.Textbox(visible=False,interactive=True,label="学校",show_label=True),
                    gr.Textbox(visible=False,interactive=True,label="专业",show_label=True),
                    gr.Textbox(visible=False,interactive=True,label="年份",show_label=True),
                    group
                ])

    # 工作经历（最多5个）
    exp_components = []
    with gr.Column() as experience_container:
        gr.Markdown("### 💼 工作经历")
        for _ in range(5):
            with gr.Group(visible=False) as group:
                exp_components.extend([
                    gr.Textbox(visible=False,interactive=True,label="公司",show_label=True),
                    gr.Textbox(visible=False,interactive=True,label="职位",show_label=True),
                    gr.Textbox(visible=False,interactive=True,label="时长",show_label=True),
                    gr.Textbox(visible=False,interactive=True,label="工作描述",show_label=True),
                    group
                ])

    # 项目经历（最多5个）
    proj_components = []
    with gr.Column() as project_container:
        gr.Markdown("### 🏆 项目经历")
        for _ in range(5):
            with gr.Group(visible=False) as group:
                proj_components.extend([
                    gr.Textbox(visible=False,interactive=True,label="项目名称",show_label=True),
                    gr.Textbox(visible=False,interactive=True,label="项目描述",show_label=True),
                    gr.Textbox(visible=False,interactive=True,label="时间",show_label=True),
                    gr.Textbox(visible=False,interactive=True,label="项目要点",show_label=True),
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

demo.launch()
from pydantic import BaseModel
from typing import List, Optional

### Pydantic 模型定义
class PersonalInfo(BaseModel):
    name: Optional[str]
    email: Optional[str]
    phone: Optional[str]
    address: Optional[str]

class Education(BaseModel):
    school: Optional[str]
    degree: Optional[str]
    year: Optional[str]

class Experience(BaseModel):
    company: Optional[str]
    role: Optional[str]
    duration: Optional[str]
    description: Optional[List[str]]

class Project(BaseModel):
    name: Optional[str]
    duration: Optional[str]
    description: Optional[str]
    bullet_points: Optional[List[str]]
    # skills: Optional[List[str]]

class ResumeData(BaseModel):
    personal_info: PersonalInfo
    education: List[Education]
    experience: List[Experience]
    projects: List[Project]
    skills: List[str]
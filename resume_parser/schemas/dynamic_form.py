from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional

class CompanyExperience(BaseModel):
    company_name: str
    position: Optional[str] = None
    job_description: str
    from_date: str  # ISO date string
    to_date: Optional[str] = None
    current_position: bool

class Project(BaseModel):
    title: str
    description: str
    url: Optional[str] = None
    technologies: list[str]
    image: Optional[str] = ""

class DynamicFormData(BaseModel):
    # Personal Information
    firstname: str
    lastname: str
    email: EmailStr
    phone_no: str
    position: str
    id: Optional[str] = None
    resume: str

    # Address
    address_1: str
    address_2: Optional[str] = None
    address_3: Optional[str] = None
    city: str

    # Description
    short_description: str
    full_description: str

    # Dynamic Fields
    skills: List[str] = Field(default_factory=list)
    companies: List[CompanyExperience]
    projects: List[Project]


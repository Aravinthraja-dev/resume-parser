from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from core.config import GOOGLE_API_KEY
import os
import json

os.environ["GOOGLE_API_KEY"] = GOOGLE_API_KEY

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0
)

PROMPT = PromptTemplate(
    input_variables=["resume_text"],
    template="""
You are an AI resume parser.

Return ONLY valid JSON.
No explanations. No markdown. No extra text.
If a value is missing, use empty string.
Do NOT rename fields. Use EXACT key names.
Do NOT invent information.

JSON format:
{{
  "firstname": "",
  "lastname": "",
  "email": "",
  "phone_no": "",
  "position": "",
  "resume": "",
  "address_1": "",
  "address_2": "",
  "address_3": "",
  "city": "",
  "short_description": "",
  "full_description": "",
  "skills": [],
  "companies": [
    {{
      "company_name": "",
      "current_position": false,
      "from_date": "",
      "to_date": "",
      "job_description": "",
      "position": ""
    }}
  ],
  "projects": [
    {{
      "title": "",
      "description": "",
      "technologies": [],
      "url": "",
      "image": ""
    }}
  ]
}}

STRICT RULES:

SKILLS:
- skills MUST be an array of strings
- Return ONLY the TOP 10 skills
- Choose skills that are MOST RELEVANT to:
  1) job experience
  2) projects
- Do NOT include soft skills unless clearly technical
- Do NOT repeat similar skills (e.g., JavaScript & JS → choose one)

PROJECTS:
- Extract ONLY projects explicitly mentioned in the resume
- technologies must be an array of strings
- Do NOT invent projects

DATES (from_date, to_date):
- Always return date as STRING in ISO format: YYYY-MM-DD
- If resume shows only month & year (e.g., "Jan 2005"):
  → return "2005-01-01"
- If resume shows only year (e.g., "2005"):
  → return "2005-01-01"
- If date is missing or unclear → empty string

GENERAL:
- Do not invent company names, dates, roles, or skills
- Do not omit required fields
- Preserve factual accuracy strictly

Resume:
{resume_text}
"""
)

def extract_resume_data(resume_text: str) -> dict:
    if not resume_text.strip():
        raise ValueError("Resume text is empty")

    chain = PROMPT | llm
    response = chain.invoke({"resume_text": resume_text})

    raw = response.content.strip()
    cleaned = raw.replace("```json", "").replace("```", "").strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        raise ValueError("Gemini returned invalid JSON")

def normalize_ai_output(data: dict) -> dict:
    # Normalize companies
    for company in data.get("companies", []):
        if not isinstance(company, dict):
            continue

        # Map AI variants
        if "current_position" not in company:
            company["current_position"] = company.get("position", "")

        if "position" not in company and "current_position" in company:
            company["position"] = company.get("current_position", "")

        if "from_date" not in company and "start_date" in company:
            company["from_date"] = company.pop("start_date")

        if "to_date" not in company and "end_date" in company:
            company["to_date"] = company.pop("end_date")

        if "job_description" not in company and "description" in company:
            company["job_description"] = company.pop("description")

        # Ensure required fields
        company.setdefault("position", "")
        company.setdefault("current_position", "")
        company.setdefault("job_description", "")
        company.setdefault("from_date", "")
        company.setdefault("to_date", "")

    # Normalize projects
    for project in data.get("projects", []):
        if not isinstance(project, dict):
            continue

        # title mapping
        if "title" not in project and "project_name" in project:
            project["title"] = project.pop("project_name")

        if "technologies" not in project:
            project["technologies"] = []
        elif isinstance(project["technologies"], str):
            project["technologies"] = [
                t.strip() for t in project["technologies"].split(",") if t.strip()
            ]

        # image
        if project.get("image") is None:
            project["image"] = ""

        # url
        project.setdefault("url", "")

    # Normalize skills
    skills = data.get("skills", [])
    if isinstance(skills, list):
        data["skills"] = [
            s.strip() for s in skills if isinstance(s, str) and s.strip()
        ]

    return data

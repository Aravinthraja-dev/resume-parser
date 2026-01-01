from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import ValidationError
from resume_parser.schemas.dynamic_form import DynamicFormData
from resume_parser.utils.pdf_reader import extract_text_from_pdf
from resume_parser.services.resume_extractor import extract_resume_data, normalize_ai_output
import shutil
import uuid
import os
from core.config import ENV
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
     allow_origins=[
        "http://localhost:4200",
        "https://resume-parser-eight-ashen.vercel.app",
        "https://dreamy-cannoli-56edca.netlify.app"
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "/tmp/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.options("/{path:path}")
async def options_handler(path: str):
    return {}


@app.post("/resume/extract", response_model=DynamicFormData)
async def extract_resume(file: UploadFile = File(...)):

    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are allowed"
        )

    file_id = f"{uuid.uuid4()}.pdf"
    file_path = os.path.join(UPLOAD_DIR, file_id)

    try:
        # Save file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Extract text
        resume_text = extract_text_from_pdf(file_path)

        if not resume_text:
            raise HTTPException(
                status_code=400,
                detail="Unable to extract text from PDF"
            )

        # Call Gemini
        extracted_data = extract_resume_data(resume_text)
        extracted_data["resume"] = file.filename

        extracted_data = normalize_ai_output(extracted_data)

        # 🔥 Validate against Pydantic schema
        validated_data = DynamicFormData(**extracted_data)

        return validated_data

    except ValidationError as ve:
        raise HTTPException(
            status_code=422,
            detail={
                "message": "Schema validation failed",
                "errors": ve.errors()
            }
        )

    except ValueError as ve:
        raise HTTPException(
            status_code=422,
            detail=str(ve)
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )

    finally:
        if os.path.exists(file_path):
            os.remove(file_path)

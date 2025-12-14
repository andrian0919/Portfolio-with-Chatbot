import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
import os
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional, Dict
import httpx
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

app = FastAPI(title="My Portfolio Backend", version="0.1.0")

load_dotenv()

allowed_origins_env = os.getenv("CORS_ALLOW_ORIGINS")
if allowed_origins_env:
    allowed_origins = [o.strip() for o in allowed_origins_env.split(",") if o.strip()]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
else:
    app.add_middleware(
        CORSMiddleware,
        allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


class ContactRequest(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    subject: str = Field(min_length=2, max_length=200)
    message: str = Field(min_length=5, max_length=5000)


class ContactResponse(BaseModel):
    ok: bool
    message: str


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/api/contact", response_model=ContactResponse)
def submit_contact(payload: ContactRequest) -> ContactResponse:
    if len(payload.message.strip()) == 0:
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    return ContactResponse(ok=True, message="Message received. Thank you!")


class Project(BaseModel):
    title: str
    description: str
    tags: List[str]


@app.get("/api/projects", response_model=List[Project])
def list_projects() -> List[Project]:
    return [
        Project(
            title="Homeowners Subdivision Website",
            description="A comprehensive website for homeowners subdivision community featuring property listings, resident information, and community management tools.",
            tags=["C#", ".NET", "MySQL", "HTML", "Tailwind"],
        ),
        Project(
            title="CCS Sit-In Monitoring System",
            description="A monitoring system for tracking sit-in activities with real-time data visualization and reporting capabilities.",
            tags=["Python", "Flask", "MySQL", "HTML", "CSS"],
        ),
        Project(
            title="Portfolio with AI Chatbot",
            description="Responsive portfolio with Python FastAPI backend and an AI chatbot.",
            tags=["React", "TypeScript", "Vite", "Tailwind", "shadcn-ui", "Radix UI", "FastAPI", "Python", "React Query"],
        ),
    ]


@app.get("/api/cv")
def download_cv():
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    c.setFont("Times-Bold", 16)
    c.drawCentredString(width / 2, height - 1 * inch, "CURRICULUM VITAE")

    c.setFont("Times-Roman", 12)
    y = height - 1.4 * inch
    lines = [
        "Name: Andrian S. Balberos",
        "Residential Address: Jayme Compound, Tipolo",
        "Mandaue City, Cebu",
        "Mobile Number: 09196395581",
        "Date of Birth: October 29, 2003",
        "Nationality: Filipino",
        "E-mail: balberos09123@gmail.com",
    ]
    for line in lines:
        c.drawString(1 * inch, y, line)
        y -= 0.25 * inch

    c.setFont("Times-Bold", 12)
    c.drawString(1 * inch, y - 0.15 * inch, "EDUCATION")
    y -= 0.4 * inch
    c.setFont("Times-Roman", 12)
    c.drawString(1 * inch, y, "BS in Information Technology")
    c.drawString(width / 2 + 0.2 * inch, y, "Senior High School")
    y -= 0.25 * inch
    c.drawString(1 * inch, y, "University of Cebu - Main Campus")
    c.drawString(width / 2 + 0.2 * inch, y, "University of Cebu - Lapu-Lapu & Mandaue")
    y -= 0.25 * inch
    c.drawString(1 * inch, y, "2022 - Present")
    c.drawString(width / 2 + 0.2 * inch, y, "2020 - 2022")

    y -= 0.5 * inch
    c.setFont("Times-Bold", 12)
    c.drawString(1 * inch, y, "EXPERIENCE")
    y -= 0.3 * inch
    c.setFont("Times-Roman", 12)
    c.drawString(1.2 * inch, y, "• Developed websites for Class Projects")

    y -= 0.5 * inch
    c.setFont("Times-Bold", 12)
    c.drawString(1 * inch, y, "SKILLS")
    y -= 0.3 * inch
    c.setFont("Times-Roman", 12)
    skills = [
        "Experienced in MySQL, MS SQL, and SQLite database management",
        "Proficient in HTML, CSS, and Python",
        "Debugging, system troubleshooting, and optimization",
        "Familiar with Git and GitHub for collaborative development",
        "Team collaboration, effective communication, and adaptability",
    ]
    for s in skills:
        c.drawString(1.2 * inch, y, f"• {s}")
        y -= 0.25 * inch

    img_path = os.path.join(os.path.dirname(__file__), "..", "frontend", "public", "images", "profile.jpg")
    if os.path.exists(img_path):
        try:
            c.drawImage(img_path, width - 2.8 * inch, height - 3 * inch, 2.5 * inch, 2.5 * inch, preserveAspectRatio=True, mask='auto')
        except Exception:
            pass

    c.showPage()
    c.save()
    buffer.seek(0)
    return StreamingResponse(buffer, media_type="application/pdf", headers={"Content-Disposition": "attachment; filename=Andrian_Balberos_CV.pdf"})

class Upload(BaseModel):
    data: str
    type: str
    name: Optional[str] = None
    mime: Optional[str] = None

class FlowisePredictRequest(BaseModel):
    question: str
    chatflow_id: Optional[str] = None
    override_config: Optional[Dict] = None
    history: Optional[List[Dict]] = None
    uploads: Optional[List[Upload]] = None

class FlowisePredictResponse(BaseModel):
    ok: bool
    data: Dict

def _flowise_settings() -> Dict[str, Optional[str]]:
    base_url = os.getenv("FLOWISE_BASE_URL")
    api_key = os.getenv("FLOWISE_API_KEY")
    default_chatflow_id = os.getenv("FLOWISE_CHATFLOW_ID")
    return {
        "base_url": base_url,
        "api_key": api_key,
        "default_chatflow_id": default_chatflow_id,
    }

@app.post("/api/flowise/predict")
async def flowise_predict(payload: FlowisePredictRequest):
    settings = _flowise_settings()
    if not settings["base_url"]:
        raise HTTPException(status_code=500, detail="FLOWISE_BASE_URL is not configured")
    chatflow_id = payload.chatflow_id or settings["default_chatflow_id"]
    if not chatflow_id:
        raise HTTPException(status_code=400, detail="chatflow_id is required")
    url = f"{settings['base_url'].rstrip('/')}/api/v1/prediction/{chatflow_id}"
    headers = {"Content-Type": "application/json"}
    if settings["api_key"]:
        headers["Authorization"] = f"Bearer {settings['api_key']}"
    body: Dict = {"question": payload.question}
    if payload.override_config is not None:
        body["overrideConfig"] = payload.override_config
    if payload.history is not None:
        body["history"] = payload.history
    if payload.uploads is not None:
        body["uploads"] = [u.model_dump() for u in payload.uploads]
    async with httpx.AsyncClient(timeout=30) as client:
        try:
            resp = await client.post(url, json=body, headers=headers)
        except httpx.RequestError as e:
            raise HTTPException(status_code=502, detail=str(e))
    if resp.status_code >= 400:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)
    return JSONResponse(content=resp.json())

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)

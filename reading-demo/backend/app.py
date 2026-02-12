import os
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from rag import answer_question

app = FastAPI(title="Reading Assistant Demo")

# Allow extension to call localhost
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # demo only; tighten later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str
    courseId: str | None = None
    tenantId: str | None = None

@app.get("/health")
def health():
    return {"ok": True}

@app.post("/chat")
def chat(req: ChatRequest):
    # Safe handling demo default: do NOT store req.message anywhere.
    # (In production you’d store only session metadata unless user/instructor opts in.)
    course_id = req.courseId or os.environ.get("DEFAULT_COURSE_ID")
    tenant_id = req.tenantId or os.environ.get("DEFAULT_TENANT_ID")

    return answer_question(req.message, course_id=course_id, tenant_id=tenant_id)

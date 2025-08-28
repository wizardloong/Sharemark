from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from repos import feedback_repo

from pydantic import BaseModel, EmailStr, constr
import html

router = APIRouter()

templates = Jinja2Templates(directory="templates")

@router.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


class FeedbackRequest(BaseModel):
    name: constr(strip_whitespace=True, min_length=1, max_length=100)
    email: EmailStr
    message: constr(strip_whitespace=True, min_length=1, max_length=2000)
    subscribe: bool = False


@router.post("/feedback", response_class=JSONResponse)
async def submit_feedback(
    name: str = Form(...),
    email: EmailStr = Form(...),
    message: str = Form(...),
    subscribe: bool = Form(False)
):
    # Валидация через модель
    feedback = FeedbackRequest(
        name=name,
        email=email,
        message=message,
        subscribe=subscribe
    )

    # Защита от XSS (если где-то потом рендеришь в HTML)
    safe_message = html.escape(feedback.message)

    # Сохранение в БД через ORM или параметризованный SQL
    feedback_repo.saveFeedback(
        name=feedback.name,
        email=feedback.email,
        message=safe_message,
        subscribe=feedback.subscribe
    )

    return {"success": True, "message": "Feedback received", "name": feedback.name}

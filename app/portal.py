from fastapi import APIRouter, Request, Form, Depends, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from repos import feedback_repo, future_repo, user_price_repo
from pydantic import EmailStr
import html
from schemas import FeedbackRequest, VoteRequest, PriceRequest
from storage.mysql import get_db
from repos import future_vote_repo
from infrastructure.helpers.client_ip import get_client_ip

router = APIRouter()

templates = Jinja2Templates(directory="public/templates")

@router.get("/", response_class=HTMLResponse)
async def read_root(
    request: Request,
    db: Session = Depends(get_db)
):
    futures = future_repo.getFutures(db)
    return templates.TemplateResponse("index.html", {"request": request, "futures": futures})

@router.get("/thank-you", response_class=HTMLResponse)
async def read_sharing_deadend(request: Request):
    return templates.TemplateResponse("sharing_deadend.html", {"request": request})

@router.get("/404", response_class=HTMLResponse)
async def read_404(request: Request):
    return templates.TemplateResponse("sharing_404.html", {"request": request})


@router.post("/feedback", response_class=JSONResponse)
async def submit_feedback(
    request: Request,
    name: str = Form(...),
    email: EmailStr = Form(...),
    message: str = Form(...),
    subscribe: bool = Form(False),
    db: Session = Depends(get_db)
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

    ip = get_client_ip(request)
    userAgent = request.headers.get("User-Agent", "unknown")

    # Сохранение в БД через ORM или параметризованный SQL
    feedback_repo.saveFeedback(
        db,
        name=feedback.name,
        email=feedback.email,
        message=safe_message,
        subscribe=feedback.subscribe,
        ip=ip,
        userAgent=userAgent
    )

    return {"success": True, "message": "Feedback received", "name": feedback.name}


@router.post("/set_vote", response_class=JSONResponse)
async def set_vote(
    data: VoteRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    if data.vote_count < 0 or data.vote_count > 3:
        raise HTTPException(status_code=400, detail="Vote must be between 0 and 3")
    
    ip = get_client_ip(request)
    userAgent = request.headers.get("User-Agent", "unknown")

    new_vote_id = future_vote_repo.saveFutureVote(
        db,
        future_id=data.feature_id,
        ip=ip,
        userAgent=userAgent,
        vote=data.vote_count
    )

    return {"success": True, "vote_id": new_vote_id, "total_votes": data.vote_count}


@router.post("/set_price", response_class=JSONResponse)
async def set_vote(
    data: PriceRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    ip = get_client_ip(request)
    userAgent = request.headers.get("User-Agent", "unknown")

    user_price_repo.savePrice(
        db,
        ip=ip,
        userAgent=userAgent,
        price=data.price
    )

    return {"success": True}


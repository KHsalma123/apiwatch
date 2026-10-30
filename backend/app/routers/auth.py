from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.core.rate_limit import limiter
from app.database.mongo import get_db
from app.schemas.auth import LoginIn, RegisterIn, TokenOut, UserOut
from app.security.tokens import create_access_token
from app.services import users as user_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
async def register(request: Request, data: RegisterIn, db=Depends(get_db)):
    user = await user_service.register(db, data.name, data.email, data.password)
    return user_service.user_out(user)


@router.post("/login", response_model=TokenOut)
@limiter.limit("10/minute")
async def login(request: Request, data: LoginIn, db=Depends(get_db)):
    user = await user_service.authenticate(db, data.email, data.password)
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    return TokenOut(access_token=create_access_token(str(user["_id"])))

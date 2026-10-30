from fastapi import APIRouter, Depends, Response, status

from app.database.mongo import get_db
from app.schemas.auth import ChangePasswordIn, UserOut, UserUpdateIn
from app.security.deps import get_current_user
from app.services import users as user_service

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserOut)
async def me(user=Depends(get_current_user)):
    return user_service.user_out(user)


@router.patch("/me", response_model=UserOut)
async def update_me(data: UserUpdateIn, user=Depends(get_current_user), db=Depends(get_db)):
    updated = await user_service.update_profile(db, user, data.name, data.email)
    return user_service.user_out(updated)


@router.post("/me/change-password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(data: ChangePasswordIn, user=Depends(get_current_user), db=Depends(get_db)):
    await user_service.change_password(db, user, data.current_password, data.new_password)
    return Response(status_code=status.HTTP_204_NO_CONTENT)

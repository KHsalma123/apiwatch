from bson import ObjectId
from fastapi import HTTPException
from pymongo.errors import DuplicateKeyError

from app.security.passwords import DUMMY_HASH, hash_password, verify_password
from app.services.common import utcnow


def user_out(u: dict) -> dict:
    return {"id": str(u["_id"]), "name": u["name"], "email": u["email"], "created_at": u["created_at"]}


async def register(db, name: str, email: str, password: str) -> dict:
    doc = {"name": name, "email": email, "hashed_password": hash_password(password), "created_at": utcnow()}
    try:
        res = await db.users.insert_one(doc)
    except DuplicateKeyError:
        raise HTTPException(status_code=409, detail="An account with this email already exists")
    doc["_id"] = res.inserted_id
    return doc


async def authenticate(db, email: str, password: str) -> dict | None:
    user = await db.users.find_one({"email": email})
    if user is None:
        # Hash anyway so response time does not reveal whether the email exists.
        verify_password(password, DUMMY_HASH)
        return None
    return user if verify_password(password, user["hashed_password"]) else None


async def update_profile(db, user: dict, name: str | None, email: str | None) -> dict:
    changes = {}
    if name is not None:
        changes["name"] = name.strip()
    if email is not None:
        changes["email"] = email
    if not changes:
        return user
    try:
        await db.users.update_one({"_id": user["_id"]}, {"$set": changes})
    except DuplicateKeyError:
        raise HTTPException(status_code=409, detail="An account with this email already exists")
    return await db.users.find_one({"_id": user["_id"]})


async def change_password(db, user: dict, current: str, new: str) -> None:
    if not verify_password(current, user["hashed_password"]):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    await db.users.update_one({"_id": user["_id"]}, {"$set": {"hashed_password": hash_password(new)}})

from fastapi import Form
from pydantic import BaseModel, Field
from bson import ObjectId


class UserBase(BaseModel):
    username: str
    password: str


class UserUpdate(UserBase):
    pass


class UserRead(UserBase):
    id: int = Field(..., alias="_id")
    username: str
    password: str

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: str
        }


class UserDelete(UserBase):
    id: int = Field(..., alias="_id")

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: str
        }

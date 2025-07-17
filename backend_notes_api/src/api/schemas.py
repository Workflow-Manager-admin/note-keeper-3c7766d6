from pydantic import BaseModel, Field
from typing import Optional

# PUBLIC_INTERFACE
class UserBase(BaseModel):
    username: str = Field(..., description="Unique username for the user")

# PUBLIC_INTERFACE
class UserCreate(UserBase):
    password: str = Field(..., description="Password for the user (plain text, will be hashed)")

# PUBLIC_INTERFACE
class UserResponse(UserBase):
    id: int

    class Config:
        orm_mode = True

# PUBLIC_INTERFACE
class NoteBase(BaseModel):
    title: str = Field(..., description="Title of the note")
    content: Optional[str] = Field(None, description="Content of the note")

# PUBLIC_INTERFACE
class NoteCreate(NoteBase):
    pass

# PUBLIC_INTERFACE
class NoteUpdate(NoteBase):
    pass

# PUBLIC_INTERFACE
class NoteResponse(NoteBase):
    id: int
    owner_id: int

    class Config:
        orm_mode = True

# PUBLIC_INTERFACE
class Token(BaseModel):
    access_token: str
    token_type: str

# PUBLIC_INTERFACE
class TokenData(BaseModel):
    username: Optional[str] = None

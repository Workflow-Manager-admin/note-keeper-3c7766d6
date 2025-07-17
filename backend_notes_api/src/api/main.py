from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import List

from . import models, schemas, database, auth, dependencies

app = FastAPI(
    title="Notes API",
    description="Backend API for note-keeper, with authentication and CRUD on notes.",
    version="1.0.0",
    openapi_tags=[
        {"name": "auth", "description": "User registration and authentication."},
        {"name": "notes", "description": "CRUD operations for notes."}
    ]
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    """Create database tables on startup if they don't exist."""
    database.Base = models.Base
    models.Base.metadata.create_all(bind=database.engine)

@app.get("/", tags=["health"])
def health_check():
    """Basic health check endpoint."""
    return {"message": "Healthy"}

# ---------- Auth Endpoints ----------

@app.post("/auth/register", response_model=schemas.UserResponse, tags=["auth"], summary="Register a new user")
def register_user(user: schemas.UserCreate, db: Session = Depends(dependencies.get_db)):
    """Create a new user account.

    - **username**: Unique username
    - **password**: Password (plain text, will be hashed)
    """
    db_user = db.query(models.User).filter(models.User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    hashed_pw = auth.get_password_hash(user.password)
    new_user = models.User(username=user.username, hashed_password=hashed_pw)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@app.post("/auth/token", response_model=schemas.Token, tags=["auth"], summary="User login to obtain JWT token")
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(dependencies.get_db)):
    """Authenticate user and return JWT access token.

    - **username** and **password** fields are required.
    """
    user = db.query(models.User).filter(models.User.username == form_data.username).first()
    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = auth.create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

# ---------- Notes CRUD Endpoints ----------

@app.post(
    "/notes/",
    response_model=schemas.NoteResponse,
    tags=["notes"],
    summary="Create a new note",
    status_code=201,
)
def create_note(
    note: schemas.NoteCreate,
    db: Session = Depends(dependencies.get_db),
    current_user: models.User = Depends(dependencies.get_current_user),
):
    """Create a new note associated with the authenticated user."""
    db_note = models.Note(title=note.title, content=note.content, owner_id=current_user.id)
    db.add(db_note)
    db.commit()
    db.refresh(db_note)
    return db_note

@app.get(
    "/notes/",
    response_model=List[schemas.NoteResponse],
    tags=["notes"],
    summary="List all your notes"
)
def read_notes(
    db: Session = Depends(dependencies.get_db),
    current_user: models.User = Depends(dependencies.get_current_user),
):
    """Get a list of all notes for the current user."""
    notes = db.query(models.Note).filter(models.Note.owner_id == current_user.id).all()
    return notes

@app.get(
    "/notes/{note_id}",
    response_model=schemas.NoteResponse,
    tags=["notes"],
    summary="Get a single note by ID"
)
def read_note(
    note_id: int,
    db: Session = Depends(dependencies.get_db),
    current_user: models.User = Depends(dependencies.get_current_user),
):
    """Retrieve a single note belonging to the current user by its ID."""
    note = db.query(models.Note).filter(models.Note.id == note_id, models.Note.owner_id == current_user.id).first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    return note

@app.put(
    "/notes/{note_id}",
    response_model=schemas.NoteResponse,
    tags=["notes"],
    summary="Update a note"
)
def update_note(
    note_id: int,
    note_update: schemas.NoteUpdate,
    db: Session = Depends(dependencies.get_db),
    current_user: models.User = Depends(dependencies.get_current_user),
):
    """Update the title or content of a note you own."""
    note = db.query(models.Note).filter(models.Note.id == note_id, models.Note.owner_id == current_user.id).first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    note.title = note_update.title
    note.content = note_update.content
    db.commit()
    db.refresh(note)
    return note

@app.delete(
    "/notes/{note_id}",
    status_code=204,
    tags=["notes"],
    summary="Delete a note"
)
def delete_note(
    note_id: int,
    db: Session = Depends(dependencies.get_db),
    current_user: models.User = Depends(dependencies.get_current_user),
):
    """Delete a note by ID if you own it."""
    note = db.query(models.Note).filter(models.Note.id == note_id, models.Note.owner_id == current_user.id).first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    db.delete(note)
    db.commit()
    return None

# Optional: You may run the server directly for development.
# if __name__ == "__main__":
#     uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

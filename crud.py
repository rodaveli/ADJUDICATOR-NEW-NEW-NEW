from sqlalchemy.orm import Session
from fastapi import UploadFile, File
import models, schemas
import uuid
import random
import string
import os


def generate_unique_username():
    return 'user' + ''.join(random.choices(string.digits, k=5))

def create_session(db: Session, session: schemas.SessionCreate):
    db_session = models.Session(
        name=session.name,
        description=session.description,
        user1_id=session.user1_id,
        user2_id=session.user2_id,
        user1_name=session.user1_name,
        user2_name=session.user2_name
    )
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    return db_session

def get_session(db: Session, session_id: int):
    return db.query(models.Session).filter(models.Session.id == session_id).first()

def update_session_username(db: Session, session_id: int, user: str, username: str, user_id: str):
    session = db.query(models.Session).filter(models.Session.id == session_id).first()
    if not session:
        return None

    if user == 'user1' and session.user1_id == user_id:
        session.user1_name = username
    elif user == 'user2' and session.user2_id == user_id:
        session.user2_name = username
    else:
        return None

    db.commit()
    db.refresh(session)
    return session

async def create_argument(db: Session, argument: schemas.ArgumentCreate, session_id: int, user_id: str, username: str, image: UploadFile = None):
    db_argument = models.Argument(content=argument.content, session_id=session_id, user_id=user_id, username=username)
    image_url = None
    if image:
        file_extension = os.path.splitext(image.filename)[1]
        image_name = f"{uuid.uuid4()}{file_extension}"
        image_path = f"images/{image_name}"
        with open(image_path, "wb") as buffer:
            buffer.write(await image.read())
        image_url = f"/images/{image_name}"
        db_argument.image_url = image_url
    db.add(db_argument)
    db.commit()
    db.refresh(db_argument)
    return db_argument

# async def create_argument(db: Session, argument: schemas.ArgumentCreate, session_id: int, user_id: str, image: UploadFile = None):
#     db_argument = models.Argument(content=argument.content, session_id=session_id, user_id=user_id)
#     if image:
#         # Handle image upload and set image_url
#         # This is a placeholder - you'll need to implement actual image handling
#         db_argument.image_url = "path/to/uploaded/image.jpg"
#     db.add(db_argument)
#     db.commit()
#     db.refresh(db_argument)
#     return db_argument

def get_arguments_by_session(db: Session, session_id: int):
    return db.query(models.Argument).filter(models.Argument.session_id == session_id).all()

def create_judgement(db: Session, judgement: schemas.JudgementCreate, session_id: int):
    db_judgement = models.Judgement(**judgement.dict(), session_id=session_id)
    db.add(db_judgement)
    db.commit()
    db.refresh(db_judgement)

    # Update the session with the new judgement
    session = db.query(models.Session).filter(models.Session.id == session_id).first()
    session.judgement = db_judgement
    db.commit()

    return db_judgement

def update_judgement(db: Session, session_id: int, judgement: schemas.JudgementCreate):
    db_judgement = db.query(models.Judgement).filter(models.Judgement.session_id == session_id).first()
    if db_judgement:
        for key, value in judgement.dict().items():
            setattr(db_judgement, key, value)
        db.commit()
        db.refresh(db_judgement)
    else:
        db_judgement = models.Judgement(**judgement.dict(), session_id=session_id)
        db.add(db_judgement)
        db.commit()
        db.refresh(db_judgement)
    return db_judgement

def create_appeal(db: Session, appeal: schemas.AppealCreate, session_id: int):
    db_appeal = models.Appeal(**appeal.dict(), session_id=session_id)
    db.add(db_appeal)
    db.commit()
    db.refresh(db_appeal)
    return db_appeal

def create_appeal_judgement(db: Session, appeal_judgement: schemas.AppealJudgementCreate, session_id: int):
    db_appeal_judgement = models.AppealJudgement(**appeal_judgement.dict(), session_id=session_id)
    db.add(db_appeal_judgement)
    db.commit()
    db.refresh(db_appeal_judgement)
    return db_appeal_judgement

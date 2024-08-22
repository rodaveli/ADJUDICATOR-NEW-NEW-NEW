from sqlalchemy.orm import Session
from fastapi import UploadFile, File
import models, schemas
import uuid
import os

def create_session(db: Session, session: schemas.SessionCreate):
    db_session = models.Session(**session.dict())
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    return db_session

def get_session(db: Session, session_id: int):
    return db.query(models.Session).filter(models.Session.id == session_id).first()

async def create_argument(db: Session, argument: schemas.ArgumentCreate, session_id: int, image: UploadFile = File(None)):
    image_url = None
    if image:
        file_extension = os.path.splitext(image.filename)[1]
        image_name = f"{uuid.uuid4()}{file_extension}"
        image_path = f"images/{image_name}"
        with open(image_path, "wb") as buffer:
            buffer.write(await image.read())
        image_url = f"/images/{image_name}"

    db_argument = models.Argument(content=argument.content, image_url=image_url, session_id=session_id)
    db.add(db_argument)
    db.commit()
    db.refresh(db_argument)
    return db_argument

def get_arguments_by_session(db: Session, session_id: int):
    return db.query(models.Argument).filter(models.Argument.session_id == session_id).all()

def create_judgement(db: Session, judgement: schemas.JudgementCreate, session_id: int):
    db_judgement = models.Judgement(**judgement.dict(), session_id=session_id)
    db.add(db_judgement)
    db.commit()
    db.refresh(db_judgement)
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
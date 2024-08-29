from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException, status, File, UploadFile, Form, Query, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import List, Dict
import logging
from starlette.websockets import WebSocketDisconnect
import json
import traceback
import crud, models, schemas
from database import SessionLocal, engine
from ai_judge import get_ai_judgement, Judgement


class UsernameUpdate(BaseModel):
    user: str
    username: str
    userId: str


models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

origins = [
    "https://adjudicator-new-new-8dqz6mpzx-rodavelis-projects.vercel.app", # replace with your frontend domain
    "http://localhost:5173",
     "https://adjudicator-new-new-lw6bmyyu8-rodavelis-projects.vercel.app" # Add this if you are also testing locally
]

# CORS middleware setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[int, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, session_id: int):
        await websocket.accept()
        if session_id not in self.active_connections:
            self.active_connections[session_id] = []
        self.active_connections[session_id].append(websocket)
        await self.broadcast(session_id, {"message": "User joined", "participant": len(self.active_connections[session_id])})

    def disconnect(self, websocket: WebSocket, session_id: int):
        self.active_connections[session_id].remove(websocket)
        if not self.active_connections[session_id]:
            del self.active_connections[session_id]

    async def broadcast(self, session_id: int, message: dict):
        if session_id in self.active_connections:
            for connection in self.active_connections[session_id]:
                await connection.send_json(message)

manager = ConnectionManager()

@app.post("/sessions/", response_model=schemas.Session)
def create_session(session: schemas.SessionCreate, db: Session = Depends(get_db)):
    try:
        return crud.create_session(db=db, session=session)
    except Exception as e:
        logger.error(f"Error creating session: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/sessions/{session_id}", response_model=schemas.Session)
def read_session(session_id: int, userId: str = Query(...), db: Session = Depends(get_db)):
    db_session = crud.get_session(db, session_id=session_id)
    if db_session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    if not db_session.user1_id:
        db_session.user1_id = userId
        db_session.user1_name = f"User {userId}"  # Set a default name
        db.commit()
    elif not db_session.user2_id and db_session.user1_id != userId:
        db_session.user2_id = userId
        db_session.user2_name = f"User {userId}"  # Set a default name
        db.commit()

    db.refresh(db_session)
    return db_session

@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: int):
    await manager.connect(websocket, session_id)
    try:
        while True:
            data = await websocket.receive_text()
            await manager.broadcast(session_id, {"message": data})
    except WebSocketDisconnect:
        manager.disconnect(websocket, session_id)
        await manager.broadcast(session_id, {"message": "A user has left the debate"})
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        manager.disconnect(websocket, session_id)

@app.post("/sessions/{session_id}/arguments/", response_model=schemas.Argument)
async def create_argument(
    session_id: int,
    content: str = Form(...),
    userId: str = Form(...),
    username: str = Form(...),  # Add this line
    image: UploadFile = File(None),
    db: Session = Depends(get_db)
):
    try:
        argument = await crud.create_argument(
            db=db,
            argument=schemas.ArgumentCreate(content=content),
            session_id=session_id,
            user_id=userId,
            username=username,  # Add this line
            image=image
        )
        logger.info(f"Created argument: {argument}")

        # Check if this is the second argument
        arguments = crud.get_arguments_by_session(db, session_id=session_id)
        if len(arguments) == 2:
            # Automatically trigger judgement
            judgement = await judge_session(session_id, db)
            await manager.broadcast(session_id, {
                "message": "Judgement ready",
                "judgement": schemas.Judgement.from_orm(judgement).dict()
            })

        await manager.broadcast(session_id, {
            "message": "New argument submitted",
            "argument": schemas.Argument.from_orm(argument).dict(),
            "argumentCount": len(arguments)
        })
        logger.info("Broadcast complete")
        return argument
    except Exception as e:
        logger.error(f"Error creating argument: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/sessions/{session_id}/invite/")
async def invite_user(session_id: int, email: str, userId: str, db: Session = Depends(get_db)):
    session = crud.get_session(db, session_id=session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Here you would typically send an email invitation
    # For now, we'll just return a success message
    return {"message": f"Invitation sent to {email} for session {session_id}"}


@app.post("/sessions/{session_id}/update_username", response_model=schemas.Session)
def update_username(
    session_id: int,
    update: UsernameUpdate,
    db: Session = Depends(get_db)
):
    session = crud.get_session(db, session_id=session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if update.user == 'user1' and session.user1_id == update.userId:
        session.user1_name = update.username
    elif update.user == 'user2' and session.user2_id == update.userId:
        session.user2_name = update.username
    else:
        raise HTTPException(status_code=400, detail="Invalid user or userId")

    db.commit()
    db.refresh(session)
    return session

@app.post("/sessions/{session_id}/judge/", response_model=schemas.Judgement)
async def judge_session(session_id: int, db: Session = Depends(get_db)):
    session = crud.get_session(db, session_id=session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    arguments = crud.get_arguments_by_session(db, session_id=session_id)
    if len(arguments) < 2:
        raise HTTPException(status_code=400, detail="Not enough arguments to judge")

    try:
        # Sort arguments based on user ID to ensure consistent order
        arguments.sort(key=lambda arg: arg.user_id)

        #schema_arguments = [schemas.Argument.from_orm(arg) for arg in arguments]
        #judgement_data = get_ai_judgement(schema_arguments)
        judgement_data = get_ai_judgement(arguments)

        # Get usernames based on user IDs from judgement_data
        winning_user_id = judgement_data.get('winning_user_id')
        losing_user_id = judgement_data.get('losing_user_id')

        # Find the arguments with matching user IDs
        winning_argument = next((arg for arg in arguments if arg.user_id == winning_user_id), None)
        losing_argument = next((arg for arg in arguments if arg.user_id == losing_user_id), None)

        # Extract usernames if arguments are found
        winning_username = winning_argument.username if winning_argument else "Unknown"
        losing_username = losing_argument.username if losing_argument else "Unknown"

        # Update the winner and loser fields with usernames
        judgement_data['winner'] = winning_username
        judgement_data['loser'] = losing_username

        judgement_create = schemas.JudgementCreate(**judgement_data)
        db_judgement = crud.create_judgement(db=db, judgement=judgement_create, session_id=session_id)

        # Update the session with the new judgement
        session = crud.get_session(db, session_id=session_id)
        session.judgement = db_judgement
        db.commit()

        # Broadcast the judgement
        judgement_dict = schemas.Judgement.from_orm(db_judgement).dict()
        await manager.broadcast(session_id, {"message": "Judgement ready", "judgement": judgement_dict})

        logger.info(f"Judgement broadcast for session {session_id}: {judgement_dict}")

        return db_judgement
    except Exception as e:
        logger.error(f"Error in judge_session: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/sessions/{session_id}/appeal/", response_model=schemas.Appeal)
async def create_appeal(session_id: int, appeal: schemas.AppealCreate, db: Session = Depends(get_db)):
    try:
        session = crud.get_session(db, session_id=session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        if not session.judgement:
            raise HTTPException(status_code=400, detail="No judgment exists for this session yet")

        # Check if the appealing user is the loser
        if appeal.user_id != session.judgement.loser:
            raise HTTPException(status_code=403, detail="Only the losing party can submit an appeal")

        db_appeal = crud.create_appeal(db=db, appeal=appeal, session_id=session_id)

        # Get all arguments and the appeal
        arguments = crud.get_arguments_by_session(db, session_id=session_id)
        appeal_judgement = get_ai_judgement(arguments, db_appeal)

        appeal_judgement_create = schemas.AppealJudgementCreate(**appeal_judgement)

        db_appeal_judgement = crud.create_appeal_judgement(db=db, appeal_judgement=appeal_judgement_create, session_id=session_id)

        await manager.broadcast(session_id, {"message": "Appeal processed", "appeal_judgement": schemas.AppealJudgement.from_orm(db_appeal_judgement).dict()})

        return db_appeal
    except Exception as e:
        logger.error(f"Error in create_appeal: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException, status, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Dict
import logging
import json
import crud, models, schemas
from database import SessionLocal, engine
from ai_judge import get_ai_judgement, Judgement

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# CORS middleware setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080"],
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
def read_session(session_id: int, db: Session = Depends(get_db)):
    db_session = crud.get_session(db, session_id=session_id)
    if db_session is None:
        raise HTTPException(status_code=404, detail="Session not found")
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

@app.post("/sessions/{session_id}/arguments/", response_model=schemas.Argument)
async def create_argument(
    session_id: int, 
    content: str = Form(...), 
    image: UploadFile = File(None), 
    db: Session = Depends(get_db)
):
    logger.info(f"Received argument submission for session {session_id}: content={content}, image={image}")
    try:
        argument = await crud.create_argument(db=db, argument=schemas.ArgumentCreate(content=content), session_id=session_id, image=image)
        logger.info(f"Created argument: {argument}")
        
        # Check if this is the second argument
        arguments = crud.get_arguments_by_session(db, session_id=session_id)
        if len(arguments) == 2:
            # Automatically trigger judgement
            await judge_session(session_id, db)  # Call judge_session here

        await manager.broadcast(session_id, {
            "message": "New argument submitted", 
            "argument": schemas.Argument.from_orm(argument).dict(),
            "participant": len(manager.active_connections.get(session_id, []))
        })
        logger.info("Broadcast complete")
        return argument
    except Exception as e:
        logger.error(f"Error creating argument: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/sessions/{session_id}/judge/", response_model=schemas.Judgement)
async def judge_session(session_id: int, db: Session = Depends(get_db)):
    session = crud.get_session(db, session_id=session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    arguments = crud.get_arguments_by_session(db, session_id=session_id)
    if len(arguments) < 2:
        raise HTTPException(status_code=400, detail="Not enough arguments to judge")
    
    try:
        schema_arguments = [schemas.Argument.from_orm(arg) for arg in arguments]
        judgement_data = get_ai_judgement(schema_arguments)
        
        judgement_create = schemas.JudgementCreate(**judgement_data)
        db_judgement = crud.create_judgement(db=db, judgement=judgement_create, session_id=session_id)
        
        # Update the session with the judgement
        db_session = crud.get_session(db, session_id=session_id)
        db_session.judgement = db_judgement
        db.commit()
        db.refresh(db_session)

        await manager.broadcast(session_id, {"message": "Judgement ready", "judgement": schemas.Judgement.from_orm(db_judgement).dict()})
        
        return db_judgement
    except Exception as e:
        logger.error(f"Error in judge_session: {str(e)}")
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
        
        arguments = crud.get_arguments_by_session(db, session_id=session_id)
        appeal_judgement = get_ai_judgement(arguments, db_appeal)
        
        appeal_judgement_create = schemas.AppealJudgementCreate(**appeal_judgement)
        
        crud.create_appeal_judgement(db=db, appeal_judgement=appeal_judgement_create, session_id=session_id)
        
        await manager.broadcast(session_id, {"message": "Appeal processed", "appeal_judgement": appeal_judgement})
        
        return db_appeal
    except Exception as e:
        logger.error(f"Error in create_appeal: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
from pydantic import BaseModel
from typing import Optional, List

class SessionBase(BaseModel):
    name: str
    description: Optional[str] = None

class SessionCreate(SessionBase):
    pass

class ArgumentBase(BaseModel):
    content: str
    image_url: Optional[str] = None

class ArgumentCreate(ArgumentBase):
    pass

class Argument(ArgumentBase):
    id: int
    session_id: int

    class Config:
        from_attributes = True

class JudgementBase(BaseModel):
    content: str
    winner: str
    winning_argument: str
    loser: str
    losing_argument: str
    reasoning: str

class JudgementCreate(JudgementBase):
    pass

class Judgement(JudgementBase):
    id: int
    session_id: int

    class Config:
        from_attributes = True  # This replaces orm_mode = True in Pydantic v2

class AppealBase(BaseModel):
    content: str
    user_id: str  # To identify which user is appealing

class AppealCreate(AppealBase):
    pass

class Appeal(AppealBase):
    id: int
    session_id: int

    class Config:
        from_attributes = True

class AppealJudgementBase(BaseModel):
    content: str
    winner: str
    winning_argument: str
    loser: str
    losing_argument: str
    reasoning: str

class AppealJudgementCreate(AppealJudgementBase):
    pass

class AppealJudgement(AppealJudgementBase):
    id: int
    session_id: int

    class Config:
        from_attributes = True

class Session(SessionBase):
    id: int
    arguments: List[Argument] = []
    judgement: Optional[Judgement] = None
    appeal_judgement: Optional[AppealJudgement] = None
    appeals: List[Appeal] = []

    class Config:
        from_attributes = True
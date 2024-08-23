from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from database import Base

class Session(Base):
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(Text)
    user1_id = Column(String)  # Add this line
    user2_id = Column(String)
    user1_name = Column(String, default="")
    user2_name = Column(String, default="")

    arguments = relationship("Argument", back_populates="session")
    judgement = relationship("Judgement", back_populates="session", uselist=False)
    appeal_judgement = relationship("AppealJudgement", back_populates="session", uselist=False)
    appeals = relationship("Appeal", back_populates="session")

class AppealJudgement(Base):
    __tablename__ = "appeal_judgements"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text)
    winner = Column(String)
    winning_argument = Column(Text)
    loser = Column(String)
    losing_argument = Column(Text)
    reasoning = Column(Text)
    session_id = Column(Integer, ForeignKey("sessions.id"))

    session = relationship("Session", back_populates="appeal_judgement")

class Argument(Base):
    __tablename__ = "arguments"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text)
    user_id = Column(String)
    username = Column(String)  # Add this line
    image_url = Column(String)
    session_id = Column(Integer, ForeignKey("sessions.id"))

    session = relationship("Session", back_populates="arguments")

class Judgement(Base):
    __tablename__ = "judgements"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text)
    winner = Column(String)
    winning_argument = Column(Text)
    winning_user_id = Column(String)  # Add this line
    loser = Column(String)
    losing_argument = Column(Text)
    losing_user_id = Column(String)  # Add this line
    reasoning = Column(Text)
    session_id = Column(Integer, ForeignKey("sessions.id"))

    session = relationship("Session", back_populates="judgement")

# class Judgement(Base):
#     __tablename__ = "judgements"

#     id = Column(Integer, primary_key=True, index=True)
#     content = Column(Text)
#     winner = Column(String)
#     winning_argument = Column(Text)
#     winning_username = Column(String)  # Add this line
#     loser = Column(String)
#     losing_argument = Column(Text)
#     losing_username = Column(String)  # Add this line
#     reasoning = Column(Text)
#     session_id = Column(Integer, ForeignKey("sessions.id"))

#     session = relationship("Session", back_populates="judgement")


class Appeal(Base):
    __tablename__ = "appeals"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text)
    session_id = Column(Integer, ForeignKey("sessions.id"))

    session = relationship("Session", back_populates="appeals")

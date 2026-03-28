from sqlalchemy import Column, Integer, String, Text, DateTime
from datetime import datetime
from database import Base

class ChatLog(Base):
    __tablename__ = "chat_logs"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    original_input = Column(Text, nullable=False)
    masked_input = Column(Text, nullable=False)
    gemini_response = Column(Text, nullable=False)
    masked_response = Column(Text, nullable=False)

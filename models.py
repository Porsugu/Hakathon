"""
Database Models for Personal Learning OS
Handles all SQLAlchemy database models and configurations
"""
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import streamlit as st

Base = declarative_base()

class LearningPlan(Base):
    __tablename__ = 'learning_plans'
    id = Column(Integer, primary_key=True)
    user_id = Column(String, default='default_user')
    learning_target = Column(Text)
    total_days = Column(Integer)
    created_date = Column(DateTime, default=datetime.utcnow)
    difficulty_level = Column(String, default='intermediate')
    estimated_hours_per_day = Column(Integer, default=2)

class DailyMission(Base):
    __tablename__ = 'daily_missions'
    id = Column(Integer, primary_key=True)
    plan_id = Column(Integer, ForeignKey('learning_plans.id'))
    day_number = Column(Integer)
    mission_title = Column(Text)
    mission_description = Column(Text)
    detailed_content = Column(Text)
    status = Column(String, default='pending')
    estimated_time_minutes = Column(Integer, default=120)

class LearningProgress(Base):
    __tablename__ = 'learning_progress'
    id = Column(Integer, primary_key=True)
    plan_id = Column(Integer, ForeignKey('learning_plans.id'))
    day_number = Column(Integer)
    content_taught = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)
    completion_score = Column(Integer, default=0)
    time_spent_minutes = Column(Integer, default=0)

class SavedExplanation(Base):
    __tablename__ = 'saved_explanations'
    id = Column(Integer, primary_key=True)
    user_query = Column(Text)
    ai_explanation = Column(Text)
    saved_date = Column(DateTime, default=datetime.utcnow)
    tags = Column(String)
    difficulty_level = Column(String, default='intermediate')
    estimated_study_time = Column(Integer, default=10)

class APIUsage(Base):
    __tablename__ = 'api_usage'
    id = Column(Integer, primary_key=True)
    endpoint_type = Column(String)
    tokens_used = Column(Integer, default=0)
    cost_estimate = Column(String, default='$0.00')
    timestamp = Column(DateTime, default=datetime.utcnow)
    success = Column(String, default='true')

@st.cache_resource
def init_database():
    """Initialize database connection with caching"""
    engine = create_engine('sqlite:///learning_os_production.db', echo=False)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    return engine, SessionLocal

def get_db_session():
    """Get database session from Streamlit session state"""
    if 'db_session' not in st.session_state:
        engine, SessionLocal = init_database()
        st.session_state.db_session = SessionLocal()
    return st.session_state.db_session

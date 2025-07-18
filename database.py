# database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base
import streamlit as st
import os

# Database connection string from Streamlit Secrets or environment variable
# For Streamlit Cloud, you'd set this in .streamlit/secrets.toml
# e.g., DATABASE_URL = "postgresql://user:password@host:port/dbname"
DATABASE_URL = st.secrets["database"]["url"]

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_tables():
    """
    Creates all defined tables in the database.
    Call this once when setting up the database for the first time.
    """
    Base.metadata.create_all(bind=engine)

def initialize_master_data(db_session):
    """
    Initializes critical master data like production process steps and
    default tags if they don't already exist.
    """
    # Production Process Steps
    existing_steps = [step.step_name for step in db_session.query(ProductionProcessStep).all()]
    production_steps_data = [
        ("Raw Material Ordered", 10),
        ("Raw Material Received", 20),
        ("Outsource Machining", 30),
        ("Frame Fabrication", 40),
        ("Coating & Painting/ Buffing", 50),
        ("Initial Assembly", 60),
        ("Electrical Wiring", 70),
        ("Loadcell Calibration", 80),
        ("Final Assembly", 90),
        ("Testing for Use", 100),
        ("Verified", 110),
        ("Cleaning", 120),
        ("Final Touch-Up", 130),
        ("Wooden Packing", 140),
        ("Added to Dispatch Box", 150),
        ("Dispatch", 160)
    ]
    for step_name, order in production_steps_data:
        if step_name not in existing_steps:
            db_session.add(ProductionProcessStep(step_name=step_name, sequence_order=order))
    db_session.commit()

    # You could also initialize default Accessory categories/tags here if needed,
    # but for now, we'll assume they are free text during accessory creation.

from models import ProductionProcessStep

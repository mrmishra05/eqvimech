import os
import datetime
import streamlit as st # Import streamlit here for caching
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker, Session
from models import Base, User, Customer, Order, MachineFamily, Accessory, FamilyAccessory, ProductionProcessStep, OrderStatusHistory, ProductionStatusHistory, StockHistory, hash_password


# Database URL from environment variable or default
# For Streamlit Cloud/Render, this will come from .streamlit/secrets.toml or environment variables
# If not found in secrets, it defaults to SQLite for local development ease.
DATABASE_URL = "sqlite:///./sql_app.db" # Default to SQLite for ease of local testing

# Check for DATABASE_URL in Streamlit secrets (for Streamlit Cloud)
if "database" in st.secrets and "url" in st.secrets["database"]:
    DATABASE_URL = st.secrets["database"]["url"]
    print(f"Using DATABASE_URL from Streamlit secrets: {DATABASE_URL}")
# Check for DATABASE_URL in environment variables (for Render.com or other deployments)
elif "DATABASE_URL" in os.environ:
    DATABASE_URL = os.environ["DATABASE_URL"]
    print(f"Using DATABASE_URL from environment variable: {DATABASE_URL}")
else:
    print(f"Using default SQLite DATABASE_URL: {DATABASE_URL}")


@st.cache_resource # Cache the database engine and session factory
def get_engine_and_session_local():
    """
    Creates and caches the SQLAlchemy engine and sessionmaker.
    This ensures the database connection is established only once per app run.
    """
    print(f"Creating SQLAlchemy engine for URL: {DATABASE_URL}")
    # connect_args={"check_same_thread": False} is needed for SQLite when using multiple threads (like Streamlit)
    # For PostgreSQL, this argument is usually not needed and can be removed.
    if DATABASE_URL.startswith("sqlite"):
        engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
    else:
        # For PostgreSQL, ensure you have psycopg2-binary installed: pip install psycopg2-binary
        engine = create_engine(DATABASE_URL)

    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return engine, SessionLocal

# Get the cached engine and SessionLocal
engine, SessionLocal = get_engine_and_session_local()


def create_tables():
    """Creates all tables defined in models.py."""
    print("Attempting to create database tables...")
    Base.metadata.create_all(bind=engine)
    print("Database tables creation process completed.")

def get_db():
    """Dependency to get a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def initialize_master_data(db: Session):
    """
    Initializes master data (users, machine families, accessories, production steps)
    if they don't already exist in the database.
    This function is designed to be idempotent (safe to run multiple times).
    """
    print("Checking and initializing master data...")

    # Initialize Users (Admin, Sales, Production)
    users_to_add = [
        ("admin", "admin_pass", "System Admin", "admin@eqvimech.com", "admin"),
        ("sales", "sales_pass", "Sales Team Lead", "sales@eqvimech.com", "sales"),
        ("production", "prod_pass", "Production Manager", "production@eqvimech.com", "production"),
    ]
    for username, password, full_name, email, role in users_to_add:
        if not db.query(User).filter_by(username=username).first():
            hashed_password = hash_password(password)
            user = User(username=username, hashed_password=hashed_password, role=role, full_name=full_name, email=email)
            db.add(user)
            print(f"Added default {role} user: {username}.")
    db.commit() # Commit users first to get their IDs if needed for other data


    # Add some Machine Families if not present
    machine_families_data = [
        ("Universal Testing Machine (UTM)", "Machines for material tensile/compression testing", True, 150000.00),
        ("Hydraulic Press", "Industrial hydraulic press machines", True, 200000.00),
        ("Hardness Tester", "Machines for measuring material hardness", True, 75000.00),
        ("Documents Bundle", "Standard documents associated with orders (e.g., manuals, certs)", False, 0.00)
    ]
    mf_map = {} # To store created objects for linking
    for name, desc, is_prod, price in machine_families_data:
        mf = db.query(MachineFamily).filter_by(name=name).first()
        if not mf:
            mf = MachineFamily(name=name, description=desc, is_product=is_prod, price_per_unit=price)
            db.add(mf)
            print(f"Added Machine Family: {name}.")
        mf_map[name] = mf
    db.commit() # Commit to get IDs for relationships
    for name, obj in mf_map.items(): # Refresh objects after commit
        db.refresh(obj)


    # Add some Accessories (Items) if not present
    accessories_data = [
        ("Load Cell 10KN", "LC-10KN-001", "10KN capacity load cell", "Loadcell", "pcs", 2, 5, 5000.00),
        ("Gripping Jaws Set (Flat)", "GJ-FLAT-001", "Set of flat gripping jaws", "Mechanical", "sets", 3, 10, 3500.00),
        ("Hydraulic Pump Unit (2HP)", "HP-2HP-001", "2HP Hydraulic Power Pack", "Hydraulic", "pcs", 1, 3, 15000.00),
        ("Brinell Indenter", "BI-001", "Hardened steel Brinell indenter", "Hardness", "pcs", 1, 5, 1200.00),
        ("User Manual (Digital)", "DOC-UM-001", "Digital User Manual for machine", "Documents", "file", 0, 100, 0.00),
        ("Calibration Certificate", "DOC-CALIB-001", "Standard Calibration Certificate", "Documents", "file", 0, 100, 0.00),
        ("Installation Report", "DOC-INSTALL-001", "Site Installation Report", "Documents", "file", 0, 100, 0.00),
        ("PLC Siemens S7-1200", "ELEC-PLC-001", "Siemens S7-1200 PLC Unit", "Electronic", "pcs", 1, 2, 25000.00)
    ]
    acc_map = {} # To store created objects for linking
    for name, acc_id, desc, cat, uom, min_stock, curr_stock, price in accessories_data:
        acc = db.query(Accessory).filter_by(accessory_id=acc_id).first()
        if not acc:
            acc = Accessory(name=name, accessory_id=acc_id, description=desc, category_tag=cat,
                            unit_of_measure=uom, min_stock_level=min_stock, current_stock_level=curr_stock,
                            price_per_unit=price)
            db.add(acc)
            print(f"Added Accessory: {name}.")
        acc_map[acc_id] = acc
    db.commit()
    for acc_id, obj in acc_map.items(): # Refresh objects after commit
        db.refresh(obj)


    # Link default accessories to machine families (e.g., UTM with Load Cell and Jaws)
    # Use a list of tuples: (machine_family_name, accessory_id, default_qty, is_variable, variable_placeholder, is_required_for_dispatch)
    family_accessory_links_data = [
        ("Universal Testing Machine (UTM)", "LC-10KN-001", 1, False, None, False),
        ("Universal Testing Machine (UTM)", "GJ-FLAT-001", 1, False, None, False),
        ("Universal Testing Machine (UTM)", "ELEC-PLC-001", 1, True, "PLC Model/Firmware: _______", False),
        ("Hydraulic Press", "HP-2HP-001", 1, False, None, False),
        ("Hardness Tester", "BI-001", 1, False, None, False),
        ("Documents Bundle", "DOC-UM-001", 1, True, "Manual Version/Date: _______", True),
        ("Documents Bundle", "DOC-CALIB-001", 1, False, None, True),
        ("Documents Bundle", "DOC-INSTALL-001", 1, False, None, True),
    ]

    for mf_name, acc_id, d_qty, is_var, var_ph, req_disp in family_accessory_links_data:
        mf = mf_map.get(mf_name)
        acc = acc_map.get(acc_id)
        if mf and acc:
            existing_link = db.query(FamilyAccessory).filter_by(machine_family_id=mf.id, accessory_id=acc.id).first()
            if not existing_link:
                new_link = FamilyAccessory(
                    machine_family_id=mf.id,
                    accessory_id=acc.id,
                    default_quantity=d_qty,
                    is_variable=is_var,
                    variable_placeholder=var_ph,
                    is_required_for_dispatch=req_disp
                )
                db.add(new_link)
                print(f"Linked {acc.name} to {mf.name}.")
    db.commit() # Commit all family accessory links


    # Add some Production Process Steps if not present
    production_steps_data = [
        ("Design Approval", "Customer approves design drawings.", 1, False),
        ("Raw Material Sourcing", "Procurement of raw materials.", 2, False),
        ("Fabrication", "Cutting, welding, and basic assembly.", 3, False),
        ("Mechanical Assembly", "Assembly of mechanical components.", 4, False),
        ("Electrical Wiring", "Wiring of electrical components and panels.", 5, False),
        ("Testing & Calibration", "Full machine testing and calibration.", 6, False),
        ("Quality Control", "Final quality inspection.", 7, False),
        ("Packaging", "Preparing machine for shipment.", 8, False),
        ("Dispatch Approval", "Final approval for dispatch.", 9, True), # Marked as dispatch step
        ("Dispatched", "Machine has left the facility.", 10, True) # Marked as dispatch step
    ]
    for name, desc, order_idx, is_dispatch in production_steps_data:
        if not db.query(ProductionProcessStep).filter_by(step_name=name).first():
            step = ProductionProcessStep(step_name=name, description=desc, order_index=order_idx, is_dispatch_step=is_dispatch)
            db.add(step)
            print(f"Added Production Step: {name}.")
    db.commit()

    print("Master data initialization completed.")

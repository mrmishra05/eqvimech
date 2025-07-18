import os
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker, Session
from models import Base, User, Customer, Order, MachineFamily, Accessory, FamilyAccessory, ProductionProcessStep, OrderStatusHistory, ProductionStatusHistory, StockHistory, hash_password
import datetime
import streamlit as st # Import streamlit here for caching

# Database URL from environment variable or default
# For Streamlit Cloud, this will come from .streamlit/secrets.toml
# You can uncomment and modify for PostgreSQL if needed.
# DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@host:port/dbname")
DATABASE_URL = "sqlite:///./sql_app.db" # Default to SQLite for ease of local testing

# If using secrets.toml on Streamlit Cloud, it's accessed via st.secrets
if "database" in st.secrets and "url" in st.secrets["database"]:
    DATABASE_URL = st.secrets["database"]["url"]

@st.cache_resource # Cache the database engine and session factory
def get_engine_and_session_local():
    """
    Creates and caches the SQLAlchemy engine and sessionmaker.
    This ensures the database connection is established only once.
    """
    print(f"Creating SQLAlchemy engine for URL: {DATABASE_URL}")
    # connect_args={"check_same_thread": False} is needed for SQLite when using multiple threads (like Streamlit)
    # For PostgreSQL, this argument is usually not needed and can be removed.
    if DATABASE_URL.startswith("sqlite"):
        engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
    else:
        engine = create_engine(DATABASE_URL) # For PostgreSQL, etc.

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
    """
    print("Checking and initializing master data...")

    # Initialize Admin User (only if no users exist)
    admin_user = db.query(User).filter_by(username="admin").first()
    if not admin_user:
        hashed_admin_password = hash_password("admin_pass") # CHANGE THIS IN PRODUCTION!
        admin_user = User(username="admin", hashed_password=hashed_admin_password, role="admin", full_name="System Admin")
        db.add(admin_user)
        print("Added default admin user.")

    sales_user = db.query(User).filter_by(username="sales").first()
    if not sales_user:
        hashed_sales_password = hash_password("sales_pass") # CHANGE THIS!
        sales_user = User(username="sales", hashed_password=hashed_sales_password, role="sales", full_name="Sales Team")
        db.add(sales_user)
        print("Added default sales user.")

    prod_user = db.query(User).filter_by(username="production").first()
    if not prod_user:
        hashed_prod_password = hash_password("prod_pass") # CHANGE THIS!
        prod_user = User(username="production", hashed_password=hashed_prod_password, role="production", full_name="Production Team")
        db.add(prod_user)
        print("Added default production user.")
    
    db.commit() # Commit users first to get their IDs if needed for other data
    db.refresh(admin_user)
    db.refresh(sales_user)
    db.refresh(prod_user)


    # Add some Machine Families if not present
    mf1 = db.query(MachineFamily).filter_by(name="Universal Testing Machine (UTM)").first()
    if not mf1:
        mf1 = MachineFamily(name="Universal Testing Machine (UTM)", description="Machines for material tensile/compression testing", is_product=True)
        db.add(mf1)
    mf2 = db.query(MachineFamily).filter_by(name="Hydraulic Press").first()
    if not mf2:
        mf2 = MachineFamily(name="Hydraulic Press", description="Industrial hydraulic press machines", is_product=True)
        db.add(mf2)
    mf3 = db.query(MachineFamily).filter_by(name="Hardness Tester").first()
    if not mf3:
        mf3 = MachineFamily(name="Hardness Tester", description="Machines for measuring material hardness", is_product=True)
        db.add(mf3)
    mf4 = db.query(MachineFamily).filter_by(name="Documents Bundle").first() # Renamed slightly for clarity
    if not mf4:
        mf4 = MachineFamily(name="Documents Bundle", description="Standard documents associated with orders (e.g., manuals, certs)", is_product=False)
        db.add(mf4)
    db.commit() # Commit to get IDs for relationships
    db.refresh(mf1)
    db.refresh(mf2)
    db.refresh(mf3)
    db.refresh(mf4)
    print("Checked/Added default Machine Families.")


    # Add some Accessories (Items) if not present
    acc1 = db.query(Accessory).filter_by(accessory_id="LC-10KN-001").first()
    if not acc1:
        acc1 = Accessory(name="Load Cell 10KN", accessory_id="LC-10KN-001", description="10KN capacity load cell", category_tag="Loadcell", unit_of_measure="pcs", min_stock_level=2, current_stock_level=5, price_per_unit=5000.00)
        db.add(acc1)
    acc2 = db.query(Accessory).filter_by(accessory_id="GJ-FLAT-001").first()
    if not acc2:
        acc2 = Accessory(name="Gripping Jaws Set (Flat)", accessory_id="GJ-FLAT-001", description="Set of flat gripping jaws", category_tag="Mechanical", unit_of_measure="sets", min_stock_level=3, current_stock_level=10, price_per_unit=3500.00)
        db.add(acc2)
    acc3 = db.query(Accessory).filter_by(accessory_id="HP-2HP-001").first()
    if not acc3:
        acc3 = Accessory(name="Hydraulic Pump Unit (2HP)", accessory_id="HP-2HP-001", description="2HP Hydraulic Power Pack", category_tag="Hydraulic", unit_of_measure="pcs", min_stock_level=1, current_stock_level=3, price_per_unit=15000.00)
        db.add(acc3)
    acc4 = db.query(Accessory).filter_by(accessory_id="BI-001").first()
    if not acc4:
        acc4 = Accessory(name="Brinell Indenter", accessory_id="BI-001", description="Hardened steel Brinell indenter", category_tag="Hardness", unit_of_measure="pcs", min_stock_level=1, current_stock_level=5, price_per_unit=1200.00)
        db.add(acc4)
    acc5 = db.query(Accessory).filter_by(accessory_id="DOC-UM-001").first()
    if not acc5:
        acc5 = Accessory(name="User Manual (Digital)", accessory_id="DOC-UM-001", description="Digital User Manual for machine", category_tag="Documents", unit_of_measure="file", min_stock_level=0, current_stock_level=100, price_per_unit=0.00)
        db.add(acc5)
    acc6 = db.query(Accessory).filter_by(accessory_id="DOC-CALIB-001").first()
    if not acc6:
        acc6 = Accessory(name="Calibration Certificate", accessory_id="DOC-CALIB-001", description="Standard Calibration Certificate", category_tag="Documents", unit_of_measure="file", min_stock_level=0, current_stock_level=100, price_per_unit=0.00)
        db.add(acc6)
    acc7 = db.query(Accessory).filter_by(accessory_id="DOC-INSTALL-001").first()
    if not acc7:
        acc7 = Accessory(name="Installation Report", accessory_id="DOC-INSTALL-001", description="Site Installation Report", category_tag="Documents", unit_of_measure="file", min_stock_level=0, current_stock_level=100, price_per_unit=0.00)
        db.add(acc7)
    db.commit()
    db.refresh(acc1)
    db.refresh(acc2)
    db.refresh(acc3)
    db.refresh(acc4)
    db.refresh(acc5)
    db.refresh(acc6)
    db.refresh(acc7)
    print("Checked/Added default Accessories.")


    # Link default accessories to machine families (e.g., UTM with Load Cell and Jaws)
    # Only add if not already linked to avoid duplicates on reruns
    if mf1 and acc1 and acc2 and not db.query(FamilyAccessory).filter_by(machine_family_id=mf1.id, accessory_id=acc1.id).first():
        fa1 = FamilyAccessory(machine_family_id=mf1.id, accessory_id=acc1.id, default_quantity=1)
        fa2 = FamilyAccessory(machine_family_id=mf1.id, accessory_id=acc2.id, default_quantity=1)
        db.add_all([fa1, fa2])
        print(f"Linked {acc1.name} and {acc2.name} to {mf1.name}.")

    if mf2 and acc3 and not db.query(FamilyAccessory).filter_by(machine_family_id=mf2.id, accessory_id=acc3.id).first():
        fa3 = FamilyAccessory(machine_family_id=mf2.id, accessory_id=acc3.id, default_quantity=1)
        db.add(fa3)
        print(f"Linked {acc3.name} to {mf2.name}.")

    if mf3 and acc4 and not db.query(FamilyAccessory).filter_by(machine_family_id=mf3.id, accessory_id=acc4.id).first():
        fa4 = FamilyAccessory(machine_family_id=mf3.id, accessory_id=acc4.id, default_quantity=1)
        db.add(fa4)
        print(f"Linked {acc4.name} to {mf3.name}.")

    # Link documents to the 'Documents Bundle' family and also mark some as variable/required for dispatch
    if mf4 and acc5 and acc6 and acc7:
        if not db.query(FamilyAccessory).filter_by(machine_family_id=mf4.id, accessory_id=acc5.id).first():
            fa_doc1 = FamilyAccessory(machine_family_id=mf4.id, accessory_id=acc5.id, default_quantity=1,
                                    is_variable=True, variable_placeholder="Manual Version/Date: _______",
                                    is_required_for_dispatch=True)
            db.add(fa_doc1)
        if not db.query(FamilyAccessory).filter_by(machine_family_id=mf4.id, accessory_id=acc6.id).first():
            fa_doc2 = FamilyAccessory(machine_family_id=mf4.id, accessory_id=acc6.id, default_quantity=1,
                                    is_variable=False, is_required_for_dispatch=True)
            db.add(fa_doc2)
        if not db.query(FamilyAccessory).filter_by(machine_family_id=mf4.id, accessory_id=acc7.id).first():
            fa_doc3 = FamilyAccessory(machine_family_id=mf4.id, accessory_id=acc7.id, default_quantity=1,
                                    is_variable=False, is_required_for_dispatch=True)
            db.add(fa_doc3)
        print(f"Linked documents to {mf4.name}.")

    db.commit() # Commit all family accessory links


    # Add some Production Process Steps if not present
    if db.query(ProductionProcessStep).count() == 0:
        steps_data = [
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
        for name, desc, order, is_dispatch in steps_data:
            step = ProductionProcessStep(step_name=name, description=desc, order_index=order, is_dispatch_step=is_dispatch)
            db.add(step)
        db.commit()
        print("Added default Production Process Steps.")

    db.commit() # Final commit for all initial data
    print("Master data initialization completed.")

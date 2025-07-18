import os
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker, Session
from models import Base, User, Customer, Order, MachineFamily, Accessory, FamilyAccessory, ProductionProcessStep, OrderStatusHistory, ProductionStatusHistory, StockHistory, hash_password
import datetime

# Database URL from environment variable or default
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./sql_app.db")

# Create the SQLAlchemy engine
# connect_args={"check_same_thread": False} is needed for SQLite when using multiple threads (like Streamlit)
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

# Create a SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

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

    # Initialize Admin User
    if not db.query(User).filter(User.username == "admin").first():
        hashed_admin_password = hash_password("admin_pass") # Change this in production!
        admin_user = User(username="admin", hashed_password=hashed_admin_password, role="admin", is_active=True)
        db.add(admin_user)
        print("Added default admin user.")

    # Initialize Sales User
    if not db.query(User).filter(User.username == "sales").first():
        hashed_sales_password = hash_password("sales_pass") # Change this!
        sales_user = User(username="sales", hashed_password=hashed_sales_password, role="sales", is_active=True)
        db.add(sales_user)
        print("Added default sales user.")

    # Initialize Production User
    if not db.query(User).filter(User.username == "production").first():
        hashed_prod_password = hash_password("prod_pass") # Change this!
        prod_user = User(username="production", hashed_password=hashed_prod_password, role="production", is_active=True)
        db.add(prod_user)
        print("Added default production user.")

    # Add some Machine Families if not present
    if not db.query(MachineFamily).first():
        mf1 = MachineFamily(name="Universal Testing Machine (UTM)", description="Machines for material tensile/compression testing", is_product=True)
        mf2 = MachineFamily(name="Hydraulic Press", description="Industrial hydraulic press machines", is_product=True)
        mf3 = MachineFamily(name="Hardness Tester", description="Machines for measuring material hardness", is_product=True)
        mf4 = MachineFamily(name="Documents", description="Standard documents associated with orders (e.g., manuals, certs)", is_product=False)
        db.add_all([mf1, mf2, mf3, mf4])
        db.commit() # Commit to get IDs for relationships
        db.refresh(mf1)
        db.refresh(mf2)
        db.refresh(mf3)
        db.refresh(mf4)
        print("Added default Machine Families.")

    # Add some Accessories (Items) if not present
    if not db.query(Accessory).first():
        acc1 = Accessory(name="Load Cell 10KN", accessory_id="LC-10KN-001", description="10KN capacity load cell", category_tag="Loadcell", unit_of_measure="pcs", min_stock_level=2, current_stock_level=5, price_per_unit=5000.00)
        acc2 = Accessory(name="Gripping Jaws Set (Flat)", accessory_id="GJ-FLAT-001", description="Set of flat gripping jaws", category_tag="Mechanical", unit_of_measure="sets", min_stock_level=3, current_stock_level=10, price_per_unit=3500.00)
        acc3 = Accessory(name="Hydraulic Pump Unit (2HP)", accessory_id="HP-2HP-001", description="2HP Hydraulic Power Pack", category_tag="Hydraulic", unit_of_measure="pcs", min_stock_level=1, current_stock_level=3, price_per_unit=15000.00)
        acc4 = Accessory(name="Brinell Indenter", accessory_id="BI-001", description="Hardened steel Brinell indenter", category_tag="Hardness", unit_of_measure="pcs", min_stock_level=1, current_stock_level=5, price_per_unit=1200.00)
        acc5 = Accessory(name="User Manual (Digital)", accessory_id="DOC-UM-001", description="Digital User Manual for machine", category_tag="Documents", unit_of_measure="file", min_stock_level=0, current_stock_level=100, price_per_unit=0.00)
        acc6 = Accessory(name="Calibration Certificate", accessory_id="DOC-CALIB-001", description="Standard Calibration Certificate", category_tag="Documents", unit_of_measure="file", min_stock_level=0, current_stock_level=100, price_per_unit=0.00)
        acc7 = Accessory(name="Installation Report", accessory_id="DOC-INSTALL-001", description="Site Installation Report", category_tag="Documents", unit_of_measure="file", min_stock_level=0, current_stock_level=100, price_per_unit=0.00)

        db.add_all([acc1, acc2, acc3, acc4, acc5, acc6, acc7])
        db.commit()
        db.refresh(acc1)
        db.refresh(acc2)
        db.refresh(acc3)
        db.refresh(acc4)
        db.refresh(acc5)
        db.refresh(acc6)
        db.refresh(acc7)
        print("Added default Accessories.")

        # Link default accessories to machine families (e.g., UTM with Load Cell and Jaws)
        if mf1 and acc1 and acc2:
            fa1 = FamilyAccessory(machine_family_id=mf1.id, accessory_id=acc1.id, default_quantity=1)
            fa2 = FamilyAccessory(machine_family_id=mf1.id, accessory_id=acc2.id, default_quantity=1)
            db.add_all([fa1, fa2])
            print(f"Linked {acc1.name} and {acc2.name} to {mf1.name}.")

        if mf2 and acc3:
            fa3 = FamilyAccessory(machine_family_id=mf2.id, accessory_id=acc3.id, default_quantity=1)
            db.add(fa3)
            print(f"Linked {acc3.name} to {mf2.name}.")

        if mf3 and acc4:
            fa4 = FamilyAccessory(machine_family_id=mf3.id, accessory_id=acc4.id, default_quantity=1)
            db.add(fa4)
            print(f"Linked {acc4.name} to {mf3.name}.")

        # Link documents to the 'Documents' family and also mark some as variable/required for dispatch
        if mf4 and acc5 and acc6 and acc7:
            # User Manual: Variable (requires version/date)
            fa_doc1 = FamilyAccessory(machine_family_id=mf4.id, accessory_id=acc5.id, default_quantity=1,
                                    is_variable=True, variable_placeholder="Manual Version/Date: _______",
                                    is_required_for_dispatch=True) # Assuming manuals are req for dispatch
            # Calibration Certificate: Not variable, required for dispatch
            fa_doc2 = FamilyAccessory(machine_family_id=mf4.id, accessory_id=acc6.id, default_quantity=1,
                                    is_variable=False, is_required_for_dispatch=True)
            # Installation Report: Not variable, required for dispatch
            fa_doc3 = FamilyAccessory(machine_family_id=mf4.id, accessory_id=acc7.id, default_quantity=1,
                                    is_variable=False, is_required_for_dispatch=True)
            db.add_all([fa_doc1, fa_doc2, fa_doc3])
            print(f"Linked documents to {mf4.name}.")

        db.commit() # Commit all family accessory links

    # Add some Production Process Steps if not present
    if not db.query(ProductionProcessStep).first():
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

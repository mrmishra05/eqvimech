from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Numeric
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from sqlalchemy.sql import func
import datetime
import bcrypt

Base = declarative_base()

# Helper function to hash passwords
def hash_password(password: str) -> str:
    # Generate a salt and hash the password
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

# Helper function to verify passwords
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, default="viewer") # e.g., 'admin', 'manager', 'viewer', 'production', 'sales'
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', role='{self.role}')>"

class Customer(Base):
    __tablename__ = 'customers'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    contact_person = Column(String)
    email = Column(String)
    phone = Column(String)
    address = Column(Text)
    gst_number = Column(String) # Goods and Services Tax Number for India
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    orders = relationship("Order", back_populates="customer")

    def __repr__(self):
        return f"<Customer(id={self.id}, name='{self.name}')>"

class Order(Base):
    __tablename__ = 'orders'
    id = Column(Integer, primary_key=True, index=True)
    order_id_prefix = Column(String, default="ORD") # e.g., "ORD"
    order_number = Column(Integer, unique=True, nullable=False) # Sequential number, combined with prefix for full ID
    customer_id = Column(Integer, ForeignKey('customers.id'), nullable=False)
    order_date = Column(DateTime(timezone=True), server_default=func.now())
    delivery_date = Column(DateTime(timezone=True), nullable=True) # Expected delivery date
    total_amount = Column(Numeric(10, 2), default=0.00)
    status = Column(String, default="Draft") # e.g., Draft, Pending Approval, Approved, In Production, Ready for Dispatch, Dispatched, Completed, Cancelled
    special_notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by_user_id = Column(Integer, ForeignKey('users.id'), nullable=True) # Who created the order

    customer = relationship("Customer", back_populates="orders")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    status_history = relationship("OrderStatusHistory", back_populates="order", cascade="all, delete-orphan", order_by="OrderStatusHistory.timestamp")
    created_by_user = relationship("User") # Relationship to the User who created it

    def generate_full_order_id(self):
        return f"{self.order_id_prefix}-{self.order_number:04d}" # Example: ORD-0001

    def __repr__(self):
        return f"<Order(id={self.id}, full_id='{self.generate_full_order_id()}', customer_name='{self.customer.name if self.customer else 'N/A'}', status='{self.status}')>"

class OrderStatusHistory(Base):
    __tablename__ = 'order_status_history'
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey('orders.id'), nullable=False)
    status = Column(String, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True) # Who changed the status
    notes = Column(Text)

    order = relationship("Order", back_populates="status_history")
    user = relationship("User")

    def __repr__(self):
        return f"<OrderStatusHistory(order_id={self.order_id}, status='{self.status}', timestamp='{self.timestamp}')>"


class MachineFamily(Base):
    __tablename__ = 'machine_families'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    description = Column(Text)
    is_product = Column(Boolean, default=True) # True for machines/products, False for document categories, etc.
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    items = relationship("OrderItem", back_populates="machine_family")
    default_accessories = relationship("FamilyAccessory", back_populates="machine_family", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<MachineFamily(id={self.id}, name='{self.name}', is_product={self.is_product})>"

class Accessory(Base):
    __tablename__ = 'accessories'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    accessory_id = Column(String, unique=True, nullable=True) # e.g., LC-10KN-001
    description = Column(Text)
    category_tag = Column(String) # e.g., "Loadcell", "Mechanical", "Electrical", "Documents"
    unit_of_measure = Column(String, default="pcs") # e.g., "pcs", "sets", "file", "liters"
    min_stock_level = Column(Integer, default=0)
    current_stock_level = Column(Integer, default=0)
    price_per_unit = Column(Numeric(10, 2), default=0.00) # For calculating order item costs
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    stock_history = relationship("StockHistory", back_populates="accessory", cascade="all, delete-orphan", order_by="StockHistory.timestamp")

    def __repr__(self):
        return f"<Accessory(id={self.id}, name='{self.name}', stock={self.current_stock_level})>"

class FamilyAccessory(Base):
    """Links Machine Families to their default or common accessories."""
    __tablename__ = 'family_accessories'
    id = Column(Integer, primary_key=True, index=True)
    machine_family_id = Column(Integer, ForeignKey('machine_families.id'), nullable=False)
    accessory_id = Column(Integer, ForeignKey('accessories.id'), nullable=False)
    default_quantity = Column(Integer, default=1)
    is_variable = Column(Boolean, default=False) # e.g., if a document requires user input (e.g., "Version: X.X")
    variable_placeholder = Column(String) # Placeholder text for variable input

    machine_family = relationship("MachineFamily", back_populates="default_accessories")
    accessory = relationship("Accessory")

    def __repr__(self):
        return f"<FamilyAccessory(family_id={self.machine_family_id}, accessory_id={self.accessory_id}, qty={self.default_quantity})>"

class OrderItem(Base):
    """Represents a primary product (e.g., a machine) in an order."""
    __tablename__ = 'order_items'
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey('orders.id'), nullable=False)
    machine_family_id = Column(Integer, ForeignKey('machine_families.id'), nullable=False) # The main product (e.g., UTM)
    item_description = Column(Text) # Specific model or custom description
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Numeric(10, 2), default=0.00) # Price of this specific item/machine
    total_price = Column(Numeric(10, 2), default=0.00)

    order = relationship("Order", back_populates="items")
    machine_family = relationship("MachineFamily", back_populates="items")
    accessories = relationship("OrderItemAccessory", back_populates="order_item", cascade="all, delete-orphan")
    production_status = relationship("ProductionStatusHistory", back_populates="order_item", cascade="all, delete-orphan", order_by="ProductionStatusHistory.timestamp")

    def __repr__(self):
        return f"<OrderItem(id={self.id}, order_id={self.order_id}, machine='{self.machine_family.name}', qty={self.quantity})>"

class OrderItemAccessory(Base):
    """Represents an accessory associated with a specific OrderItem (machine)."""
    __tablename__ = 'order_item_accessories'
    id = Column(Integer, primary_key=True, index=True)
    order_item_id = Column(Integer, ForeignKey('order_items.id'), nullable=False)
    accessory_id = Column(Integer, ForeignKey('accessories.id'), nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Numeric(10, 2), default=0.00) # Price for this accessory at the time of order
    is_required_for_dispatch = Column(Boolean, default=False) # To track if this accessory is mandatory for dispatch
    notes = Column(Text) # For variable notes (e.g., document version)

    order_item = relationship("OrderItem", back_populates="accessories")
    accessory = relationship("Accessory")

    def __repr__(self):
        return f"<OrderItemAccessory(id={self.id}, item_id={self.order_item_id}, acc='{self.accessory.name}', qty={self.quantity})>"

class ProductionProcessStep(Base):
    __tablename__ = 'production_process_steps'
    id = Column(Integer, primary_key=True, index=True)
    step_name = Column(String, unique=True, nullable=False)
    description = Column(Text)
    order_index = Column(Integer, unique=True, nullable=False) # Order of the step in the process
    is_active = Column(Boolean, default=True)
    is_dispatch_step = Column(Boolean, default=False) # Marks this step as the final dispatch-related stage
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<ProductionProcessStep(id={self.id}, name='{self.step_name}', order={self.order_index})>"

class ProductionStatusHistory(Base):
    """Tracks the status of a specific OrderItem (machine) through production steps."""
    __tablename__ = 'production_status_history'
    id = Column(Integer, primary_key=True, index=True)
    order_item_id = Column(Integer, ForeignKey('order_items.id'), nullable=False)
    step_id = Column(Integer, ForeignKey('production_process_steps.id'), nullable=False)
    status = Column(String, default="Pending") # e.g., "Pending", "In Progress", "Completed", "On Hold"
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    completed_by_user_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    notes = Column(Text)

    order_item = relationship("OrderItem", back_populates="production_status")
    process_step = relationship("ProductionProcessStep")
    user = relationship("User")

    def __repr__(self):
        return f"<ProductionStatusHistory(item_id={self.order_item_id}, step='{self.process_step.step_name}', status='{self.status}')>"

class StockHistory(Base):
    __tablename__ = 'stock_history'
    id = Column(Integer, primary_key=True, index=True)
    accessory_id = Column(Integer, ForeignKey('accessories.id'), nullable=False)
    change_type = Column(String, nullable=False) # e.g., "Inbound", "Outbound", "Adjustment"
    quantity_change = Column(Integer, nullable=False) # Positive for inbound, negative for outbound
    new_stock_level = Column(Integer, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True) # Who made the change
    notes = Column(Text)

    accessory = relationship("Accessory", back_populates="stock_history")
    user = relationship("User")

    def __repr__(self):
        return f"<StockHistory(acc_id={self.accessory_id}, type='{self.change_type}', change={self.quantity_change}, new_stock={self.new_stock_level})>"

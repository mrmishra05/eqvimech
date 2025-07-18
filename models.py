import datetime
from sqlalchemy import (
    create_engine, Column, Integer, String, Float, DateTime,
    ForeignKey, Boolean, Text, UniqueConstraint
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker, Mapped, mapped_column
from sqlalchemy import LargeBinary # For storing hashed passwords
import bcrypt # For hashing passwords

Base = declarative_base()

# Helper function for password hashing and verification
def hash_password(password: str) -> bytes:
    """Hashes a password using bcrypt."""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

def verify_password(plain_password: str, hashed_password: bytes) -> bool:
    """Verifies a plain password against a hashed one."""
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password)


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(LargeBinary, nullable=False) # Store as bytes
    role = Column(String, default="viewer", nullable=False) # e.g., 'admin', 'sales', 'production', 'viewer'
    full_name = Column(String, nullable=True)
    email = Column(String, unique=True, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.now)
    updated_at = Column(DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now)

    orders_created = relationship("Order", back_populates="created_by_user")
    order_status_history = relationship("OrderStatusHistory", back_populates="user")
    production_status_history = relationship("ProductionStatusHistory", back_populates="user")
    stock_history = relationship("StockHistory", back_populates="user")

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', role='{self.role}')>"


class Customer(Base):
    __tablename__ = 'customers'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    contact_person = Column(String, nullable=True)
    email = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    address = Column(Text, nullable=True)
    gst_number = Column(String, nullable=True) # Goods and Services Tax number (India specific)
    created_at = Column(DateTime, default=datetime.datetime.now)
    updated_at = Column(DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now)

    orders = relationship("Order", back_populates="customer")

    def __repr__(self):
        return f"<Customer(id={self.id}, name='{self.name}')>"


class Order(Base):
    __tablename__ = 'orders'
    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey('customers.id'), nullable=False)
    order_number = Column(Integer, nullable=False, index=True) # Sequential number, e.g., 1, 2, 3...
    order_id_prefix = Column(String, default="EQV-ORD", nullable=False) # e.g., "EQV-ORD"
    order_date = Column(DateTime, default=datetime.datetime.now, nullable=False)
    delivery_date = Column(DateTime, nullable=True) # Expected delivery date
    total_amount = Column(Float, default=0.0, nullable=False)
    status = Column(String, default="Draft", nullable=False) # e.g., Draft, Pending Approval, Approved, In Production, Ready for Dispatch, Dispatched, Completed, Cancelled
    special_notes = Column(Text, nullable=True)
    created_by_user_id = Column(Integer, ForeignKey('users.id'), nullable=True) # Nullable if order created by system/no user logged in
    created_at = Column(DateTime, default=datetime.datetime.now)
    updated_at = Column(DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now)

    customer = relationship("Customer", back_populates="orders")
    created_by_user = relationship("User", back_populates="orders_created")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    status_history = relationship("OrderStatusHistory", back_populates="order", cascade="all, delete-orphan")

    __table_args__ = (UniqueConstraint('order_id_prefix', 'order_number', name='_order_number_uc'),)

    def generate_full_order_id(self):
        return f"{self.order_id_prefix}-{self.order_number:04d}" # EQV-ORD-0001


class MachineFamily(Base):
    __tablename__ = 'machine_families'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    description = Column(Text, nullable=True)
    is_product = Column(Boolean, default=True, nullable=False) # True if this family can be sold as a standalone product
    created_at = Column(DateTime, default=datetime.datetime.now)
    updated_at = Column(DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now)

    order_items = relationship("OrderItem", back_populates="machine_family")
    default_accessories = relationship("FamilyAccessory", back_populates="machine_family", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<MachineFamily(id={self.id}, name='{self.name}')>"


class Accessory(Base):
    __tablename__ = 'accessories'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    accessory_id = Column(String, unique=True, index=True, nullable=False) # Your internal accessory ID/SKU
    description = Column(Text, nullable=True)
    category_tag = Column(String, nullable=True) # e.g., 'Electrical', 'Mechanical', 'Bought Out', 'Loadcell', 'Documents'
    unit_of_measure = Column(String, default="pcs", nullable=False)
    min_stock_level = Column(Integer, default=0, nullable=False)
    current_stock_level = Column(Integer, default=0, nullable=False)
    price_per_unit = Column(Float, default=0.0, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.now)
    updated_at = Column(DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now)

    family_links = relationship("FamilyAccessory", back_populates="accessory", cascade="all, delete-orphan")
    order_item_links = relationship("OrderItemAccessory", back_populates="accessory", cascade="all, delete-orphan")
    stock_history = relationship("StockHistory", back_populates="accessory")

    def __repr__(self):
        return f"<Accessory(id={self.id}, name='{self.name}', acc_id='{self.accessory_id}')>"


class FamilyAccessory(Base):
    """Links MachineFamily to Accessories that are default for it."""
    __tablename__ = 'family_accessories'
    id = Column(Integer, primary_key=True, index=True)
    machine_family_id = Column(Integer, ForeignKey('machine_families.id'), nullable=False)
    accessory_id = Column(Integer, ForeignKey('accessories.id'), nullable=False)
    default_quantity = Column(Integer, default=1, nullable=False)
    is_variable = Column(Boolean, default=False) # Is this accessory's detail variable per order? (e.g., specific model number)
    variable_placeholder = Column(String, nullable=True) # e.g., "Enter PLC Model: ______"
    is_required_for_dispatch = Column(Boolean, default=False, nullable=False) # Is this accessory required to be complete before dispatch
    created_at = Column(DateTime, default=datetime.datetime.now)
    updated_at = Column(DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now)

    machine_family = relationship("MachineFamily", back_populates="default_accessories")
    accessory = relationship("Accessory", back_populates="family_links")

    __table_args__ = (UniqueConstraint('machine_family_id', 'accessory_id', name='_family_accessory_uc'),)


class OrderItem(Base):
    """Represents a single product/machine family item within an order."""
    __tablename__ = 'order_items'
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey('orders.id'), nullable=False)
    machine_family_id = Column(Integer, ForeignKey('machine_families.id'), nullable=False)
    item_description = Column(String, nullable=True) # Specific model, color, custom notes for this item
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Float, nullable=False)
    total_price = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.now)
    updated_at = Column(DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now)

    order = relationship("Order", back_populates="items")
    machine_family = relationship("MachineFamily", back_populates="order_items")
    accessories = relationship("OrderItemAccessory", back_populates="order_item", cascade="all, delete-orphan")
    production_status = relationship("ProductionStatusHistory", back_populates="order_item", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<OrderItem(id={self.id}, order_id={self.order_id}, machine_family='{self.machine_family.name}', qty={self.quantity})>"


class OrderItemAccessory(Base):
    """Links a specific OrderItem to an Accessory, representing an accessory needed for that item."""
    __tablename__ = 'order_item_accessories'
    id = Column(Integer, primary_key=True, index=True)
    order_item_id = Column(Integer, ForeignKey('order_items.id'), nullable=False)
    accessory_id = Column(Integer, ForeignKey('accessories.id'), nullable=False)
    quantity = Column(Integer, nullable=False) # Quantity of this accessory needed for this order item
    unit_price = Column(Float, default=0.0, nullable=False)
    is_required_for_dispatch = Column(Boolean, default=False, nullable=False) # Is this specific accessory required to be complete/attached before dispatch?
    notes = Column(Text, nullable=True) # For variable accessories, e.g., "PLC Model: Siemens S7-1200"
    created_at = Column(DateTime, default=datetime.datetime.now)
    updated_at = Column(DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now)

    order_item = relationship("OrderItem", back_populates="accessories")
    accessory = relationship("Accessory", back_populates="order_item_links")

    __table_args__ = (UniqueConstraint('order_item_id', 'accessory_id', name='_order_item_accessory_uc'),)


class ProductionProcessStep(Base):
    __tablename__ = 'production_process_steps'
    id = Column(Integer, primary_key=True, index=True)
    step_name = Column(String, unique=True, nullable=False)
    description = Column(Text, nullable=True)
    order_index = Column(Integer, unique=True, nullable=False) # To define the sequence of steps
    is_dispatch_step = Column(Boolean, default=False, nullable=False) # Marks steps that signify completion towards dispatch
    created_at = Column(DateTime, default=datetime.datetime.now)
    updated_at = Column(DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now)

    production_status_history = relationship("ProductionStatusHistory", back_populates="process_step")

    def __repr__(self):
        return f"<ProductionProcessStep(id={self.id}, name='{self.step_name}', order={self.order_index})>"


class OrderStatusHistory(Base):
    """Logs changes to the overall order status."""
    __tablename__ = 'order_status_history'
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey('orders.id'), nullable=False)
    status = Column(String, nullable=False) # Status at this point in time
    timestamp = Column(DateTime, default=datetime.datetime.now, nullable=False)
    notes = Column(Text, nullable=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True) # User who changed the status (if applicable)

    order = relationship("Order", back_populates="status_history")
    user = relationship("User", back_populates="order_status_history")


class ProductionStatusHistory(Base):
    """Logs the progress of individual order items through production steps."""
    __tablename__ = 'production_status_history'
    id = Column(Integer, primary_key=True, index=True)
    order_item_id = Column(Integer, ForeignKey('order_items.id'), nullable=False)
    step_id = Column(Integer, ForeignKey('production_process_steps.id'), nullable=False)
    status = Column(String, nullable=False) # e.g., "In Progress", "Completed", "On Hold", "Not Started"
    timestamp = Column(DateTime, default=datetime.datetime.now, nullable=False)
    notes = Column(Text, nullable=True)
    completed_by_user_id = Column(Integer, ForeignKey('users.id'), nullable=True) # User who marked this step status

    order_item = relationship("OrderItem", back_populates="production_status")
    process_step = relationship("ProductionProcessStep", back_populates="production_status_history")
    user = relationship("User", back_populates="production_status_history")

    __table_args__ = (UniqueConstraint('order_item_id', 'step_id', name='_order_item_step_uc'),)


class StockHistory(Base):
    """Logs all stock movements for accessories."""
    __tablename__ = 'stock_history'
    id = Column(Integer, primary_key=True, index=True)
    accessory_id = Column(Integer, ForeignKey('accessories.id'), nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.now, nullable=False)
    change_type = Column(String, nullable=False) # e.g., "IN", "OUT", "ADJUSTMENT"
    quantity_change = Column(Integer, nullable=False) # Positive for IN, negative for OUT/ADJUSTMENT
    new_stock_level = Column(Integer, nullable=False) # Stock level after this change
    reason = Column(Text, nullable=True) # e.g., "Supplier delivery", "Issued for Order #XYZ"
    order_id = Column(Integer, ForeignKey('orders.id'), nullable=True) # Link to order if stock issued for one
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True) # User who recorded the change

    accessory = relationship("Accessory", back_populates="stock_history")
    order = relationship("Order", foreign_keys=[order_id]) # Direct link to Order if applicable
    user = relationship("User", back_populates="stock_history")

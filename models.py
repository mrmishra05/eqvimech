# models.py
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Numeric
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from sqlalchemy.sql import func
import datetime

Base = declarative_base()

class Customer(Base):
    __tablename__ = 'customers'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    company = Column(String, nullable=True)
    contact_person = Column(String, nullable=True)
    contact_number = Column(String, nullable=True)
    email = Column(String, nullable=True)
    billing_address = Column(Text, nullable=True)
    shipping_address = Column(Text, nullable=True)

    orders = relationship("Order", back_populates="customer")

    def __repr__(self):
        return f"<Customer(name='{self.name}', company='{self.company}')>"

class Order(Base):
    __tablename__ = 'orders'
    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey('customers.id'), nullable=False)
    order_date = Column(DateTime, default=func.now())
    expected_delivery_date = Column(DateTime, nullable=False)
    overall_status = Column(String, default="New") # e.g., New, Pending Production, In Production - Assembly, Ready for Dispatch, Dispatched
    notes = Column(Text, nullable=True)

    customer = relationship("Customer", back_populates="orders")
    order_items = relationship("OrderItem", back_populates="order")
    status_history = relationship("OrderStatusHistory", back_populates="order")

    def __repr__(self):
        return f"<Order(id={self.id}, customer_name='{self.customer.name}', status='{self.overall_status}')>"

class OrderStatusHistory(Base):
    __tablename__ = 'order_status_history'
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey('orders.id'), nullable=False)
    timestamp = Column(DateTime, default=func.now())
    status_from = Column(String, nullable=True)
    status_to = Column(String, nullable=False)
    notes = Column(Text, nullable=True)
    # user_id = Column(Integer, ForeignKey('users.id')) # Will add User model later

    order = relationship("Order", back_populates="status_history")

class MachineFamily(Base):
    __tablename__ = 'machine_families'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False) # e.g., UTM Machine, Wedge Grip Set
    description = Column(Text, nullable=True)
    is_product = Column(Boolean, default=True) # Can be sold as a standalone product

    default_accessories = relationship("FamilyAccessory", back_populates="machine_family")
    order_items = relationship("OrderItem", back_populates="machine_family")


    def __repr__(self):
        return f"<MachineFamily(name='{self.name}')>"

class Accessory(Base):
    __tablename__ = 'accessories'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    accessory_id = Column(String, unique=True, nullable=False) # Your internal accessory ID
    description = Column(Text, nullable=True)
    category_tag = Column(String, nullable=False) # e.g., Mechanical, Electronic, Bought Out, Documents
    unit_of_measure = Column(String, default="pcs")
    min_stock_level = Column(Integer, default=0)
    current_stock_level = Column(Integer, default=0)

    # Relationship to FamilyAccessory is established via FamilyAccessory
    stock_history = relationship("StockHistory", back_populates="accessory")

    def __repr__(self):
        return f"<Accessory(name='{self.name}', tag='{self.category_tag}', stock={self.current_stock_level})>"

class FamilyAccessory(Base):
    # This links MachineFamilies to their default Accessories
    __tablename__ = 'family_accessories'
    id = Column(Integer, primary_key=True, index=True)
    machine_family_id = Column(Integer, ForeignKey('machine_families.id'), nullable=False)
    accessory_id = Column(Integer, ForeignKey('accessories.id'), nullable=False)
    default_quantity = Column(Integer, nullable=False, default=1)
    is_variable = Column(Boolean, default=False) # True for "Gearbox Model : _______"
    variable_placeholder = Column(String, nullable=True) # Stores the placeholder text if is_variable is True

    machine_family = relationship("MachineFamily", back_populates="default_accessories")
    accessory = relationship("Accessory")

    def __repr__(self):
        return f"<FamilyAccessory(family='{self.machine_family.name}', accessory='{self.accessory.name}', qty={self.default_quantity})>"


class OrderItem(Base):
    # Represents a machine/product or an accessory bundle added to a specific order
    __tablename__ = 'order_items'
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey('orders.id'), nullable=False)
    machine_family_id = Column(Integer, ForeignKey('machine_families.id'), nullable=False) # Links to the ordered family
    quantity_ordered = Column(Integer, nullable=False, default=1)
    current_production_status = Column(String, default="Raw Material Ordered") # First step in your process

    order = relationship("Order", back_populates="order_items")
    machine_family = relationship("MachineFamily", back_populates="order_items")
    # For sub-accessories specific to this order item
    order_item_accessories = relationship("OrderItemAccessory", back_populates="order_item")
    production_status_history = relationship("ProductionStatusHistory", back_populates="order_item")


    def __repr__(self):
        return f"<OrderItem(order_id={self.order_id}, family='{self.machine_family.name}', qty={self.quantity_ordered}, status='{self.current_production_status}')>"

class OrderItemAccessory(Base):
    # Represents an individual accessory within an OrderItem, including its specific requirements for THIS order
    __tablename__ = 'order_item_accessories'
    id = Column(Integer, primary_key=True, index=True)
    order_item_id = Column(Integer, ForeignKey('order_items.id'), nullable=False)
    accessory_id = Column(Integer, ForeignKey('accessories.id'), nullable=False)
    required_quantity = Column(Integer, nullable=False, default=1)
    variable_value = Column(String, nullable=True) # Actual value for variable items (e.g., 'Gearbox Model XYS')
    current_status = Column(String, default="Pending") # e.g., Pending, Raw Material Ordered, Received, Integrated, Added to Dispatch Box
    is_custom = Column(Boolean, default=False) # True if added manually, not from default family list

    order_item = relationship("OrderItem", back_populates="order_item_accessories")
    accessory = relationship("Accessory")

    def __repr__(self):
        return f"<OrderItemAccessory(item_id={self.order_item_id}, acc='{self.accessory.name}', qty={self.required_quantity}, status='{self.current_status}')>"


class StockHistory(Base):
    # Logs all inventory movements
    __tablename__ = 'stock_history'
    id = Column(Integer, primary_key=True, index=True)
    accessory_id = Column(Integer, ForeignKey('accessories.id'), nullable=False)
    timestamp = Column(DateTime, default=func.now())
    change_type = Column(String, nullable=False) # e.g., 'IN', 'OUT', 'ADJUSTMENT'
    quantity_change = Column(Integer, nullable=False) # Positive for IN, negative for OUT/ADJUSTMENT
    new_stock_level = Column(Integer, nullable=False)
    reason = Column(Text, nullable=True) # For adjustments or specific 'OUT' reasons
    order_id = Column(Integer, ForeignKey('orders.id'), nullable=True) # Link to order if stock out for order

    accessory = relationship("Accessory", back_populates="stock_history")
    order = relationship("Order") # Link to Order if applicable

    def __repr__(self):
        return f"<StockHistory(acc='{self.accessory.name}', type='{self.change_type}', qty_change={self.quantity_change})>"

class ProductionProcessStep(Base):
    # Defines the sequence of production steps
    __tablename__ = 'production_process_steps'
    id = Column(Integer, primary_key=True, index=True)
    step_name = Column(String, unique=True, nullable=False)
    sequence_order = Column(Integer, unique=True, nullable=False) # For ordering the steps
    is_milestone = Column(Boolean, default=False) # e.g., Final Assembly, Testing for Use

    def __repr__(self):
        return f"<ProductionProcessStep(name='{self.step_name}', order={self.sequence_order})>"

class ProductionStatusHistory(Base):
    # Logs the status changes for individual OrderItems
    __tablename__ = 'production_status_history'
    id = Column(Integer, primary_key=True, index=True)
    order_item_id = Column(Integer, ForeignKey('order_items.id'), nullable=False)
    timestamp = Column(DateTime, default=func.now())
    status_from = Column(String, nullable=True)
    status_to = Column(String, nullable=False)
    notes = Column(Text, nullable=True)
    # user_id = Column(Integer, ForeignKey('users.id')) # Will add User model later

    order_item = relationship("OrderItem", back_populates="production_status_history")

# --- User & Permissions (Basic for now, will expand as needed) ---
class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False) # Store hashed passwords
    full_name = Column(String, nullable=True)
    email = Column(String, nullable=True)
    role = Column(String, default="General User") # e.g., Admin, General User (Production Manager is an Admin)

    def __repr__(self):
        return f"<User(username='{self.username}', role='{self.role}')>"

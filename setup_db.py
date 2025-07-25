import os
import sys
from datetime import datetime, timedelta, date
from werkzeug.security import generate_password_hash
from app import create_app, db
from models.user import User, UserRole
from models.customer import Customer
from models.product import Product, ProductFamily, ProductTag
from models.order import Order, OrderStatus, OrderStatusHistory

def create_users():
    """Create default users"""
    users = [
        {
            'username': 'admin',
            'email': 'admin@eqvimech.in',
            'password': 'admin123',
            'role': UserRole.ADMIN.value,
            'first_name': 'Admin',
            'last_name': 'User'
        },
        {
            'username': 'operator',
            'email': 'operator@eqvimech.in',
            'password': 'operator123',
            'role': UserRole.OPERATOR.value,
            'first_name': 'Operator',
            'last_name': 'User'
        },
        {
            'username': 'accountant',
            'email': 'accountant@eqvimech.in',
            'password': 'accountant123',
            'role': UserRole.ACCOUNTANT.value,
            'first_name': 'Accountant',
            'last_name': 'User'
        }
    ]
    
    for user_data in users:
        if not User.query.filter_by(username=user_data['username']).first():
            user = User(
                username=user_data['username'],
                email=user_data['email'],
                role=user_data['role'],
                first_name=user_data['first_name'],
                last_name=user_data['last_name'],
                password_hash=generate_password_hash(user_data['password'])
            )
            db.session.add(user)
    
    db.session.commit()
    print("Created default users")

def create_product_families():
    """Create product families"""
    families = [
        {
            'name': 'UTM Machine',
            'description': 'Universal Testing Machines for material testing'
        },
        {
            'name': 'Electronic Components',
            'description': 'Electronic parts and components for testing machines'
        },
        {
            'name': 'Mechanical Components',
            'description': 'Mechanical parts and components for testing machines'
        },
        {
            'name': 'Hardware',
            'description': 'Hardware components and accessories'
        },
        {
            'name': 'Software & Documentation',
            'description': 'Software and documentation for testing machines'
        },
        {
            'name': 'Vendor Ready Items',
            'description': 'Ready-to-use items from vendors'
        }
    ]
    
    for family_data in families:
        if not ProductFamily.query.filter_by(name=family_data['name']).first():
            family = ProductFamily(
                name=family_data['name'],
                description=family_data['description']
            )
            db.session.add(family)
    
    db.session.commit()
    print("Created product families")

def create_product_tags():
    """Create product tags"""
    tags = [
        {'name': 'Electronic', 'color': 'blue'},
        {'name': 'Mechanical', 'color': 'green'},
        {'name': 'Bought Out', 'color': 'purple'},
        {'name': 'Hardware', 'color': 'orange'},
        {'name': 'Software', 'color': 'cyan'},
        {'name': 'Documents', 'color': 'yellow'},
        {'name': 'VendorReady', 'color': 'red'}
    ]
    
    for tag_data in tags:
        if not ProductTag.query.filter_by(name=tag_data['name']).first():
            tag = ProductTag(
                name=tag_data['name'],
                color=tag_data['color']
            )
            db.session.add(tag)
    
    db.session.commit()
    print("Created product tags")

def create_products():
    """Create products"""
    # Get families and tags
    utm_family = ProductFamily.query.filter_by(name='UTM Machine').first()
    electronic_family = ProductFamily.query.filter_by(name='Electronic Components').first()
    mechanical_family = ProductFamily.query.filter_by(name='Mechanical Components').first()
    hardware_family = ProductFamily.query.filter_by(name='Hardware').first()
    software_family = ProductFamily.query.filter_by(name='Software & Documentation').first()
    vendor_family = ProductFamily.query.filter_by(name='Vendor Ready Items').first()
    
    electronic_tag = ProductTag.query.filter_by(name='Electronic').first()
    mechanical_tag = ProductTag.query.filter_by(name='Mechanical').first()
    bought_out_tag = ProductTag.query.filter_by(name='Bought Out').first()
    hardware_tag = ProductTag.query.filter_by(name='Hardware').first()
    software_tag = ProductTag.query.filter_by(name='Software').first()
    documents_tag = ProductTag.query.filter_by(name='Documents').first()
    vendor_tag = ProductTag.query.filter_by(name='VendorReady').first()
    
    products = [
        {
            'name': 'UTM-100 Universal Testing Machine',
            'description': '100kN capacity universal testing machine',
            'sku': 'UTM-100',
            'family': utm_family,
            'price': 850000,
            'cost': 650000,
            'lead_time_days': 45,
            'tags': [mechanical_tag, electronic_tag]
        },
        {
            'name': 'UTM-50 Universal Testing Machine',
            'description': '50kN capacity universal testing machine',
            'sku': 'UTM-50',
            'family': utm_family,
            'price': 650000,
            'cost': 480000,
            'lead_time_days': 40,
            'tags': [mechanical_tag, electronic_tag]
        },
        {
            'name': 'UTM-25 Universal Testing Machine',
            'description': '25kN capacity universal testing machine',
            'sku': 'UTM-25',
            'family': utm_family,
            'price': 450000,
            'cost': 320000,
            'lead_time_days': 35,
            'tags': [mechanical_tag, electronic_tag]
        },
        {
            'name': 'Load Cell 100kN',
            'description': '100kN capacity load cell for UTM',
            'sku': 'LC-100',
            'family': electronic_family,
            'price': 120000,
            'cost': 85000,
            'lead_time_days': 20,
            'tags': [electronic_tag, bought_out_tag]
        },
        {
            'name': 'Load Cell 50kN',
            'description': '50kN capacity load cell for UTM',
            'sku': 'LC-50',
            'family': electronic_family,
            'price': 85000,
            'cost': 60000,
            'lead_time_days': 20,
            'tags': [electronic_tag, bought_out_tag]
        },
        {
            'name': 'Load Cell 25kN',
            'description': '25kN capacity load cell for UTM',
            'sku': 'LC-25',
            'family': electronic_family,
            'price': 65000,
            'cost': 45000,
            'lead_time_days': 20,
            'tags': [electronic_tag, bought_out_tag]
        },
        {
            'name': 'Control Panel Assembly',
            'description': 'Electronic control panel for UTM',
            'sku': 'CP-UTM',
            'family': electronic_family,
            'price': 75000,
            'cost': 52000,
            'lead_time_days': 15,
            'tags': [electronic_tag]
        },
        {
            'name': 'Frame Assembly 100kN',
            'description': 'Frame assembly for 100kN UTM',
            'sku': 'FR-100',
            'family': mechanical_family,
            'price': 180000,
            'cost': 125000,
            'lead_time_days': 25,
            'tags': [mechanical_tag]
        },
        {
            'name': 'Frame Assembly 50kN',
            'description': 'Frame assembly for 50kN UTM',
            'sku': 'FR-50',
            'family': mechanical_family,
            'price': 140000,
            'cost': 95000,
            'lead_time_days': 25,
            'tags': [mechanical_tag]
        },
        {
            'name': 'Frame Assembly 25kN',
            'description': 'Frame assembly for 25kN UTM',
            'sku': 'FR-25',
            'family': mechanical_family,
            'price': 100000,
            'cost': 68000,
            'lead_time_days': 25,
            'tags': [mechanical_tag]
        },
        {
            'name': 'Grip Set Universal',
            'description': 'Universal grip set for UTM',
            'sku': 'GS-UNI',
            'family': mechanical_family,
            'price': 45000,
            'cost': 30000,
            'lead_time_days': 15,
            'tags': [mechanical_tag, bought_out_tag]
        },
        {
            'name': 'Grip Set Tensile',
            'description': 'Tensile grip set for UTM',
            'sku': 'GS-TEN',
            'family': mechanical_family,
            'price': 35000,
            'cost': 24000,
            'lead_time_days': 15,
            'tags': [mechanical_tag, bought_out_tag]
        },
        {
            'name': 'Grip Set Compression',
            'description': 'Compression grip set for UTM',
            'sku': 'GS-COM',
            'family': mechanical_family,
            'price': 30000,
            'cost': 20000,
            'lead_time_days': 15,
            'tags': [mechanical_tag, bought_out_tag]
        },
        {
            'name': 'UTM Software License',
            'description': 'Software license for UTM control and analysis',
            'sku': 'SW-UTM',
            'family': software_family,
            'price': 50000,
            'cost': 15000,
            'lead_time_days': 5,
            'tags': [software_tag]
        },
        {
            'name': 'UTM Documentation Package',
            'description': 'Complete documentation package for UTM',
            'sku': 'DOC-UTM',
            'family': software_family,
            'price': 15000,
            'cost': 8000,
            'lead_time_days': 10,
            'tags': [documents_tag]
        },
        {
            'name': 'Calibration Certificate',
            'description': 'Calibration certificate for UTM',
            'sku': 'CERT-CAL',
            'family': software_family,
            'price': 25000,
            'cost': 18000,
            'lead_time_days': 7,
            'tags': [documents_tag, vendor_tag]
        },
        {
            'name': 'Hardware Kit Standard',
            'description': 'Standard hardware kit for UTM assembly',
            'sku': 'HW-STD',
            'family': hardware_family,
            'price': 12000,
            'cost': 8000,
            'lead_time_days': 10,
            'tags': [hardware_tag, bought_out_tag]
        },
        {
            'name': 'Hardware Kit Premium',
            'description': 'Premium hardware kit for UTM assembly',
            'sku': 'HW-PRE',
            'family': hardware_family,
            'price': 18000,
            'cost': 12000,
            'lead_time_days': 10,
            'tags': [hardware_tag, bought_out_tag]
        },
        {
            'name': 'Sensor Package Basic',
            'description': 'Basic sensor package for UTM',
            'sku': 'SENS-BAS',
            'family': electronic_family,
            'price': 35000,
            'cost': 24000,
            'lead_time_days': 15,
            'tags': [electronic_tag, bought_out_tag]
        },
        {
            'name': 'Sensor Package Advanced',
            'description': 'Advanced sensor package for UTM',
            'sku': 'SENS-ADV',
            'family': electronic_family,
            'price': 55000,
            'cost': 38000,
            'lead_time_days': 15,
            'tags': [electronic_tag, bought_out_tag]
        }
    ]
    
    for product_data in products:
        if not Product.query.filter_by(sku=product_data['sku']).first():
            product = Product(
                name=product_data['name'],
                description=product_data['description'],
                sku=product_data['sku'],
                family_id=product_data['family'].id,
                price=product_data['price'],
                cost=product_data['cost'],
                lead_time_days=product_data['lead_time_days'],
                tags=product_data['tags']
            )
            db.session.add(product)
    
    db.session.commit()
    print("Created products")

def create_customers():
    """Create customers"""
    customers = [
        {
            'name': 'Automotive Testing Labs',
            'contact_person': 'Rajesh Kumar',
            'email': 'rajesh@autotestlabs.com',
            'phone': '9876543210',
            'address': '123 Industrial Area, Phase 1',
            'city': 'Pune',
            'state': 'Maharashtra',
            'pincode': '411001',
            'gstin': '27AABCU9603R1ZX'
        },
        {
            'name': 'Materials Research Institute',
            'contact_person': 'Priya Sharma',
            'email': 'priya@mri.org',
            'phone': '8765432109',
            'address': '456 Research Park',
            'city': 'Bangalore',
            'state': 'Karnataka',
            'pincode': '560001',
            'gstin': '29AABCU9603R1ZX'
        },
        {
            'name': 'Engineering College of Delhi',
            'contact_person': 'Dr. Amit Patel',
            'email': 'amit@ecd.edu',
            'phone': '7654321098',
            'address': 'Delhi University Campus',
            'city': 'New Delhi',
            'state': 'Delhi',
            'pincode': '110001',
            'gstin': '07AABCU9603R1ZX'
        },
        {
            'name': 'Quality Testing Services',
            'contact_person': 'Sanjay Gupta',
            'email': 'sanjay@qts.in',
            'phone': '6543210987',
            'address': '789 Industrial Estate',
            'city': 'Chennai',
            'state': 'Tamil Nadu',
            'pincode': '600001',
            'gstin': '33AABCU9603R1ZX'
        },
        {
            'name': 'Metallurgical Industries Ltd.',
            'contact_person': 'Vikram Singh',
            'email': 'vikram@mil.com',
            'phone': '5432109876',
            'address': '234 Steel Zone',
            'city': 'Jamshedpur',
            'state': 'Jharkhand',
            'pincode': '831001',
            'gstin': '20AABCU9603R1ZX'
        },
        {
            'name': 'Construction Materials Corp',
            'contact_person': 'Anita Desai',
            'email': 'anita@cmc.co.in',
            'phone': '4321098765',
            'address': '567 Builder Complex',
            'city': 'Mumbai',
            'state': 'Maharashtra',
            'pincode': '400001',
            'gstin': '27AABCU9603R2ZX'
        }
    ]
    
    for customer_data in customers:
        if not Customer.query.filter_by(name=customer_data['name']).first():
            customer = Customer(
                name=customer_data['name'],
                contact_person=customer_data['contact_person'],
                email=customer_data['email'],
                phone=customer_data['phone'],
                address=customer_data['address'],
                city=customer_data['city'],
                state=customer_data['state'],
                pincode=customer_data['pincode'],
                gstin=customer_data['gstin']
            )
            db.session.add(customer)
    
    db.session.commit()
    print("Created customers")

def create_orders():
    """Create sample orders"""
    # Get products
    utm_100 = Product.query.filter_by(sku='UTM-100').first()
    utm_50 = Product.query.filter_by(sku='UTM-50').first()
    utm_25 = Product.query.filter_by(sku='UTM-25').first()
    
    # Get customers
    customers = Customer.query.all()
    
    # Get admin user
    admin = User.query.filter_by(username='admin').first()
    
    # Create orders
    today = date.today()
    
    # Sample order statuses for different stages
    statuses = list(OrderStatus)
    
    # Create 60 orders with different statuses and dates
    for i in range(60):
        # Select product based on index
        if i % 3 == 0:
            product = utm_100
        elif i % 3 == 1:
            product = utm_50
        else:
            product = utm_25
        
        # Select customer
        customer = customers[i % len(customers)]
        
        # Set dates
        start_date = today - timedelta(days=90 - i)
        delivery_date = start_date + timedelta(days=product.lead_time_days)
        
        # Set status based on progress
        status_index = min(i % len(statuses), len(statuses) - 1)
        status = statuses[status_index].value
        
        # Set amount and payment
        amount = product.price
        amount_received = amount if status in [OrderStatus.VERIFIED.value, OrderStatus.DISPATCH.value] else (amount * 0.5 if i % 2 == 0 else 0)
        
        # Create order
        order = Order(
            product_id=product.id,
            customer_id=customer.id,
            order_number=f'EM-{start_date.strftime("%Y%m%d")}-{i+1:03d}',
            start_date=start_date,
            delivery_date=delivery_date,
            status=status,
            amount=amount,
            amount_received=amount_received,
            notes=f'Sample order {i+1} for {product.name}'
        )
        db.session.add(order)
        db.session.flush()  # Get the order ID
        
        # Create status history
        for j in range(status_index + 1):
            history = OrderStatusHistory(
                order_id=order.id,
                old_status='' if j == 0 else statuses[j-1].value,
                new_status=statuses[j].value,
                notes=f'Status updated to {statuses[j].value}',
                user_id=admin.id,
                timestamp=datetime.now() - timedelta(days=90 - i - j*2)
            )
            db.session.add(history)
    
    db.session.commit()
    print("Created sample orders")

def setup_database():
    """Set up the database with initial data"""
    app = create_app()
    with app.app_context():
        # Create tables
        db.create_all()
        
        # Create data
        create_users()
        create_product_families()
        create_product_tags()
        create_products()
        create_customers()
        create_orders()
        
        print("Database setup complete!")

if __name__ == '__main__':
    setup_database()


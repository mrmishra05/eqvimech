#!/usr/bin/env python3
import os
import sys
sys.path.insert(0, os.path.dirname(__file__))

from src.main import app
from src.models.user import db, User
from src.models.customer import Customer
from src.models.product import Product, ProductFamily
from src.models.order import Order
from datetime import datetime, timedelta
import random

def seed_data():
    with app.app_context():
        # Clear existing data
        print("Clearing existing data...")
        db.drop_all()
        db.create_all()
        
        # Create users
        print("Creating users...")
        admin = User(username='admin', email='admin@eqvimech.com', role='admin')
        admin.set_password('admin123')
        
        operator = User(username='operator', email='operator@eqvimech.com', role='operator')
        operator.set_password('operator123')
        
        accountant = User(username='accountant', email='accountant@eqvimech.com', role='accountant')
        accountant.set_password('accountant123')
        
        db.session.add_all([admin, operator, accountant])
        db.session.commit()
        
        # Create product families
        print("Creating product families...")
        families = [
            ProductFamily(name='Hydraulic Systems', description='Hydraulic pumps, cylinders, and valves'),
            ProductFamily(name='Pneumatic Systems', description='Air compressors, pneumatic cylinders, and controls'),
            ProductFamily(name='Mechanical Components', description='Gears, bearings, and mechanical assemblies'),
            ProductFamily(name='Control Systems', description='PLCs, sensors, and automation equipment'),
            ProductFamily(name='Custom Machinery', description='Specialized manufacturing equipment')
        ]
        
        db.session.add_all(families)
        db.session.commit()
        
        # Create products
        print("Creating products...")
        products = [
            # Hydraulic Systems
            Product(name='Hydraulic Pump HP-2000', code='HP-2000', family_id=1, 
                   base_price=2500.00, production_time_days=14, tags='pump,hydraulic,high-pressure'),
            Product(name='Hydraulic Cylinder HC-500', code='HC-500', family_id=1, 
                   base_price=800.00, production_time_days=7, tags='cylinder,hydraulic,heavy-duty'),
            Product(name='Hydraulic Valve HV-100', code='HV-100', family_id=1, 
                   base_price=350.00, production_time_days=5, tags='valve,hydraulic,control'),
            
            # Pneumatic Systems
            Product(name='Air Compressor AC-1500', code='AC-1500', family_id=2, 
                   base_price=1800.00, production_time_days=10, tags='compressor,pneumatic,industrial'),
            Product(name='Pneumatic Cylinder PC-300', code='PC-300', family_id=2, 
                   base_price=450.00, production_time_days=6, tags='cylinder,pneumatic,automation'),
            
            # Mechanical Components
            Product(name='Precision Gear Set PG-200', code='PG-200', family_id=3, 
                   base_price=1200.00, production_time_days=12, tags='gear,precision,mechanical'),
            Product(name='Heavy Duty Bearing HDB-50', code='HDB-50', family_id=3, 
                   base_price=300.00, production_time_days=4, tags='bearing,heavy-duty,mechanical'),
            
            # Control Systems
            Product(name='PLC Control Unit PCU-400', code='PCU-400', family_id=4, 
                   base_price=2200.00, production_time_days=8, tags='plc,control,automation'),
            Product(name='Pressure Sensor PS-100', code='PS-100', family_id=4, 
                   base_price=180.00, production_time_days=3, tags='sensor,pressure,monitoring'),
            
            # Custom Machinery
            Product(name='Custom Assembly Line CAL-1000', code='CAL-1000', family_id=5, 
                   base_price=15000.00, production_time_days=45, tags='custom,assembly,automation')
        ]
        
        db.session.add_all(products)
        db.session.commit()
        
        # Create customers
        print("Creating customers...")
        customers = [
            Customer(name='AutoTech Industries', company='AutoTech Industries Inc.', 
                    email='orders@autotech.com', phone='+1-555-0101', 
                    contact_person='John Smith', address='123 Industrial Blvd, Detroit, MI'),
            Customer(name='Manufacturing Solutions', company='Manufacturing Solutions LLC', 
                    email='procurement@mansol.com', phone='+1-555-0102', 
                    contact_person='Sarah Johnson', address='456 Factory St, Chicago, IL'),
            Customer(name='Heavy Machinery Corp', company='Heavy Machinery Corp', 
                    email='orders@heavymach.com', phone='+1-555-0103', 
                    contact_person='Mike Wilson', address='789 Equipment Ave, Houston, TX'),
            Customer(name='Precision Works', company='Precision Works Ltd.', 
                    email='info@precisionworks.com', phone='+1-555-0104', 
                    contact_person='Lisa Chen', address='321 Precision Dr, San Jose, CA'),
            Customer(name='Industrial Dynamics', company='Industrial Dynamics Inc.', 
                    email='purchasing@indyndyn.com', phone='+1-555-0105', 
                    contact_person='Robert Brown', address='654 Dynamic Way, Phoenix, AZ')
        ]
        
        db.session.add_all(customers)
        db.session.commit()
        
        # Create orders
        print("Creating orders...")
        statuses = ['pending', 'in_production', 'quality_check', 'completed', 'delayed']
        priorities = ['low', 'normal', 'high', 'urgent']
        
        orders = []
        for i in range(50):
            # Random dates within the last 6 months
            order_date = datetime.utcnow() - timedelta(days=random.randint(1, 180))
            start_date = order_date + timedelta(days=random.randint(1, 5))
            delivery_date = start_date + timedelta(days=random.randint(7, 30))
            
            product = random.choice(products)
            customer = random.choice(customers)
            quantity = random.randint(1, 10)
            unit_price = product.base_price * random.uniform(0.9, 1.2)  # ±20% variation
            
            status = random.choice(statuses)
            actual_delivery_date = None
            if status == 'completed':
                # For completed orders, set actual delivery date
                actual_delivery_date = delivery_date + timedelta(days=random.randint(-3, 7))
            
            order = Order(
                order_number=f"EQV-{order_date.strftime('%Y%m%d')}-{i+1:03d}",
                product_id=product.id,
                customer_id=customer.id,
                quantity=quantity,
                unit_price=unit_price,
                order_date=order_date,
                start_date=start_date,
                delivery_date=delivery_date,
                actual_delivery_date=actual_delivery_date,
                status=status,
                priority=random.choice(priorities),
                created_by=admin.id,
                notes=f"Sample order {i+1} for testing purposes"
            )
            
            # Calculate amounts
            order.calculate_amounts()
            
            # Set payment information
            if status == 'completed':
                order.amount_received = order.total_amount
            elif status in ['in_production', 'quality_check']:
                order.amount_received = order.total_amount * random.uniform(0.3, 0.8)
            else:
                order.amount_received = order.total_amount * random.uniform(0, 0.5)
            
            order.update_payment_status()
            orders.append(order)
        
        db.session.add_all(orders)
        db.session.commit()
        
        print(f"Seed data created successfully!")
        print(f"- {len([admin, operator, accountant])} users created")
        print(f"- {len(families)} product families created")
        print(f"- {len(products)} products created")
        print(f"- {len(customers)} customers created")
        print(f"- {len(orders)} orders created")
        print("\nDefault login credentials:")
        print("Admin: admin / admin123")
        print("Operator: operator / operator123")
        print("Accountant: accountant / accountant123")

if __name__ == '__main__':
    seed_data()


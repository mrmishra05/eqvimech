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

def update_seed_data():
    with app.app_context():
        # Clear existing data
        print("Clearing existing data...")
        db.drop_all()
        db.create_all()
        
        # Create users (keep existing users)
        print("Creating users...")
        admin = User(username='admin', email='admin@eqvimech.com', role='admin')
        admin.set_password('admin123')
        
        operator = User(username='operator', email='operator@eqvimech.com', role='operator')
        operator.set_password('operator123')
        
        accountant = User(username='accountant', email='accountant@eqvimech.com', role='accountant')
        accountant.set_password('accountant123')
        
        db.session.add_all([admin, operator, accountant])
        db.session.commit()
        
        # Create product families based on Excel data
        print("Creating product families...")
        families = [
            ProductFamily(name='UTM Machine', description='Universal Testing Machine components and assemblies'),
            ProductFamily(name='Electronic Components', description='Electronic sensors, controllers, and wiring'),
            ProductFamily(name='Mechanical Components', description='Mechanical parts, frames, and assemblies'),
            ProductFamily(name='Hardware Components', description='Bolts, fasteners, and hardware items'),
            ProductFamily(name='Software & Documentation', description='Software packages and technical documentation'),
            ProductFamily(name='Vendor Ready Items', description='Items ready for vendor dispatch')
        ]
        
        db.session.add_all(families)
        db.session.commit()
        
        # Create products based on Excel data
        print("Creating products...")
        products = [
            # UTM Machine Family
            Product(name='UTM Machine Complete Assembly', code='UTM-001', family_id=1, 
                   base_price=25000.00, production_time_days=45, tags='Product,Mechanical,Electronic'),
            Product(name='Load Frame Assembly', code='UTM-002', family_id=1, 
                   base_price=8000.00, production_time_days=20, tags='Mechanical,Product'),
            Product(name='Control Panel Assembly', code='UTM-003', family_id=1, 
                   base_price=3500.00, production_time_days=15, tags='Electronic,Product'),
            
            # Electronic Components
            Product(name='Limit Sensor (Up)', code='ELC-001', family_id=2, 
                   base_price=150.00, production_time_days=3, tags='Electronic,Bought Out'),
            Product(name='Limit Sensor (Down)', code='ELC-002', family_id=2, 
                   base_price=150.00, production_time_days=3, tags='Electronic,Bought Out'),
            Product(name='Magnet for Sensor', code='ELC-003', family_id=2, 
                   base_price=25.00, production_time_days=2, tags='Electronic,Bought Out'),
            Product(name='Load Cell 50kN', code='ELC-004', family_id=2, 
                   base_price=1200.00, production_time_days=7, tags='Loadcell,Electronic'),
            Product(name='Control Wiring Harness', code='ELC-005', family_id=2, 
                   base_price=300.00, production_time_days=5, tags='Electronic,Hardware'),
            
            # Mechanical Components
            Product(name='Main Frame Structure', code='MEC-001', family_id=3, 
                   base_price=4500.00, production_time_days=18, tags='Mechanical,Product'),
            Product(name='Crosshead Assembly', code='MEC-002', family_id=3, 
                   base_price=2200.00, production_time_days=12, tags='Mechanical,Product'),
            Product(name='Base Plate Assembly', code='MEC-003', family_id=3, 
                   base_price=1800.00, production_time_days=10, tags='Mechanical,Product'),
            Product(name='Lead Screw Assembly', code='MEC-004', family_id=3, 
                   base_price=1500.00, production_time_days=8, tags='Mechanical,Bought Out'),
            
            # Hardware Components
            Product(name='Mounting Bolts Set', code='HW-001', family_id=4, 
                   base_price=45.00, production_time_days=1, tags='Hardware,Bought Out'),
            Product(name='Safety Guards', code='HW-002', family_id=4, 
                   base_price=350.00, production_time_days=5, tags='Hardware,Mechanical'),
            Product(name='Leveling Feet Set', code='HW-003', family_id=4, 
                   base_price=120.00, production_time_days=2, tags='Hardware,Bought Out'),
            
            # Software & Documentation
            Product(name='UTM Control Software', code='SW-001', family_id=5, 
                   base_price=2500.00, production_time_days=10, tags='Software,Product'),
            Product(name='User Manual & Documentation', code='DOC-001', family_id=5, 
                   base_price=200.00, production_time_days=3, tags='Documents,Product'),
            Product(name='Calibration Certificate', code='DOC-002', family_id=5, 
                   base_price=150.00, production_time_days=2, tags='Documents,Testing fo Use'),
            
            # Vendor Ready Items
            Product(name='Packaging & Dispatch Kit', code='VR-001', family_id=6, 
                   base_price=300.00, production_time_days=2, tags='VendorReady,Product'),
            Product(name='Spare Parts Kit', code='VR-002', family_id=6, 
                   base_price=800.00, production_time_days=5, tags='VendorReady,Hardware')
        ]
        
        db.session.add_all(products)
        db.session.commit()
        
        # Create customers (manufacturing companies that would use UTM machines)
        print("Creating customers...")
        customers = [
            Customer(name='Automotive Testing Labs', company='Automotive Testing Labs Inc.', 
                    email='procurement@autotestlabs.com', phone='+1-555-0201', 
                    contact_person='Dr. Sarah Mitchell', address='1234 Research Blvd, Detroit, MI'),
            Customer(name='Materials Research Institute', company='Materials Research Institute', 
                    email='orders@materialresearch.edu', phone='+1-555-0202', 
                    contact_person='Prof. James Chen', address='5678 University Ave, Boston, MA'),
            Customer(name='Quality Control Systems', company='Quality Control Systems LLC', 
                    email='purchasing@qcsystems.com', phone='+1-555-0203', 
                    contact_person='Maria Rodriguez', address='9012 Industrial Park, Houston, TX'),
            Customer(name='Aerospace Components Ltd', company='Aerospace Components Ltd', 
                    email='testing@aerocomp.com', phone='+1-555-0204', 
                    contact_person='David Thompson', address='3456 Aerospace Dr, Seattle, WA'),
            Customer(name='Steel Testing Corporation', company='Steel Testing Corporation', 
                    email='lab@steeltest.com', phone='+1-555-0205', 
                    contact_person='Jennifer Wang', address='7890 Steel Mill Rd, Pittsburgh, PA'),
            Customer(name='Construction Materials Lab', company='Construction Materials Lab', 
                    email='orders@constmatlab.com', phone='+1-555-0206', 
                    contact_person='Michael Brown', address='2468 Construction Ave, Denver, CO')
        ]
        
        db.session.add_all(customers)
        db.session.commit()
        
        # Create orders with realistic manufacturing stages
        print("Creating orders...")
        # Updated statuses based on Excel data
        statuses = [
            'raw_material_ordered', 'raw_material_received', 'frame_fabrication', 
            'outsource_machining', 'initial_assembly', 'electrical_wiring', 
            'final_assembly', 'loadcell_calibration', 'verified', 'dispatch'
        ]
        priorities = ['low', 'normal', 'high', 'urgent']
        
        orders = []
        for i in range(60):
            # Random dates within the last 8 months
            order_date = datetime.utcnow() - timedelta(days=random.randint(1, 240))
            start_date = order_date + timedelta(days=random.randint(1, 7))
            delivery_date = start_date + timedelta(days=random.randint(10, 60))
            
            product = random.choice(products)
            customer = random.choice(customers)
            quantity = random.randint(1, 5) if 'Assembly' in product.name else random.randint(1, 20)
            unit_price = product.base_price * random.uniform(0.85, 1.15)  # ±15% variation
            
            status = random.choice(statuses)
            actual_delivery_date = None
            if status in ['verified', 'dispatch']:
                # For completed orders, set actual delivery date
                actual_delivery_date = delivery_date + timedelta(days=random.randint(-5, 10))
            
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
                notes=f"Manufacturing order for {product.name} - Stage: {status.replace('_', ' ').title()}"
            )
            
            # Calculate amounts
            order.calculate_amounts()
            
            # Set payment information based on order status
            if status in ['verified', 'dispatch']:
                order.amount_received = order.total_amount * random.uniform(0.8, 1.0)
            elif status in ['final_assembly', 'loadcell_calibration']:
                order.amount_received = order.total_amount * random.uniform(0.5, 0.8)
            elif status in ['initial_assembly', 'electrical_wiring']:
                order.amount_received = order.total_amount * random.uniform(0.3, 0.6)
            else:
                order.amount_received = order.total_amount * random.uniform(0, 0.4)
            
            order.update_payment_status()
            orders.append(order)
        
        db.session.add_all(orders)
        db.session.commit()
        
        print(f"Updated seed data created successfully!")
        print(f"- {len([admin, operator, accountant])} users created")
        print(f"- {len(families)} product families created")
        print(f"- {len(products)} products created")
        print(f"- {len(customers)} customers created")
        print(f"- {len(orders)} orders created")
        print("\nProduct families include:")
        for family in families:
            print(f"  - {family.name}")
        print("\nOrder statuses include realistic manufacturing stages:")
        for status in statuses:
            print(f"  - {status.replace('_', ' ').title()}")
        print("\nDefault login credentials:")
        print("Admin: admin / admin123")
        print("Operator: operator / operator123")
        print("Accountant: accountant / accountant123")

if __name__ == '__main__':
    update_seed_data()


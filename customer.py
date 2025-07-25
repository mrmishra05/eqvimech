from src.models.user import db
from datetime import datetime

class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    company = db.Column(db.String(100))
    email = db.Column(db.String(120))
    phone = db.Column(db.String(20))
    address = db.Column(db.Text)
    contact_person = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationship with orders
    orders = db.relationship('Order', backref='customer', lazy=True)

    def __repr__(self):
        return f'<Customer {self.name}>'

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'company': self.company,
            'email': self.email,
            'phone': self.phone,
            'address': self.address,
            'contact_person': self.contact_person,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'is_active': self.is_active
        }

    def get_total_orders(self):
        return len(self.orders)

    def get_total_amount(self):
        return sum(order.total_amount for order in self.orders if order.total_amount)

    def get_pending_amount(self):
        return sum(order.total_amount - order.amount_received for order in self.orders 
                  if order.total_amount and order.amount_received and order.status != 'completed')


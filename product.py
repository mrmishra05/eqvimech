from src.models.user import db
from datetime import datetime

class ProductFamily(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship with products
    products = db.relationship('Product', backref='family', lazy=True)

    def __repr__(self):
        return f'<ProductFamily {self.name}>'

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(50), unique=True)
    description = db.Column(db.Text)
    family_id = db.Column(db.Integer, db.ForeignKey('product_family.id'))
    tags = db.Column(db.String(200))  # Comma-separated tags
    base_price = db.Column(db.Float)
    production_time_days = db.Column(db.Integer)  # Standard production time
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship with orders
    orders = db.relationship('Order', backref='product', lazy=True)

    def __repr__(self):
        return f'<Product {self.name}>'

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'code': self.code,
            'description': self.description,
            'family_id': self.family_id,
            'family_name': self.family.name if self.family else None,
            'tags': self.tags.split(',') if self.tags else [],
            'base_price': self.base_price,
            'production_time_days': self.production_time_days,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    def get_tags_list(self):
        return [tag.strip() for tag in self.tags.split(',') if tag.strip()] if self.tags else []

    def set_tags_list(self, tags_list):
        self.tags = ','.join(tags_list) if tags_list else None


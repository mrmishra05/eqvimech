from app import create_app, db
from config import get_config
from models.user import User
from models.customer import Customer
from models.product import Product, ProductFamily, ProductTag
from models.order import Order

app = create_app(get_config())

@app.shell_context_processor
def make_shell_context():
    return {
        'db': db, 
        'User': User, 
        'Customer': Customer, 
        'Product': Product,
        'ProductFamily': ProductFamily,
        'ProductTag': ProductTag,
        'Order': Order
    }

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)


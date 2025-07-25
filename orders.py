from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from models.user import User
from models.order import Order, OrderStatus, OrderStatusHistory
from models.product import Product
from models.customer import Customer
from sqlalchemy import or_, and_, desc
from datetime import datetime, date

orders_bp = Blueprint('orders', __name__)

@orders_bp.route('', methods=['GET'])
@jwt_required()
def get_orders():
    """Get all orders with filtering and pagination"""
    try:
        # Get filter parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        status = request.args.get('status')
        customer_id = request.args.get('customer_id', type=int)
        product_id = request.args.get('product_id', type=int)
        search = request.args.get('search')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        sort_by = request.args.get('sort_by', 'id')
        sort_order = request.args.get('sort_order', 'desc')
        is_delayed = request.args.get('is_delayed', type=bool)
        
        # Build query
        query = Order.query
        
        # Apply filters
        if status:
            query = query.filter(Order.status == status)
        
        if customer_id:
            query = query.filter(Order.customer_id == customer_id)
        
        if product_id:
            query = query.filter(Order.product_id == product_id)
        
        if search:
            search_term = f"%{search}%"
            query = query.join(Product).join(Customer).filter(
                or_(
                    Order.order_number.ilike(search_term),
                    Product.name.ilike(search_term),
                    Customer.name.ilike(search_term)
                )
            )
        
        if start_date:
            try:
                start_date_obj = datetime.fromisoformat(start_date).date()
                query = query.filter(Order.start_date >= start_date_obj)
            except ValueError:
                return jsonify({"error": "Invalid start_date format. Use ISO format (YYYY-MM-DD)"}), 400
        
        if end_date:
            try:
                end_date_obj = datetime.fromisoformat(end_date).date()
                query = query.filter(Order.start_date <= end_date_obj)
            except ValueError:
                return jsonify({"error": "Invalid end_date format. Use ISO format (YYYY-MM-DD)"}), 400
        
        if is_delayed is not None:
            today = date.today()
            if is_delayed:
                query = query.filter(
                    and_(
                        ~Order.status.in_([OrderStatus.VERIFIED.value, OrderStatus.DISPATCH.value]),
                        Order.delivery_date < today
                    )
                )
            else:
                query = query.filter(
                    or_(
                        Order.status.in_([OrderStatus.VERIFIED.value, OrderStatus.DISPATCH.value]),
                        Order.delivery_date >= today
                    )
                )
        
        # Apply sorting
        if sort_by == 'product_name':
            query = query.join(Product).order_by(
                desc(Product.name) if sort_order == 'desc' else Product.name
            )
        elif sort_by == 'customer_name':
            query = query.join(Customer).order_by(
                desc(Customer.name) if sort_order == 'desc' else Customer.name
            )
        else:
            # Default to sorting by Order attributes
            sort_column = getattr(Order, sort_by, Order.id)
            query = query.order_by(
                desc(sort_column) if sort_order == 'desc' else sort_column
            )
        
        # Execute query with pagination
        paginated_orders = query.paginate(page=page, per_page=per_page, error_out=False)
        
        # Prepare response
        orders_data = []
        for order in paginated_orders.items:
            order_dict = order.to_dict()
            # Add product and customer names
            order_dict['product_name'] = order.product.name
            order_dict['customer_name'] = order.customer.name
            orders_data.append(order_dict)
        
        return jsonify({
            'orders': orders_data,
            'total': paginated_orders.total,
            'pages': paginated_orders.pages,
            'current_page': paginated_orders.page
        }), 200
    except Exception as e:
        return jsonify({'error': f'Failed to fetch orders: {str(e)}'}), 500

@orders_bp.route('/<int:id>', methods=['GET'])
@jwt_required()
def get_order(id):
    """Get a specific order by ID"""
    try:
        order = Order.query.get(id)
        if not order:
            return jsonify({'error': 'Order not found'}), 404
        
        # Get detailed information with status history
        order_data = order.to_dict_with_history()
        
        # Add product and customer details
        order_data['product'] = order.product.to_dict()
        order_data['customer'] = order.customer.to_dict()
        
        return jsonify(order_data), 200
    except Exception as e:
        return jsonify({'error': f'Failed to fetch order: {str(e)}'}), 500

@orders_bp.route('', methods=['POST'])
@jwt_required()
def create_order():
    """Create a new order"""
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)
    
    # Check permissions (admin or operator)
    if not current_user or not current_user.is_operator:
        return jsonify({'error': 'Unauthorized access'}), 403
    
    if not request.is_json:
        return jsonify({'error': 'Missing JSON in request'}), 400
    
    data = request.json
    
    # Validate required fields
    required_fields = ['product_id', 'customer_id', 'delivery_date', 'amount']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Missing required field: {field}'}), 400
    
    # Validate product and customer exist
    product = Product.query.get(data['product_id'])
    if not product:
        return jsonify({'error': 'Product not found'}), 404
    
    customer = Customer.query.get(data['customer_id'])
    if not customer:
        return jsonify({'error': 'Customer not found'}), 404
    
    try:
        # Create order
        order = Order.from_dict(data)
        
        # Generate order number if not provided
        if not order.order_number:
            # Format: EM-YYYYMMDD-XXX (XXX is sequential number for the day)
            today_str = datetime.now().strftime('%Y%m%d')
            last_order = Order.query.filter(
                Order.order_number.like(f'EM-{today_str}-%')
            ).order_by(Order.id.desc()).first()
            
            if last_order and last_order.order_number:
                try:
                    last_num = int(last_order.order_number.split('-')[-1])
                    new_num = last_num + 1
                except (ValueError, IndexError):
                    new_num = 1
            else:
                new_num = 1
            
            order.order_number = f'EM-{today_str}-{new_num:03d}'
        
        db.session.add(order)
        db.session.flush()  # Get the order ID
        
        # Create initial status history entry
        history = OrderStatusHistory(
            order_id=order.id,
            old_status='',
            new_status=order.status,
            notes='Order created',
            user_id=current_user_id
        )
        db.session.add(history)
        
        db.session.commit()
        
        # Return the created order
        return jsonify(order.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to create order: {str(e)}'}), 500

@orders_bp.route('/<int:id>', methods=['PUT'])
@jwt_required()
def update_order(id):
    """Update an existing order"""
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)
    
    # Check permissions based on what's being updated
    if not current_user:
        return jsonify({'error': 'Unauthorized access'}), 403
    
    order = Order.query.get(id)
    if not order:
        return jsonify({'error': 'Order not found'}), 404
    
    if not request.is_json:
        return jsonify({'error': 'Missing JSON in request'}), 400
    
    data = request.json
    
    # Check permissions based on fields being updated
    payment_fields = ['amount', 'amount_received']
    status_fields = ['status']
    other_fields = ['product_id', 'customer_id', 'order_number', 'start_date', 
                   'delivery_date', 'notes']
    
    # Only admins can update certain fields
    if any(field in data for field in other_fields) and not current_user.is_admin:
        return jsonify({'error': 'Only admins can update these fields'}), 403
    
    # Operators can update status
    if any(field in data for field in status_fields) and not current_user.is_operator:
        return jsonify({'error': 'Only operators or admins can update status'}), 403
    
    # Accountants can update payment fields
    if any(field in data for field in payment_fields) and not (current_user.is_admin or current_user.is_accountant):
        return jsonify({'error': 'Only accountants or admins can update payment information'}), 403
    
    try:
        # Update order
        old_status = order.status
        order.update_from_dict(data)
        
        # If status changed, add status history entry
        if 'status' in data and old_status != data['status']:
            history = OrderStatusHistory(
                order_id=order.id,
                old_status=old_status,
                new_status=data['status'],
                notes=data.get('status_notes', ''),
                user_id=current_user_id
            )
            db.session.add(history)
        
        db.session.commit()
        
        # Return the updated order
        return jsonify(order.to_dict()), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to update order: {str(e)}'}), 500

@orders_bp.route('/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_order(id):
    """Delete an order (admin only)"""
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)
    
    # Check permissions (admin only)
    if not current_user or not current_user.is_admin:
        return jsonify({'error': 'Unauthorized access'}), 403
    
    order = Order.query.get(id)
    if not order:
        return jsonify({'error': 'Order not found'}), 404
    
    try:
        db.session.delete(order)
        db.session.commit()
        return jsonify({'message': 'Order deleted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to delete order: {str(e)}'}), 500

@orders_bp.route('/statuses', methods=['GET'])
@jwt_required()
def get_order_statuses():
    """Get all possible order statuses"""
    try:
        statuses = [status.value for status in OrderStatus]
        return jsonify(statuses), 200
    except Exception as e:
        return jsonify({'error': f'Failed to fetch order statuses: {str(e)}'}), 500


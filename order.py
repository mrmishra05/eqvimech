from flask import Blueprint, request, jsonify, session
from src.models.user import db
from src.models.order import Order
from src.models.customer import Customer
from src.models.product import Product
from src.routes.auth import login_required, role_required
from datetime import datetime

order_bp = Blueprint('order', __name__)

@order_bp.route('/orders', methods=['GET'])
@login_required
def get_orders():
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        status = request.args.get('status')
        customer_id = request.args.get('customer_id', type=int)
        product_id = request.args.get('product_id', type=int)
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        search = request.args.get('search', '')
        
        query = Order.query
        
        # Apply filters
        if status:
            query = query.filter(Order.status == status)
        if customer_id:
            query = query.filter(Order.customer_id == customer_id)
        if product_id:
            query = query.filter(Order.product_id == product_id)
        
        if start_date:
            start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            query = query.filter(Order.order_date >= start_dt)
        if end_date:
            end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            query = query.filter(Order.order_date <= end_dt)
        
        if search:
            query = query.join(Customer).join(Product).filter(
                Order.order_number.contains(search) |
                Customer.name.contains(search) |
                Product.name.contains(search)
            )
        
        # Order by most recent first
        query = query.order_by(Order.order_date.desc())
        
        orders = query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'orders': [order.to_dict() for order in orders.items],
            'total': orders.total,
            'pages': orders.pages,
            'current_page': page
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@order_bp.route('/orders/<int:order_id>', methods=['GET'])
@login_required
def get_order(order_id):
    try:
        order = Order.query.get_or_404(order_id)
        return jsonify({'order': order.to_dict()}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@order_bp.route('/orders', methods=['POST'])
@role_required(['admin', 'operator'])
def create_order():
    try:
        data = request.get_json()
        
        required_fields = ['product_id', 'customer_id', 'quantity']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'{field} is required'}), 400
        
        # Validate product and customer exist
        product = Product.query.get(data['product_id'])
        customer = Customer.query.get(data['customer_id'])
        
        if not product:
            return jsonify({'error': 'Product not found'}), 404
        if not customer:
            return jsonify({'error': 'Customer not found'}), 404
        
        # Generate order number
        order_number = Order.generate_order_number()
        
        order = Order(
            order_number=order_number,
            product_id=data['product_id'],
            customer_id=data['customer_id'],
            quantity=data['quantity'],
            unit_price=data.get('unit_price', product.base_price),
            notes=data.get('notes'),
            priority=data.get('priority', 'normal'),
            created_by=session['user_id']
        )
        
        # Set dates
        if 'start_date' in data:
            order.start_date = datetime.fromisoformat(data['start_date'].replace('Z', '+00:00'))
        if 'delivery_date' in data:
            order.delivery_date = datetime.fromisoformat(data['delivery_date'].replace('Z', '+00:00'))
        
        # Calculate amounts
        order.calculate_amounts()
        order.update_payment_status()
        
        db.session.add(order)
        db.session.commit()
        
        return jsonify({
            'message': 'Order created successfully',
            'order': order.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@order_bp.route('/orders/<int:order_id>', methods=['PUT'])
@login_required
def update_order(order_id):
    try:
        order = Order.query.get_or_404(order_id)
        data = request.get_json()
        user_role = session.get('user_role')
        
        # Role-based field restrictions
        if user_role == 'operator':
            # Operators can only update status and notes
            allowed_fields = ['status', 'notes', 'actual_delivery_date']
            for field in data:
                if field not in allowed_fields:
                    return jsonify({'error': f'Operators cannot update {field}'}), 403
        
        elif user_role == 'accountant':
            # Accountants can only update payment-related fields
            allowed_fields = ['amount_received', 'payment_status', 'notes']
            for field in data:
                if field not in allowed_fields:
                    return jsonify({'error': f'Accountants cannot update {field}'}), 403
        
        # Update fields based on role permissions
        if 'status' in data and user_role in ['admin', 'operator']:
            valid_statuses = [
                'raw_material_ordered', 'raw_material_received', 'frame_fabrication', 
                'outsource_machining', 'initial_assembly', 'electrical_wiring', 
                'final_assembly', 'loadcell_calibration', 'verified', 'dispatch', 'cancelled'
            ]
            if data['status'] in valid_statuses:
                order.status = data['status']
                
                # Auto-set actual delivery date when dispatched
                if data['status'] == 'dispatch' and not order.actual_delivery_date:
                    order.actual_delivery_date = datetime.utcnow()
        
        if 'quantity' in data and user_role == 'admin':
            order.quantity = data['quantity']
        if 'unit_price' in data and user_role == 'admin':
            order.unit_price = data['unit_price']
        if 'start_date' in data and user_role == 'admin':
            order.start_date = datetime.fromisoformat(data['start_date'].replace('Z', '+00:00'))
        if 'delivery_date' in data and user_role == 'admin':
            order.delivery_date = datetime.fromisoformat(data['delivery_date'].replace('Z', '+00:00'))
        if 'actual_delivery_date' in data and user_role in ['admin', 'operator']:
            order.actual_delivery_date = datetime.fromisoformat(data['actual_delivery_date'].replace('Z', '+00:00'))
        if 'priority' in data and user_role == 'admin':
            order.priority = data['priority']
        if 'notes' in data:
            order.notes = data['notes']
        
        # Payment updates (admin and accountant)
        if 'amount_received' in data and user_role in ['admin', 'accountant']:
            order.amount_received = data['amount_received']
        
        # Recalculate amounts and payment status
        order.calculate_amounts()
        order.update_payment_status()
        
        db.session.commit()
        
        return jsonify({
            'message': 'Order updated successfully',
            'order': order.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@order_bp.route('/orders/<int:order_id>', methods=['DELETE'])
@role_required(['admin'])
def delete_order(order_id):
    try:
        order = Order.query.get_or_404(order_id)
        
        db.session.delete(order)
        db.session.commit()
        
        return jsonify({'message': 'Order deleted successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@order_bp.route('/orders/stats', methods=['GET'])
@login_required
def get_order_stats():
    try:
        # Basic counts
        total_orders = Order.query.count()
        completed_orders = Order.query.filter(Order.status == 'completed').count()
        pending_orders = Order.query.filter(Order.status.in_(['pending', 'in_production', 'quality_check'])).count()
        delayed_orders = Order.query.filter(Order.status == 'delayed').count()
        
        # Calculate delay rate
        delay_rate = (delayed_orders / total_orders * 100) if total_orders > 0 else 0
        
        # On-time delivery calculation
        completed_on_time = Order.query.filter(
            Order.status == 'completed',
            Order.actual_delivery_date <= Order.delivery_date
        ).count()
        on_time_delivery_rate = (completed_on_time / completed_orders * 100) if completed_orders > 0 else 0
        
        # Revenue stats
        total_revenue = db.session.query(db.func.sum(Order.total_amount)).filter(
            Order.status == 'completed'
        ).scalar() or 0
        
        pending_revenue = db.session.query(db.func.sum(Order.total_amount)).filter(
            Order.status.in_(['pending', 'in_production', 'quality_check'])
        ).scalar() or 0
        
        return jsonify({
            'total_orders': total_orders,
            'completed_orders': completed_orders,
            'pending_orders': pending_orders,
            'delayed_orders': delayed_orders,
            'delay_rate': round(delay_rate, 2),
            'on_time_delivery_rate': round(on_time_delivery_rate, 2),
            'total_revenue': total_revenue,
            'pending_revenue': pending_revenue
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


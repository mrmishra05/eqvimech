from flask import Blueprint, request, jsonify
from src.models.user import db
from src.models.order import Order
from src.models.customer import Customer
from src.models.product import Product, ProductFamily
from src.routes.auth import login_required
from datetime import datetime, timedelta
from sqlalchemy import func, extract

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/dashboard/kpis', methods=['GET'])
@login_required
def get_dashboard_kpis():
    try:
        # Date range filter
        days = request.args.get('days', 30, type=int)
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Basic KPIs
        total_orders = Order.query.count()
        
        # Status values might be stored in different formats (lowercase with underscores or title case with spaces)
        # We'll check for both formats
        completed_statuses = ['verified', 'dispatch', 'Verified', 'Dispatch']
        pending_statuses = [
            'raw_material_ordered', 'raw_material_received', 'frame_fabrication', 
            'outsource_machining', 'initial_assembly', 'electrical_wiring', 
            'final_assembly', 'loadcell_calibration',
            'Raw Material Ordered', 'Raw Material Received', 'Frame Fabrication',
            'Outsource Machining', 'Initial Assembly', 'Electrical Wiring',
            'Final Assembly', 'Loadcell Calibration'
        ]
        
        completed_orders = Order.query.filter(Order.status.in_(completed_statuses)).count()
        pending_orders = Order.query.filter(Order.status.in_(pending_statuses)).count()
        
        # Calculate delayed orders based on delivery date
        delayed_orders = Order.query.filter(
            ~Order.status.in_(completed_statuses),
            Order.delivery_date < datetime.utcnow()
        ).count()
        
        # Period-specific KPIs
        period_orders = Order.query.filter(Order.order_date >= start_date).count()
        period_completed = Order.query.filter(
            Order.status.in_(completed_statuses),
            Order.order_date >= start_date
        ).count()
        
        # Calculate rates
        completion_rate = (completed_orders / total_orders * 100) if total_orders > 0 else 0
        delay_rate = (delayed_orders / total_orders * 100) if total_orders > 0 else 0
        
        # On-time delivery rate
        completed_on_time = Order.query.filter(
            Order.status.in_(completed_statuses),
            Order.actual_delivery_date <= Order.delivery_date
        ).count() or 0
        
        on_time_delivery_rate = (completed_on_time / completed_orders * 100) if completed_orders > 0 else 0
        
        # Revenue calculations
        total_revenue = db.session.query(func.sum(Order.total_amount)).filter(
            Order.status.in_(completed_statuses)
        ).scalar() or 0
        
        period_revenue = db.session.query(func.sum(Order.total_amount)).filter(
            Order.status.in_(completed_statuses),
            Order.order_date >= start_date
        ).scalar() or 0
        
        # Outstanding payments
        outstanding_amount = db.session.query(func.sum(Order.amount_due)).filter(
            Order.amount_due > 0
        ).scalar() or 0
        
        return jsonify({
            'totalOrders': total_orders,
            'completedOrders': completed_orders,
            'pendingOrders': pending_orders,
            'delayedOrders': delayed_orders,
            'periodOrders': period_orders,
            'periodCompleted': period_completed,
            'completionRate': round(completion_rate, 2),
            'delayRate': round(delay_rate, 2),
            'onTimeDelivery': round(on_time_delivery_rate, 2),
            'totalRevenue': float(total_revenue) if total_revenue else 0,
            'periodRevenue': float(period_revenue) if period_revenue else 0,
            'outstandingAmount': float(outstanding_amount) if outstanding_amount else 0,
            'periodDays': days
        }), 200
        
    except Exception as e:
        print(f"Dashboard KPI Error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@dashboard_bp.route('/dashboard/sales-trends', methods=['GET'])
@login_required
def get_sales_trends():
    try:
        period = request.args.get('period', 'monthly')  # monthly, quarterly, yearly
        months = request.args.get('months', 12, type=int)
        
        if period == 'monthly':
            # Monthly sales for the last N months
            trends = db.session.query(
                extract('year', Order.order_date).label('year'),
                extract('month', Order.order_date).label('month'),
                func.count(Order.id).label('order_count'),
                func.sum(Order.total_amount).label('revenue')
            ).filter(
                Order.order_date >= datetime.utcnow() - timedelta(days=months*30)
            ).group_by(
                extract('year', Order.order_date),
                extract('month', Order.order_date)
            ).order_by(
                extract('year', Order.order_date),
                extract('month', Order.order_date)
            ).all()
            
            trend_data = []
            for trend in trends:
                trend_data.append({
                    'period': f"{int(trend.year)}-{int(trend.month):02d}",
                    'order_count': trend.order_count,
                    'revenue': float(trend.revenue) if trend.revenue else 0
                })
        
        elif period == 'quarterly':
            # Quarterly sales
            trends = db.session.query(
                extract('year', Order.order_date).label('year'),
                func.floor((extract('month', Order.order_date) - 1) / 3 + 1).label('quarter'),
                func.count(Order.id).label('order_count'),
                func.sum(Order.total_amount).label('revenue')
            ).group_by(
                extract('year', Order.order_date),
                func.floor((extract('month', Order.order_date) - 1) / 3 + 1)
            ).order_by(
                extract('year', Order.order_date),
                func.floor((extract('month', Order.order_date) - 1) / 3 + 1)
            ).all()
            
            trend_data = []
            for trend in trends:
                trend_data.append({
                    'period': f"{int(trend.year)}-Q{int(trend.quarter)}",
                    'order_count': trend.order_count,
                    'revenue': float(trend.revenue) if trend.revenue else 0
                })
        
        return jsonify({
            'period': period,
            'trends': trend_data
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@dashboard_bp.route('/dashboard/order-status-distribution', methods=['GET'])
@login_required
def get_order_status_distribution():
    try:
        status_counts = db.session.query(
            Order.status,
            func.count(Order.id).label('count')
        ).group_by(Order.status).all()
        
        distribution = []
        for status, count in status_counts:
            distribution.append({
                'status': status,
                'count': count
            })
        
        return jsonify({'distribution': distribution}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@dashboard_bp.route('/dashboard/product-family-performance', methods=['GET'])
@login_required
def get_product_family_performance():
    try:
        performance = db.session.query(
            ProductFamily.name.label('family_name'),
            func.count(Order.id).label('order_count'),
            func.sum(Order.total_amount).label('revenue')
        ).join(Product, ProductFamily.id == Product.family_id)\
         .join(Order, Product.id == Order.product_id)\
         .group_by(ProductFamily.id, ProductFamily.name)\
         .order_by(func.sum(Order.total_amount).desc()).all()
        
        performance_data = []
        for family_name, order_count, revenue in performance:
            performance_data.append({
                'family_name': family_name,
                'order_count': order_count,
                'revenue': float(revenue) if revenue else 0
            })
        
        return jsonify({'performance': performance_data}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@dashboard_bp.route('/dashboard/top-customers', methods=['GET'])
@login_required
def get_top_customers():
    try:
        limit = request.args.get('limit', 10, type=int)
        
        top_customers = db.session.query(
            Customer.name,
            func.count(Order.id).label('order_count'),
            func.sum(Order.total_amount).label('total_revenue')
        ).join(Order, Customer.id == Order.customer_id)\
         .group_by(Customer.id, Customer.name)\
         .order_by(func.sum(Order.total_amount).desc())\
         .limit(limit).all()
        
        customers_data = []
        for name, order_count, total_revenue in top_customers:
            customers_data.append({
                'name': name,
                'order_count': order_count,
                'total_revenue': float(total_revenue) if total_revenue else 0
            })
        
        return jsonify({'top_customers': customers_data}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@dashboard_bp.route('/dashboard/delivery-performance', methods=['GET'])
@login_required
def get_delivery_performance():
    try:
        # Get delivery performance metrics
        completed_orders = Order.query.filter(Order.status.in_(['verified', 'dispatch'])).all()
        
        on_time = 0
        early = 0
        late = 0
        
        for order in completed_orders:
            if order.actual_delivery_date and order.delivery_date:
                if order.actual_delivery_date <= order.delivery_date:
                    on_time += 1
                elif order.actual_delivery_date < order.delivery_date:
                    early += 1
                else:
                    late += 1
        
        total_completed = len(completed_orders)
        
        performance = {
            'on_time': on_time,
            'early': early,
            'late': late,
            'total_completed': total_completed,
            'on_time_percentage': (on_time / total_completed * 100) if total_completed > 0 else 0
        }
        
        return jsonify({'delivery_performance': performance}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


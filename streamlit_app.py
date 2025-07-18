import streamlit as st
from database import create_tables, get_db, initialize_master_data, engine # Import engine for inspect
from models import (
    User, Customer, Order, MachineFamily, Accessory, FamilyAccessory,
    OrderItem, OrderItemAccessory, ProductionProcessStep,
    OrderStatusHistory, ProductionStatusHistory, StockHistory,
    hash_password, verify_password
)
from sqlalchemy.orm import Session, selectinload, joinedload
from sqlalchemy import func, inspect, text, desc # Import desc for descending order
import datetime
import pandas as pd


# --- Streamlit Page Configuration ---
st.set_page_config(
    page_title="EQVIMECH Production Dashboard",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Database Initialization (Run once on app startup) ---
# This ensures tables are created and master data is initialized when the app first runs.
# It now uses the cached 'engine' from database.py.
if 'db_initialized' not in st.session_state:
    db_session = None
    try:
        db_session = next(get_db()) # Get a session to perform operations
        inspector = inspect(engine) # Use the imported 'engine' directly

        if not inspector.has_table("users"): # Check for a base table, 'users' is good
            st.toast("Initializing database for the first time...")
            create_tables()
            initialize_master_data(db_session)
            st.toast("Database tables created and master data initialized!")
        st.session_state.db_initialized = True
    except Exception as e:
        st.error(f"Error during initial database setup: {e}")
        st.stop() # Stop the app if DB setup fails
    finally:
        if db_session:
            db_session.close()

# --- Initialize Session State Variables ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'username' not in st.session_state:
    st.session_state.username = ""
if 'role' not in st.session_state:
    st.session_state.role = ""
if 'user_id' not in st.session_state: # Store user ID for audit trails
    st.session_state.user_id = None
if 'current_page' not in st.session_state:
    st.session_state.current_page = "Dashboard" # Default starting page

if 'order_items_config' not in st.session_state:
    st.session_state.order_items_config = [] # To store items added to current order

if 'current_customer_id' not in st.session_state:
    st.session_state.current_customer_id = None # Store selected customer for order

# --- Authentication Functions ---
def verify_login(db: Session, username, password):
    user = db.query(User).filter_by(username=username).first()
    if user and verify_password(password, user.hashed_password):
        return user
    return None

def add_user(db: Session, username, password, full_name, email, role="viewer"):
    if db.query(User).filter_by(username=username).first():
        return False, "Username already exists."
    if email and db.query(User).filter_by(email=email).first():
        return False, "Email already exists."
    
    hashed_pass = hash_password(password)
    new_user = User(username=username, hashed_password=hashed_pass, full_name=full_name, email=email, role=role)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return True, f"User '{username}' created successfully with role '{role}'."


# --- Utility Functions (Cached for performance) ---

@st.cache_data(ttl=3600) # Cache for 1 hour, or clear manually
def get_all_customers_cached():
    db = next(get_db())
    try:
        return db.query(Customer).order_by(Customer.name).all()
    finally:
        db.close()

@st.cache_data(ttl=3600)
def get_all_machine_families_cached():
    db = next(get_db())
    try:
        return db.query(MachineFamily).order_by(MachineFamily.name).all()
    finally:
        db.close()

@st.cache_data(ttl=3600)
def get_all_accessories_cached():
    db = next(get_db())
    try:
        return db.query(Accessory).order_by(Accessory.name).all()
    finally:
        db.close()

@st.cache_data(ttl=3600)
def get_all_production_steps_cached():
    db = next(get_db())
    try:
        return db.query(ProductionProcessStep).order_by(ProductionProcessStep.order_index).all()
    finally:
        db.close()

@st.cache_data(ttl=60) # Cache for 1 minute for dashboard metrics
def get_dashboard_metrics_cached():
    db = next(get_db())
    try:
        active_orders_count = db.query(Order).filter(Order.status.in_(["Approved", "In Production", "Ready for Dispatch", "Pending Approval"])).count()
        product_families_count = db.query(MachineFamily).filter(MachineFamily.is_product == True).count()

        # Get IDs of final dispatch steps
        final_step_ids = [s.id for s in db.query(ProductionProcessStep).filter(ProductionProcessStep.is_dispatch_step == True).all()]

        # Items in progress: Where the latest status is NOT a final dispatch step
        # This requires a subquery or advanced filtering to get the LATEST status for each item
        # For a more robust solution, we'd need a subquery for max(timestamp) per order_item_id
        # For dashboard simplicity, let's count items that have not yet reached ANY final dispatch step
        items_in_progress_count = db.query(OrderItem).filter(
            ~OrderItem.production_status.any(ProductionStatusHistory.step_id.in_(final_step_ids))
        ).count()

        # Items Completed: Where the item HAS reached at least one final dispatch step
        items_completed_count = db.query(OrderItem).filter(
            OrderItem.production_status.any(ProductionStatusHistory.step_id.in_(final_step_ids))
        ).count()

        # Items Blocked: Items that have a production status of "On Hold"
        items_blocked_count = db.query(OrderItem).filter(
            OrderItem.production_status.any(ProductionStatusHistory.status == "On Hold")
        ).count()

        total_order_items = db.query(OrderItem).count()
        overall_progress_percent = (items_completed_count / total_order_items * 100) if total_order_items > 0 else 0

        return {
            "active_orders": active_orders_count,
            "product_families": product_families_count,
            "items_in_progress": items_in_progress_count,
            "items_completed": items_completed_count,
            "items_blocked": items_blocked_count,
            "overall_progress": overall_progress_percent
        }
    finally:
        db.close()

@st.cache_data(ttl=30) # Cache recent activity for 30 seconds
def get_recent_activity_cached():
    db = next(get_db())
    try:
        # Fetch recent order status changes (last 5)
        recent_order_status_changes = db.query(OrderStatusHistory).options(
            joinedload(OrderStatusHistory.order).selectinload(Order.customer), # Load order and customer
            joinedload(OrderStatusHistory.user) # Load user who made change
        ).order_by(desc(OrderStatusHistory.timestamp)).limit(5).all()

        # Fetch recent production status changes (last 5)
        recent_production_status_changes = db.query(ProductionStatusHistory).options(
            joinedload(ProductionStatusHistory.order_item).selectinload(OrderItem.machine_family), # Load order item and machine family
            joinedload(ProductionStatusHistory.process_step), # Load the process step
            joinedload(ProductionStatusHistory.user) # Load user who made change
        ).order_by(desc(ProductionStatusHistory.timestamp)).limit(5).all()

        all_activities = []
        for osc in recent_order_status_changes:
            all_activities.append({
                "Timestamp": osc.timestamp, # Keep as datetime for sorting
                "Time": osc.timestamp.strftime("%Y-%m-%d %H:%M %p"),
                "Action": "Order Status Updated",
                "Details": f"Order {osc.order.generate_full_order_id()} - Status: {osc.status}",
                "User": osc.user.username if osc.user else "System"
            })

        for psc in recent_production_status_changes:
            all_activities.append({
                "Timestamp": psc.timestamp, # Keep as datetime for sorting
                "Time": psc.timestamp.strftime("%Y-%m-%d %H:%M %p"),
                "Action": "Production Status Updated",
                "Details": f"Item: {psc.order_item.machine_family.name} - Step: {psc.process_step.step_name} - Status: {psc.status}",
                "User": psc.user.username if psc.user else "System"
            })
        
        # Sort all activities by actual timestamp, newest first
        all_activities.sort(key=lambda x: x["Timestamp"], reverse=True)

        return all_activities
    finally:
        db.close()


def update_overall_order_status(db_session, order_id, new_status, user_id=None):
    order = db_session.query(Order).get(order_id)
    if order and order.status != new_status:
        old_status = order.status
        order.status = new_status
        db_session.add(OrderStatusHistory(
            order_id=order_id,
            status=new_status,
            notes=f"Status updated from '{old_status}' to '{new_status}' by {st.session_state.username or 'System'}",
            user_id=user_id # Use actual user ID from session state
        ))
        db_session.commit()
        st.toast(f"Order {order.generate_full_order_id()} status updated to '{new_status}'")
        get_dashboard_metrics_cached.clear() # Clear dashboard cache
        get_recent_activity_cached.clear() # Clear activity cache
        # If there's a cached function for all orders, clear that too
        # get_all_orders_cached.clear()
    else:
        st.warning("Status is already the same or order not found.")

def update_order_item_production_status(db_session, order_item_id, new_step_name, user_id=None, status="Completed"):
    order_item = db_session.query(OrderItem).get(order_item_id)
    if order_item:
        new_step = db_session.query(ProductionProcessStep).filter_by(step_name=new_step_name).first()
        if not new_step:
            st.error(f"Production step '{new_step_name}' not found.")
            return

        # Check if the status is actually changing for the *latest* step
        latest_prod_status = db_session.query(ProductionStatusHistory).options(selectinload(ProductionStatusHistory.process_step)).filter_by(
            order_item_id=order_item_id
        ).order_by(desc(ProductionStatusHistory.timestamp)).first()

        if not latest_prod_status or latest_prod_status.step_id != new_step.id or latest_prod_status.status != status:
            db_session.add(ProductionStatusHistory(
                order_item_id=order_item_id,
                step_id=new_step.id,
                status=status,
                notes=f"Production status updated to '{new_step_name}' by {st.session_state.username or 'System'}",
                completed_by_user_id=user_id # Use actual user ID from session state
            ))
            db_session.commit()
            st.toast(f"Item '{order_item.machine_family.name}' production status updated to '{new_step_name}'")
            get_dashboard_metrics_cached.clear()
            get_recent_activity_cached.clear()
        else:
            st.info(f"Item '{order_item.machine_family.name}' is already at '{new_step_name}' with status '{status}'.")
    else:
        st.warning("Order item not found.")


# --- Page Functions ---

def show_login_page():
    st.title("Eqvimech Manufacturing Order Tracker - Login")
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submit_button = st.form_submit_button("Login")

        if submit_button:
            db = next(get_db())
            user = verify_login(db, username, password)
            if user:
                st.session_state.logged_in = True
                st.session_state.username = user.username
                st.session_state.role = user.role
                st.session_state.user_id = user.id # Store user ID
                st.session_state.current_page = "Dashboard" # Redirect to dashboard after login
                st.success(f"Welcome, {user.full_name or user.username} ({user.role})!")
                st.rerun()
            else:
                st.error("Invalid username or password.")
            db.close()
    st.markdown("---")
    st.subheader("Initial Admin Setup (Run this ONCE to create admin user)")
    with st.expander("Create Initial Admin User"):
        with st.form("create_admin_form"):
            admin_username = st.text_input("Admin Username", key="admin_user_input")
            admin_password = st.text_input("Admin Password", type="password", key="admin_pass_input")
            admin_full_name = st.text_input("Admin Full Name", key="admin_full_name_input")
            admin_email = st.text_input("Admin Email (Optional)", key="admin_email_input")
            create_admin_button = st.form_submit_button("Create Admin User")
            if create_admin_button:
                db = next(get_db())
                # Check if admin user already exists to prevent duplicates
                existing_admin = db.query(User).filter_by(role="admin").first()
                if existing_admin:
                    st.warning("An admin user already exists. Please login or reset password if needed.")
                else:
                    success, message = add_user(db, admin_username, admin_password, admin_full_name, admin_email, "admin")
                    if success:
                        st.success(message)
                        st.session_state.admin_user_created = True # Set a flag
                    else:
                        st.error(message)
                db.close()
    # Provide credentials for testing if no admin user is created yet
    if not st.session_state.get('admin_user_created', False) and not db.query(User).filter_by(role="admin").first():
         st.info("Default Admin User will be created on first run if no users exist (admin/admin_pass).")


def show_dashboard():
    if not st.session_state.logged_in:
        st.warning("Please log in to view the dashboard.")
        return

    st.title("⚙️ Production Dashboard")
    st.markdown("Real-time manufacturing tracking for your 4-member team")
    st.markdown("---")

    metrics = get_dashboard_metrics_cached()

    # --- Metrics ---
    col1, col2, col3, col4, col5, col6 = st.columns(6)

    col1.metric("Active Orders", metrics["active_orders"])
    col2.metric("Product Families", metrics["product_families"])
    col3.metric("Items In Progress", metrics["items_in_progress"])
    col4.metric("Items Completed", metrics["items_completed"])
    col5.metric("Items Blocked", metrics["items_blocked"])
    col6.metric("Overall Progress", f"{metrics['overall_progress']:.0f}%")

    st.markdown("---")

    # --- Recent Activity ---
    st.subheader("Recent Activity")
    recent_activities = get_recent_activity_cached()

    if recent_activities:
        # Remove the 'Timestamp' column for display
        display_activities = [{k: v for k, v in d.items() if k != 'Timestamp'} for d in recent_activities]
        st.dataframe(pd.DataFrame(display_activities), use_container_width=True, hide_index=True)
    else:
        st.info("No recent activity to display.")


def show_create_order_page():
    if not st.session_state.logged_in:
        st.warning("Please log in to create orders.")
        return
    if st.session_state.role not in ["admin", "sales"]:
        st.warning("You do not have permission to create orders.")
        return

    st.title("📝 Create New Order")
    st.markdown("---")

    db = next(get_db()) # Get DB session
    try:
        # --- 1. Select or Add Customer ---
        st.subheader("1. Select or Add Customer")
        existing_customers = get_all_customers_cached()
        customer_options = {c.name: c for c in existing_customers}
        customer_names = ["-- Select Customer --"] + sorted(list(customer_options.keys())) # Sort alphabetically
        
        # Determine initial index for selectbox based on session state
        initial_customer_idx = 0
        if st.session_state.current_customer_id:
            selected_customer_obj_from_state = db.query(Customer).get(st.session_state.current_customer_id)
            if selected_customer_obj_from_state and selected_customer_obj_from_state.name in customer_names:
                initial_customer_idx = customer_names.index(selected_customer_obj_from_state.name)

        selected_customer_name = st.selectbox(
            "Select Existing Customer:",
            customer_names,
            index=initial_customer_idx,
            key="select_customer_for_order"
        )

        selected_customer_obj = None
        if selected_customer_name != "-- Select Customer --":
            selected_customer_obj = customer_options.get(selected_customer_name)
            st.session_state.current_customer_id = selected_customer_obj.id if selected_customer_obj else None
            if selected_customer_obj:
                st.info(f"Selected Customer: **{selected_customer_obj.name}** (Contact: {selected_customer_obj.contact_person or 'N/A'})")
        else:
            st.session_state.current_customer_id = None
            st.markdown("Or **Add New Customer**:")
            with st.expander("Add New Customer Details"):
                with st.form("new_customer_form"):
                    new_customer_name = st.text_input("Customer Name *", key="new_cust_name_input")
                    new_customer_contact = st.text_input("Contact Person", key="new_cust_contact_input")
                    new_customer_email = st.text_input("Email", key="new_cust_email_input")
                    new_customer_phone = st.text_input("Phone", key="new_cust_phone_input")
                    new_customer_address = st.text_area("Address", key="new_cust_address_input")
                    new_customer_gst = st.text_input("GST Number", key="new_cust_gst_input")
                    save_new_customer_btn = st.form_submit_button("Save New Customer")

                    if save_new_customer_btn:
                        if new_customer_name:
                            existing_customer = db.query(Customer).filter(func.lower(Customer.name) == func.lower(new_customer_name)).first()
                            if existing_customer:
                                st.warning(f"Customer '{new_customer_name}' already exists. Please select them.")
                            else:
                                new_customer = Customer(
                                    name=new_customer_name,
                                    contact_person=new_customer_contact,
                                    email=new_customer_email,
                                    phone=new_customer_phone,
                                    address=new_customer_address,
                                    gst_number=new_customer_gst
                                )
                                db.add(new_customer)
                                db.commit()
                                db.refresh(new_customer)
                                st.success(f"Customer '{new_customer.name}' added successfully!")
                                st.session_state.current_customer_id = new_customer.id
                                get_all_customers_cached.clear() # Clear cache to refresh selectbox
                                st.experimental_rerun() # Rerun to update customer selectbox
                        else:
                            st.error("Customer Name cannot be empty.")

        if st.session_state.current_customer_id is None:
            st.info("Please select or add a customer to proceed with order details.")
            return # Stop here if no customer is selected/added

        st.markdown("---")

        # --- 2. Add Products/Machine Families ---
        st.subheader("2. Add Products/Machine Families to Order")
        col_product, col_qty = st.columns([3, 1])

        machine_families = get_all_machine_families_cached()
        # Filter for products (is_product=True)
        product_families = sorted([mf for mf in machine_families if mf.is_product], key=lambda x: x.name)
        machine_family_names = ["-- Select Product/Family --"] + [mf.name for mf in product_families]

        selected_family_name = col_product.selectbox(
            "Select Product/Family to Add",
            machine_family_names,
            key="add_product_family_select"
        )
        selected_family_obj = None
        if selected_family_name != "-- Select Product/Family --":
            selected_family_obj = next((mf for mf in product_families if mf.name == selected_family_name), None)

        quantity = col_qty.number_input("Quantity", min_value=1, value=1, step=1, key="product_family_qty")

        if st.button("Add Product/Family to Order", key="add_product_to_order_btn"):
            if selected_family_obj:
                # Use a unique key for the text_input so it resets properly when a new selection is made
                item_description_key = f"desc_input_{selected_family_obj.id}_{datetime.datetime.now().timestamp()}"
                item_description = st.text_input(f"Specific Model/Description for {selected_family_obj.name}",
                                                  value="", # Default empty
                                                  key=item_description_key)
                # Check if this family is already added with the same description to sum quantities
                existing_entry_idx = -1
                for idx, item in enumerate(st.session_state.order_items_config):
                    if item['id'] == selected_family_obj.id and item['item_description'] == item_description:
                        existing_entry_idx = idx
                        break

                if existing_entry_idx != -1:
                    st.session_state.order_items_config[existing_entry_idx]['quantity'] += quantity
                    st.success(f"Quantity for '{selected_family_obj.name}' updated to {st.session_state.order_items_config[existing_entry_idx]['quantity']}.")
                else:
                    st.session_state.order_items_config.append({
                        "type": "machine_family",
                        "id": selected_family_obj.id,
                        "name": selected_family_obj.name,
                        "quantity": quantity,
                        "item_description": item_description,
                        "unit_price": float(selected_family_obj.price_per_unit) if selected_family_obj.price_per_unit is not None else 0.0
                    })
                    st.success(f"Added {quantity} x {selected_family_obj.name} to current order configuration.")

                # Reset selectbox and quantity after adding (rerun will re-render them)
                st.session_state.add_product_family_select = "-- Select Product/Family --"
                st.session_state.product_family_qty = 1
                st.experimental_rerun()
            else:
                st.warning("Please select a product/family to add.")

        st.markdown("---")

        # --- 3. Current Order Configuration ---
        st.subheader("3. Current Order Configuration")
        if st.session_state.order_items_config:
            df_display = []
            for i, item in enumerate(st.session_state.order_items_config):
                df_display.append({
                    "Product/Family": item['name'],
                    "Description": item['item_description'],
                    "Quantity": item['quantity'],
                    "Unit Price": f"₹{item['unit_price']:.2f}",
                    "Total Item Price": f"₹{(item['quantity'] * item['unit_price']):.2f}",
                    "Remove": f"Remove_{i}" # For removal button
                })
            
            # Use data_editor for an interactive table with a remove button
            edited_df = st.data_editor(
                pd.DataFrame(df_display),
                column_config={
                    "Remove": st.column_config.ButtonColumn(
                        "Remove",
                        help="Click to remove item from order",
                        width="small"
                    )
                },
                hide_index=True,
                use_container_width=True,
                key="order_items_data_editor"
            )

            # Handle removal from data_editor
            for i, row in enumerate(edited_df.itertuples()):
                if getattr(row, "Remove"): # If the remove button was clicked
                    st.session_state.order_items_config.pop(i)
                    st.success("Product/Family removed from current order configuration.")
                    st.experimental_rerun()

            total_order_amount_display = sum(item['quantity'] * item['unit_price'] for item in st.session_state.order_items_config)
            st.markdown(f"#### **Total Order Value: ₹{total_order_amount_display:.2f}**")

            if st.button("Clear All Order Items", key="clear_all_order_items_btn"):
                st.session_state.order_items_config = []
                st.experimental_rerun()
        else:
            st.info("No products/families added to this order yet.")

        st.markdown("---")

        # --- 4. Finalize Order ---
        st.subheader("4. Finalize Order")
        order_delivery_date = st.date_input("Expected Delivery Date", datetime.date.today() + datetime.timedelta(days=30), key="final_delivery_date")
        special_notes = st.text_area("Special Notes for Order", key="final_special_notes")

        if st.button("Create Order", key="finalize_order_btn", type="primary"):
            if not st.session_state.current_customer_id:
                st.error("Please select or add a customer first.")
            elif not st.session_state.order_items_config:
                st.error("Please add at least one product/family to the order.")
            else:
                try:
                    # Get the next order number (simple auto-increment logic)
                    last_order = db.query(Order).order_by(desc(Order.order_number)).first()
                    new_order_number = (last_order.order_number + 1) if last_order else 1

                    total_order_amount = sum(item['quantity'] * item['unit_price'] for item in st.session_state.order_items_config)

                    new_order = Order(
                        customer_id=st.session_state.current_customer_id,
                        order_number=new_order_number,
                        delivery_date=order_delivery_date,
                        total_amount=total_order_amount,
                        status="Draft", # Initial status
                        special_notes=special_notes,
                        created_by_user_id=st.session_state.user_id # Set to logged-in user ID
                    )
                    db.add(new_order)
                    db.flush() # Flush to get new_order.id before committing

                    # Add order items and their default accessories
                    for item_data in st.session_state.order_items_config:
                        order_item = OrderItem(
                            order_id=new_order.id,
                            machine_family_id=item_data['id'],
                            item_description=item_data['item_description'],
                            quantity=item_data['quantity'],
                            unit_price=item_data['unit_price'],
                            total_price=item_data['quantity'] * item_data['unit_price']
                        )
                        db.add(order_item)
                        db.flush() # Flush to get order_item.id if you need it for accessories

                        # Auto-add default accessories for the machine family
                        family_with_defaults = db.query(MachineFamily).options(
                            selectinload(MachineFamily.default_accessories).selectinload(FamilyAccessory.accessory)
                        ).get(item_data['id'])

                        if family_with_defaults:
                            for fa in family_with_defaults.default_accessories:
                                order_item_acc = OrderItemAccessory(
                                    order_item_id=order_item.id,
                                    accessory_id=fa.accessory.id,
                                    quantity=fa.default_quantity * item_data['quantity'], # Qty based on product qty
                                    unit_price=float(fa.accessory.price_per_unit) if fa.accessory.price_per_unit is not None else 0.0,
                                    is_required_for_dispatch=fa.is_required_for_dispatch,
                                    notes=fa.variable_placeholder if fa.is_variable else None # Store placeholder as initial note
                                )
                                db.add(order_item_acc)

                    # Add initial order status history
                    order_status_history = OrderStatusHistory(
                        order_id=new_order.id,
                        status="Draft",
                        user_id=st.session_state.user_id, # Use logged-in user ID
                        notes="Order created"
                    )
                    db.add(order_status_history)

                    db.commit()
                    st.success(f"Order **{new_order.generate_full_order_id()}** created successfully!")
                    st.balloons()
                    # Clear session state for new order
                    st.session_state.order_items_config = []
                    st.session_state.current_customer_id = None
                    # Clear caches that might be affected
                    get_dashboard_metrics_cached.clear()
                    get_recent_activity_cached.clear()
                    # Redirect to View All Orders page
                    st.session_state.current_page = "View All Orders"
                    st.experimental_rerun()
                except Exception as e:
                    db.rollback() # Rollback on error
                    st.error(f"Error creating order: {e}")
                    st.exception(e) # Display full traceback for debugging
    finally:
        db.close()


def show_view_orders_page():
    if not st.session_state.logged_in:
        st.warning("Please log in to view orders.")
        return

    st.title("📋 View All Orders")
    st.markdown("---")
    db = next(get_db())

    # --- Filters ---
    st.sidebar.header("Order Filters")
    all_customers = get_all_customers_cached()
    customer_filter_options = ["All"] + sorted([c.name for c in all_customers])
    selected_customer_filter = st.sidebar.selectbox("Filter by Customer", customer_filter_options, key="view_order_cust_filter")

    all_order_statuses = ["All", "Draft", "Pending Approval", "Approved", "In Production", "Ready for Dispatch", "Dispatched", "Completed", "Cancelled"]
    selected_status_filter = st.sidebar.selectbox("Filter by Overall Status", all_order_statuses, key="view_order_status_filter")

    min_date = st.sidebar.date_input("Order Date From", value=datetime.date.today() - datetime.timedelta(days=365), key="view_order_date_from")
    max_date = st.sidebar.date_input("Order Date To", value=datetime.date.today() + datetime.timedelta(days=30), key="view_order_date_to")

    # --- Query Orders ---
    query = db.query(Order).options(selectinload(Order.customer), selectinload(Order.created_by_user)).order_by(desc(Order.order_date))

    if selected_customer_filter != "All":
        customer_id = next((c.id for c in all_customers if c.name == selected_customer_filter), None)
        if customer_id:
            query = query.filter(Order.customer_id == customer_id)
    if selected_status_filter != "All":
        query = query.filter(Order.status == selected_status_filter)
    
    query = query.filter(Order.order_date >= min_date)
    query = query.filter(Order.order_date <= max_date + datetime.timedelta(days=1)) # To include max_date end of day

    orders = query.all()

    # --- Display Orders Summary ---
    st.subheader("Orders List")
    if orders:
        order_data = []
        for order in orders:
            # Calculate delay
            today = datetime.date.today()
            expected_date = order.delivery_date.date() if order.delivery_date else today
            delay_days = (today - expected_date).days if today > expected_date else 0
            delay_color = "green"
            delay_str = "On Track"
            if today > expected_date and order.status not in ["Dispatched", "Completed", "Cancelled"]:
                delay_str = f"{delay_days} days delayed"
                delay_color = "red" if delay_days > 7 else "orange" # Example thresholds for color
            elif order.status in ["Dispatched", "Completed", "Cancelled"]:
                delay_str = "N/A" # Not applicable if already completed/dispatched/cancelled
                delay_color = "gray"


            order_data.append({
                "Order ID": order.generate_full_order_id(),
                "Customer": order.customer.name,
                "Order Date": order.order_date.strftime("%Y-%m-%d"),
                "Expected Delivery": order.delivery_date.strftime("%Y-%m-%d") if order.delivery_date else "N/A",
                "Total Amount": f"₹{order.total_amount:.2f}",
                "Status": order.status,
                "Delay": f":{delay_color}[{delay_str}]",
                "Created By": order.created_by_user.username if order.created_by_user else "N/A",
                "Order Object ID": order.id # Hidden column to retrieve object for detail view
            })
        
        # Use st.data_editor for better interaction with a "View Details" button-like column
        # Ensure 'Order Object ID' is hidden
        edited_df = st.data_editor(
            pd.DataFrame(order_data),
            column_config={
                "Order Object ID": st.column_config.Column(
                    "Order Object ID",
                    help="Internal ID of the order object",
                    disabled=True,
                    width="hidden"
                ),
                "View Details": st.column_config.ButtonColumn(
                    "View Details",
                    help="Click to view order details",
                    width="small"
                )
            },
            hide_index=True,
            use_container_width=True,
            key="orders_list_data_editor"
        )

        selected_order_id_from_editor = None
        for i, row in enumerate(edited_df.itertuples()):
            if getattr(row, "View Details"):
                selected_order_id_from_editor = order_data[i]["Order Object ID"]
                break

        st.markdown("---")
        # --- Order Detail View ---
        st.subheader("Order Details")
        
        # Use a selectbox for explicit selection, or auto-select if clicked from data_editor
        order_id_display_options = ["-- Select Order ID --"] + [order.generate_full_order_id() for order in orders]
        order_id_map = {order.generate_full_order_id(): order.id for order in orders}

        # Determine initial selection for the selectbox
        initial_select_idx = 0
        if selected_order_id_from_editor:
            selected_order_obj_for_display = db.query(Order).get(selected_order_id_from_editor)
            if selected_order_obj_for_display:
                try:
                    initial_select_idx = order_id_display_options.index(selected_order_obj_for_display.generate_full_order_id())
                except ValueError:
                    initial_select_idx = 0 # Fallback

        selected_order_display_id = st.selectbox(
            "Select Order ID to View Details",
            order_id_display_options,
            index=initial_select_idx,
            key="selected_order_id_detail_view"
        )

        if selected_order_display_id != "-- Select Order ID --":
            selected_order_id = order_id_map[selected_order_display_id]
            selected_order = db.query(Order).options(
                selectinload(Order.customer),
                selectinload(Order.created_by_user),
                selectinload(Order.items).selectinload(OrderItem.machine_family),
                selectinload(Order.items).selectinload(OrderItem.accessories).selectinload(OrderItemAccessory.accessory)
            ).get(selected_order_id)

            if selected_order:
                st.markdown(f"### Order {selected_order.generate_full_order_id()} Details")
                st.write(f"**Customer:** {selected_order.customer.name} (Contact: {selected_order.customer.contact_person or 'N/A'}, Phone: {selected_order.customer.phone or 'N/A'})")
                st.write(f"**Order Date:** {selected_order.order_date.strftime('%Y-%m-%d')}")
                st.write(f"**Expected Delivery Date:** {selected_order.delivery_date.strftime('%Y-%m-%d') if selected_order.delivery_date else 'N/A'}")
                st.write(f"**Total Amount:** ₹{selected_order.total_amount:.2f}")
                st.write(f"**Overall Status:** **{selected_order.status}**")
                st.write(f"**Special Notes:** {selected_order.special_notes or 'N/A'}")
                st.write(f"**Created By:** {selected_order.created_by_user.username if selected_order.created_by_user else 'System'}")

                st.markdown("#### Update Overall Order Status")
                selectable_order_statuses = [s for s in all_order_statuses if s != "All"]
                try:
                    current_selectable_idx = selectable_order_statuses.index(selected_order.status)
                except ValueError:
                    current_selectable_idx = 0

                new_overall_status = st.selectbox(
                    "Select New Overall Status",
                    selectable_order_statuses,
                    index=current_selectable_idx,
                    key=f"overall_status_select_{selected_order.id}",
                    disabled=(st.session_state.role not in ["admin", "sales"]) # Only sales/admin can change overall status
                )
                if st.button(f"Update Order {selected_order.generate_full_order_id()} Status", key=f"update_order_status_btn_{selected_order.id}",
                             disabled=(st.session_state.role not in ["admin", "sales"])):
                    # Check for document completion before dispatch if "Documents" family exists
                    documents_family = db.query(MachineFamily).filter_by(name="Documents Bundle").first() # Use "Documents Bundle"
                    
                    can_update = True
                    if new_overall_status in ["Ready for Dispatch", "Dispatched"] and documents_family:
                        # Find if this order has any items that are part of the "Documents Bundle" family
                        document_order_items = db.query(OrderItem).filter_by(
                            order_id=selected_order.id,
                            machine_family_id=documents_family.id
                        ).all()

                        if document_order_items:
                            all_docs_completed = True
                            for doc_order_item in document_order_items:
                                for oia in doc_order_item.accessories:
                                    if oia.is_required_for_dispatch and oia.notes != "Attached":
                                        all_docs_completed = False
                                        st.error(f"Cannot update to '{new_overall_status}'. Required document '{oia.accessory.name}' is not marked as 'Attached' (Variable Value: '{oia.notes or 'Empty'}').")
                                        break
                                if not all_docs_completed:
                                    break
                            if not all_docs_completed:
                                can_update = False
                        else:
                            st.warning("No 'Documents Bundle' products/families found in this order. Proceeding with status update without document check.")
                    
                    if can_update:
                        update_overall_order_status(db, selected_order.id, new_overall_status, user_id=st.session_state.user_id)
                        st.experimental_rerun()


                st.markdown("#### Order Items & Production Progress")
                for order_item in selected_order.items:
                    st.markdown(f"##### **{order_item.machine_family.name}** (Qty: {order_item.quantity})")
                    st.write(f"Item Description: {order_item.item_description or 'N/A'}")
                    st.write(f"Unit Price: ₹{order_item.unit_price:.2f}, Total Item Price: ₹{order_item.total_price:.2f}")

                    # Get the latest production status for this item
                    latest_prod_status = db.query(ProductionStatusHistory).options(selectinload(ProductionStatusHistory.process_step)).filter_by(
                        order_item_id=order_item.id
                    ).order_by(desc(ProductionStatusHistory.timestamp)).first()
                    
                    current_prod_status_name = latest_prod_status.process_step.step_name if latest_prod_status else "Not Started"
                    st.write(f"Current Production Status: **{current_prod_status_name}**")

                    # Update Production Status for this OrderItem
                    production_steps = get_all_production_steps_cached()
                    production_steps_names = ["-- Select Step --"] + [s.step_name for s in production_steps]
                    
                    current_prod_status_idx = production_steps_names.index(current_prod_status_name) if current_prod_status_name in production_steps_names else 0
                    
                    new_prod_status_name = st.selectbox(
                        f"Update Production Status for {order_item.machine_family.name} (ID: {order_item.id})",
                        production_steps_names,
                        index=current_prod_status_idx,
                        key=f"prod_status_select_{order_item.id}",
                        disabled=(st.session_state.role not in ["admin", "production"])
                    )
                    if new_prod_status_name != "-- Select Step --":
                        if st.button(f"Update Production Status to '{new_prod_status_name}'", key=f"update_prod_status_btn_{order_item.id}",
                                     disabled=(st.session_state.role not in ["admin", "production"])):
                            update_order_item_production_status(db, order_item.id, new_prod_status_name, user_id=st.session_state.user_id)
                            st.experimental_rerun()

                    # Accessories for this OrderItem
                    st.markdown("###### Required Accessories:")
                    acc_details_data = []
                    for oia in order_item.accessories:
                        current_stock = oia.accessory.current_stock_level
                        required_qty = oia.quantity
                        stock_status = ""
                        if current_stock >= required_qty:
                            stock_status = f":green[Available ({current_stock}/{required_qty})]"
                        elif current_stock > 0:
                            stock_status = f":orange[Partially Available ({current_stock}/{required_qty})]"
                        else:
                            stock_status = f":red[Out of Stock ({current_stock}/{required_qty})]"

                        acc_details_data.append({
                            "Accessory Name": oia.accessory.name,
                            "Accessory ID": oia.accessory.accessory_id,
                            "Category": oia.accessory.category_tag,
                            "Required Qty": oia.quantity,
                            "Unit Price": f"₹{oia.unit_price:.2f}",
                            "Variable Value/Notes": oia.notes if oia.notes else "",
                            "Stock Status": stock_status,
                            "Required for Dispatch": "Yes" if oia.is_required_for_dispatch else "No",
                            "Update": f"Update_{oia.id}" # For update button
                        })
                    
                    edited_acc_df = st.data_editor(
                        pd.DataFrame(acc_details_data),
                        column_config={
                            "Update": st.column_config.ButtonColumn(
                                "Update Status/Value",
                                help="Click to update this accessory's status/value",
                                width="small",
                                disabled=(st.session_state.role not in ["admin", "production"]) # Only production/admin can update accessory notes
                            )
                        },
                        hide_index=True,
                        use_container_width=True,
                        key=f"order_item_acc_editor_{order_item.id}"
                    )

                    # Handle updates from data_editor for accessories
                    # This needs to be done carefully as data_editor can trigger reruns
                    # and the form will be re-rendered.
                    # We will use a separate form for the actual update.
                    for i, row in enumerate(edited_acc_df.itertuples()):
                        if getattr(row, "Update"):
                            oia_id_to_update = int(str(acc_details_data[i]["Update"]).split("_")[1]) # Extract ID
                            st.session_state.oia_to_edit_id = oia_id_to_update
                            st.experimental_rerun() # Rerun to show the update form

                if 'oia_to_edit_id' in st.session_state and st.session_state.oia_to_edit_id is not None:
                    oia_to_update = db.query(OrderItemAccessory).get(st.session_state.oia_to_edit_id)
                    if oia_to_update:
                        st.markdown(f"**Update {oia_to_update.accessory.name}**")
                        with st.form(f"update_oia_form_{oia_to_update.id}"):
                            new_oia_notes = st.text_input(
                                "Variable Value/Notes",
                                value=oia_to_update.notes or "",
                                key=f"oia_notes_input_{oia_to_update.id}"
                            )
                            submit_oia_update = st.form_submit_button("Save Accessory Update",
                                                                       disabled=(st.session_state.role not in ["admin", "production"]))
                            if submit_oia_update:
                                oia_to_update.notes = new_oia_notes
                                db.commit()
                                st.toast(f"Accessory '{oia_to_update.accessory.name}' notes updated.")
                                del st.session_state.oia_to_edit_id # Clear the ID after update
                                st.experimental_rerun()
                            if st.form_submit_button("Cancel", key=f"cancel_oia_update_{oia_to_update.id}"):
                                del st.session_state.oia_to_edit_id
                                st.experimental_rerun()
                    else:
                        del st.session_state.oia_to_edit_id # Clear if ID is invalid
                        st.experimental_rerun()


                st.markdown("---") # Separator between order items

                st.markdown("#### Order Status History")
                status_history = db.query(OrderStatusHistory).options(selectinload(OrderStatusHistory.user)).filter_by(order_id=selected_order.id).order_by(OrderStatusHistory.timestamp.asc()).all()
                if status_history:
                    history_df = pd.DataFrame([
                        {"Timestamp": hs.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                         "Status": hs.status,
                         "Notes": hs.notes or "N/A",
                         "User": hs.user.username if hs.user else "System"}
                        for hs in status_history
                    ])
                    st.dataframe(history_df, use_container_width=True, hide_index=True)
                else:
                    st.info("No status history for this order.")

                st.markdown("#### Production Status History (Per Item)")
                for order_item in selected_order.items:
                    prod_history = db.query(ProductionStatusHistory).options(
                        selectinload(ProductionStatusHistory.process_step),
                        selectinload(ProductionStatusHistory.user)
                    ).filter_by(order_item_id=order_item.id).order_by(ProductionStatusHistory.timestamp.asc()).all()
                    if prod_history:
                        st.markdown(f"**History for {order_item.machine_family.name} (Item ID: {order_item.id}):**")
                        prod_history_df = pd.DataFrame([
                            {"Timestamp": ph.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                             "Step": ph.process_step.step_name,
                             "Status": ph.status,
                             "Notes": ph.notes or "N/A",
                             "User": ph.user.username if ph.user else "System"}
                            for ph in prod_history
                        ])
                        st.dataframe(prod_history_df, use_container_width=True, hide_index=True)
                    else:
                        st.info(f"No production status history for {order_item.machine_family.name}.")
            else:
                st.error("Order not found.")
    else:
        st.info("No orders found based on current filters.")
    db.close()


def show_inventory_page():
    if not st.session_state.logged_in:
        st.warning("Please log in to view inventory.")
        return

    st.title("📦 Inventory Management")
    st.markdown("---")
    db = next(get_db())

    # --- Filters ---
    st.sidebar.header("Inventory Filters")
    # Dynamically get distinct categories from accessories
    all_accessories_for_filter = get_all_accessories_cached()
    category_tags = ["All"] + sorted(list(set(a.category_tag for a in all_accessories_for_filter if a.category_tag)))
    selected_tag_filter = st.sidebar.selectbox("Filter by Category/Tag", category_tags, key="inv_tag_filter")
    show_low_stock_only = st.sidebar.checkbox("Show Low Stock Only", value=False, key="inv_low_stock_filter")
    search_query = st.sidebar.text_input("Search by Name/ID", key="inv_search")

    # --- Query Accessories ---
    query = db.query(Accessory).order_by(Accessory.name)

    if selected_tag_filter != "All":
        query = query.filter(Accessory.category_tag == selected_tag_filter)
    if show_low_stock_only:
        query = query.filter(Accessory.current_stock_level < Accessory.min_stock_level)
    if search_query:
        query = query.filter(
            (Accessory.name.ilike(f"%{search_query}%")) |
            (Accessory.accessory_id.ilike(f"%{search_query}%"))
        )

    accessories = query.all()

    # --- Display Accessory Catalog ---
    st.subheader("Accessory Catalog & Current Stock")
    if accessories:
        acc_data_display = []
        for acc in accessories:
            stock_status_color = "green"
            stock_level_display = str(acc.current_stock_level)
            if acc.current_stock_level <= acc.min_stock_level:
                stock_status_color = "red" if acc.current_stock_level == 0 else "orange"
                stock_level_display = f"**{acc.current_stock_level}**" # Highlight low stock

            acc_data_display.append({
                "Accessory Name": acc.name,
                "Accessory ID": acc.accessory_id,
                "Category": acc.category_tag,
                "Unit": acc.unit_of_measure,
                "Min Stock": acc.min_stock_level,
                "Current Stock": f":{stock_status_color}[{stock_level_display}]",
                "Description": acc.description,
                "Price": f"₹{acc.price_per_unit:.2f}"
            })
        st.dataframe(pd.DataFrame(acc_data_display), use_container_width=True, hide_index=True)
    else:
        st.info("No accessories found matching the filters. Add some in Master Data.")

    st.markdown("---")
    # --- Stock Adjustment Forms ---
    st.subheader("Inventory Movements")

    acc_options = {f"{a.name} (ID: {a.accessory_id})": a for a in get_all_accessories_cached()}
    acc_names_list = list(acc_options.keys())

    selected_acc_for_movement_name = st.selectbox(
        "Select Accessory for Stock Movement",
        ["-- Select --"] + acc_names_list,
        key="inv_acc_select",
        disabled=(st.session_state.role not in ["admin", "production"])
    )

    if selected_acc_for_movement_name != "-- Select --":
        selected_acc_for_movement = acc_options[selected_acc_for_movement_name]
        st.write(f"**Current Stock for {selected_acc_for_movement.name}:** {selected_acc_for_movement.current_stock_level} {selected_acc_for_movement.unit_of_measure}")

        col_in, col_out, col_adjust = st.columns(3)

        with col_in:
            st.markdown("##### Stock In (Receipt)")
            with st.form("stock_in_form", clear_on_submit=True):
                qty_in = st.number_input("Quantity to Add", min_value=1, value=1, key="qty_in_form")
                reason_in = st.text_input("Reason (e.g., Supplier delivery, Production return)", key="reason_in_form")
                record_in_btn = st.form_submit_button("Record Stock In", disabled=(st.session_state.role not in ["admin", "production"]))
                if record_in_btn:
                    if qty_in > 0:
                        selected_acc_for_movement.current_stock_level += qty_in
                        db.add(StockHistory(
                            accessory_id=selected_acc_for_movement.id,
                            change_type="IN",
                            quantity_change=qty_in,
                            new_stock_level=selected_acc_for_movement.current_stock_level,
                            reason=reason_in,
                            user_id=st.session_state.user_id # Current user ID
                        ))
                        db.commit()
                        st.success(f"{qty_in} units of {selected_acc_for_movement.name} added to stock.")
                        get_all_accessories_cached.clear() # Clear cache
                        st.experimental_rerun()
                    else:
                        st.warning("Quantity to add must be greater than 0.")

        with col_out:
            st.markdown("##### Stock Out (Issuance)")
            with st.form("stock_out_form", clear_on_submit=True):
                qty_out = st.number_input("Quantity to Issue", min_value=1, value=1, key="qty_out_form")
                reason_out = st.text_input("Reason (e.g., For Order #, Assembly Line)", key="reason_out_form")
                order_id_out_str = st.text_input("Associated Order ID (e.g., EQV-ORD-0001) (Optional)", key="order_id_out_form")
                
                record_out_btn = st.form_submit_button("Record Stock Out", disabled=(st.session_state.role not in ["admin", "production"]))
                
                if record_out_btn:
                    if qty_out <= 0:
                        st.warning("Quantity to issue must be greater than 0.")
                    elif selected_acc_for_movement.current_stock_level < qty_out:
                        st.error("Not enough stock available!")
                    else:
                        associated_order_id = None
                        if order_id_out_str:
                            # Try to parse order_id_out_str into an actual Order ID
                            parts = order_id_out_str.split('-')
                            if len(parts) == 3 and parts[0] == "EQV" and parts[1] == "ORD" and parts[2].isdigit():
                                order_num = int(parts[2])
                                order_obj = db.query(Order).filter_by(order_number=order_num, order_id_prefix="EQV-ORD").first()
                                if order_obj:
                                    associated_order_id = order_obj.id
                                else:
                                    st.warning(f"Order ID '{order_id_out_str}' not found. Stock will be issued without order linkage.")
                            else:
                                st.warning(f"Invalid Order ID format. Stock will be issued without order linkage. Expected format: EQV-ORD-0001")

                        selected_acc_for_movement.current_stock_level -= qty_out
                        db.add(StockHistory(
                            accessory_id=selected_acc_for_movement.id,
                            change_type="OUT",
                            quantity_change=-qty_out,
                            new_stock_level=selected_acc_for_movement.current_stock_level,
                            reason=reason_out,
                            order_id=associated_order_id,
                            user_id=st.session_state.user_id # Current user ID
                        ))
                        db.commit()
                        st.success(f"{qty_out} units of {selected_acc_for_movement.name} issued from stock.")
                        get_all_accessories_cached.clear() # Clear cache
                        st.experimental_rerun()

        with col_adjust:
            if st.session_state.role == "admin": # Only Admin can do manual adjustments
                st.markdown("##### Manual Adjustment (Admin Only)")
                with st.form("stock_adjust_form", clear_on_submit=True):
                    adjust_qty = st.number_input("Adjustment Quantity", value=0, help="Positive to add, Negative to remove", key="adjust_qty_form")
                    adjust_reason = st.text_input("Reason for Adjustment *", key="adjust_reason_form")
                    record_adjust_btn = st.form_submit_button("Record Adjustment")
                    if record_adjust_btn:
                        if adjust_reason:
                            selected_acc_for_movement.current_stock_level += adjust_qty
                            db.add(StockHistory(
                                accessory_id=selected_acc_for_movement.id,
                                change_type="ADJUSTMENT",
                                quantity_change=adjust_qty,
                                new_stock_level=selected_acc_for_movement.current_stock_level,
                                reason=f"Manual Adjustment: {adjust_reason}",
                                user_id=st.session_state.user_id # Current user ID
                            ))
                            db.commit()
                            st.success(f"Stock for {selected_acc_for_movement.name} adjusted by {adjust_qty}.")
                            get_all_accessories_cached.clear() # Clear cache
                            st.experimental_rerun()
                        else:
                            st.error("Reason for adjustment is required.")
            else:
                st.info("Manual Adjustment is for Admin only.")

    st.markdown("---")
    st.subheader("Inventory History for Selected Accessory")
    if selected_acc_for_movement_name != "-- Select --":
        selected_acc_for_history = acc_options[selected_acc_for_movement_name]
        history_records = db.query(StockHistory).options(selectinload(StockHistory.user)).filter_by(accessory_id=selected_acc_for_history.id).order_by(desc(StockHistory.timestamp)).all()
        if history_records:
            history_df = pd.DataFrame([
                {"Timestamp": h.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                 "Type": h.change_type,
                 "Quantity Change": h.quantity_change,
                 "New Stock Level": h.new_stock_level,
                 "Reason": h.reason or "N/A",
                 "Order ID": h.order.generate_full_order_id() if h.order else "N/A", # Display full order ID
                 "User": h.user.username if h.user else "System"}
                for h in history_records
            ])
            st.dataframe(history_df, use_container_width=True, hide_index=True)
        else:
            st.info("No stock history for this accessory.")
    else:
        st.info("Select an accessory above to view its history.")

    db.close()


def show_master_data_page():
    if not st.session_state.logged_in:
        st.warning("Please log in to manage master data.")
        return
    if st.session_state.role != "admin": # Only Admin can access
        st.warning("You do not have permission to access this page.")
        return

    st.title("🗄️ Master Data Management")
    st.markdown("---")
    db = next(get_db())

    # --- Manage Machine Families ---
    st.subheader("Manage Machine Families (Products/Bundles)")
    with st.expander("Add New Machine Family"):
        with st.form("new_machine_family_form"):
            new_mf_name = st.text_input("Machine Family Name *", key="new_mf_name_input")
            new_mf_description = st.text_area("Description", key="new_mf_desc_input")

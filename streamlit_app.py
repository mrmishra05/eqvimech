import streamlit as st
from database import create_tables, get_db, initialize_master_data
from models import Customer, Order, MachineFamily, Accessory, FamilyAccessory, OrderItem, OrderItemAccessory, User, ProductionProcessStep, OrderStatusHistory, StockHistory, ProductionStatusHistory
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import func
import datetime
import bcrypt
import pandas as pd

# --- Page Configuration ---
st.set_page_config(
    page_title="Eqvimech Order Tracker",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Global App State Management (for user login, current page) ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""
if "role" not in st.session_state:
    st.session_state.role = ""
if "current_page" not in st.session_state:
    st.session_state.current_page = "Dashboard"

# --- Database Initialization (Run once on app startup) ---
# This ensures tables are created and master data is initialized when the app first runs.
if 'db_initialized' not in st.session_state:
    try:
        with Session(get_db()) as db:
            # Check if any table exists (e.g., users table)
            # This is a simple heuristic to see if tables are already created
            if not db.bind.dialect.has_table(db.bind, "users"):
                create_tables()
                initialize_master_data(db)
                st.toast("Database tables created and master data initialized.")
            st.session_state.db_initialized = True
    except Exception as e:
        st.error(f"Error during initial database setup: {e}")
        st.stop()


# --- Utility Functions ---
def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def check_password(password, hashed_password):
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))

def add_user(db: Session, username, password, full_name, email, role):
    if db.query(User).filter(User.username == username).first():
        return False, "Username already exists."
    hashed_pwd = hash_password(password)
    new_user = User(username=username, password_hash=hashed_pwd, full_name=full_name, email=email, role=role)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return True, "User created successfully."

def verify_login(db: Session, username, password):
    user = db.query(User).filter(User.username == username).first()
    if user and check_password(password, user.password_hash):
        return user
    return None

def remove_order_item_config(index):
    """Callback to remove an item from current_order_items."""
    if 0 <= index < len(st.session_state.current_order_items):
        st.session_state.current_order_items.pop(index)
        st.success("Product/Family removed from current order configuration.")

# Function to get production steps for dynamic dropdowns
def get_production_steps(db_session):
    return db_session.query(ProductionProcessStep).order_by(ProductionProcessStep.sequence_order).all()

# Function to update overall order status
def update_overall_order_status(db_session, order_id, new_status):
    order = db_session.query(Order).get(order_id)
    if order and order.overall_status != new_status:
        old_status = order.overall_status
        order.overall_status = new_status
        db_session.add(OrderStatusHistory(
            order_id=order_id,
            status_from=old_status,
            status_to=new_status,
            notes=f"Status updated to '{new_status}' by {st.session_state.username}"
        ))
        db_session.commit()
        st.toast(f"Order #{order_id} status updated to '{new_status}'")
    else:
        st.warning("Status is already the same or order not found.")

# Function to update order item production status
def update_order_item_production_status(db_session, order_item_id, new_status):
    order_item = db_session.query(OrderItem).get(order_item_id)
    if order_item and order_item.current_production_status != new_status:
        old_status = order_item.current_production_status
        order_item.current_production_status = new_status
        db_session.add(ProductionStatusHistory(
            order_item_id=order_item_id,
            status_from=old_status,
            status_to=new_status,
            notes=f"Production status updated to '{new_status}' by {st.session_state.username}"
        ))
        db_session.commit()
        st.toast(f"Item #{order_item_id} production status updated to '{new_status}'")
    else:
        st.warning("Production status is already the same or item not found.")


# --- UI Components ---
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
                st.session_state.current_page = "Dashboard" # Redirect to dashboard after login
                st.success(f"Welcome, {user.full_name or user.username}!")
                st.rerun()
            else:
                st.error("Invalid username or password.")
            db.close()
    st.markdown("---")
    st.subheader("Admin Setup (Run this ONCE to create initial admin user)")
    with st.expander("Create Initial Admin User"):
        with st.form("create_admin_form"):
            admin_username = st.text_input("Admin Username")
            admin_password = st.text_input("Admin Password", type="password")
            admin_full_name = st.text_input("Admin Full Name (e.g., Production Manager)")
            admin_email = st.text_input("Admin Email")
            create_admin_button = st.form_submit_button("Create Admin User")
            if create_admin_button:
                db = next(get_db())
                # Ensure tables are created and master data is initialized before creating user
                # This is now handled by the app-wide initialization block, but keep here for explicit clarity
                success, message = add_user(db, admin_username, admin_password, admin_full_name, admin_email, "Admin")
                if success:
                    st.success(message)
                else:
                    st.error(message)
                db.close()


def show_dashboard():
    st.title(f"Dashboard - Welcome, {st.session_state.username} ({st.session_state.role})")
    st.write("Overview of your orders, production progress, and inventory.")

    db = next(get_db()) # Get DB session

    st.subheader("Active Orders")
    orders = db.query(Order).options(selectinload(Order.customer)).order_by(Order.order_date.desc()).all()
    if orders:
        order_data = []
        for order in orders:
            # Calculate delay
            today = datetime.date.today()
            expected_date = order.expected_delivery_date.date() if order.expected_delivery_date else today
            delay_days = (today - expected_date).days if today > expected_date else 0
            delay_color = "green"
            delay_str = "On Track"
            if delay_days > 0:
                delay_str = f"-{delay_days} days"
                delay_color = "red" if delay_days > 3 else "orange" # Example thresholds for color

            order_data.append({
                "Order ID": order.id,
                "Customer": order.customer.name,
                "Company": order.customer.company,
                "Order Date": order.order_date.strftime("%Y-%m-%d"),
                "Expected Delivery": order.expected_delivery_date.strftime("%Y-%m-%d") if order.expected_delivery_date else "N/A",
                "Status": order.overall_status,
                "Delay": f":{delay_color}[{delay_str}]"
            })
        st.dataframe(pd.DataFrame(order_data), use_container_width=True, hide_index=True)
    else:
        st.info("No active orders found. Create a new order to get started!")

    st.subheader("Low Stock Alerts")
    low_stock_accessories = db.query(Accessory).filter(Accessory.current_stock_level < Accessory.min_stock_level).all()
    if low_stock_accessories:
        stock_data = []
        for acc in low_stock_accessories:
            stock_data.append({
                "Accessory ID": acc.accessory_id,
                "Name": acc.name,
                "Tag": acc.category_tag,
                "Current Stock": acc.current_stock_level,
                "Min Stock": acc.min_stock_level
            })
        st.warning("The following accessories are running low on stock:")
        st.dataframe(pd.DataFrame(stock_data), use_container_width=True, hide_index=True)
    else:
        st.success("All accessories are currently above minimum stock levels!")
    db.close()


def show_create_order_page():
    st.title("Create New Order")
    db = next(get_db()) # Get DB session

    # --- Customer Selection/Creation ---
    st.subheader("1. Customer Information")
    customers = db.query(Customer).order_by(Customer.name).all()
    customer_options = {f"{c.name} ({c.company or 'N/A'})": c.id for c in customers}
    customer_names = list(customer_options.keys())

    customer_selection_method = st.radio("Select existing customer or create new?", ["Select Existing", "Create New"], horizontal=True, key="customer_method_radio")

    selected_customer_id = None
    if customer_selection_method == "Select Existing":
        if customer_names:
            selected_customer_name = st.selectbox("Select Customer", customer_names, key="select_customer")
            selected_customer_id = customer_options[selected_customer_name]
        else:
            st.warning("No customers found. Please create a new customer.")
            # Set to create new if no customers exist, for better UX
            st.session_state.customer_method_radio_index = 1 # Force radio button
            st.rerun()

    if customer_selection_method == "Create New":
        st.write("---")
        st.markdown("##### New Customer Details")
        new_customer_name = st.text_input("Customer Name *", key="new_cust_name")
        new_customer_company = st.text_input("Company Name", key="new_cust_company")
        new_contact_person = st.text_input("Contact Person", key="new_cust_person")
        new_contact_number = st.text_input("Contact Number", key="new_cust_number")
        new_email = st.text_input("Email", key="new_cust_email")
        new_billing_address = st.text_area("Billing Address", key="new_cust_billing")
        new_shipping_address = st.text_area("Shipping Address (leave blank if same as billing)", key="new_cust_shipping")

        if st.button("Add New Customer", key="add_new_customer_btn"):
            if not new_customer_name:
                st.error("Customer Name is required.")
            else:
                existing_customer = db.query(Customer).filter(func.lower(Customer.name) == func.lower(new_customer_name)).first()
                if existing_customer:
                    st.warning(f"Customer '{new_customer_name}' already exists. Please select them or use a different name.")
                else:
                    customer = Customer(
                        name=new_customer_name,
                        company=new_customer_company,
                        contact_person=new_contact_person,
                        contact_number=new_contact_number,
                        email=new_email,
                        billing_address=new_billing_address,
                        shipping_address=new_shipping_address if new_shipping_address else new_billing_address
                    )
                    db.add(customer)
                    db.commit()
                    db.refresh(customer)
                    selected_customer_id = customer.id
                    st.success(f"Customer '{new_customer_name}' added successfully!")
                    st.session_state.create_order_customer_id = selected_customer_id # Store for later steps
                    st.rerun() # Rerun to refresh customer list

    # Store selected customer for subsequent steps if it was selected/created
    if selected_customer_id:
        st.session_state.create_order_customer_id = selected_customer_id
        current_customer = db.query(Customer).get(selected_customer_id)
        st.info(f"Selected Customer: **{current_customer.name}** ({current_customer.company or 'N/A'})")
    else:
        st.warning("Please select or create a customer to proceed with order details.")
        db.close()
        return # Stop execution if no customer is selected/created yet


    # --- Order Details (if customer is selected) ---
    st.subheader("2. Order Details")
    expected_delivery_date = st.date_input("Expected Delivery Date *", value=datetime.date.today() + datetime.timedelta(days=30), key="order_delivery_date")
    order_notes = st.text_area("Order Notes", key="order_notes")

    # Initialize order_items in session state if not present
    if "current_order_items" not in st.session_state:
        st.session_state.current_order_items = [] # Stores dicts like {'family_id': X, 'qty': Y, 'accessories': [...]}

    # --- Add Machine Families / Products ---
    st.subheader("3. Add Products/Machine Families")
    machine_families = db.query(MachineFamily).order_by(MachineFamily.name).all()
    family_options = {f"{mf.name}": mf.id for mf in machine_families}
    family_names = list(family_options.keys())

    col1, col2 = st.columns([0.7, 0.3])
    with col1:
        selected_family_name_to_add = st.selectbox("Select Product/Family to Add", ["-- Select --"] + family_names, key="add_family_select")
    with col2:
        family_qty_to_add = st.number_input("Quantity", min_value=1, value=1, key="add_family_qty")

    if st.button("Add Product/Family to Order", key="add_product_family_btn"):
        if selected_family_name_to_add != "-- Select --":
            family_id = family_options[selected_family_name_to_add]
            # Check if this family is already added
            existing_entry = next((item for item in st.session_state.current_order_items if item['family_id'] == family_id), None)
            if existing_entry:
                existing_entry['qty'] += family_qty_to_add
                st.success(f"Quantity for '{selected_family_name_to_add}' updated to {existing_entry['qty']}!")
            else:
                # Load default accessories for the selected family
                family_with_accessories = db.query(MachineFamily).options(selectinload(MachineFamily.default_accessories).selectinload(FamilyAccessory.accessory)).get(family_id)
                accessories_for_order_item = []
                for fa in family_with_accessories.default_accessories:
                    accessories_for_order_item.append({
                        'accessory_id': fa.accessory.id,
                        'name': fa.accessory.name,
                        'tag': fa.accessory.category_tag,
                        'default_quantity': fa.default_quantity, # Default quantity from master data
                        'required_quantity': fa.default_quantity * family_qty_to_add, # Adjusted for order item quantity
                        'is_variable': fa.is_variable,
                        'variable_placeholder': fa.variable_placeholder,
                        'variable_value': None, # To be filled by user if is_variable is True
                        'is_custom': False # This is a default accessory
                    })
                st.session_state.current_order_items.append({
                    'family_id': family_id,
                    'family_name': selected_family_name_to_add,
                    'qty': family_qty_to_add,
                    'accessories': accessories_for_order_item # List of dicts for accessories
                })
                st.success(f"'{selected_family_name_to_add}' added to order with quantity {family_qty_to_add}!")
            st.rerun() # Rerun to update the displayed list of order items
        else:
            st.warning("Please select a product/family to add.")

    # --- Display Current Order Items ---
    st.subheader("4. Current Order Configuration")
    if st.session_state.current_order_items:
        for i, order_item_config in enumerate(st.session_state.current_order_items):
            st.markdown(f"**{i+1}. {order_item_config['family_name']} (Qty: {order_item_config['qty']})**")
            # --- Manage Accessories for each Order Item ---
            with st.expander(f"Manage Accessories for {order_item_config['family_name']}"):
                acc_df_data = []
                for acc_idx, acc_data in enumerate(order_item_config['accessories']):
                    # Get stock level for display
                    current_acc_obj = db.query(Accessory).get(acc_data['accessory_id'])
                    stock_info = f"Stock: {current_acc_obj.current_stock_level}" if current_acc_obj else "N/A"

                    acc_df_data.append({
                        "Accessory": acc_data['name'],
                        "Tag": acc_data['tag'],
                        "Required Quantity": acc_data['required_quantity'],
                        "Variable Detail": acc_data['variable_placeholder'] if acc_data['is_variable'] else "N/A",
                        "Current Value": acc_data['variable_value'] if acc_data['variable_value'] else "PENDING" if acc_data['is_variable'] else "N/A",
                        "Stock Status": stock_info,
                        "Custom": "Yes" if acc_data['is_custom'] else "No"
                    })
                st.dataframe(pd.DataFrame(acc_df_data), use_container_width=True, hide_index=True)

                st.markdown("---")
                st.markdown("##### Edit/Add Accessories for this Item")

                # Combine edit and custom add in columns for better layout
                edit_acc_col, add_custom_acc_col = st.columns(2)

                with edit_acc_col:
                    st.markdown("###### Edit/Remove Existing")
                    acc_to_edit_idx = st.selectbox(
                        f"Select Accessory to Edit/Remove for {order_item_config['family_name']}",
                        ["-- Select --"] + [acc['name'] for acc in order_item_config['accessories']],
                        key=f"edit_acc_select_{i}"
                    )
                    if acc_to_edit_idx != "-- Select --":
                        selected_acc_data = next((acc for acc in order_item_config['accessories'] if acc['name'] == acc_to_edit_idx), None)
                        if selected_acc_data:
                            new_required_qty = st.number_input(
                                f"New Required Quantity for {selected_acc_data['name']}",
                                min_value=0,
                                value=selected_acc_data['required_quantity'],
                                key=f"edit_acc_qty_{i}_{selected_acc_data['accessory_id']}"
                            )
                            new_variable_value = selected_acc_data['variable_value']
                            if selected_acc_data['is_variable']:
                                new_variable_value = st.text_input(
                                    f"Variable Value for {selected_acc_data['name']} ({selected_acc_data['variable_placeholder']})",
                                    value=selected_acc_data['variable_value'] or "",
                                    key=f"edit_acc_var_{i}_{selected_acc_data['accessory_id']}"
                                )

                            if st.button(f"Update '{selected_acc_data['name']}' Qty/Value", key=f"update_acc_btn_{i}_{selected_acc_data['accessory_id']}"):
                                selected_acc_data['required_quantity'] = new_required_qty
                                selected_acc_data['variable_value'] = new_variable_value
                                st.success("Accessory updated in order config!")
                                st.rerun()

                            if st.button(f"Remove '{selected_acc_data['name']}' from this item", key=f"remove_acc_btn_{i}_{selected_acc_data['accessory_id']}"):
                                order_item_config['accessories'].remove(selected_acc_data)
                                st.success("Accessory removed from this order item!")
                                st.rerun()

                with add_custom_acc_col:
                    st.markdown("###### Add Custom Accessory")
                    all_accessories_master = db.query(Accessory).order_by(Accessory.name).all() # Use a different var name
                    all_acc_options_master = {f"{a.name} ({a.category_tag})": a.id for a in all_accessories_master}
                    all_acc_names_master = list(all_acc_options_master.keys())

                    custom_acc_to_add_name = st.selectbox("Select Custom Accessory", ["-- Select --"] + all_acc_names_master, key=f"add_custom_acc_select_{i}")
                    custom_acc_qty = st.number_input("Quantity", min_value=1, value=1, key=f"add_custom_acc_qty_{i}")

                    add_custom_acc_btn = st.button("Add Custom Accessory to Item", key=f"add_custom_acc_btn_{i}")

                    if add_custom_acc_btn:
                        if custom_acc_to_add_name != "-- Select --":
                            custom_acc_id = all_acc_options_master[custom_acc_to_add_name]
                            custom_accessory_obj = db.query(Accessory).get(custom_acc_id)
                            already_added = next((acc for acc in order_item_config['accessories'] if acc['accessory_id'] == custom_acc_id), None)
                            if already_added:
                                already_added['required_quantity'] += custom_acc_qty
                                st.success(f"Quantity for '{custom_accessory_obj.name}' updated!")
                            else:
                                order_item_config['accessories'].append({
                                    'accessory_id': custom_acc_id,
                                    'name': custom_accessory_obj.name,
                                    'tag': custom_accessory_obj.category_tag,
                                    'default_quantity': 0,
                                    'required_quantity': custom_acc_qty,
                                    'is_variable': False,
                                    'variable_placeholder': None,
                                    'variable_value': None,
                                    'is_custom': True
                                })
                                st.success(f"Custom accessory '{custom_accessory_obj.name}' added to item!")
                            st.rerun()
                        else:
                            st.warning("Please select a custom accessory to add.")


            st.markdown("---")
            st.button(f"Remove {order_item_config['family_name']} from Order", key=f"remove_family_btn_{i}", on_click=lambda: remove_order_item_config(i))
            st.markdown("---")
    else:
        st.info("No products/families added to this order yet.")

    # --- Finalize Order Button ---
    st.subheader("5. Finalize Order")
    if st.button("Create Order", key="create_final_order_btn", type="primary"):
        if not st.session_state.current_order_items:
            st.error("Please add at least one product/family to the order.")
        else:
            try:
                # Create the main order
                new_order = Order(
                    customer_id=st.session_state.create_order_customer_id,
                    expected_delivery_date=expected_delivery_date,
                    notes=order_notes,
                    overall_status="New" # Initial status
                )
                db.add(new_order)
                db.flush() # Flush to get new_order.id before committing

                # Add order items and their accessories
                for item_config in st.session_state.current_order_items:
                    order_item = OrderItem(
                        order_id=new_order.id,
                        machine_family_id=item_config['family_id'],
                        quantity_ordered=item_config['qty'],
                        current_production_status="Raw Material Ordered" # Initial production status for order item
                    )
                    db.add(order_item)
                    db.flush() # Flush to get order_item.id

                    for acc_data in item_config['accessories']:
                        order_item_acc = OrderItemAccessory(
                            order_item_id=order_item.id,
                            accessory_id=acc_data['accessory_id'],
                            required_quantity=acc_data['required_quantity'],
                            variable_value=acc_data['variable_value'],
                            is_custom=acc_data['is_custom'],
                            current_status="Pending" # Default status for order item accessory
                        )
                        db.add(order_item_acc)

                # Add initial order status history
                db.add(OrderStatusHistory(order_id=new_order.id, status_to="New", notes="Order created"))
                db.commit()

                st.success(f"Order #{new_order.id} created successfully!")
                st.session_state.current_order_items = [] # Clear form
                st.session_state.create_order_customer_id = None
                st.session_state.current_page = "View All Orders" # Redirect
                st.rerun()

            except Exception as e:
                db.rollback()
                st.error(f"Error creating order: {e}")
            finally:
                db.close()


def show_view_orders_page():
    st.title("View All Orders")
    db = next(get_db())

    # --- Filters ---
    st.sidebar.header("Order Filters")
    all_customers = db.query(Customer).order_by(Customer.name).all()
    customer_filter_options = ["All"] + [c.name for c in all_customers]
    selected_customer_filter = st.sidebar.selectbox("Filter by Customer", customer_filter_options, key="order_cust_filter")

    all_order_statuses = ["All", "New", "Pending Production", "In Production - Assembly", "Ready for Dispatch", "Dispatched"]
    selected_status_filter = st.sidebar.selectbox("Filter by Overall Status", all_order_statuses, key="order_status_filter")

    min_date = st.sidebar.date_input("Order Date From", value=datetime.date.today() - datetime.timedelta(days=365), key="order_date_from")
    max_date = st.sidebar.date_input("Order Date To", value=datetime.date.today() + datetime.timedelta(days=30), key="order_date_to")

    # --- Query Orders ---
    query = db.query(Order).options(selectinload(Order.customer)).order_by(Order.order_date.desc())

    if selected_customer_filter != "All":
        query = query.join(Customer).filter(Customer.name == selected_customer_filter)
    if selected_status_filter != "All":
        query = query.filter(Order.overall_status == selected_status_filter)
    
    query = query.filter(Order.order_date >= min_date)
    query = query.filter(Order.order_date <= max_date + datetime.timedelta(days=1)) # To include max_date

    orders = query.all()

    # --- Display Orders Summary ---
    st.subheader("Orders List")
    if orders:
        order_data = []
        production_steps_names = [s.step_name for s in get_production_steps(db)] # For production status dropdowns

        for order in orders:
            # Calculate delay
            today = datetime.date.today()
            expected_date = order.expected_delivery_date.date()
            delay_days = (today - expected_date).days if today > expected_date else 0
            delay_color = "green"
            delay_str = "On Track"
            if delay_days > 0:
                delay_str = f"-{delay_days} days"
                delay_color = "red" if delay_days > 3 else "orange" # Example thresholds for color

            order_data.append({
                "Order ID": order.id,
                "Customer": order.customer.name,
                "Company": order.customer.company,
                "Order Date": order.order_date.strftime("%Y-%m-%d"),
                "Expected Delivery": order.expected_delivery_date.strftime("%Y-%m-%d"),
                "Overall Status": order.overall_status,
                "Delay": f":{delay_color}[{delay_str}]"
            })
        st.dataframe(pd.DataFrame(order_data), use_container_width=True, hide_index=True)

        st.markdown("---")
        # --- Order Detail View ---
        st.subheader("Order Details")
        order_ids = [order.id for order in orders]
        selected_order_id = st.selectbox("Select Order ID to View Details", ["-- Select --"] + order_ids, key="view_order_select")

        if selected_order_id != "-- Select --":
            selected_order = db.query(Order).options(
                selectinload(Order.customer),
                selectinload(Order.order_items).selectinload(OrderItem.machine_family),
                selectinload(Order.order_items).selectinload(OrderItem.order_item_accessories).selectinload(OrderItemAccessory.accessory)
            ).get(selected_order_id)

            if selected_order:
                st.markdown(f"### Order #{selected_order.id} Details")
                st.write(f"**Customer:** {selected_order.customer.name} ({selected_order.customer.company or 'N/A'})")
                st.write(f"**Order Date:** {selected_order.order_date.strftime('%Y-%m-%d')}")
                st.write(f"**Expected Delivery Date:** {selected_order.expected_delivery_date.strftime('%Y-%m-%d')}")
                st.write(f"**Overall Status:** **{selected_order.overall_status}** {delay_str}")
                st.write(f"**Notes:** {selected_order.notes or 'N/A'}")

                st.markdown("#### Update Overall Order Status")
                current_overall_status_idx = all_order_statuses.index(selected_order.overall_status) if selected_order.overall_status in all_order_statuses else 0
                # Filter out 'All' from selection
                selectable_order_statuses = [s for s in all_order_statuses if s != "All"]
                try:
                    current_selectable_idx = selectable_order_statuses.index(selected_order.overall_status)
                except ValueError:
                    current_selectable_idx = 0 # Default if current status isn't in selectable list

                new_overall_status = st.selectbox(
                    "Select New Overall Status",
                    selectable_order_statuses,
                    index=current_selectable_idx,
                    key=f"overall_status_select_{selected_order.id}"
                )
                if st.button(f"Update Order #{selected_order.id} Status", key=f"update_order_status_btn_{selected_order.id}"):
                    # Check for document completion before dispatch
                    if new_overall_status in ["Wooden Packing", "Added to Dispatch Box", "Dispatch"]:
                        document_family = db.query(MachineFamily).filter_by(name="Documents").first()
                        if document_family:
                            document_order_item = next((oi for oi in selected_order.order_items if oi.machine_family_id == document_family.id), None)
                            if document_order_item:
                                all_docs_completed = True
                                for oia in document_order_item.order_item_accessories:
                                    if oia.accessory.category_tag == "Documents" and oia.current_status != "Attached": # Assuming "Attached" means complete
                                        all_docs_completed = False
                                        st.error(f"Cannot update status to '{new_overall_status}'. Document '{oia.accessory.name}' is not marked as 'Attached'.")
                                        break
                                if all_docs_completed:
                                    update_overall_order_status(db, selected_order.id, new_overall_status)
                                    st.rerun()
                            else:
                                st.warning("No 'Documents' family found in this order. Proceeding with status update without document check.")
                                update_overall_order_status(db, selected_order.id, new_overall_status)
                                st.rerun()
                        else:
                            st.warning("No 'Documents' Machine Family defined. Proceeding with status update without document check.")
                            update_overall_order_status(db, selected_order.id, new_overall_status)
                            st.rerun()
                    else:
                        update_overall_order_status(db, selected_order.id, new_overall_status)
                        st.rerun()


                st.markdown("#### Order Items & Production Progress")
                for order_item in selected_order.order_items:
                    st.markdown(f"##### **{order_item.machine_family.name}** (Qty: {order_item.quantity_ordered})")
                    st.write(f"Current Production Status: **{order_item.current_production_status}**")

                    # Update Production Status for this OrderItem
                    current_prod_status_idx = production_steps_names.index(order_item.current_production_status) if order_item.current_production_status in production_steps_names else 0
                    new_prod_status = st.selectbox(
                        f"Update Production Status for {order_item.machine_family.name}",
                        production_steps_names,
                        index=current_prod_status_idx,
                        key=f"prod_status_select_{order_item.id}"
                    )
                    if st.button(f"Update Production Status for '{order_item.machine_family.name}'", key=f"update_prod_status_btn_{order_item.id}"):
                        update_order_item_production_status(db, order_item.id, new_prod_status)
                        st.rerun()

                    # Accessories for this OrderItem
                    st.markdown("###### Required Accessories:")
                    acc_details_data = []
                    for oia in order_item.order_item_accessories:
                        # Get stock status
                        current_stock = oia.accessory.current_stock_level
                        required_qty = oia.required_quantity
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
                            "Required Qty": oia.required_quantity,
                            "Variable Value": oia.variable_value if oia.variable_value else ("PENDING" if oia.accessory.category_tag == "Documents" else "N/A"), # Documents pending status for variable
                            "Stock Status": stock_status,
                            "Current Item Status": oia.current_status,
                            "Custom": "Yes" if oia.is_custom else "No"
                        })
                    st.dataframe(pd.DataFrame(acc_details_data), use_container_width=True, hide_index=True)

                    # Update Accessory Item Status (e.g., Raw Material Ordered, Received, Integrated)
                    st.markdown("###### Update Individual Accessory Status for this item:")
                    acc_status_options = ["Pending", "Raw Material Ordered", "Raw Material Received", "Integrated into Assembly", "Added to Dispatch Box", "Attached"] # Added 'Attached' for documents
                    selected_oia_display = st.selectbox(
                        f"Select Accessory to update for {order_item.machine_family.name} (ID: {order_item.id})",
                        ["-- Select --"] + [f"{oia.accessory.name} (Status: {oia.current_status})" for oia in order_item.order_item_accessories],
                        key=f"oia_status_select_{order_item.id}"
                    )
                    if selected_oia_display != "-- Select --":
                        oia_name_only = selected_oia_display.split(" (Status:")[0]
                        oia_to_update = next((oia for oia in order_item.order_item_accessories if oia.accessory.name == oia_name_only), None)
                        if oia_to_update:
                            current_oia_status_idx = acc_status_options.index(oia_to_update.current_status) if oia_to_update.current_status in acc_status_options else 0
                            new_oia_status = st.selectbox(
                                f"New Status for {oia_to_update.accessory.name}",
                                acc_status_options,
                                index=current_oia_status_idx,
                                key=f"new_oia_status_{oia_to_update.id}"
                            )
                            if oia_to_update.is_variable: # For documents or other variable items
                                new_oia_variable_value = st.text_input(
                                    f"Update Variable Value for {oia_to_update.accessory.name}",
                                    value=oia_to_update.variable_value or "",
                                    key=f"oia_var_val_{oia_to_update.id}"
                                )
                            else:
                                new_oia_variable_value = oia_to_update.variable_value

                            if st.button(f"Update '{oia_to_update.accessory.name}' Status/Value", key=f"update_oia_btn_{oia_to_update.id}"):
                                oia_to_update.current_status = new_oia_status
                                oia_to_update.variable_value = new_oia_variable_value # Update variable value here
                                db.commit()
                                st.toast(f"Accessory '{oia_to_update.accessory.name}' status updated to '{new_oia_status}'")
                                st.rerun()

                st.markdown("---") # Separator between order items

                st.markdown("#### Order Status History")
                status_history = db.query(OrderStatusHistory).filter_by(order_id=selected_order.id).order_by(OrderStatusHistory.timestamp.asc()).all()
                if status_history:
                    history_df = pd.DataFrame([
                        {"Timestamp": hs.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                         "From": hs.status_from or "N/A",
                         "To": hs.status_to,
                         "Notes": hs.notes or "N/A"}
                        for hs in status_history
                    ])
                    st.dataframe(history_df, use_container_width=True, hide_index=True)
                else:
                    st.info("No status history for this order.")

                st.markdown("#### Production Status History (Per Item)")
                for order_item in selected_order.order_items:
                    prod_history = db.query(ProductionStatusHistory).filter_by(order_item_id=order_item.id).order_by(ProductionStatusHistory.timestamp.asc()).all()
                    if prod_history:
                        st.markdown(f"**History for {order_item.machine_family.name}:**")
                        prod_history_df = pd.DataFrame([
                            {"Timestamp": ph.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                             "From": ph.status_from or "N/A",
                             "To": ph.status_to,
                             "Notes": ph.notes or "N/A"}
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
    st.title("Inventory Management")
    db = next(get_db())

    # --- Filters ---
    st.sidebar.header("Inventory Filters")
    category_tags = ["All", "Product", "Mechanical", "Bought Out", "Electronic", "Loadcell", "Hardware", "Software", "Documents", "VendorReady", "Testing for Use"]
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
            if acc.current_stock_level <= acc.min_stock_level:
                stock_status_color = "red" if acc.current_stock_level == 0 else "orange"

            acc_data_display.append({
                "Accessory Name": acc.name,
                "Accessory ID": acc.accessory_id,
                "Category": acc.category_tag,
                "Unit": acc.unit_of_measure,
                "Min Stock": acc.min_stock_level,
                "Current Stock": f":{stock_status_color}[{acc.current_stock_level}]",
                "Description": acc.description
            })
        st.dataframe(pd.DataFrame(acc_data_display), use_container_width=True, hide_index=True)
    else:
        st.info("No accessories found matching the filters. Add some in Master Data.")

    st.markdown("---")
    # --- Stock Adjustment Forms ---
    st.subheader("Inventory Movements")

    acc_options = {f"{a.name} (ID: {a.accessory_id})": a for a in db.query(Accessory).order_by(Accessory.name).all()}
    acc_names_list = list(acc_options.keys())

    selected_acc_for_movement_name = st.selectbox(
        "Select Accessory for Stock Movement",
        ["-- Select --"] + acc_names_list,
        key="inv_acc_select"
    )

    if selected_acc_for_movement_name != "-- Select --":
        selected_acc_for_movement = acc_options[selected_acc_for_movement_name]
        st.write(f"**Current Stock for {selected_acc_for_movement.name}:** {selected_acc_for_movement.current_stock_level} {selected_acc_for_movement.unit_of_measure}")

        col_in, col_out, col_adjust = st.columns(3)

        with col_in:
            st.markdown("##### Stock In (Receipt)")
            qty_in = st.number_input("Quantity to Add", min_value=1, value=1, key="qty_in")
            reason_in = st.text_input("Reason (e.g., Supplier delivery, Production return)", key="reason_in")
            if st.button("Record Stock In", key="record_in_btn"):
                if qty_in > 0:
                    selected_acc_for_movement.current_stock_level += qty_in
                    db.add(StockHistory(
                        accessory_id=selected_acc_for_movement.id,
                        change_type="IN",
                        quantity_change=qty_in,
                        new_stock_level=selected_acc_for_movement.current_stock_level,
                        reason=reason_in
                    ))
                    db.commit()
                    st.success(f"{qty_in} units of {selected_acc_for_movement.name} added to stock.")
                    st.rerun()
                else:
                    st.warning("Quantity to add must be greater than 0.")

        with col_out:
            st.markdown("##### Stock Out (Issuance)")
            qty_out = st.number_input("Quantity to Issue", min_value=1, value=1, key="qty_out")
            reason_out = st.text_input("Reason (e.g., For Order #, Assembly Line)", key="reason_out")
            order_id_out_str = st.text_input("Associated Order ID (Optional)", key="order_id_out")
            order_id_out = int(order_id_out_str) if order_id_out_str.isdigit() else None
            
            if st.button("Record Stock Out", key="record_out_btn"):
                if qty_out > 0 and selected_acc_for_movement.current_stock_level >= qty_out:
                    selected_acc_for_movement.current_stock_level -= qty_out
                    db.add(StockHistory(
                        accessory_id=selected_acc_for_movement.id,
                        change_type="OUT",
                        quantity_change=-qty_out,
                        new_stock_level=selected_acc_for_movement.current_stock_level,
                        reason=reason_out,
                        order_id=order_id_out
                    ))
                    db.commit()
                    st.success(f"{qty_out} units of {selected_acc_for_movement.name} issued from stock.")
                    st.rerun()
                elif qty_out <= 0:
                    st.warning("Quantity to issue must be greater than 0.")
                else:
                    st.error("Not enough stock available!")

        with col_adjust:
            if st.session_state.role == "Admin": # Only Admin can do manual adjustments
                st.markdown("##### Manual Adjustment (Admin Only)")
                adjust_qty = st.number_input("Adjustment Quantity", value=0, help="Positive to add, Negative to remove", key="adjust_qty")
                adjust_reason = st.text_input("Reason for Adjustment *", key="adjust_reason")
                if st.button("Record Adjustment", key="record_adjust_btn"):
                    if adjust_reason:
                        selected_acc_for_movement.current_stock_level += adjust_qty
                        db.add(StockHistory(
                            accessory_id=selected_acc_for_movement.id,
                            change_type="ADJUSTMENT",
                            quantity_change=adjust_qty,
                            new_stock_level=selected_acc_for_movement.current_stock_level,
                            reason=f"Manual Adjustment: {adjust_reason}"
                        ))
                        db.commit()
                        st.success(f"Stock for {selected_acc_for_movement.name} adjusted by {adjust_qty}.")
                        st.rerun()
                    else:
                        st.error("Reason for adjustment is required.")
            else:
                st.info("Manual Adjustment is for Admin only.")

    st.markdown("---")
    st.subheader("Inventory History for Selected Accessory")
    if selected_acc_for_movement_name != "-- Select --":
        selected_acc_for_history = acc_options[selected_acc_for_movement_name]
        history_records = db.query(StockHistory).filter_by(accessory_id=selected_acc_for_history.id).order_by(StockHistory.timestamp.desc()).all()
        if history_records:
            history_df = pd.DataFrame([
                {"Timestamp": h.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                 "Type": h.change_type,
                 "Quantity Change": h.quantity_change,
                 "New Stock Level": h.new_stock_level,
                 "Reason": h.reason or "N/A",
                 "Order ID": h.order_id or "N/A"}
                for h in history_records
            ])
            st.dataframe(history_df, use_container_width=True, hide_index=True)
        else:
            st.info("No stock history for this accessory.")
    else:
        st.info("Select an accessory above to view its history.")

    db.close()


def show_master_data_page():
    if st.session_state.role != "Admin":
        st.warning("You do not have permission to access this page.")
        return

    st.title("Master Data Management")
    db = next(get_db())

    st.subheader("Manage Machine Families (Products/Bundles)")
    with st.expander("Add New Machine Family"):
        with st.form("new_machine_family_form"):
            new_mf_name = st.text_input("Machine Family Name *", key="new_mf_name_input")
            new_mf_description = st.text_area("Description", key="new_mf_desc_input")
            new_mf_is_product = st.checkbox("Can be sold as independent product?", value=True, key="new_mf_is_product_cb")
            submit_mf_btn = st.form_submit_button("Add Machine Family")

            if submit_mf_btn:
                if new_mf_name:
                    existing_mf = db.query(MachineFamily).filter(func.lower(MachineFamily.name) == func.lower(new_mf_name)).first()
                    if existing_mf:
                        st.warning(f"Machine Family '{new_mf_name}' already exists.")
                    else:
                        mf = MachineFamily(name=new_mf_name, description=new_mf_description, is_product=new_mf_is_product)
                        db.add(mf)
                        db.commit()
                        db.refresh(mf)
                        st.success(f"Machine Family '{new_mf_name}' added!")
                        st.rerun()
                else:
                    st.error("Machine Family Name is required.")

    st.markdown("---")
    st.subheader("Existing Machine Families")
    mfs = db.query(MachineFamily).order_by(MachineFamily.name).all()
    if mfs:
        mf_options = {f"{mf.name}": mf for mf in mfs}
        selected_mf_name = st.selectbox("Select Machine Family to Edit Accessories", ["-- Select --"] + list(mf_options.keys()), key="edit_mf_select")

        if selected_mf_name != "-- Select --":
            selected_mf = mf_options[selected_mf_name]
            st.markdown(f"**Editing: {selected_mf.name}** (ID: {selected_mf.id})")

            # Display current default accessories
            st.markdown("##### Current Default Accessories:")
            # Corrected query to eager-load accessory details
            selected_mf_accessories = db.query(FamilyAccessory).options(selectinload(FamilyAccessory.accessory)).filter(FamilyAccessory.machine_family_id == selected_mf.id).order_by(Accessory.name).all()
            if selected_mf_accessories:
                acc_data_display = []
                for fa in selected_mf_accessories:
                    acc_data_display.append({
                        "Accessory Name": fa.accessory.name,
                        "ID": fa.accessory.accessory_id,
                        "Category": fa.accessory.category_tag,
                        "Default Qty": fa.default_quantity,
                        "Variable?": "Yes" if fa.is_variable else "No",
                        "Placeholder": fa.variable_placeholder if fa.is_variable else "N/A"
                    })
                st.dataframe(pd.DataFrame(acc_data_display), use_container_width=True, hide_index=True)
            else:
                st.info("No default accessories configured for this family yet.")

            st.markdown("##### Add/Remove Default Accessories:")
            all_accessories = db.query(Accessory).order_by(Accessory.name).all()
            all_acc_options = {f"{a.name} ({a.category_tag})": a for a in all_accessories}
            all_acc_names = list(all_acc_options.keys())

            col_add_mf_acc1, col_add_mf_acc2, col_add_mf_acc3 = st.columns([0.6, 0.2, 0.2])
            with col_add_mf_acc1:
                acc_to_add_to_mf = st.selectbox("Select Accessory", ["-- Select --"] + all_acc_names, key=f"add_acc_to_mf_select_{selected_mf.id}")
            with col_add_mf_acc2:
                default_qty = st.number_input("Default Quantity", min_value=1, value=1, key=f"default_qty_{selected_mf.id}")
            with col_add_mf_acc3:
                is_variable = st.checkbox("Is Variable?", key=f"is_variable_{selected_mf.id}")

            variable_placeholder_text = ""
            if is_variable:
                variable_placeholder_text = st.text_input("Variable Placeholder (e.g., 'Gearbox Model : _______')", key=f"var_placeholder_{selected_mf.id}")


            if st.button(f"Add Default Accessory to {selected_mf.name}", key=f"add_default_acc_btn_{selected_mf.id}"):
                if acc_to_add_to_mf != "-- Select --":
                    selected_acc_obj = all_acc_options[acc_to_add_to_mf]
                    existing_link = db.query(FamilyAccessory).filter(
                        FamilyAccessory.machine_family_id == selected_mf.id,
                        FamilyAccessory.accessory_id == selected_acc_obj.id
                    ).first()

                    if existing_link:
                        st.warning(f"'{selected_acc_obj.name}' is already a default accessory for '{selected_mf.name}'. Updating quantity.")
                        existing_link.default_quantity = default_qty
                        existing_link.is_variable = is_variable
                        existing_link.variable_placeholder = variable_placeholder_text
                        db.commit()
                    else:
                        new_link = FamilyAccessory(
                            machine_family_id=selected_mf.id,
                            accessory_id=selected_acc_obj.id,
                            default_quantity=default_qty,
                            is_variable=is_variable,
                            variable_placeholder=variable_placeholder_text
                        )
                        db.add(new_link)
                        db.commit()
                        st.success(f"'{selected_acc_obj.name}' added as default for '{selected_mf.name}'.")
                    st.rerun()
                else:
                    st.warning("Please select an accessory to add.")

            st.markdown("---")
            # Remove default accessories
            if selected_mf_accessories:
                acc_to_remove_from_mf_option = st.selectbox("Remove Default Accessory", ["-- Select --"] + [fa.accessory.name for fa in selected_mf_accessories], key=f"remove_acc_from_mf_select_{selected_mf.id}")
                if acc_to_remove_from_mf_option != "-- Select --":
                    if st.button(f"Remove '{acc_to_remove_from_mf_option}' from {selected_mf.name}", key=f"remove_default_acc_btn_{selected_mf.id}"):
                        link_to_remove = db.query(FamilyAccessory).filter(
                            FamilyAccessory.machine_family_id == selected_mf.id,
                            FamilyAccessory.accessory.has(name=acc_to_remove_from_mf_option)
                        ).first()
                        if link_to_remove:
                            db.delete(link_to_remove)
                            db.commit()
                            st.success(f"'{acc_to_remove_from_mf_option}' removed from default for '{selected_mf.name}'.")
                            st.rerun()
            st.markdown("---")
            if st.button(f"Delete Machine Family '{selected_mf.name}'", key=f"delete_mf_btn_{selected_mf.id}", help="This will also remove all its default accessory links. Orders using this family will remain but link to non-existent family."):
                if st.warning(f"Are you sure you want to delete '{selected_mf.name}'? This action cannot be undone and will affect existing orders."):
                    # In a real app, you'd add checks here if this family is used in any active orders.
                    # For now, we allow deletion.
                    db.delete(selected_mf)
                    db.commit()
                    st.success(f"Machine Family '{selected_mf.name}' deleted.")
                    st.rerun()
    else:
        st.info("No machine families defined yet. Add one above.")

    st.markdown("---")
    st.subheader("Manage Accessories")
    with st.expander("Add New Accessory"):
        with st.form("new_accessory_form"):
            new_acc_name = st.text_input("Accessory Name *", key="new_acc_name_input")
            new_acc_id = st.text_input("Accessory ID (Unique Identifier) *", key="new_acc_id_input")
            new_acc_description = st.text_area("Description", key="new_acc_desc_input")
            category_tags = ["Product", "Mechanical", "Bought Out", "Electronic", "Loadcell", "Hardware", "Software", "Documents", "VendorReady", "Testing for Use"]
            new_acc_tag = st.selectbox("Category/Tag *", category_tags, key="new_acc_tag_select")
            new_acc_uom = st.text_input("Unit of Measure (e.g., pcs, sets)", value="pcs", key="new_acc_uom_input")
            new_acc_min_stock = st.number_input("Minimum Stock Level", min_value=0, value=0, key="new_acc_min_stock_input")
            new_acc_current_stock = st.number_input("Initial Current Stock Level", min_value=0, value=0, key="new_acc_current_stock_input")
            submit_acc_btn = st.form_submit_button("Add Accessory")

            if submit_acc_btn:
                if new_acc_name and new_acc_id and new_acc_tag:
                    existing_acc = db.query(Accessory).filter(func.lower(Accessory.accessory_id) == func.lower(new_acc_id)).first()
                    if existing_acc:
                        st.warning(f"Accessory with ID '{new_acc_id}' already exists.")
                    else:
                        acc = Accessory(
                            name=new_acc_name,
                            accessory_id=new_acc_id,
                            description=new_acc_description,
                            category_tag=new_acc_tag,
                            unit_of_measure=new_acc_uom,
                            min_stock_level=new_acc_min_stock,
                            current_stock_level=new_acc_current_stock
                        )
                        db.add(acc)
                        db.commit()
                        db.refresh(acc)
                        st.success(f"Accessory '{new_acc_name}' (ID: {new_acc_id}) added!")
                        st.rerun()
                else:
                    st.error("Accessory Name, ID, and Category/Tag are required.")

    st.markdown("---")
    st.subheader("Existing Accessories")
    accessories = db.query(Accessory).order_by(Accessory.name).all()
    if accessories:
        acc_df = pd.DataFrame([
            {"Name": a.name, "ID": a.accessory_id, "Category": a.category_tag,
             "UoM": a.unit_of_measure, "Min Stock": a.min_stock_level,
             "Current Stock": a.current_stock_level, "Description": a.description}
            for a in accessories
        ])
        st.dataframe(acc_df, use_container_width=True, hide_index=True)

        selected_acc_to_edit_id = st.selectbox(
            "Select Accessory to Edit/Delete",
            ["-- Select --"] + [f"{a.name} (ID: {a.accessory_id})" for a in accessories],
            key="edit_accessory_select"
        )
        if selected_acc_to_edit_id != "-- Select --":
            acc_id_str = selected_acc_to_edit_id.split("(ID: ")[1].rstrip(")")
            selected_acc = db.query(Accessory).filter_by(accessory_id=acc_id_str).first()

            if selected_acc:
                st.markdown(f"**Editing: {selected_acc.name}** (ID: {selected_acc.accessory_id})")
                with st.form(f"edit_accessory_form_{selected_acc.id}"):
                    edited_acc_name = st.text_input("Accessory Name", value=selected_acc.name, key=f"edited_acc_name_{selected_acc.id}")
                    edited_acc_description = st.text_area("Description", value=selected_acc.description, key=f"edited_acc_desc_{selected_acc.id}")
                    category_tags = ["Product", "Mechanical", "Bought Out", "Electronic", "Loadcell", "Hardware", "Software", "Documents", "VendorReady", "Testing for Use"]
                    edited_acc_tag = st.selectbox("Category/Tag", category_tags, index=category_tags.index(selected_acc.category_tag), key=f"edited_acc_tag_{selected_acc.id}")
                    edited_acc_uom = st.text_input("Unit of Measure", value=selected_acc.unit_of_measure, key=f"edited_acc_uom_{selected_acc.id}")
                    edited_acc_min_stock = st.number_input("Minimum Stock Level", min_value=0, value=selected_acc.min_stock_level, key=f"edited_acc_min_stock_{selected_acc.id}")
                    update_acc_btn = st.form_submit_button("Update Accessory")

                    if update_acc_btn:
                        selected_acc.name = edited_acc_name
                        selected_acc.description = edited_acc_description
                        selected_acc.category_tag = edited_acc_tag
                        selected_acc.unit_of_measure = edited_acc_uom
                        selected_acc.min_stock_level = edited_acc_min_stock
                        db.commit()
                        st.success(f"Accessory '{selected_acc.name}' updated!")
                        st.rerun()

                if st.button(f"Delete Accessory '{selected_acc.name}'", key=f"delete_acc_btn_{selected_acc.id}"):
                    # In a real app, you'd add checks here if this accessory is used in any active families or orders.
                    # For now, we allow deletion.
                    if st.warning(f"Are you sure you want to delete '{selected_acc.name}'? This action cannot be undone and will affect families/orders that use it."):
                        db.delete(selected_acc)
                        db.commit()
                        st.success(f"Accessory '{selected_acc.name}' deleted.")
                        st.rerun()

    st.markdown("---")
    st.subheader("Production Process Steps")
    production_steps = db.query(ProductionProcessStep).order_by(ProductionProcessStep.sequence_order).all()
    if production_steps:
        steps_df = pd.DataFrame([
            {"Step Name": s.step_name, "Order": s.sequence_order}
            for s in production_steps
        ])
        st.dataframe(steps_df, use_container_width=True, hide_index=True)
        st.info("Production process steps are pre-defined. Contact admin for changes if needed.")
    db.close()


def show_reports_page():
    st.title("Reports")
    db = next(get_db())

    report_type = st.selectbox(
        "Select Report Type",
        ["Orders by Status", "Delayed Orders", "Low Stock Accessories", "Inventory Movement Log"],
        key="report_type_select"
    )

    if report_type == "Orders by Status":
        st.subheader("Orders by Status")
        statuses = ["New", "Pending Production", "In Production - Assembly", "Ready for Dispatch", "Dispatched"]
        status_counts = {}
        for status in statuses:
            count = db.query(Order).filter_by(overall_status=status).count()
            status_counts[status] = count
        
        status_df = pd.DataFrame(list(status_counts.items()), columns=["Status", "Number of Orders"])
        st.dataframe(status_df, use_container_width=True, hide_index=True)

        st.bar_chart(status_df.set_index("Status"))

    elif report_type == "Delayed Orders":
        st.subheader("Delayed Orders")
        today = datetime.date.today()
        # Find orders where expected_delivery_date is in the past and status is not Dispatched
        delayed_orders_query = db.query(Order).options(selectinload(Order.customer)).filter(
            Order.expected_delivery_date < today,
            Order.overall_status != "Dispatched"
        ).order_by(Order.expected_delivery_date.asc()).all()

        if delayed_orders_query:
            delayed_data = []
            for order in delayed_orders_query:
                delay_days = (today - order.expected_delivery_date.date()).days
                delayed_data.append({
                    "Order ID": order.id,
                    "Customer": order.customer.name,
                    "Company": order.customer.company,
                    "Expected Delivery": order.expected_delivery_date.strftime("%Y-%m-%d"),
                    "Current Status": order.overall_status,
                    "Delay (Days)": delay_days,
                    "Order Date": order.order_date.strftime("%Y-%m-%d")
                })
            st.warning("The following orders are currently delayed:")
            st.dataframe(pd.DataFrame(delayed_data), use_container_width=True, hide_index=True)
        else:
            st.success("No delayed orders found! All orders are on track or dispatched.")

    elif report_type == "Low Stock Accessories":
        st.subheader("Low Stock Accessories")
        low_stock_accessories = db.query(Accessory).filter(Accessory.current_stock_level < Accessory.min_stock_level).all()
        if low_stock_accessories:
            stock_data = []
            for acc in low_stock_accessories:
                stock_data.append({
                    "Accessory ID": acc.accessory_id,
                    "Name": acc.name,
                    "Tag": acc.category_tag,
                    "Current Stock": acc.current_stock_level,
                    "Min Stock": acc.min_stock_level,
                    "Description": acc.description
                })
            st.warning("The following accessories are running low on stock:")
            st.dataframe(pd.DataFrame(stock_data), use_container_width=True, hide_index=True)
        else:
            st.success("All accessories are currently above minimum stock levels!")

    elif report_type == "Inventory Movement Log":
        st.subheader("Inventory Movement Log")
        all_movements = db.query(StockHistory).options(selectinload(StockHistory.accessory)).order_by(StockHistory.timestamp.desc()).all()
        if all_movements:
            move_data = []
            for move in all_movements:
                move_data.append({
                    "Timestamp": move.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                    "Accessory": move.accessory.name,
                    "Accessory ID": move.accessory.accessory_id,
                    "Type": move.change_type,
                    "Qty Change": move.quantity_change,
                    "New Stock": move.new_stock_level,
                    "Reason": move.reason or "N/A",
                    "Order ID": move.order_id or "N/A"
                })
            st.dataframe(pd.DataFrame(move_data), use_container_width=True, hide_index=True)
        else:
            st.info("No inventory movements recorded yet.")

    db.close()


# --- Main App Logic ---
if not st.session_state.logged_in:
    show_login_page()
else:
    # Sidebar Navigation
    st.sidebar.title("Navigation")
    pages = {
        "Dashboard": show_dashboard,
        "Create New Order": show_create_order_page,
        "View All Orders": show_view_orders_page,
        "Inventory Management": show_inventory_page,
        "Reports": show_reports_page
    }
    if st.session_state.role == "Admin":
        pages["Master Data Management"] = show_master_data_page

    selected_page = st.sidebar.radio("Go to", list(pages.keys()), index=list(pages.keys()).index(st.session_state.current_page))
    st.session_state.current_page = selected_page

    # Display selected page
    pages[st.session_state.current_page]()

    st.sidebar.markdown("---")
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.session_state.role = ""
        st.session_state.current_page = "Dashboard"
        st.rerun()

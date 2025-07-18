import streamlit as st
from database import create_tables, get_db, initialize_master_data
from models import (
    Customer, Order, MachineFamily, Accessory, FamilyAccessory,
    OrderItem, OrderItemAccessory, User, ProductionProcessStep,
    OrderStatusHistory, ProductionStatusHistory, StockHistory,
    hash_password, verify_password # Keep if needed for user tracking, otherwise remove
)
from sqlalchemy.orm import Session, selectinload, joinedload # Add joinedload for efficient fetching
from sqlalchemy import func, inspect, text # Ensure 'text' for advanced queries if needed
import datetime
import pandas as pd
import bcrypt # Keep this if you still hash passwords for other reasons, otherwise remove

# --- Streamlit Page Configuration ---
st.set_page_config(
    page_title="EQVIMECH Dashboard",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Database Initialization (Run once on app startup) ---
# Ensure this block is at the very top of your script.
if 'db_initialized' not in st.session_state:
    db_session = None
    try:
        db_session = next(get_db())
        engine = db_session.bind
        inspector = inspect(engine)

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
if 'current_page' not in st.session_state:
    st.session_state.current_page = "Dashboard" # Default starting page

if 'order_items_config' not in st.session_state:
    st.session_state.order_items_config = [] # To store items added to current order

if 'current_customer_id' not in st.session_state:
    st.session_state.current_customer_id = None # Store selected customer for order

# --- Helper Functions ---
def get_machine_families_for_selectbox():
    db = next(get_db())
    try:
        # Filter for products (is_product=True) if you only want machines in this dropdown
        families = db.query(MachineFamily).filter(MachineFamily.is_product == True).all()
        # st.write(f"Fetched {len(families)} machine families for selectbox.") # For debugging
        return families
    finally:
        db.close()

def get_accessories_for_selectbox(family_id=None):
    db = next(get_db())
    try:
        if family_id:
            # Fetch accessories linked to the selected family
            accessories = db.query(Accessory).join(FamilyAccessory).filter(FamilyAccessory.machine_family_id == family_id).all()
        else:
            # Fetch all active accessories if no family is selected
            accessories = db.query(Accessory).filter(Accessory.is_active == True).all()
        # st.write(f"Fetched {len(accessories)} accessories for selectbox.") # For debugging
        return accessories
    finally:
        db.close()

def get_customers_for_selectbox():
    db = next(get_db())
    try:
        customers = db.query(Customer).all()
        return customers
    finally:
        db.close()

# --- Page Functions ---

def show_dashboard():
    st.title("⚙️ Production Dashboard - Enhanced Version")
    st.markdown("Real-time manufacturing tracking for your 4-member team")
    st.markdown("---")

    db = next(get_db())
    try:
        # --- Metrics ---
        col1, col2, col3, col4, col5, col6 = st.columns(6)

        active_orders_count = db.query(Order).filter(Order.status.in_(["Approved", "In Production", "Pending Approval"])).count()
        col1.metric("Active Orders", active_orders_count)

        product_families_count = db.query(MachineFamily).filter(MachineFamily.is_product == True).count()
        col2.metric("Product Families", product_families_count)

        # Items In Progress (e.g., items in any production step except "Completed" or "Dispatched")
        # This requires joining OrderItem to ProductionStatusHistory
        items_in_progress_count = db.query(OrderItem).join(ProductionStatusHistory).join(ProductionProcessStep).filter(
            ProductionStatusHistory.status.in_(["In Progress", "Pending", "On Hold"]),
            ~ProductionProcessStep.is_dispatch_step # Exclude dispatch steps if 'In Progress' for them means dispatched
        ).distinct(OrderItem.id).count()
        col3.metric("Items In Progress", items_in_progress_count)

        # Items Completed (e.g., items where the last production step is "Completed" for the final step)
        # This query can be complex, for simplicity, we'll count items where at least one step is 'Completed' for a final step.
        # A more robust solution might involve querying the LAST status for each OrderItem
        items_completed_count = db.query(OrderItem).join(ProductionStatusHistory).join(ProductionProcessStep).filter(
            ProductionStatusHistory.status == "Completed",
            ProductionProcessStep.is_dispatch_step == True # Assuming the last production step is a dispatch one.
        ).distinct(OrderItem.id).count()
        col4.metric("Items Completed", items_completed_count)

        # Items Blocked (example: items on hold in production)
        items_blocked_count = db.query(OrderItem).join(ProductionStatusHistory).filter(
            ProductionStatusHistory.status == "On Hold"
        ).distinct(OrderItem.id).count()
        col5.metric("Items Blocked", items_blocked_count)

        # Overall Progress (example: (completed_items / (in_progress + completed)) * 100)
        total_producible_items = db.query(OrderItem).count() # Total items ever ordered
        if total_producible_items > 0:
            overall_progress_percent = (items_completed_count / total_producible_items) * 100
        else:
            overall_progress_percent = 0
        col6.metric("Overall Progress", f"{overall_progress_percent:.0f}%")

        st.markdown("---")

        # --- Recent Activity ---
        st.subheader("Recent Activity")

        # Fetch recent order status changes (last 10)
        recent_order_status_changes = db.query(OrderStatusHistory).options(
            joinedload(OrderStatusHistory.order).selectinload(Order.customer), # Load order and customer
            joinedload(OrderStatusHistory.user) # Load user who made change
        ).order_by(OrderStatusHistory.timestamp.desc()).limit(5).all()

        # Fetch recent production status changes (last 10)
        recent_production_status_changes = db.query(ProductionStatusHistory).options(
            joinedload(ProductionStatusHistory.order_item).selectinload(OrderItem.machine_family), # Load order item and machine family
            joinedload(ProductionStatusHistory.process_step), # Load the process step
            joinedload(ProductionStatusHistory.user) # Load user who made change
        ).order_by(ProductionStatusHistory.timestamp.desc()).limit(5).all()

        # Combine and sort all recent activities
        all_activities = []

        for osc in recent_order_status_changes:
            all_activities.append({
                "Time": osc.timestamp.strftime("%H:%M %p"),
                "Action": "Order Status Updated",
                "Details": f"Order {osc.order.generate_full_order_id()} - New Status: {osc.status}",
                "User": osc.user.username if osc.user else "System"
            })

        for psc in recent_production_status_changes:
            item_name = psc.order_item.machine_family.name if psc.order_item and psc.order_item.machine_family else "N/A"
            step_name = psc.process_step.step_name if psc.process_step else "N/A"
            all_activities.append({
                "Time": psc.timestamp.strftime("%H:%M %p"),
                "Action": "Production Status Updated",
                "Details": f"{item_name} - Step: {step_name} - Status: {psc.status}",
                "User": psc.user.username if psc.user else "System"
            })
        
        # Sort all activities by time, newest first
        all_activities.sort(key=lambda x: datetime.datetime.strptime(x["Time"], "%H:%M %p"), reverse=True)

        if all_activities:
            st.table(pd.DataFrame(all_activities))
        else:
            st.info("No recent activity to display.")

    except Exception as e:
        st.error(f"Error fetching dashboard data: {e}")
    finally:
        db.close()


def show_order_creation():
    st.title("📝 Create New Order")
    st.markdown("---")

    db = next(get_db()) # Get a session for this function
    try:
        # --- 1. Select/Create Customer ---
        st.subheader("1. Select or Add Customer")
        existing_customers = get_customers_for_selectbox()
        customer_names = ["-- Select Customer --"] + [c.name for c in existing_customers]
        selected_customer_name = st.selectbox("Select Existing Customer:", customer_names, key="select_customer_for_order")

        selected_customer_obj = None
        if selected_customer_name != "-- Select Customer --":
            selected_customer_obj = next((c for c in existing_customers if c.name == selected_customer_name), None)
            st.session_state.current_customer_id = selected_customer_obj.id if selected_customer_obj else None
            st.write(f"Selected Customer: **{selected_customer_obj.name}**")
        else:
            st.session_state.current_customer_id = None
            st.markdown("Or **Add New Customer**:")
            with st.expander("Add New Customer Details"):
                new_customer_name = st.text_input("Customer Name", key="new_cust_name")
                new_customer_contact = st.text_input("Contact Person", key="new_cust_contact")
                new_customer_email = st.text_input("Email", key="new_cust_email")
                new_customer_phone = st.text_input("Phone", key="new_cust_phone")
                new_customer_address = st.text_area("Address", key="new_cust_address")
                new_customer_gst = st.text_input("GST Number", key="new_cust_gst")

                if st.button("Save New Customer", key="save_new_customer_btn"):
                    if new_customer_name:
                        try:
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
                            st.experimental_rerun() # Rerun to update customer selectbox
                        except Exception as e:
                            st.error(f"Error adding new customer: {e}")
                    else:
                        st.warning("Customer Name cannot be empty.")

        if st.session_state.current_customer_id is None:
            st.info("Please select or add a customer to proceed with order creation.")
            return # Stop here if no customer is selected/added

        st.markdown("---")

        # --- 2. Add Products/Machine Families ---
        st.subheader("2. Add Products/Machine Families to Order")
        col_product, col_qty = st.columns([3, 1])

        # Get Machine Families for the dropdown
        machine_families = get_machine_families_for_selectbox()
        machine_family_names = ["-- Select Product/Family --"] + [mf.name for mf in machine_families]

        selected_family_name = col_product.selectbox(
            "Select Product/Family to Add",
            machine_family_names,
            key="add_product_family_select"
        )
        selected_family_obj = None
        if selected_family_name != "-- Select Product/Family --":
            selected_family_obj = next((mf for mf in machine_families if mf.name == selected_family_name), None)

        quantity = col_qty.number_input("Quantity", min_value=1, value=1, step=1, key="product_family_qty")

        # Fetch accessories based on selected machine family for display, not for initial selectbox
        # This will be used in an "Add Accessories" section later if needed
        # For now, we are adding the machine family itself as OrderItem.
        
        if st.button("Add Product/Family to Order", key="add_product_to_order_btn"):
            if selected_family_obj:
                item_description = st.text_input(f"Specific Model/Description for {selected_family_obj.name}",
                                                  key=f"desc_{selected_family_obj.id}")
                st.session_state.order_items_config.append({
                    "type": "machine_family",
                    "id": selected_family_obj.id,
                    "name": selected_family_obj.name,
                    "quantity": quantity,
                    "item_description": item_description,
                    "unit_price": selected_family_obj.price_per_unit # Assuming MachineFamily can have a base price
                                                                      # If not, you might need another field or remove
                })
                st.success(f"Added {quantity} x {selected_family_obj.name} to current order configuration.")
                # Reset selectbox and quantity after adding
                st.session_state.add_product_family_select = "-- Select Product/Family --"
                st.session_state.product_family_qty = 1
                st.experimental_rerun() # Rerun to clear inputs and show updated config
            else:
                st.warning("Please select a product/family to add.")

        st.markdown("---")

        # --- 3. Current Order Configuration ---
        st.subheader("3. Current Order Configuration")
        if st.session_state.order_items_config:
            df = pd.DataFrame(st.session_state.order_items_config)
            df['Total Item Price'] = df['quantity'] * df['unit_price']
            st.table(df[['name', 'item_description', 'quantity', 'unit_price', 'Total Item Price']])

            if st.button("Clear Order Configuration", key="clear_order_config_btn"):
                st.session_state.order_items_config = []
                st.experimental_rerun()
        else:
            st.info("No products/families added to this order yet.")

        st.markdown("---")

        # --- 4. Finalize Order ---
        st.subheader("4. Finalize Order")
        order_delivery_date = st.date_input("Expected Delivery Date", datetime.date.today() + datetime.timedelta(days=30))
        special_notes = st.text_area("Special Notes for Order")

        if st.button("Create Order", key="finalize_order_btn"):
            if not st.session_state.current_customer_id:
                st.error("Please select or add a customer first.")
            elif not st.session_state.order_items_config:
                st.error("Please add at least one product/family to the order.")
            else:
                try:
                    # Get the next order number (simple auto-increment logic)
                    last_order = db.query(Order).order_by(Order.order_number.desc()).first()
                    new_order_number = (last_order.order_number + 1) if last_order else 1

                    total_order_amount = sum(item['quantity'] * item['unit_price'] for item in st.session_state.order_items_config)

                    new_order = Order(
                        customer_id=st.session_state.current_customer_id,
                        order_number=new_order_number,
                        delivery_date=order_delivery_date,
                        total_amount=total_order_amount,
                        status="Draft", # Initial status
                        special_notes=special_notes,
                        created_by_user_id=None # Set to None as no login. Or get a 'system' user ID.
                    )
                    db.add(new_order)
                    db.flush() # Flush to get new_order.id before committing

                    # Add order items
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

                        # If you had accessories associated with the FamilyAccessory model,
                        # you'd add them here as OrderItemAccessory
                        # For now, let's assume they are handled separately or later.

                    # Add initial order status history
                    order_status_history = OrderStatusHistory(
                        order_id=new_order.id,
                        status="Draft",
                        user_id=None, # Or system user ID
                        notes="Order created"
                    )
                    db.add(order_status_history)

                    db.commit()
                    st.success(f"Order {new_order.generate_full_order_id()} created successfully!")
                    st.balloons()
                    # Clear session state for new order
                    st.session_state.order_items_config = []
                    st.session_state.current_customer_id = None
                    st.experimental_rerun() # Refresh page
                except Exception as e:
                    db.rollback() # Rollback on error
                    st.error(f"Error creating order: {e}")
    finally:
        db.close()


# --- Navigation (Sidebar) ---
st.sidebar.header("Navigation")

# Define pages dictionary (maps button text to function)
pages = {
    "Dashboard": show_dashboard,
    "Orders": lambda: st.write("Orders List Page (To be implemented)"), # Placeholder
    "Checklist": lambda: st.write("Checklist Page (To be implemented)"), # Placeholder
    "Product Families": lambda: st.write("Product Families Management (To be implemented)"), # Placeholder
    "Reports": lambda: st.write("Reports Page (To be implemented)"), # Placeholder
    "Create New Order": show_order_creation, # Your dedicated creation page
}

# Create buttons for navigation
for page_name, page_function in pages.items():
    if st.sidebar.button(page_name, key=f"nav_button_{page_name}"):
        st.session_state.current_page = page_name

# Display the selected page content
if st.session_state.current_page in pages:
    pages[st.session_state.current_page]()
else:
    # Fallback if current_page is somehow invalid
    show_dashboard()

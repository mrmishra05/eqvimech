# streamlit_app.py
import streamlit as st
from database import create_tables, get_db, initialize_master_data
from models import Customer, Order, MachineFamily, Accessory, FamilyAccessory, OrderItem, OrderItemAccessory, User, ProductionProcessStep
from sqlalchemy.orm import Session
from sqlalchemy import func
import datetime
import bcrypt # For password hashing

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

# --- Database Initialization (Run once on app startup or manually via admin) ---
# It's better to run create_tables() and initialize_master_data() once manually
# when you first set up your database, not on every app run.
# For simplicity in testing locally, you can uncomment it, but for production
# deployment, typically you'd do this via a separate script or database migration.

# with Session(get_db()) as db:
#     create_tables()
#     initialize_master_data(db)
#     st.success("Database tables created and master data initialized (if not already present).")


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
                create_tables()
                initialize_master_data(db)
                success, message = add_user(db, admin_username, admin_password, admin_full_name, admin_email, "Admin")
                if success:
                    st.success(message)
                else:
                    st.error(message)
                db.close()


def show_dashboard():
    st.title(f"Dashboard - Welcome, {st.session_state.username} ({st.session_state.role})")
    st.write("Overview of your orders, production progress, and inventory.")

    st.subheader("Active Orders")
    db = next(get_db())
    orders = db.query(Order).options(st.session_state.current_page.customer).order_by(Order.order_date.desc()).all()
    if orders:
        order_data = []
        for order in orders:
            # Calculate delay
            today = datetime.date.today()
            expected_date = order.expected_delivery_date.date() if order.expected_delivery_date else today
            delay_days = (today - expected_date).days if today > expected_date else 0
            delay_str = f"-{delay_days} days" if delay_days > 0 else "On Track"

            order_data.append({
                "Order ID": order.id,
                "Customer": order.customer.name,
                "Company": order.customer.company,
                "Order Date": order.order_date.strftime("%Y-%m-%d"),
                "Expected Delivery": order.expected_delivery_date.strftime("%Y-%m-%d") if order.expected_delivery_date else "N/A",
                "Status": order.overall_status,
                "Delay": delay_str
            })
        st.dataframe(order_data, use_container_width=True)
    else:
        st.info("No active orders found. Create a new order to get started!")
    db.close()

    st.subheader("Low Stock Alerts")
    db = next(get_db())
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
        st.dataframe(stock_data, use_container_width=True)
    else:
        st.success("All accessories are currently above minimum stock levels!")
    db.close()

def show_create_order_page():
    st.title("Create New Order")
    # Form for creating an order (will be detailed in next steps)
    st.info("This page will contain the form to create a new order, select customers, machines, and accessories.")
    st.write("Coming soon...")

def show_view_orders_page():
    st.title("View All Orders")
    st.info("This page will list all orders with filters and options to view details.")
    st.write("Coming soon...")

def show_inventory_page():
    st.title("Inventory Management")
    st.info("This page will show accessory catalog, stock levels, and allow stock movements.")
    st.write("Coming soon...")

def show_master_data_page():
    if st.session_state.role != "Admin":
        st.warning("You do not have permission to access this page.")
        return

    st.title("Master Data Management")
    st.info("This page allows Admin to manage Machine Families, Accessories, and Production Steps.")
    st.write("Coming soon...")

def show_reports_page():
    st.title("Reports")
    st.info("This page will provide various reports like production progress, delays, etc.")
    st.write("Coming soon...")

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

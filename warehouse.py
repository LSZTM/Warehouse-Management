import streamlit as st
import pandas as pd
import mysql.connector
import hashlib
import time
from datetime import datetime
import plotly.express as px

# MySQL Connection Details
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "root",
    "database": "warehouse_inventory_1"
}

# Database Functions
def get_db_connection():
    try:
        return mysql.connector.connect(**DB_CONFIG)
    except mysql.connector.Error as err:
        st.error(f"Database connection failed: {err}")
        return None

def init_db():
    conn = get_db_connection()
    if conn is None:
        return
        
    cursor = conn.cursor()
    tables = [
        """CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            password VARCHAR(100) NOT NULL,
            role VARCHAR(20) DEFAULT 'user',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""",
        """CREATE TABLE IF NOT EXISTS inventory (
            id INT AUTO_INCREMENT PRIMARY KEY,
            item_name VARCHAR(100) NOT NULL,
            description TEXT,
            category VARCHAR(50),
            stock INT NOT NULL,
            min_stock INT DEFAULT 5,
            price DECIMAL(10,2),
            supplier VARCHAR(100) NOT NULL,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        )""",
        """CREATE TABLE IF NOT EXISTS orders (
            order_id INT AUTO_INCREMENT PRIMARY KEY,
            item_id INT NOT NULL,
            item_name VARCHAR(100) NOT NULL,
            quantity INT NOT NULL,
            status ENUM('Pending', 'Processing', 'Shipped', 'Delivered') DEFAULT 'Pending',
            ordered_by VARCHAR(50),
            order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (item_id) REFERENCES inventory(id)
        )""",
        """CREATE TABLE IF NOT EXISTS suppliers (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            contact_person VARCHAR(100),
            email VARCHAR(100),
            phone VARCHAR(20),
            lead_time_days INT,
            rating INT
        )""",
        """CREATE TABLE IF NOT EXISTS activity_log (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT,
            action VARCHAR(100),
            details TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )"""
    ]
    
    for table in tables:
        cursor.execute(table)
    conn.commit()
    conn.close()

init_db()

# Utility Functions
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def log_activity(user_id, action, details=""):
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO activity_log (user_id, action, details)
            VALUES (%s, %s, %s)
        """, (user_id, action, details))
        conn.commit()
        conn.close()

def apply_custom_css_styles():
    """Applies custom CSS with vibrant blue background and larger buttons"""
    st.set_page_config(
        page_title="Warehouse Management System", 
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    st.markdown("""
                <style>
                    /* ----- Base Reset & Layout ----- */
                    #MainMenu, header, footer, .stDeployButton, #stDecoration {
                        visibility: hidden;
                        display: none !important;
                    }

                    /* ----- Vibrant Blue Background ----- */
                    .stApp {
                        background: linear-gradient(135deg, #0f1b3d 0%, #1a3a8f 100%) !important;
                        background-attachment: fixed;
                        color: #ffffff;
                        padding: 2rem 4rem;
                        min-height: 100vh;
                        transition: all 0.3s ease;
                    }

                    /* ----- Data Visualization Styling ----- */
                    .stDataFrame, table {
                        background-color: rgba(26, 32, 64, 0.7) !important;
                        color: white !important;
                        border-radius: 10px !important;
                        border: 1px solid #4e54c8 !important;
                    }

                    .stDataFrame th {
                        background-color: #4e54c8 !important;
                        color: white !important;
                        font-weight: bold !important;
                    }

                    .stDataFrame tr:nth-child(even) {
                        background-color: rgba(78, 84, 200, 0.2) !important;
                    }

                    .stDataFrame tr:hover {
                        background-color: rgba(142, 148, 251, 0.3) !important;
                    }

                    .stPlotlyChart {
                        background-color: rgba(26, 32, 64, 0.7) !important;
                        border-radius: 10px !important;
                        border: 1px solid #4e54c8 !important;
                        padding: 10px !important;
                    }

                    .stMetric {
                        background-color: rgba(26, 32, 64, 0.7) !important;
                        border-radius: 10px !important;
                        border: 1px solid #4e54c8 !important;
                        padding: 15px !important;
                    }

                    .stMetric label {
                        color: #8f94fb !important;
                        font-size: 1rem !important;
                    }

                    .stMetric div {
                        color: white !important;
                        font-size: 1.8rem !important;
                        font-weight: bold !important;
                    }

                    /* ----- Tabs Styling: Fixed underline and spacing ----- */
                    .stTabs [role="tablist"] {
                        background-color: rgba(26, 32, 64, 0.7) !important;
                        border-radius: 10px 10px 0 0 !important;
                        padding: 0 1rem !important;
                        display: flex !important;
                        flex-wrap: wrap;
                        gap: 0.5rem;
                    }

                    .stTabs [role="tab"] {
                        color: #8f94fb !important;
                        background-color: transparent !important;
                        font-size: 1rem !important;
                        padding: 0.75rem 1.5rem !important;
                        font-weight: 500;
                        white-space: nowrap;
                        border: none !important;
                        outline: none !important;
                        position: relative;
                        transition: all 0.3s ease-in-out;
                    }

                    .stTabs [role="tab"][aria-selected="true"] {
                        color: white !important;
                        background-color: transparent !important;
                        font-weight: 700;
                        border-bottom: none !important;
                        box-shadow: none !important;
                    }

                    

                    @media screen and (max-width: 768px) {
                        .stTabs [role="tab"] {
                            font-size: 0.9rem !important;
                            padding: 0.5rem 1rem !important;
                        }
                    }

                    /* ----- Input Widgets ----- */
                    .stTextInput input, .stTextArea textarea, .stNumberInput input,
                    .stSelectbox select, .stDateInput input {
                        background-color: rgba(26, 32, 64, 0.7) !important;
                        color: white !important;
                        border: 1px solid #4e54c8 !important;
                    }

                    /* ----- Loader Styling ----- */
                    .loader-container {
                        position: fixed;
                        top: 50%;
                        left: 50%;
                        transform: translate(-50%, -50%);
                        z-index: 9999;
                        background: rgba(26, 26, 46, 0.9);
                        width: 100vw;
                        height: 100vh;
                        display: flex;
                        justify-content: center;
                        align-items: center;
                    }

                    .loading svg polyline {
                        fill: none;
                        stroke-width: 3;
                        stroke-linecap: round;
                        stroke-linejoin: round;
                    }

                    .loading svg polyline#back {
                        stroke: #8f94fb33;
                    }

                    .loading svg polyline#front {
                        stroke: #4e54c8;
                        stroke-dasharray: 48, 144;
                        stroke-dashoffset: 192;
                        animation: dash_682 1.4s linear infinite;
                    }

                    @keyframes dash_682 {
                        72.5% { opacity: 0; }
                        to { stroke-dashoffset: 0; }
                    }

                    [data-testid="stSidebar"] {
                        z-index: 999 !important;
                    }

                    /* ----- Text Shadows for All Text ----- */
                    h1, h2, h3, h4, h5, h6, p, div, span, label {
                        text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3) !important;
                    }

                    /* ----- Animated Gradient Button ----- */
                    .stButton>button {
                        position: relative;
                        display: inline-flex !important;
                        align-items: center;
                        justify-content: center;
                        padding: 0.75em 2em !important;
                        font-size: 16px !important;
                        font-weight: 600 !important;
                        font-family: inherit;
                        color: #fff !important;
                        text-align: center;
                        text-decoration: none;
                        background: linear-gradient(270deg, #03a9f4, #f441a5, #ffeb3b, #03a9f4);
                        background-size: 600% 600%;
                        border: none !important;
                        border-radius: 30px !important;
                        cursor: pointer;
                        overflow: hidden;
                        z-index: 1;
                        transition: all 0.3s ease-in-out !important;
                        white-space: nowrap;
                    }

                    .stButton>button:hover {
                        animation: gradientMove 8s ease infinite !important;
                        transform: translateY(-3px);
                        box-shadow: 0 8px 20px rgba(255, 255, 255, 0.3);
                    }

                    @keyframes gradientMove {
                        0% { background-position: 0% 50%; }
                        50% { background-position: 100% 50%; }
                        100% { background-position: 0% 50%; }
                    }

                    .stButton>button::before {
                        content: "";
                        position: absolute;
                        top: -5px;
                        left: -5px;
                        right: -5px;
                        bottom: -5px;
                        z-index: -1;
                        background: inherit;
                        background-size: 600% 600%;
                        border-radius: 40px;
                        filter: blur(15px);
                        opacity: 0;
                        transition: opacity 0.3s ease;
                    }

                    .stButton>button:hover::before {
                        opacity: 1;
                    }

                    .stButton>button:active {
                        transform: scale(0.98);
                        box-shadow: 0 2px 4px rgba(0,0,0,0.2);
                    }

                    /* ----- Fancy H1 Styling ----- */
                    .stApp h1 {
                        text-align: center;
                        margin-bottom: 2rem;
                        font-weight: 700;
                        letter-spacing: 0.5px;
                        position: relative;
                        padding-bottom: 15px;
                        color: #ffffff !important;
                        text-shadow: 0 0 10px rgba(142, 148, 251, 0.7) !important;
                    }

                    .stApp h1:after {
                        content: "";
                        position: absolute;
                        bottom: 0;
                        left: 50%;
                        transform: translateX(-50%);
                        width: 100px;
                        height: 3px;
                        background: linear-gradient(90deg, #4e54c8 0%, #8f94fb 100%);
                        border-radius: 3px;
                        box-shadow: 0 2px 8px rgba(142, 148, 251, 0.6);
                    }

                    /* ----- Sidebar Styling ----- */
                    [data-testid="stSidebar"] {
                        background: linear-gradient(195deg, #0f1b3d 0%, #142a6b 100%) !important;
                        border-right: 1px solid #4e54c8 !important;
                        box-shadow: 8px 0 20px rgba(0,0,0,0.3) !important;
                    }
                </style>
                """, unsafe_allow_html=True)



def show_loader():
    """Displays animated loader with proper positioning on the main content"""
    st.markdown("""
    <div class="loader-container">
        <div class="loader-animation">
            <svg width="64px" height="48px">
                <polyline points="0.157 23.954, 14 23.954, 21.843 48, 43 0, 50 24, 64 24" 
                          id="back" stroke="#8f94fb33" fill="none" 
                          stroke-width="3" stroke-linecap="round" 
                          stroke-linejoin="round"></polyline>
                <polyline points="0.157 23.954, 14 23.954, 21.843 48, 43 0, 50 24, 64 24" 
                          id="front" stroke="#4e54c8" fill="none"
                          stroke-width="3" stroke-linecap="round"
                          stroke-linejoin="round" stroke-dasharray="48, 144"
                          stroke-dashoffset="192"></polyline>
            </svg>
        </div>
    </div>
    <style>
        @keyframes dash_682 {
            72.5% { opacity: 0; }
            to { stroke-dashoffset: 0; }
        }
        #front {
            animation: dash_682 1.4s linear infinite;
        }
    </style>
    """, unsafe_allow_html=True)
    st.empty()


def navigate_to(page):
    if st.session_state.current_page != page:
        st.session_state.current_page = page
        show_loader()
        time.sleep(0.5)
        st.rerun()

# Authentication Functions
def authenticate(username, password):
    conn = get_db_connection()
    if not conn:
        return False
        
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE username=%s AND password=%s", 
                  (username, hash_password(password)))
    user = cursor.fetchone()
    conn.close()
    
    if user:
        st.session_state.update({
            'authenticated': True,
            'user': user['username'],
            'user_id': user['id'],
            'user_role': user.get('role', 'user'),
            'current_page': 'Dashboard'
        })
        log_activity(user['id'], "Login")
        return True
    return False

def register_user(username, password, role='user'):
    conn = get_db_connection()
    if not conn:
        return False
        
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO users (username, password, role)
            VALUES (%s, %s, %s)
        """, (username, hash_password(password), role))
        user_id = cursor.lastrowid
        conn.commit()
        log_activity(user_id, "Account created")
        return True
    except mysql.connector.Error as err:
        st.error(f"Error: {err}")
        return False
    finally:
        conn.close()

# Page Components
def show_login():
    st.title("🔐 Login to Warehouse Management System")
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        
        if st.form_submit_button("Login"):
            if authenticate(username, password):
                st.success(f"Welcome {username}!")
                navigate_to("Dashboard")
            else:
                st.error("Invalid credentials")

    if st.button("Create New Account"):
        navigate_to("Signup")

def show_signup():
    st.title("🚀 Sign Up for Warehouse Management")
    with st.form("signup_form"):
        new_username = st.text_input("Username")
        new_password = st.text_input("Password", type="password")
        confirm_password = st.text_input("Confirm Password", type="password")
        role = st.selectbox("Role", ["user"], disabled=True)
        
        if st.form_submit_button("Register"):
            if new_password != confirm_password:
                st.error("Passwords don't match!")
            elif len(new_password) < 8:
                st.error("Password must be at least 8 characters")
            else:
                if register_user(new_username, new_password, role):
                    st.success("Account created successfully!")
                    time.sleep(1)
                    navigate_to("Login")

    if st.button("Back to Login"):
        navigate_to("Login")

def show_sidebar():
    with st.sidebar:
        st.image("https://via.placeholder.com/150x50?text=WIMS", width=150)
        st.title(f"Welcome, {st.session_state.user}")
        
        st.session_state.current_page_options = ["Dashboard", "Inventory", "Orders", "Suppliers", "Reports", "Settings"]
        if st.session_state.user_role == 'admin':
            st.session_state.current_page_options.append("User Management")
        
        st.session_state.current_page_selection = st.selectbox("Navigation", st.session_state.current_page_options, key='st.session_state.current_page_selection')
        
        if st.session_state.current_page_selection != st.session_state.current_page:
            navigate_to(st.session_state.current_page_selection)
        
        st.markdown("---")
        if st.button("Logout"):
            log_activity(st.session_state.user_id, "Logout")
            st.session_state.update({
                'authenticated': False,
                'user': None,
                'user_id': None,
                'user_role': None,
                'current_page': 'Login'
            })
            navigate_to("Login")
        
        st.markdown("---")
        st.caption(f"Role: {st.session_state.user_role}")
        st.caption(f"v1.2.0 | {datetime.now().strftime('%Y-%m-%d %H:%M')}")

# Main Content Functions
def show_dashboard():
    st.title("📊 Warehouse Dashboard")
    conn = get_db_connection()
    
    # Key Metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM inventory")
        total_items = int(cursor.fetchone()[0])  # Convert to int
        st.metric("Total Items", total_items)
    
    with col2:
        cursor.execute("SELECT COUNT(*) FROM orders WHERE status = 'Pending'")
        pending_orders = int(cursor.fetchone()[0])  # Convert to int
        st.metric("Pending Orders", pending_orders)
    
    with col3:
        cursor.execute("SELECT COUNT(DISTINCT supplier) FROM inventory")
        suppliers = int(cursor.fetchone()[0])  # Convert to int
        st.metric("Active Suppliers", suppliers)
    
    with col4:
        cursor.execute("SELECT SUM(stock) FROM inventory")
        total_stock = float(cursor.fetchone()[0])  # Convert to float
        st.metric("Total Stock Units", total_stock)
    
    # Charts Row
    st.markdown("---")
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Stock Levels by Category")
        cursor.execute("SELECT category, SUM(stock) as total FROM inventory GROUP BY category")
        stock_data = pd.DataFrame(cursor.fetchall(), columns=["Category", "Total"])
        
        if not stock_data.empty:
            stock_data["Total"] = stock_data["Total"].astype(float)
            
            # Create pie chart with dark theme styling
            fig = px.pie(
                stock_data, 
                values="Total", 
                names="Category", 
                hole=0.3,
                color_discrete_sequence=px.colors.qualitative.Pastel  # Bright colors that work on dark bg
            )
            
            # Apply dark theme formatting
            fig.update_layout(
                plot_bgcolor='rgba(26, 32, 64, 0.7)',  # Semi-transparent dark blue
                paper_bgcolor='rgba(26, 32, 64, 0.7)',  # Matches the table background
                font_color='white',
                legend=dict(
                    bgcolor='rgba(0,0,0,0.5)',  # Semi-transparent legend background
                    font=dict(color='white')
                ),
                hoverlabel=dict(
                    bgcolor='#4e54c8',  # Purple hover label
                    font=dict(color='white')
                ),
                margin=dict(t=30, b=30)  # Add some margin
            )
            
            # Make the pie chart edges smoother
            fig.update_traces(
                textposition='inside',
                textinfo='percent+label',
                marker=dict(line=dict(color='#1a1a2e', width=1)),  # Dark border for slices
                hoverinfo='label+percent+value',
                hovertemplate='<b>%{label}</b><br>%{percent}<br>Total: %{value}'
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
        else:
            st.info("No category data available")
    
    with col2:
        st.subheader("Recent Orders")
        cursor.execute("""
            SELECT o.item_name, o.quantity, o.order_date, o.status 
            FROM orders o
            ORDER BY o.order_date DESC LIMIT 10
        """)
        orders = pd.DataFrame(cursor.fetchall(), columns=["Item", "Quantity", "Date", "Status"])
        st.dataframe(orders, hide_index=True, use_container_width=True)
    
    # Low Stock Alerts
    st.markdown("---")
    st.subheader("⚠️ Low Stock Alerts")
    cursor.execute("SELECT item_name, stock, min_stock FROM inventory WHERE stock < min_stock")
    low_stock = pd.DataFrame(cursor.fetchall(), columns=["Item", "Current Stock", "Min Stock"])
    
    if not low_stock.empty:
        st.dataframe(low_stock, hide_index=True, use_container_width=True)
    else:
        st.success("All items are sufficiently stocked!")
    
    conn.close()

# Main Application
def main():
    apply_custom_css_styles()
    
    # Initialize session state
    if 'authenticated' not in st.session_state:
        st.session_state.update({
            'authenticated': False,
            'user': None,
            'user_id': None,
            'user_role': None,
            'current_page': 'Login',
            'st.session_state.current_page_selection': 'Dashboard'
        })

    # Page routing
    if not st.session_state.authenticated:
        if st.session_state.current_page == "Login":
            show_login()
        elif st.session_state.current_page == "Signup":
            show_signup()
    else:
        show_sidebar()
        
        st.markdown('<div class="page-transition">', unsafe_allow_html=True)
        
        if st.session_state.current_page == "Dashboard":
            show_dashboard()
        elif st.session_state.current_page == "Inventory":
            st.title("📦 Inventory Management")
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            
            tab1, tab2, tab3 = st.tabs(["View Inventory", "Add New Item", "Update Stock"])
            
            with tab1:
                st.subheader("Current Inventory")
                cursor.execute("SELECT * FROM inventory")
                inventory = pd.DataFrame(cursor.fetchall())
                
                if not inventory.empty:
                    st.dataframe(inventory, hide_index=True, use_container_width=True)
                    
                    # Export button
                    csv = inventory.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        "Export to CSV",
                        csv,
                        "inventory_report.csv",
                        "text/csv",
                        key='download-csv'
                    )
                else:
                    st.info("No inventory items found")
            
            with tab2:
                st.subheader("Add New Inventory Item")
                with st.form("add_item_form"):
                    item_name = st.text_input("Item Name*", placeholder="Enter item name")
                    description = st.text_area("Description", placeholder="Optional description")
                    category = st.text_input("Category", placeholder="e.g., Electronics, Furniture")
                    stock = st.number_input("Initial Stock*", min_value=0, value=10)
                    min_stock = st.number_input("Minimum Stock Level*", min_value=1, value=5)
                    price = st.number_input("Unit Price", min_value=0.0, value=0.0, step=0.01)
                    supplier = st.text_input("Supplier*", placeholder="Supplier name")
                    
                    if st.form_submit_button("Add Item"):
                        if item_name and supplier:
                            cursor.execute("""
                                INSERT INTO inventory 
                                (item_name, description, category, stock, min_stock, price, supplier)
                                VALUES (%s, %s, %s, %s, %s, %s, %s)
                            """, (item_name, description, category, stock, min_stock, price, supplier))
                            conn.commit()
                            log_activity(st.session_state.user_id, "Item added", f"Added {item_name}")
                            st.success(f"{item_name} added to inventory!")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error("Please fill required fields (*)")
            with tab3:
                if st.session_state.user_role in ['manager', 'admin']:
                    st.subheader("Update Order Status")
                    cursor.execute("SELECT order_id, item_name, quantity, status FROM orders")
                    orders = cursor.fetchall()
                    
                    if orders:
                        order_options = {f"Order #{order['order_id']} - {order['item_name']} x{order['quantity']}": order['order_id'] for order in orders}
                        selected_order = st.selectbox("Select Order", options=list(order_options.keys()))
                        order_id = order_options[selected_order]
                        
                        current_status = next(order['status'] for order in orders if order['order_id'] == order_id)
                        new_status = st.selectbox("Update Status", 
                                                ["Pending", "Processing", "Shipped", "Delivered"],
                                                index=["Pending", "Processing", "Shipped", "Delivered"].index(current_status))
                        
                        if st.button("Update Status") and new_status != current_status:
                            cursor.execute("UPDATE orders SET status = %s WHERE order_id = %s", (new_status, order_id))
                            conn.commit()
                            log_activity(st.session_state.user_id, "Order status updated", 
                                        f"Order #{order_id} from {current_status} to {new_status}")
                            st.success(f"Order #{order_id} status updated to {new_status}!")
                            time.sleep(1)
                            st.rerun()
                    else:
                        st.info("No orders available")
                else:
                    st.warning("You don't have permission to update order status")
            
            conn.close()
        elif st.session_state.current_page == "Suppliers":
        
            st.title("🏭 Supplier Management")
            
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            
            tab1, tab2 = st.tabs(["Supplier Directory", "Add Supplier"])
            
            with tab1:
                st.subheader("Supplier List")
                cursor.execute("SELECT * FROM suppliers")
                suppliers = pd.DataFrame(cursor.fetchall())
                
                if not suppliers.empty:
                    st.dataframe(suppliers, hide_index=True, use_container_width=True)
                else:
                    st.info("No suppliers found")
            
            with tab2:
                st.subheader("Add New Supplier")
                with st.form("add_supplier_form"):
                    name = st.text_input("Supplier Name*")
                    contact = st.text_input("Contact Person")
                    email = st.text_input("Email")
                    phone = st.text_input("Phone")
                    lead_time = st.number_input("Lead Time (days)", min_value=1, value=7)
                    rating = st.slider("Rating (1-5)", 1, 5, 3)
                    
                    if st.form_submit_button("Add Supplier"):
                        if name:
                            cursor.execute("""
                                INSERT INTO suppliers 
                                (name, contact_person, email, phone, lead_time_days, rating)
                                VALUES (%s, %s, %s, %s, %s, %s)
                            """, (name, contact, email, phone, lead_time, rating))
                            conn.commit()
                            log_activity(st.session_state.user_id, "Supplier added", f"Added {name}")
                            st.success(f"Supplier {name} added successfully!")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error("Supplier name is required")
            
            conn.close()
        elif st.session_state.current_page == "Orders":
        
            st.title("📝 Order Management")
            
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            
            tab1, tab2, tab3 = st.tabs(["New Order", "Order History", "Order Status"])
            
            with tab1:
                st.subheader("Place New Order")
                cursor.execute("SELECT id, item_name, stock FROM inventory")
                inventory_items = cursor.fetchall()
                
                if inventory_items:
                    item_options = {f"{item['item_name']} (Stock: {item['stock']})": item['id'] for item in inventory_items}
                    selected_item = st.selectbox("Select Item", options=list(item_options.keys()))
                    item_id = item_options[selected_item]
                    
                    current_stock = next(item['stock'] for item in inventory_items if item['id'] == item_id)
                    max_order = min(current_stock, 100)  # Limit large orders
                    
                    quantity = st.number_input("Quantity", min_value=1, max_value=max_order, value=1,
                                            help=f"Maximum available: {current_stock}")
                    
                    notes = st.text_area("Order Notes", placeholder="Special instructions or requirements")
                    
                    if st.button("Place Order"):
                        # Get item name
                        item_name = next(item['item_name'] for item in inventory_items if item['id'] == item_id)
                        
                        # Create order
                        cursor.execute("""
                            INSERT INTO orders (item_id, item_name, quantity, ordered_by, status)
                            VALUES (%s, %s, %s, %s, 'Pending')
                        """, (item_id, item_name, quantity, st.session_state.user))
                        
                        # Update inventory
                        new_stock = current_stock - quantity
                        cursor.execute("UPDATE inventory SET stock = %s WHERE id = %s", (new_stock, item_id))
                        
                        conn.commit()
                        log_activity(st.session_state.user_id, "Order placed", 
                                    f"Order for {quantity} {item_name}(s)")
                        st.success(f"Order placed for {quantity} {item_name}(s)!")
                        time.sleep(1)
                        st.rerun()
                else:
                    st.warning("No items available to order")
            
            with tab2:
                st.subheader("Order History")
                cursor.execute("""
                    SELECT o.order_id, o.item_name, o.quantity, o.status, o.order_date, o.ordered_by
                    FROM orders o
                    ORDER BY o.order_date DESC
                """)
                orders = pd.DataFrame(cursor.fetchall())
                
                if not orders.empty:
                    st.dataframe(orders, hide_index=True, use_container_width=True)
                else:
                    st.info("No orders found")
            
            with tab3:
                if st.session_state.user_role in ['manager', 'admin']:
                    st.subheader("Update Order Status")
                    cursor.execute("SELECT order_id, item_name, quantity, status FROM orders")
                    orders = cursor.fetchall()
                    
                    if orders:
                        order_options = {f"Order #{order['order_id']} - {order['item_name']} x{order['quantity']}": order['order_id'] for order in orders}
                        selected_order = st.selectbox("Select Order", options=list(order_options.keys()))
                        order_id = order_options[selected_order]
                        
                        current_status = next(order['status'] for order in orders if order['order_id'] == order_id)
                        new_status = st.selectbox("Update Status", 
                                                ["Pending", "Processing", "Shipped", "Delivered"],
                                                index=["Pending", "Processing", "Shipped", "Delivered"].index(current_status))
                        
                        if st.button("Update Status") and new_status != current_status:
                            cursor.execute("UPDATE orders SET status = %s WHERE order_id = %s", (new_status, order_id))
                            conn.commit()
                            log_activity(st.session_state.user_id, "Order status updated", 
                                        f"Order #{order_id} from {current_status} to {new_status}")
                            st.success(f"Order #{order_id} status updated to {new_status}!")
                            time.sleep(1)
                            st.rerun()
                    else:
                        st.info("No orders available")
                else:
                    st.warning("You don't have permission to update order status")
            
            conn.close()

    # Reports


    # Reports
        elif st.session_state.current_page == "Reports":
        
            st.title("📈 Reports & Analytics")
            
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            
            report_type = st.selectbox("Select Report", 
                                    ["Inventory Summary", "Order History", "Supplier Performance"])
            
            if report_type == "Inventory Summary":
                st.subheader("Inventory Summary Report")
                cursor.execute("""
                    SELECT category, COUNT(*) as item_count, 
                        SUM(stock) as total_stock, 
                        AVG(price) as avg_price
                    FROM inventory
                    GROUP BY category
                    ORDER BY total_stock DESC
                """)
                inventory_summary = pd.DataFrame(cursor.fetchall())
                
                if not inventory_summary.empty:
                    st.dataframe(inventory_summary, hide_index=True, use_container_width=True)
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.subheader("Stock by Category")
                        fig = px.bar(
                            inventory_summary, 
                            x="category", 
                            y="total_stock",
                            color="category",  # Color by category
                            color_discrete_sequence=px.colors.qualitative.Pastel,  # Bright colors
                            labels={'total_stock': 'Total Stock', 'category': 'Category'}  # Better axis labels
                        )
                        
                        # Apply dark theme formatting
                        fig.update_layout(
                            plot_bgcolor='rgba(26, 32, 64, 0.7)',
                            paper_bgcolor='rgba(26, 32, 64, 0.7)',
                            font_color='white',
                            xaxis=dict(
                                title_font=dict(size=14),
                                gridcolor='rgba(142, 148, 251, 0.2)',
                                showgrid=False  # Remove vertical grid lines
                            ),
                            yaxis=dict(
                                title_font=dict(size=14),
                                gridcolor='rgba(142, 148, 251, 0.2)',
                                showgrid=True
                            ),
                            legend=dict(
                                bgcolor='rgba(0,0,0,0.5)',
                                font=dict(color='white')
                            ),
                            hoverlabel=dict(
                                bgcolor='#4e54c8',
                                font=dict(color='white', size=12)
                            ),
                            margin=dict(t=40, b=40, l=40, r=40)  # Balanced margins
                        )
                        
                        # Customize bars
                        fig.update_traces(
                            marker_line_color='#1a1a2e',
                            marker_line_width=1.5,
                            opacity=0.9,
                            hovertemplate='<b>%{x}</b><br>Stock: %{y}'
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)

                    with col2:
                        st.subheader("Average Price by Category")
                        fig = px.pie(
                            inventory_summary, 
                            names="category", 
                            values="avg_price",
                            color_discrete_sequence=px.colors.qualitative.Pastel,
                            hole=0.3  # Add donut hole for modern look
                        )
                        
                        # Apply dark theme formatting
                        fig.update_layout(
                            plot_bgcolor='rgba(26, 32, 64, 0.7)',
                            paper_bgcolor='rgba(26, 32, 64, 0.7)',
                            font_color='white',
                            legend=dict(
                                bgcolor='rgba(0,0,0,0.5)',
                                font=dict(color='white'),
                                orientation='h',  # Horizontal legend
                                yanchor='bottom',
                                y=-0.2,
                                xanchor='center',
                                x=0.5
                            ),
                            hoverlabel=dict(
                                bgcolor='#4e54c8',
                                font=dict(color='white')
                            ),
                            margin=dict(t=40, b=40, l=40, r=40)
                        )
                        
                        # Customize pie slices
                        fig.update_traces(
                            textposition='inside',
                            textinfo='percent+label',
                            marker=dict(line=dict(color='#1a1a2e', width=1.5)),
                            hovertemplate='<b>%{label}</b><br>Avg Price: %{value:.2f}<br>%{percent}'
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No inventory data available")
            
            elif report_type == "Order History":
                st.subheader("Order History Report")
                
                date_range = st.date_input("Select Date Range", [], key="order_history_date_range")
                
                if len(date_range) == 2:
                    start_date, end_date = date_range
                    cursor.execute("""
                        SELECT DATE(order_date) as day, 
                            COUNT(*) as order_count,
                            SUM(quantity) as total_items
                        FROM orders
                        WHERE DATE(order_date) BETWEEN %s AND %s
                        GROUP BY DATE(order_date)
                        ORDER BY day
                    """, (start_date, end_date))
                    
                    order_history = pd.DataFrame(cursor.fetchall(), columns=["day", "order_count", "total_items"])
                    
                    if not order_history.empty:
                        # Style the dataframe
                        st.dataframe(
                            order_history.style
                            .background_gradient(cmap='Blues', subset=['order_count', 'total_items'])
                            .format({'order_count': '{:,.0f}', 'total_items': '{:,.0f}'}),
                            hide_index=True,
                            use_container_width=True
                        )
                        
                        # Create line chart with dark theme
                        fig = px.line(
                            order_history, 
                            x="day", 
                            y="order_count",
                            title="Daily Order Trends",
                            labels={'day': 'Date', 'order_count': 'Number of Orders'},
                            color_discrete_sequence=['#8f94fb']  # Use your theme color
                        )
                        
                        # Apply dark theme formatting
                        fig.update_layout(
                            plot_bgcolor='rgba(26, 32, 64, 0.7)',
                            paper_bgcolor='rgba(26, 32, 64, 0.7)',
                            font_color='white',
                            xaxis=dict(
                                gridcolor='rgba(142, 148, 251, 0.2)',
                                showgrid=True,
                                title_font=dict(size=14)
                            ),
                            yaxis=dict(
                                gridcolor='rgba(142, 148, 251, 0.2)',
                                showgrid=True,
                                title_font=dict(size=14)
                            ),
                            hoverlabel=dict(
                                bgcolor='#4e54c8',
                                font=dict(color='white')
                            ),
                            title_font=dict(size=18),
                            margin=dict(t=40, b=40, l=40, r=40)
                        )
                        
                        # Customize line appearance
                        fig.update_traces(
                            line=dict(width=3),
                            mode='lines+markers',
                            marker=dict(size=8, line=dict(width=1, color='#1a1a2e')),
                            hovertemplate='<b>%{x|%b %d}</b><br>Orders: %{y}'
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # Add secondary chart for items ordered
                        fig_items = px.area(
                            order_history,
                            x="day",
                            y="total_items",
                            title="Total Items Ordered",
                            labels={'day': 'Date', 'total_items': 'Items Ordered'},
                            color_discrete_sequence=['#4e54c8']  # Use your theme color
                        )
                        
                        fig_items.update_layout(
                            plot_bgcolor='rgba(26, 32, 64, 0.7)',
                            paper_bgcolor='rgba(26, 32, 64, 0.7)',
                            font_color='white',
                            hoverlabel=dict(bgcolor='#4e54c8')
                        )
                        
                        st.plotly_chart(fig_items, use_container_width=True)
                    else:
                        st.info("No orders found in selected date range")

            elif report_type == "Supplier Performance":
                st.subheader("Supplier Performance Report")
                cursor.execute("""
                    SELECT s.name, 
                        COUNT(i.id) as item_count,
                        AVG(s.lead_time_days) as avg_lead_time,
                        s.rating
                    FROM suppliers s
                    LEFT JOIN inventory i ON s.name = i.supplier
                    GROUP BY s.name, s.rating
                    ORDER BY s.rating DESC
                """)
                
                supplier_performance = pd.DataFrame(cursor.fetchall(), 
                                                columns=["name", "item_count", "avg_lead_time", "rating"])
                
                if not supplier_performance.empty:
                    # Style the dataframe with conditional formatting
                    st.dataframe(
                        supplier_performance.style
                        .background_gradient(cmap='YlGnBu', subset=['rating'])
                        .format({'avg_lead_time': '{:,.1f} days', 'rating': '{:,.1f}'}),
                        hide_index=True,
                        use_container_width=True
                    )
                    
                    # Create bubble chart with dark theme
                    fig = px.scatter(
                        supplier_performance, 
                        x="avg_lead_time", 
                        y="rating",
                        size="item_count",
                        color="name",
                        title="Supplier Rating vs Lead Time",
                        labels={
                            'avg_lead_time': 'Average Lead Time (days)',
                            'rating': 'Supplier Rating',
                            'item_count': 'Items Supplied',
                            'name': 'Supplier'
                        },
                        color_discrete_sequence=px.colors.qualitative.Pastel,
                        size_max=40  # Control bubble size
                    )
                    
                    # Apply dark theme formatting
                    fig.update_layout(
                        plot_bgcolor='rgba(26, 32, 64, 0.7)',
                        paper_bgcolor='rgba(26, 32, 64, 0.7)',
                        font_color='white',
                        xaxis=dict(
                            gridcolor='rgba(142, 148, 251, 0.2)',
                            showgrid=True
                        ),
                        yaxis=dict(
                            gridcolor='rgba(142, 148, 251, 0.2)',
                            showgrid=True,
                            range=[0,5.5]  # Fixed scale for ratings
                        ),
                        legend=dict(
                            bgcolor='rgba(0,0,0,0.5)',
                            font=dict(color='white')
                        ),
                        hoverlabel=dict(
                            bgcolor='#4e54c8',
                            font=dict(color='white')
                        ),
                        margin=dict(t=40, b=40, l=40, r=40)
                    )
                    
                    # Customize markers
                    fig.update_traces(
                        marker=dict(
                            line=dict(width=1, color='#1a1a2e'),
                            opacity=0.8
                        ),
                        hovertemplate='<b>%{customdata[0]}</b><br>'
                                    'Lead Time: %{x:.1f} days<br>'
                                    'Rating: %{y:.1f}/5<br>'
                                    'Items: %{marker.size}'
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Add bar chart for quick comparison
                    fig_bar = px.bar(
                        supplier_performance.sort_values('rating', ascending=False),
                        x='name',
                        y='rating',
                        color='name',
                        title='Supplier Ratings',
                        color_discrete_sequence=px.colors.qualitative.Pastel
                    )
                    
                    fig_bar.update_layout(
                        plot_bgcolor='rgba(26, 32, 64, 0.7)',
                        paper_bgcolor='rgba(26, 32, 64, 0.7)',
                        font_color='white',
                        xaxis_title='',
                        yaxis_range=[0,5]
                    )
                    
                    st.plotly_chart(fig_bar, use_container_width=True)
                else:
                    st.info("No supplier data available")

            conn.close()

    # Settings
        elif st.session_state.current_page == "Settings":
       
            st.title("⚙️ Settings")
            
            tab1, tab2 = st.tabs(["Profile", "System"])
            
            with tab1:
                st.subheader("User Profile")
                
                conn = get_db_connection()
                cursor = conn.cursor(dictionary=True)
                cursor.execute("SELECT * FROM users WHERE id = %s", (st.session_state.user_id,))
                user = cursor.fetchone()
                
                if user:
                    with st.form("profile_form"):
                        st.text_input("Username", value=user['username'], disabled=True)
                        st.text_input("Role", value=user.get('role', 'user'), disabled=True)
                        
                        new_password = st.text_input("New Password", type="password")
                        confirm_password = st.text_input("Confirm Password", type="password")
                        
                        if st.form_submit_button("Update Password"):
                            if new_password and new_password == confirm_password:
                                if len(new_password) >= 8:
                                    cursor.execute("""
                                        UPDATE users 
                                        SET password = %s 
                                        WHERE id = %s
                                    """, (hash_password(new_password), st.session_state.user_id))
                                    conn.commit()
                                    log_activity(st.session_state.user_id, "Password changed")
                                    st.success("Password updated successfully!")
                                else:
                                    st.error("Password must be at least 8 characters")
                            else:
                                st.error("Passwords don't match or are empty")
                
                conn.close()
            
            with tab2:
                if st.session_state.user_role == 'admin':
                    st.subheader("System Settings")
                    
                    # Placeholder for system settings
                    st.info("System configuration options will appear here")
                else:
                    st.warning("You don't have permission to access system settings")

        # User Management (Admin only)
        elif st.session_state.current_page == "User Management" and st.session_state.user_role == 'admin':
            
            st.title("👥 User Management")
            
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            
            tab1, tab2 = st.tabs(["User List", "Add User"])
            
            with tab1:
                st.subheader("Registered Users")
                cursor.execute("SELECT id, username, role, created_at FROM users")
                users = pd.DataFrame(cursor.fetchall())
                
                if not users.empty:
                    st.dataframe(users, hide_index=True, use_container_width=True)
                else:
                    st.info("No users found")
            
            with tab2:
                st.subheader("Create New User")
                with st.form("create_user_form"):
                    username = st.text_input("Username*")
                    password = st.text_input("Password*", type="password")
                    role = st.selectbox("Role*", ["user", "manager", "admin"])
                    
                    if st.form_submit_button("Create User"):
                        if username and password:
                            if len(password) >= 8:
                                if register_user(username, password, role):
                                    st.success(f"User {username} created with {role} role!")
                                    time.sleep(1)
                                    st.rerun()
                                else:
                                    st.error("Username already exists")
                            else:
                                st.error("Password must be at least 8 characters")
                        else:
                            st.error("Please fill all required fields (*)")
            
            conn.close()    
            # Add other pages similarly
            
            st.markdown("</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
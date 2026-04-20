import streamlit as st
import pandas as pd
import app_helpers


def init_session():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
        st.session_state.guest = False
        st.session_state.user_email = ""
        st.session_state.user_name = ""
        st.session_state.history = pd.DataFrame()
        st.session_state.login_error = ""
        st.session_state.just_signed_out = False


def clear_session(preserve_logout: bool = False):
    st.session_state.authenticated = False
    st.session_state.guest = False
    st.session_state.user_email = ""
    st.session_state.user_name = ""
    st.session_state.history = pd.DataFrame()
    st.session_state.login_error = ""
    st.session_state.just_signed_out = preserve_logout


def sign_in_user(email: str, guest: bool = False):
    st.session_state.authenticated = True
    st.session_state.guest = guest
    st.session_state.user_email = "guest" if guest else app_helpers.normalize_email(email)
    st.session_state.user_name = "Guest" if guest else app_helpers.normalize_email(email)
    st.session_state.history = pd.DataFrame() if guest else app_helpers.load_history(st.session_state.user_email)
    st.session_state.login_error = ""
    st.session_state.just_signed_out = False


def get_welcome_message() -> str:
    if st.session_state.guest:
        return "Welcome, Guest! Run a one-time health assessment and download your report."
    if not st.session_state.history.empty:
        return f"Welcome back, {st.session_state.user_email}! Your health history is ready."
    return f"Welcome, {st.session_state.user_email}! Start your first assessment to generate a personalized report."


def show_welcome_banner():
    message = get_welcome_message()
    st.markdown(
        f"""
        <div class='status-banner'>
            <strong>{message}</strong>
        </div>
        """,
        unsafe_allow_html=True,
    )


def show_error_modal():
    pass


def show_login_page():
    st.markdown("# 🔐 Secure Login")
    st.markdown("""
    <div class='card login-card'>
        <h3>Sign in to access your saved health history</h3>
        <p>Use your email and password to load your past reports. Or continue as a guest for a one-time assessment.</p>
    </div>
    """, unsafe_allow_html=True)

    email = st.text_input("Email", value="", placeholder="name@example.com")
    password = st.text_input("Password", type="password", value="", placeholder="Enter your password")

    error_placeholder = st.empty()

    col1, col2 = st.columns([1, 1])
    login_clicked = col1.button("Sign In", type="primary", key="login_btn")
    register_clicked = col2.button("Create Account", type="secondary", key="register_btn")

    guest_col, help_col = st.columns([1, 1])
    guest_clicked = guest_col.button("Continue as Guest", key="guest_btn")
    help_col.markdown("""
    <div class='card login-card'>
        <h4>Quick access</h4>
        <ul>
            <li><strong>Saved history:</strong> loads automatically after login</li>
            <li><strong>Guest mode:</strong> one-time access without saving data</li>
            <li><strong>Secure storage:</strong> passwords are hashed locally</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

    if login_clicked:
        if not email and not password:
            st.session_state.login_error = "Please enter your email address and password to sign in."
        elif not email:
            st.session_state.login_error = "Please enter your email address."
        elif not password:
            st.session_state.login_error = "Please enter your password."
        elif app_helpers.authenticate_user(email, password):
            sign_in_user(email)
            st.success("You are signed in successfully.")
            st.session_state.login_error = ""
            st.rerun()
        elif app_helpers.user_exists(email):
            st.session_state.login_error = "Incorrect password. Please try again."
        else:
            st.session_state.login_error = "No account found. Click Create Account to register."

    if register_clicked:
        if not email and not password:
            st.session_state.login_error = "Please enter an email address and password to create your account."
        elif not email:
            st.session_state.login_error = "Please enter a valid email address."
        elif not password:
            st.session_state.login_error = "Please enter a password for your account."
        elif app_helpers.user_exists(email):
            st.session_state.login_error = "This email is already registered. Please sign in."
        else:
            app_helpers.register_user(email, password)
            sign_in_user(email)
            st.success("Account created and signed in successfully.")
            st.session_state.login_error = ""
            st.rerun()

    if guest_clicked:
        sign_in_user("guest", guest=True)
        st.success("Continuing as guest. Your session will not be saved.")
        st.session_state.login_error = ""
        st.rerun()

    if st.session_state.login_error:
        error_placeholder.error(st.session_state.login_error)

    if st.session_state.just_signed_out:
        st.success("You have signed out successfully. See you again soon!")
        st.session_state.just_signed_out = False


st.markdown("""
<style>
html, body, [class*="css"]  {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    background-color: #f8f9fa;
    color: #333;
}

h1 {
    font-size: 42px !important;
    font-weight: 800;
    color: #2c3e50;
    text-align: center;
    margin-bottom: 20px;
}

h2 {
    font-size: 30px !important;
    font-weight: 700;
    color: #34495e;
}

h3 {
    font-size: 22px !important;
    font-weight: 600;
    color: #2c3e50;
}

.stMetric {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border-radius: 12px;
    padding: 15px;
    color: white;
    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
}

.stButton>button {
    background-color: #3498db;
    color: white;
    border: none;
    border-radius: 8px;
    padding: 10px 20px;
    font-size: 16px;
    cursor: pointer;
    transition: background-color 0.3s;
}

.stButton>button:hover {
    background-color: #2980b9;
}

.stTextInput>div>div>input, .stNumberInput>div>div>input, .stSelectbox>div>div>select {
    border-radius: 8px;
    border: 1px solid #ddd;
    padding: 10px;
}

.stSidebar {
    background-color: #2c3e50;
    color: white;
}

.stSidebar .stMarkdown h1, .stSidebar .stMarkdown h2, .stSidebar .stMarkdown h3 {
    color: white;
}

[data-testid="stSidebarNav"] {
    background-color: #34495e;
    position: relative;
    padding-top: 72px;
}

[data-testid="stSidebarNav"]::before {
    content: "CLINIXA AI";
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    text-align: center;
    font-size: 28px;
    font-weight: 800;
    color: #ffffff;
    padding: 18px 0 12px 0;
    border-bottom: 1px solid rgba(255,255,255,0.18);
}

[data-testid="stSidebarNav"] * {
    font-size: 18px !important;
    font-weight: 600 !important;
}

.card {
    background: white;
    color: #2c3e50;
    border-radius: 12px;
    padding: 20px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    margin-bottom: 20px;
}

.card h3,
.card p,
.card ul,
.card li {
    color: #2c3e50;
}

.card ul {
    padding-left: 18px;
}

.card li {
    margin-bottom: 8px;
}

.disclaimer-card {
    border: 3px solid #e74c3c;
    background: #fff7f7;
}

.feature-card {
    background: #fffef7;
    border: 1px solid #f1c40f;
}

.login-card {
    background: white;
    border: 1px solid #d8d8d8;
    border-radius: 16px;
    padding: 24px;
    box-shadow: 0 12px 28px rgba(0,0,0,0.08);
    margin-bottom: 20px;
}

.login-card h3,
.login-card h4,
.login-card p,
.login-card li {
    color: #2c3e50;
}

.login-card ul {
    padding-left: 18px;
}

.status-banner {
    background: #e8f5ff;
    border: 1px solid #b3d8ff;
    color: #1f497d;
    border-radius: 14px;
    padding: 18px 22px;
    margin-bottom: 24px;
    font-size: 16px;
}

.info-box {
    background: linear-gradient(135deg, #74b9ff 0%, #0984e3 100%);
    color: white;
    padding: 20px;
    border-radius: 12px;
    margin: 20px 0;
}

.info-box h3,
.info-box p,
.info-box ul,
.info-box li {
    color: white;
}

@keyframes fadeIn {
    from { opacity: 0; transform: translateY(-10px); }
    to { opacity: 1; transform: translateY(0); }
}

/* Responsive Modal Styles */
@media (max-width: 768px) {
    /* Tablet and mobile styles */
    .stButton > button {
        font-size: 16px !important; /* Prevent zoom on iOS */
        padding: 12px 20px !important;
        min-height: 44px !important; /* Minimum touch target */
        border-radius: 8px !important;
    }

    /* Ensure modal content is readable on small screens */
    .stMarkdown p {
        font-size: 16px !important;
        line-height: 1.4 !important;
    }
}

@media (max-width: 480px) {
    /* Small mobile styles */
    .stButton > button {
        font-size: 16px !important;
        padding: 14px 24px !important;
        min-height: 48px !important; /* Larger touch target for small screens */
        width: 100% !important; /* Full width button */
    }

    /* Adjust column layout for very small screens */
    .stColumns {
        gap: 0.5rem !important;
    }
}

@media (min-width: 769px) {
    /* Desktop styles */
    .stButton > button {
        font-size: 14px !important;
        padding: 10px 24px !important;
        min-height: 40px !important;
    }
}
</style>
""", unsafe_allow_html=True)

st.set_page_config(
    page_title="Clinixa AI",
    layout="wide",
    page_icon="🏥",
    initial_sidebar_state="expanded"
)

init_session()

if st.session_state.authenticated:
    st.sidebar.markdown(
        f"<div style='text-align:center; padding:14px 0; color:#ffffff;'>"
        f"<strong>{'Guest User' if st.session_state.guest else st.session_state.user_email}</strong>"
        f"</div>",
        unsafe_allow_html=True
    )
    if st.sidebar.button("Sign Out", type="secondary"):
        clear_session(preserve_logout=True)
        st.rerun()
else:
    show_login_page()
    st.stop()

show_welcome_banner()

pg = st.navigation([
    st.Page("pages/1_Home.py", title="Home", icon="🏠"),
    st.Page("pages/2_Prediction.py", title="Health Assessment", icon="📊"),
    st.Page("pages/3_History.py", title="History", icon="📈"),
])

pg.run()
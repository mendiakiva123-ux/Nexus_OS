import streamlit as st
from streamlit_option_menu import option_menu
import datetime

# --- 1. הגדרות מערכת ---
st.set_page_config(page_title="Nexus OS | Multi-Device Access", layout="wide")

# --- 2. ניהול משתמשים (10 קודים) ---
# הזיכרון הזה הוא פר-מכשיר, לכן תצטרך להקיש את הקוד פעם אחת בכל מכשיר
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_name = ""

# מילון המשתמשים - הקודים שלך
USER_REGISTRY = {
    "mendi2026": "Mendi Akiva",  # הקוד האישי שלך
    "nexus02": "User Two",
    "nexus03": "User Three",
    "nexus04": "User Four",
    "nexus05": "User Five",
    "nexus06": "User Six",
    "nexus07": "User Seven",
    "nexus08": "User Eight",
    "nexus09": "User Nine",
    "nexus10": "User Ten"
}

# --- 3. מסך התחברות יוקרתי ---
def login_screen():
    st.markdown("""
        <style>
        .login-container {
            text-align: center;
            padding: 40px;
            background: rgba(255, 255, 255, 0.05);
            border-radius: 20px;
            border: 1px solid #00D1FF;
            backdrop-filter: blur(15px);
            margin: auto;
            max-width: 500px;
            margin-top: 50px;
        }
        [data-testid="stAppViewContainer"] {
            background: linear-gradient(rgba(0, 0, 0, 0.8), rgba(0, 0, 0, 0.8)), 
                        url('https://images.unsplash.com/photo-1507842217343-583bb7270b66?auto=format&fit=crop&w=1920&q=80') !important;
            background-size: cover !important;
        }
        </style>
    """, unsafe_allow_html=True)
    
    st.markdown("<div class='login-container'>", unsafe_allow_html=True)
    st.markdown("<h1 style='color: #00D1FF;'>NEXUS OS</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color: white;'>Enter your access code to unlock the system</p>", unsafe_allow_html=True)
    
    # שימוש ב-key כדי למנוע התנגשויות
    input_code = st.text_input("Access Code", type="password", key="login_input")
    
    if st.button("Unlock System", use_container_width=True):
        if input_code in USER_REGISTRY:
            st.session_state.logged_in = True
            st.session_state.user_name = USER_REGISTRY[input_code]
            st.rerun()
        else:
            st.error("❌ Invalid Code. Please try again.")
    st.markdown("</div>", unsafe_allow_html=True)

# בדיקה: אם לא מחובר, מציג מסך לוגין ועוצר
if not st.session_state.logged_in:
    login_screen()
    st.stop()

# --- 4. אם מחובר - הצגת האפליקציה ---
st.markdown("""
    <style>
    .stApp { background-color: #0f172a; }
    h1, h2, h3, p, span { color: white !important; }
    </style>
    """, unsafe_allow_html=True)

with st.sidebar:
    st.markdown(f"<h3 style='text-align: center; color: #00D1FF;'>{st.session_state.user_name}</h3>", unsafe_allow_html=True)
    selected = option_menu(
        "Nexus Menu", ["Dashboard", "AI Tutor", "Settings"], 
        icons=["house", "robot", "gear"], default_index=0
    )
    if st.button("Logout"):
        st.session_state.logged_in = False
        st.rerun()

if selected == "Dashboard":
    st.title(f"🚀 Welcome back, {st.session_state.user_name}")
    st.info("System is synced across all your devices.")
    
elif selected == "AI Tutor":
    st.title("🤖 Nexus AI Tutor")
    st.write("Ready for your questions...")

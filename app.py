import streamlit as st
from streamlit_option_menu import option_menu
import datetime

# --- 1. הגדרות מערכת ---
st.set_page_config(page_title="Nexus OS | Multi-Language", layout="wide")

# --- 2. ניהול משתמשים ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_name = ""

# אתחול שפה בזיכרון
if 'lang' not in st.session_state:
    st.session_state.lang = "עברית"

USER_REGISTRY = {
    "mendi2026": "Mendi Akiva",
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

# --- 3. מסך התחברות ---
def login_screen():
    st.markdown("""
        <style>
        .login-container {
            text-align: center;
            padding: 50px;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 15px;
            border: 1px solid #00D1FF;
            backdrop-filter: blur(10px);
            margin-top: 100px;
        }
        </style>
    """, unsafe_allow_html=True)
    
    st.markdown("<div class='login-container'>", unsafe_allow_html=True)
    st.title("🔐 NEXUS OS SECURE ACCESS")
    input_code = st.text_input("Access Code", type="password")
    
    if st.button("Unlock System"):
        if input_code in USER_REGISTRY:
            st.session_state.logged_in = True
            st.session_state.user_name = USER_REGISTRY[input_code]
            st.rerun()
        else:
            st.error("❌ Invalid Code.")
    st.markdown("</div>", unsafe_allow_html=True)

if not st.session_state.logged_in:
    login_screen()
    st.stop()

# --- 4. עיצוב CSS (כולל צבע חיצים לבן) ---
st.markdown("""
    <style>
    .stApp { background: #0f172a; color: white; }
    button[data-testid="sidebar-button"] svg { fill: white !important; color: white !important; }
    h1, h2, h3, p, span, label { color: white !important; }
    /* עיצוב כפתור בחירת שפה */
    div[data-testid="stWidgetLabel"] p { color: #00D1FF !important; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- 5. סיידבר עם בחירת שפה ---
with st.sidebar:
    st.markdown(f"<h2 style='text-align: center; color: #00D1FF;'>{st.session_state.user_name}</h2>", unsafe_allow_html=True)
    
    # --- כאן נמצא שינוי השפה שביקשת! ---
    lang_choice = st.radio("Language / שפה", ["עברית", "English"], 
                          index=0 if st.session_state.lang == "עברית" else 1,
                          horizontal=True)
    
    if lang_choice != st.session_state.lang:
        st.session_state.lang = lang_choice
        st.rerun()
    
    st.divider()
    
    selected = option_menu(
        menu_title=None,
        options=["Dashboard", "Subjects", "AI Tutor", "Settings"],
        icons=["house", "book", "robot", "gear"],
        styles={
            "container": {"background-color": "#0f172a"},
            "nav-link": {"color": "white", "text-align": "left"},
            "nav-link-selected": {"background-color": "#00D1FF", "color": "black"}
        }
    )
    
    st.divider()
    if st.button("Logout"):
        st.session_state.logged_in = False
        st.rerun()

# --- 6. תוכן הדפים ---
if selected == "Dashboard":
    welcome_text = "ברוך הבא" if st.session_state.lang == "עברית" else "Welcome"
    st.title(f"🚀 {welcome_text}, {st.session_state.user_name}")
    st.write(f"System Language: {st.session_state.lang}")

else:
    st.title(selected)
    st.write("Content coming soon...")

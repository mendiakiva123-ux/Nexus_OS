import streamlit as st
from streamlit_option_menu import option_menu
import datetime

# --- 1. הגדרות מערכת ---
st.set_page_config(page_title="Nexus OS | Multi-User Edition", layout="wide")

# --- 2. ניהול משתמשים ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_name = ""

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
    st.subheader("Please enter your private access code")
    
    input_code = st.text_input("Access Code", type="password")
    
    if st.button("Unlock System"):
        if input_code in USER_REGISTRY:
            st.session_state.logged_in = True
            st.session_state.user_name = USER_REGISTRY[input_code]
            st.rerun()
        else:
            st.error("❌ Invalid Code. Access Denied.")
    st.markdown("</div>", unsafe_allow_html=True)

if not st.session_state.logged_in:
    login_screen()
    st.stop()

# --- 4. עיצוב ו-CSS משופר (צבע חיצים וטקסט) ---
st.markdown("""
    <style>
    /* רקע כללי */
    .stApp { background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); color: white; }
    
    /* הפיכת החיצים (Sidebar Arrows) ללבן */
    button[data-testid="sidebar-button"] svg {
        fill: white !important;
        color: white !important;
    }
    
    /* צבע טקסט כללי בתוך הסיידבר */
    section[data-testid="stSidebar"] span, section[data-testid="stSidebar"] p {
        color: white !important;
    }

    /* תיקון צבע הכותרות */
    h1, h2, h3, p { color: white !important; }
    
    /* עיצוב כפתור ה-Logout */
    .stButton>button {
        color: white !important;
        border-color: #00D1FF !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 5. תפריט ניווט בסיידבר ---
with st.sidebar:
    st.markdown(f"<h3 style='text-align: center; color: #00D1FF;'>Hello, {st.session_state.user_name}</h3>", unsafe_allow_html=True)
    st.divider()
    
    selected = option_menu(
        menu_title="Nexus OS Menu",
        options=["Dashboard", "Subjects", "AI Tutor", "Files", "Settings"],
        icons=["house", "book", "robot", "folder", "gear"],
        default_index=0,
        styles={
            "container": {"padding": "5px!", "background-color": "#0f172a", "border": "1px solid #1e293b"},
            "icon": {"color": "#00D1FF", "font-size": "20px"}, 
            "nav-link": {
                "font-size": "16px", 
                "text-align": "left", 
                "margin":"0px", 
                "--hover-color": "#1e293b",
                "color": "white"  # <--- טקסט לבן בתוך התפריט
            },
            "nav-link-selected": {
                "background-color": "#00D1FF", 
                "color": "black", # טקסט שחור רק כשנבחר (בשביל הניגודיות)
                "font-weight": "bold"
            },
        }
    )
    
    st.divider()
    if st.button("🚪 Logout", use_container_width=True):
        st.session_state.logged_in = False
        st.rerun()

# --- 6. לוגיקת דפים ---
if selected == "Dashboard":
    st.title(f"🚀 Dashboard: Welcome, {st.session_state.user_name}")
    st.write(f"Status: **Encrypted & Online** | Date: {datetime.date.today()}")

    c1, c2, c3 = st.columns(3)
    c1.metric("System Load", "Minimal", "Stable")
    c2.metric("Security Level", "Alpha", "Locked")
    c3.metric("User Access", "Authorized", f"{st.session_state.user_name}")
    
    st.divider()
    st.info("Your academic personal assistant is ready to work.")

elif selected == "Subjects":
    st.title("📚 Course Inventory")
    st.write("Displaying personal curriculum...")

elif selected == "AI Tutor":
    st.title("🤖 Nexus AI Assistant")
    user_q = st.chat_input(f"Ask me anything, {st.session_state.user_name}...")
    if user_q:
        with st.chat_message("user"):
            st.markdown(user_q)
        with st.chat_message("assistant"):
            st.write("I am processing your request using the Gemini Intelligence Engine...")

elif selected == "Settings":
    st.title("⚙️ System Settings")
    st.write(f"Logged in as: **{st.session_state.user_name}**")
    st.write("System Language: Hebrew/English")

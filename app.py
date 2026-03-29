import streamlit as st
from streamlit_option_menu import option_menu
import pandas as pd
import plotly.express as px
import os
import datetime
from database_manager import init_db, save_grade, get_all_grades, clear_db
from ai_manager import process_file_to_db, get_ai_response_stream

# --- 1. הגדרות מערכת (שיפור מהירות) ---
st.set_page_config(page_title="Nexus OS | Elite", layout="wide", initial_sidebar_state="collapsed")
init_db()

if not os.path.exists("ai_data/uploads"):
    os.makedirs("ai_data/uploads", exist_ok=True)

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

# --- 3. מסך התחברות יוקרתי ---
def login_screen():
    st.markdown("""
        <style>
        [data-testid="stAppViewContainer"] {
            background: linear-gradient(rgba(0, 0, 0, 0.7), rgba(0, 0, 0, 0.7)), 
                        url('https://images.unsplash.com/photo-1507842217343-583bb7270b66?auto=format&fit=crop&w=1920&q=80') !important;
            background-size: cover !important;
        }
        .login-box {
            background: rgba(255, 255, 255, 0.1);
            padding: 40px; border-radius: 20px; border: 2px solid #00D1FF;
            text-align: center; backdrop-filter: blur(10px);
        }
        /* טקסט שחור בתיבת הסיסמה */
        .stTextInput input { color: black !important; background-color: white !important; font-weight: 800 !important; }
        </style>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<div style='height: 100px;'></div>", unsafe_allow_html=True)
        st.markdown("<div class='login-box'>", unsafe_allow_html=True)
        st.markdown("<h1 style='color: #00D1FF;'>NEXUS OS</h1>", unsafe_allow_html=True)
        input_code = st.text_input("Security Code", type="password", label_visibility="collapsed")
        if st.button("Authenticate", use_container_width=True):
            if input_code in USER_REGISTRY:
                st.session_state.logged_in = True
                st.session_state.user_name = USER_REGISTRY[input_code]
                st.rerun()
            else:
                st.error("❌ Access Denied.")
        st.markdown("</div>", unsafe_allow_html=True)

if not st.session_state.logged_in:
    login_screen()
    st.stop()

# --- 4. הגדרות שפה ---
if 'lang' not in st.session_state: st.session_state.lang = "עברית"
if 'chat_history' not in st.session_state: st.session_state.chat_history = []

t = {
    "עברית": {
        "welcome": "ברוך הבא", "dash": "דאשבורד", "analyst": "מצב דאטה אנליסט",
        "tutor": "AI Tutor 🤖", "history": "היסטוריה", "settings": "הגדרות",
        "avg": "ממוצע אקדמי", "total": "סה\"כ משימות", "add": "הזנת ציונים",
        "sub": "מקצוע", "topic": "נושא", "grade": "ציון", "save": "שמור בכספת",
        "upload_title": "העלאת חומר ל-AI", "assign_sub": "שייך חומר למקצוע",
        "upload_label": "PDF, Word, Excel, CSV (גרור לכאן)", "analyze_btn": "בצע אנליזה",
        "no_data": "אין נתונים.", "ask": "שאל את ה-Tutor...",
        "subjects": ["מתמטיקה", "פיזיקה", "מדעי המחשב", "כתיבה אקדמאית", "עברית", "אחר..."]
    },
    "English": {
        "welcome": "Welcome", "dash": "Dashboard", "analyst": "Analyst Mode",
        "tutor": "AI Tutor 🤖", "history": "History", "settings": "Settings",
        "avg": "Average Score", "total": "Total Tasks", "add": "Add Grade",
        "sub": "Subject", "topic": "Topic", "grade": "Grade", "save": "Save to Vault",
        "upload_title": "Upload Content", "assign_sub": "Assign to Subject",
        "upload_label": "Drag PDF, Word, Excel, CSV here", "analyze_btn": "Analyze Content",
        "no_data": "No data.", "ask": "Ask Nexus AI...",
        "subjects": ["Math", "Physics", "Computer Science", "Academic Writing", "Hebrew", "Other..."]
    }
}
cur = t[st.session_state.lang]

# --- 5. עיצוב פנימי (CSS - שיפור מהירות וצבעים) ---
st.markdown(f"""
    <style>
    /* ביטול אנימציות למהירות */
    * {{ transition: none !important; animation: none !important; }}
    
    [data-testid="stAppViewContainer"] {{
        background: linear-gradient(rgba(0, 0, 0, 0.8), rgba(0, 0, 0, 0.8)), 
                    url('https://images.unsplash.com/photo-1507842217343-583bb7270b66?auto=format&fit=crop&w=1920&q=80') !important;
        background-size: cover !important; background-attachment: fixed !important;
    }}

    /* טקסטים לבנים */
    h1, h2, h3, h4, p, label, span {{ color: white !important; text-shadow: 1px 1px 2px black; }}
    
    /* חיצים שחורים על רקע לבן */
    button[data-testid="sidebar-button"] svg {{ 
        fill: black !important; color: black !important; 
        background-color: white !important; border-radius: 5px;
    }}

    /* תיקון קריטי: טקסט שחור בתוך כל תיבות הטקסט והבחירה */
    input, select, textarea, .stSelectbox div, div[data-baseweb="select"], .stNumberInput input {{
        color: black !important; 
        background-color: white !important; 
        font-weight: 900 !important;
    }}
    
    /* טקסט שחור ברשימות נפתחות (Dropdown Menu) */
    div[role="listbox"] ul li {{ color: black !important; font-weight: bold !important; }}

    /* העלאת קבצים - טקסט שחור */
    div[data-testid="stFileUploader"] section {{ background-color: white !important; }}
    div[data-testid="stFileUploader"] label, div[data-testid="stFileUploader"] p {{ color: black !important; }}

    div[data-testid="stMetric"] {{ background: rgba(255, 255, 255, 0.1) !important; border: 1px solid #00D1FF !important; }}
    div[data-testid="stMetricValue"] {{ color: #00D1FF !important; }}

    section[data-testid="stSidebar"] {{ background-color: #0f172a !important; }}
    </style>
    """, unsafe_allow_html=True)

# --- 6. סיידבר ---
with st.sidebar:
    st.markdown(f"<h3 style='text-align: center; color: #00D1FF;'>{st.session_state.user_name}</h3>", unsafe_allow_html=True)
    lang_choice = st.radio("שפה / Language", ["עברית", "English"], horizontal=True)
    if lang_choice != st.session_state.lang:
        st.session_state.lang = lang_choice
        st.rerun()

    selected = option_menu(None, [cur["dash"], cur["analyst"], cur["tutor"], cur["history"], cur["settings"]],
                           icons=["house", "graph-up", "robot", "clock-history", "gear"], 
                           default_index=0, styles={
                                "container": {"background-color": "#0f172a"},
                                "nav-link": {"color": "white", "text-align": "left"},
                                "nav-link-selected": {"background-color": "#00D1FF", "color": "black"}
                           })
    
    if st.button("🚪 Logout", use_container_width=True):
        st.session_state.logged_in = False
        st.rerun()

df = get_all_grades()

# --- 7. לוגיקת דפים ---
if selected == cur["dash"]:
    st.markdown(f"<h1 style='text-align: center;'>{cur['welcome']}, {st.session_state.user_name}</h1>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    c1.metric(cur["avg"], f"{df['grade'].mean():.1f}" if not df.empty else "0.0")
    c2.metric(cur["total"], len(df))
    st.divider()

    col1, col2 = st.columns(2)
    with col1:
        st.subheader(cur["add"])
        with st.form("grade_form", clear_on_submit=True):
            # שימוש ב-selectbox עם טקסט שחור (מוגדר ב-CSS)
            s = st.selectbox(cur["sub"], cur["subjects"])
            tp = st.text_input(cur["topic"])
            g = st.number_input(cur["grade"], 0, 100, 90)
            if st.form_submit_button(cur["save"]):
                save_grade(s, tp, g)
                st.toast("✅ Saved!")
                st.rerun()

    with col2:
        st.subheader(cur["upload_title"])
        up_s = st.selectbox(cur["assign_sub"], cur["subjects"], key="up_sub")
        f = st.file_uploader(cur["upload_label"], type=["pdf", "docx", "csv", "xlsx"])
        if f and st.button(cur["analyze_btn"]):
            with st.spinner("Analyzing..."):
                path = f"ai_data/uploads/{f.name}"
                with open(path, "wb") as file: file.write(f.getbuffer())
                process_file_to_db(path, up_s)
                st.success("Ready!")

elif selected == cur["tutor"]:
    st.header(cur["tutor"])
    chat_sub = st.selectbox(cur["assign_sub"], ["General / כללי"] + cur["subjects"])
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]): st.markdown(msg["content"])

    if prompt := st.chat_input(cur["ask"]):
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)
        with st.chat_message("assistant"):
            try:
                sub_key = "general" if "General" in chat_sub or "כללי" in chat_sub else chat_sub
                response_placeholder = st.empty()
                full_response = ""
                # עדכון המודל לגרסה היציבה ביותר למניעת שגיאות 404
                for chunk in get_ai_response_stream(sub_key, prompt):
                    content = chunk.content if hasattr(chunk, 'content') else str(chunk)
                    full_response += content
                    response_placeholder.markdown(full_response + "▌")
                response_placeholder.markdown(full_response)
                st.session_state.chat_history.append({"role": "assistant", "content": full_response})
            except Exception as e:
                st.error(f"AI Error: {str(e)}")

elif selected == cur["analyst"]:
    st.header(cur["analyst"])
    if df.empty: st.info(cur["no_data"])
    else:
        fig = px.line(df, x='date', y='grade', color='subject', markers=True, template="plotly_dark")
        fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig, use_container_width=True)

elif selected == cur["history"]:
    st.header(cur["history"])
    if df.empty: st.info(cur["no_data"])
    else: st.dataframe(df.sort_values(by='date', ascending=False), use_container_width=True)

elif selected == cur["settings"]:
    st.header(cur["settings"])
    if st.button("🚨 Reset All Data"): clear_db(); st.rerun()

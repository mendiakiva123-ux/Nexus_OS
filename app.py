import streamlit as st
from streamlit_option_menu import option_menu
import pandas as pd
import plotly.express as px
import os
import datetime
from database_manager import init_db, save_grade, get_all_grades, clear_db
from ai_manager import process_file_to_db, get_ai_response_stream

# --- 1. הגדרות מערכת ---
st.set_page_config(page_title="Nexus OS | Elite Command Center", layout="wide")
init_db()

# --- 2. ניהול משתמשים (10 קודים) ---
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

# --- 3. מסך התחברות יוקרתי עם רקע ---
def login_screen():
    st.markdown("""
        <style>
        [data-testid="stAppViewContainer"] {
            background: linear-gradient(rgba(0, 0, 0, 0.6), rgba(0, 0, 0, 0.6)), 
                        url('https://images.unsplash.com/photo-1507842217343-583bb7270b66?ixlib=rb-4.0.3&auto=format&fit=crop&w=1920&q=80') !important;
            background-size: cover !important;
            background-position: center !important;
        }
        .login-box {
            background: rgba(255, 255, 255, 0.1);
            padding: 50px;
            border-radius: 25px;
            border: 2px solid #00D1FF;
            text-align: center;
            backdrop-filter: blur(15px);
            box-shadow: 0 10px 30px rgba(0,0,0,0.5);
        }
        h1, p { color: white !important; text-shadow: 2px 2px 4px black; }
        /* עיצוב תיבת הקלט במסך הכניסה */
        .stTextInput input {
            color: black !important;
            background-color: white !important;
            font-weight: bold !important;
        }
        </style>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<div style='height: 100px;'></div>", unsafe_allow_html=True)
        st.markdown("<div class='login-box'>", unsafe_allow_html=True)
        st.markdown("<h1 style='color: #00D1FF;'>NEXUS OS</h1>", unsafe_allow_html=True)
        st.markdown("<p>Enter your elite access code</p>", unsafe_allow_html=True)
        
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

# --- 4. הגדרות שפה וזיכרון ---
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
        "no_data": "אין נתונים בכספת.", "ask": "שאל את ה-Tutor...",
        "subjects": ["מתמטיקה", "פיזיקה", "מדעי המחשב", "כתיבה אקדמאית", "עברית", "אחר..."]
    },
    "English": {
        "welcome": "Welcome", "dash": "Dashboard", "analyst": "Analyst Mode",
        "tutor": "AI Tutor 🤖", "history": "History", "settings": "Settings",
        "avg": "Average Score", "total": "Total Tasks", "add": "Add Grade",
        "sub": "Subject", "topic": "Topic", "grade": "Grade", "save": "Save to Vault",
        "upload_title": "Upload Content", "assign_sub": "Assign to Subject",
        "upload_label": "Drag PDF, Word, Excel, CSV here", "analyze_btn": "Analyze Content",
        "no_data": "No data in vault.", "ask": "Ask Nexus AI...",
        "subjects": ["Math", "Physics", "Computer Science", "Academic Writing", "Hebrew", "Other..."]
    }
}
cur = t[st.session_state.lang]

# --- 5. עיצוב פנימי (CSS משודרג) ---
st.markdown(f"""
    <style>
    /* רקע הספרייה בדפים הפנימיים */
    [data-testid="stAppViewContainer"] {{
        background: linear-gradient(rgba(0, 0, 0, 0.75), rgba(0, 0, 0, 0.75)), 
                    url('https://images.unsplash.com/photo-1507842217343-583bb7270b66?ixlib=rb-4.0.3&auto=format&fit=crop&w=1920&q=80') !important;
        background-size: cover !important;
        background-attachment: fixed !important;
    }}

    /* טקסטים לבנים וברורים */
    h1, h2, h3, h4, p, label, span, li {{ 
        color: white !important; 
        text-shadow: 2px 2px 4px black; 
    }}
    
    /* תיקון קריטי: טקסט שחור על רקע לבן בתיבות הקלט */
    input, select, textarea, div[data-baseweb="select"], .stNumberInput input {{
        color: black !important; 
        background-color: white !important; 
        font-weight: bold !important;
        border-radius: 10px !important;
    }}

    /* עיצוב המדדים (Metrics) */
    div[data-testid="stMetric"] {{
        background: rgba(255, 255, 255, 0.1) !important; 
        border: 2px solid #00D1FF !important; 
        border-radius: 20px !important; 
        backdrop-filter: blur(10px);
    }}
    div[data-testid="stMetricValue"] {{ color: #00D1FF !important; font-weight: 800 !important; }}

    /* סיידבר כהה וחיצים לבנים */
    section[data-testid="stSidebar"] {{ 
        background-color: rgba(15, 23, 42, 0.98) !important; 
        border-{"left" if st.session_state.lang == "עברית" else "right"}: 2px solid #00D1FF;
    }}
    button[data-testid="sidebar-button"] svg {{ fill: white !important; color: white !important; }}
    
    /* צבע הרדיו באטן של השפה */
    div[data-testid="stWidgetLabel"] p {{ color: #00D1FF !important; }}
    </style>
    """, unsafe_allow_html=True)

# --- 6. סיידבר ---
with st.sidebar:
    st.markdown(f"<h3 style='text-align: center; color: #00D1FF;'>{st.session_state.user_name}</h3>", unsafe_allow_html=True)
    st.markdown("<h1 style='color: #00D1FF; text-align: center; margin-top: -15px;'>NEXUS OS</h1>", unsafe_allow_html=True)
    
    lang_choice = st.radio("Language / שפה", ["עברית", "English"], 
                          index=0 if st.session_state.lang == "עברית" else 1, horizontal=True)
    if lang_choice != st.session_state.lang:
        st.session_state.lang = lang_choice
        st.rerun()

    selected = option_menu(None, [cur["dash"], cur["analyst"], cur["tutor"], cur["history"], cur["settings"]],
                           icons=["house", "graph-up", "robot", "clock-history", "gear"], 
                           default_index=0,
                           styles={
                                "container": {"background-color": "#0f172a"},
                                "nav-link": {"color": "white", "text-align": "left", "font-weight": "bold"},
                                "nav-link-selected": {"background-color": "#00D1FF", "color": "black"}
                           })
    
    st.divider()
    if st.button("🚪 Logout", use_container_width=True):
        st.session_state.logged_in = False
        st.rerun()

df = get_all_grades()

# --- 7. לוגיקת דפים ---
if selected == cur["dash"]:
    st.markdown(f"<h1 style='text-align: center; font-size: 3.5rem;'>{cur['welcome']}, {st.session_state.user_name}</h1>", unsafe_allow_html=True)
    
    c1, c2 = st.columns(2)
    c1.metric(cur["avg"], f"{df['grade'].mean():.1f}" if not df.empty else "0.0")
    c2.metric(cur["total"], len(df))
    st.divider()

    col1, col2 = st.columns(2)
    with col1:
        st.subheader(cur["add"])
        with st.form("grade_form", clear_on_submit=True):
            s = st.selectbox(cur["sub"], cur["subjects"])
            tp = st.text_input(cur["topic"])
            g = st.number_input(cur["grade"], 0, 100, 90)
            if st.form_submit_button(cur["save"]):
                save_grade(s, tp, g)
                st.toast("🔒 Saved!")
                st.rerun()

    with col2:
        st.subheader(cur["upload_title"])
        up_s = st.selectbox(cur["assign_sub"], cur["subjects"], key="upload_sub")
        f = st.file_uploader(cur["upload_label"], type=["pdf", "docx", "csv", "xlsx"])
        if f and st.button(cur["analyze_btn"]):
            with st.spinner("Analyzing..."):
                path = f"ai_data/uploads/{f.name}"
                os.makedirs("ai_data/uploads", exist_ok=True)
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
            sub_key = "general" if "General" in chat_sub or "כללי" in chat_sub else chat_sub
            response_placeholder = st.empty()
            full_response = ""
            for chunk in get_ai_response_stream(sub_key, prompt):
                full_response += (chunk.content if hasattr(chunk, 'content') else str(chunk))
                response_placeholder.markdown(full_response + "▌")
            response_placeholder.markdown(full_response)
            st.session_state.chat_history.append({"role": "assistant", "content": full_response})

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
    st.write(f"Logged in as: **{st.session_state.user_name}**")
    if st.button("🚨 Reset All Data"): clear_db(); st.rerun()

import streamlit as st
import streamlit.components.v1 as components
from streamlit_option_menu import option_menu
import pandas as pd
import plotly.express as px
import datetime
from zoneinfo import ZoneInfo
import io
from database_manager import authenticate_user, update_user_name, save_grade, get_all_grades, clear_db, save_chat_message, get_persistent_chat_history, clear_chat_history, save_task, get_all_tasks, delete_task
from ai_manager import get_ai_response_stream, extract_text_from_file

# --- הגדרות ליבה ---
st.set_page_config(page_title="NEXUS CORE", page_icon="💎", layout="wide", initial_sidebar_state="expanded")

BG_IMAGE_URL = "https://images.unsplash.com/photo-1507842217343-583bb7270b66?q=80&w=2560&auto=format&fit=crop"

# --- 1. מסך נעילה וזיהוי משתמש ---
if 'authenticated' not in st.session_state: st.session_state.authenticated = False
if 'user_id' not in st.session_state: st.session_state.user_id = None
if 'user_name' not in st.session_state: st.session_state.user_name = None
if 'dark_mode' not in st.session_state: st.session_state.dark_mode = False

if not st.session_state.authenticated:
    st.markdown(f"""
        <style>
        .stApp {{ background-image: linear-gradient(rgba(0,0,0,0.65), rgba(0,0,0,0.85)), url('{BG_IMAGE_URL}'); background-size: cover; background-position: center; background-attachment: fixed; display: flex; align-items: center; justify-content: center; }}
        .lock-container {{ background: rgba(255, 255, 255, 0.1); backdrop-filter: blur(25px); border: 1px solid rgba(255, 255, 255, 0.2); border-radius: 30px; padding: 50px 30px; text-align: center; direction: rtl; color: white; }}
        input {{ font-size: 1.2rem !important; text-align: center !important; background: rgba(255,255,255,0.9) !important; border-radius: 10px !important; color: #000 !important; }}
        </style>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<div class='lock-container'><h1>NEXUS CORE</h1>", unsafe_allow_html=True)
        pwd = st.text_input("הזן קוד גישה / Access Code", type="password", placeholder="****", max_chars=4)
        
        if len(pwd) == 4:
            user_data = authenticate_user(pwd)
            if user_data:
                st.session_state.user_id = user_data['user_id']
                if not user_data['user_name']:
                    # משתמש חדש ללא שם
                    name_input = st.text_input("איך לקרוא לך? / What's your name?")
                    if st.button("שמור והכנס / Save & Enter"):
                        if name_input:
                            update_user_name(st.session_state.user_id, name_input)
                            st.session_state.user_name = name_input
                            st.session_state.authenticated = True
                            st.rerun()
                else:
                    st.session_state.user_name = user_data['user_name']
                    st.session_state.authenticated = True
                    st.rerun()
            else:
                st.error("קוד שגוי / Invalid Code")
        st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

# ==========================================
# --- האפליקציה המלאה (אחרי התחברות) ---
# ==========================================

if 'lang' not in st.session_state: st.session_state.lang = "עברית"
if 'chat_history' not in st.session_state: st.session_state.chat_history = []
if 'file_contexts' not in st.session_state: st.session_state.file_contexts = {} 
if 'font_size' not in st.session_state: st.session_state.font_size = "1.1rem" 

def get_greeting(lang, name):
    hour = datetime.datetime.now(ZoneInfo("Asia/Jerusalem")).hour
    if lang == "עברית":
        greet = "בוקר טוב" if 5 <= hour < 12 else "צהריים טובים" if 12 <= hour < 18 else "ערב טוב" if 18 <= hour < 22 else "לילה טוב"
        return f"{greet}, {name}! ✨"
    else:
        greet = "Good Morning" if 5 <= hour < 12 else "Good Afternoon" if 12 <= hour < 18 else "Good Evening" if 18 <= hour < 22 else "Good Night"
        return f"{greet}, {name}! ✨"

greeting_text = get_greeting(st.session_state.lang, st.session_state.user_name)

T = {
    "עברית": {
        "title": "NEXUS ACADEMY", "m1": "מרכז אקדמי", "m2": "מנטור AI", "m3": "Vault", "m4": "משימות 📅", "m5": "הגדרות",
        "avg": "ממוצע משוקלל", "count": "קורסים", "sub": "מקצוע", "grd": "ציון", "cred": "נ\"ז", "sync": "שמור", "analyst": "מצב דאטה אנליסט 📊", "ask": "שאל את הבוט..."
    },
    "English": {
        "title": "NEXUS ACADEMY", "m1": "Dashboard", "m2": "AI Mentor", "m3": "Vault", "m4": "Tasks 📅", "m5": "Settings",
        "avg": "Weighted GPA", "count": "Courses", "sub": "Subject", "grd": "Grade", "cred": "Credits", "sync": "Save", "analyst": "Analyst Mode 📊", "ask": "Ask NEXUS..."
    }
}
cur = T[st.session_state.lang]

# עיצוב UI
overlay_color = "rgba(255, 255, 255, 0.7)" if not st.session_state.dark_mode else "rgba(15, 23, 42, 0.85)"
bg_css = f"background-image: linear-gradient({overlay_color}, {overlay_color}), url('{BG_IMAGE_URL}'); background-size: cover; background-position: center; background-attachment: fixed;"
text_color = "#1e293b" if not st.session_state.dark_mode else "#f8fafc"
glass_bg = "rgba(255, 255, 255, 0.4)" if not st.session_state.dark_mode else "rgba(30, 41, 59, 0.5)"

st.markdown(f"""
    <style>
    header[data-testid="stHeader"] {{ background: transparent !important; }}
    footer {{visibility: hidden !important;}}
    .stApp {{ {bg_css} color: {text_color}; font-family: 'Assistant', sans-serif; }}
    {" .main, [data-testid='stSidebar'], [data-testid='stChatMessageContent'] { direction: rtl !important; text-align: right !important; } " if st.session_state.lang == "עברית" else ""}
    div[data-testid="stMetric"], .stChatMessage, .stForm {{ background: {glass_bg} !important; backdrop-filter: blur(25px) !important; border-radius: 20px !important; box-shadow: 0 8px 32px rgba(0,0,0, 0.1) !important; padding: 15px; }}
    .stButton>button {{ background: linear-gradient(135deg, #00C9FF 0%, #92FE9D 100%) !important; color: #0b3d2c !important; font-weight: 800; border-radius: 50px !important; }}
    .greeting-box {{ text-align: center; font-size: 1.8rem; font-weight: 800; color: {text_color}; margin-top: -10px; margin-bottom: 25px; }}
    </style>
""", unsafe_allow_html=True)

df = get_all_grades(st.session_state.user_id)
tasks_df = get_all_tasks(st.session_state.user_id)

# תרגום מקצועות
if st.session_state.lang == "עברית":
    base_subjects = ["כללי", "מתמטיקה", "מדעי המחשב", "אנגלית", "פיזיקה", "כתיבה אקדמית"]
    add_new_str = "➕ הוסף מקצוע חדש..."
else:
    base_subjects = ["General", "Math", "Computer Science", "English", "Physics", "Academic Writing"]
    add_new_str = "➕ Add New Subject..."

db_subjects = df['subject'].unique().tolist() if not df.empty else []
all_subjects = sorted(list(set(base_subjects + db_subjects))) + [add_new_str]
idx_general = all_subjects.index("כללי") if "כללי" in all_subjects else (all_subjects.index("General") if "General" in all_subjects else 0)

with st.sidebar:
    st.markdown("<h2>NEXUS OS</h2>", unsafe_allow_html=True)
    lang = st.radio("Language", ["עברית", "English"], horizontal=True, label_visibility="collapsed")
    if lang != st.session_state.lang: st.session_state.lang = lang; st.rerun()
    st.session_state.dark_mode = st.toggle("🌙 Dark Mode", value=st.session_state.dark_mode)
    st.divider()
    analyst_on = st.toggle(cur["analyst"], value=True)
    if st.button("Logout"): st.session_state.authenticated = False; st.rerun()

st.markdown(f"<div class='greeting-box'>{greeting_text}</div>", unsafe_allow_html=True)

menu = option_menu(None, [cur["m1"], cur["m2"], cur["m3"], cur["m4"], cur["m5"]], 
                   icons=["bar-chart-fill", "chat-quote-fill", "database-fill", "calendar-check-fill", "gear-fill"], 
                   orientation="horizontal")

df_valid = df[df['topic'] != 'System_Init'] if not df.empty else df
total_credits = df_valid['credits'].sum() if not df_valid.empty else 0.0
weighted_avg = (df_valid['grade'] * df_valid['credits']).sum() / total_credits if total_credits > 0 else 0.0

if menu == cur["m1"]:
    c1, c2, c3 = st.columns(3)
    c1.metric(cur["avg"], f"{weighted_avg:.2f}") 
    c2.metric(cur["count"], len(df_valid))
    c3.metric(cur["cred"], f"{total_credits:.1f}")
    st.divider()
    l, r = st.columns([1, 2.5])
    with l:
        with st.form("entry", clear_on_submit=True):
            sub = st.selectbox(cur["sub"], all_subjects)
            new_s = st.text_input("Name:") if sub == add_new_str else ""
            c_input = st.number_input(cur["cred"], 0.5, 10.0, 3.0)
            g_input = st.number_input(cur["grd"], 0, 100, 90)
            if st.form_submit_button(cur["sync"]):
                final_s = new_s if sub == add_new_str else sub
                save_grade(st.session_state.user_id, final_s, "", g_input, c_input); st.rerun()
    with r:
        if not df_valid.empty:
            fig = px.bar(df_valid, x='subject', y='grade', color='grade', color_continuous_scale='Mint')
            fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color=text_color)
            st.plotly_chart(fig, use_container_width=True)

elif menu == cur["m2"]:
    if not st.session_state.chat_history:
        st.session_state.chat_history = [{"role": m["role"], "content": m["content"]} for m in get_persistent_chat_history(st.session_state.user_id)]
    chat_sub = st.selectbox(cur["sub"], all_subjects[:-1], index=idx_general)
    
    colA, colB = st.columns([3, 1])
    with colB: 
        if st.button("📝 Quiz"):
            if chat_sub in st.session_state.file_contexts:
                placeholder = st.empty(); full_res = ""
                for chunk in get_ai_response_stream(chat_sub, "ייצר מבחן.", [], st.session_state.file_contexts[chat_sub], st.session_state.lang, analyst_on, is_quiz=True):
                    full_res += chunk; placeholder.markdown(f'<div style="background:white; padding:10px; border-radius:10px; color:black;">{full_res}</div>', unsafe_allow_html=True)

    chat_container = st.container(height=400)
    with chat_container:
        for m in st.session_state.chat_history:
            with st.chat_message(m["role"]): st.markdown(m["content"])
    
    if p := st.chat_input(cur["ask"]):
        st.session_state.chat_history.append({"role": "user", "content": p})
        save_chat_message(st.session_state.user_id, "user", p)
        with chat_container.chat_message("user"): st.markdown(p)
        with chat_container.chat_message("assistant"):
            placeholder = st.empty(); full_res = ""
            for chunk in get_ai_response_stream(chat_sub, p, st.session_state.chat_history[:-1], st.session_state.file_contexts.get(chat_sub, ""), st.session_state.lang, analyst_on):
                full_res += chunk; placeholder.markdown(full_res)
        st.session_state.chat_history.append({"role": "assistant", "content": full_res})
        save_chat_message(st.session_state.user_id, "assistant", full_res)

elif menu == cur["m3"]:
    if not df_valid.empty:
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer: df_valid.to_excel(writer, index=False)
        st.download_button(label="📥 Export Excel", data=buffer.getvalue(), file_name="Grades.xlsx")
    st.dataframe(df_valid, use_container_width=True, height=500) 

elif menu == cur["m4"]:
    colA, colB = st.columns([1, 2])
    with colA:
        with st.form("task"):
            t_title = st.text_input("Task")
            t_sub = st.selectbox(cur["sub"], all_subjects[:-1])
            t_due = st.date_input("Date")
            if st.form_submit_button("Add"):
                save_task(st.session_state.user_id, t_title, t_sub, t_due); st.rerun()
    with colB:
        if not tasks_df.empty:
            for idx, row in tasks_df.iterrows():
                st.markdown(f"**{row['title']}** ({row['subject']})")
                if st.button("✅", key=f"t_{row['id']}"): delete_task(row['id']); st.rerun()

elif menu == cur["m5"]:
    if st.button("Clear Chat"): clear_chat_history(st.session_state.user_id); st.session_state.chat_history = []; st.rerun()
    if st.button("Reset DB"): clear_db(st.session_state.user_id); st.rerun()

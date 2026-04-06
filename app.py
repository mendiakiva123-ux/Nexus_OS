import streamlit as st
import streamlit.components.v1 as components
from streamlit_option_menu import option_menu
import pandas as pd
import plotly.express as px
import datetime
from zoneinfo import ZoneInfo
import io
from database_manager import save_grade, get_all_grades, clear_db, save_chat_message, get_persistent_chat_history, clear_chat_history, save_task, get_all_tasks, delete_task
from ai_manager import get_ai_response_stream, extract_text_from_file

# --- הגדרות ליבה ---
st.set_page_config(page_title="NEXUS CORE", page_icon="💎", layout="wide", initial_sidebar_state="expanded")

# --- מסך נעילה חכם ---
if 'authenticated' not in st.session_state: st.session_state.authenticated = False
if 'dark_mode' not in st.session_state: st.session_state.dark_mode = False

if not st.session_state.authenticated:
    st.markdown("""
        <style>
        .stApp { background: linear-gradient(-45deg, #ee7752, #e73c7e, #23a6d5, #23d5ab); background-size: 400% 400%; animation: gradientBG 12s ease infinite; display: flex; align-items: center; justify-content: center; }
        @keyframes gradientBG { 0% {background-position: 0% 50%;} 50% {background-position: 100% 50%;} 100% {background-position: 0% 50%;} }
        .lock-container { background: rgba(255, 255, 255, 0.15); backdrop-filter: blur(25px); border: 1px solid rgba(255, 255, 255, 0.3); border-radius: 30px; padding: 50px 30px; box-shadow: 0 20px 40px rgba(0,0,0,0.3); text-align: center; direction: rtl; }
        input[type="password"] { font-size: 2rem !important; text-align: center !important; letter-spacing: 0.5rem; background: rgba(255,255,255,0.8) !important; border-radius: 15px !important; }
        </style>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<div class='lock-container'><h1 style='color:white; text-shadow: 0 4px 15px rgba(0,0,0,0.4); font-size:3.5rem;'>NEXUS</h1><p style='color:white; font-size:1.2rem; font-weight:bold;'>קוד גישה</p>", unsafe_allow_html=True)
        components.html("""<script>setTimeout(function() { var inputs = window.parent.document.querySelectorAll('input[type="password"]'); for(var i=0; i<inputs.length; i++){ inputs[i].setAttribute('inputmode', 'numeric'); inputs[i].setAttribute('pattern', '[0-9]*'); } }, 500);</script>""", height=0)
        pwd = st.text_input("", type="password", placeholder="****", max_chars=4, label_visibility="collapsed")
        if pwd == "7707": st.session_state.authenticated = True; st.rerun()
        elif len(pwd) == 4 and pwd != "7707": st.error("קוד שגוי.")
        st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

# ==========================================
# --- מכאן מתחילה האפליקציה ---
# ==========================================

if 'lang' not in st.session_state: st.session_state.lang = "עברית"
if 'chat_history' not in st.session_state: st.session_state.chat_history = []
if 'file_contexts' not in st.session_state: st.session_state.file_contexts = {} 
if 'font_size' not in st.session_state: st.session_state.font_size = "1.1rem" 

def get_greeting():
    hour = datetime.datetime.now(ZoneInfo("Asia/Jerusalem")).hour
    if 5 <= hour < 12: return "בוקר טוב"
    elif 12 <= hour < 18: return "צהריים טובים"
    elif 18 <= hour < 22: return "ערב טוב"
    else: return "לילה טוב"
greeting_text = f"{get_greeting()}, מנדי עקיבא! ✨"

# מילון השפות שהוחזר
T = {
    "עברית": {
        "title": "NEXUS ACADEMY", "m1": "מרכז אקדמי", "m2": "מנטור AI", "m3": "מסד נתונים", "m4": "לוח משימות 📅", "m5": "הגדרות",
        "avg": "ממוצע משוקלל", "count": "קורסים", "sub": "מקצוע", "grd": "ציון", "cred": "נ\"ז", "sync": "שמור נתונים",
        "analyst": "מצב דאטה אנליסט 📊", "ask": "שאל את הבוט...", "clear": "נקה זיכרון"
    },
    "English": {
        "title": "NEXUS ACADEMY", "m1": "Dashboard", "m2": "AI Mentor", "m3": "Vault", "m4": "Task Board 📅", "m5": "Settings",
        "avg": "Weighted GPA", "count": "Courses", "sub": "Subject", "grd": "Grade", "cred": "Credits", "sync": "Save",
        "analyst": "Analyst Mode 📊", "ask": "Ask NEXUS...", "clear": "Clear Memory"
    }
}
cur = T[st.session_state.lang]

# --- עיצוב דינמי (תומך Dark Mode) ---
bg_css = "background: radial-gradient(circle at 15% 50%, #fdfbfb, #ebedee), radial-gradient(circle at 85% 30%, #e0c3fc, #8ec5fc);" if not st.session_state.dark_mode else "background: #0f2027; background: -webkit-linear-gradient(to right, #2c5364, #203a43, #0f2027); background: linear-gradient(to right, #2c5364, #203a43, #0f2027);"
text_color = "#2c3e50" if not st.session_state.dark_mode else "#ffffff"
glass_bg = "rgba(255, 255, 255, 0.55)" if not st.session_state.dark_mode else "rgba(0, 0, 0, 0.4)"

st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Assistant:wght@300;600;800&display=swap');
    header[data-testid="stHeader"] {{ background: transparent !important; }}
    .stAppDeployButton {{display: none;}} footer {{visibility: hidden !important;}} html, body {{ max-width: 100vw; overflow-x: hidden; }}
    .stApp {{ {bg_css} color: {text_color}; font-family: 'Assistant', sans-serif; }}
    {" .main, [data-testid='stSidebar'], [data-testid='stChatMessageContent'] { direction: rtl !important; text-align: right !important; } " if st.session_state.lang == "עברית" else ""}
    div[data-testid="stMetric"], .stChatMessage, .stForm {{ background: {glass_bg} !important; backdrop-filter: blur(20px) !important; border: 1px solid rgba(255, 255, 255, 0.3) !important; border-radius: 20px !important; box-shadow: 0 8px 32px rgba(0,0,0, 0.1) !important; padding: 15px; transition: transform 0.3s, box-shadow 0.3s; color: {text_color} !important; }}
    div[data-testid="stMetric"]:hover {{ transform: translateY(-8px); box-shadow: 0 15px 35px rgba(0,0,0, 0.2) !important; }}
    h1, h2, h3 {{ color: {text_color}; text-align: center; font-weight: 800; }}
    .stButton>button {{ background: linear-gradient(135deg, #00C9FF 0%, #92FE9D 100%) !important; color: #0b3d2c !important; font-weight: 800; border: none; border-radius: 50px !important; width: 100%; box-shadow: 0 8px 20px rgba(0, 201, 255, 0.3) !important; transition: all 0.3s ease !important; text-transform: uppercase; letter-spacing: 0.5px; }}
    .stButton>button:hover {{ transform: translateY(-5px) !important; box-shadow: 0 12px 25px rgba(0, 201, 255, 0.5) !important; }}
    [data-testid="stChatMessageContent"] p, [data-testid="stChatMessageContent"] li {{ font-size: {st.session_state.font_size} !important; color: {text_color}; }}
    .greeting-box {{ text-align: center; font-size: 1.3rem; font-weight: 800; color: {text_color}; margin-top: -15px; margin-bottom: 20px; }}
    </style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=60)
def fetch_grades_cached(): return get_all_grades()

@st.cache_data(ttl=60)
def fetch_tasks_cached(): return get_all_tasks()

df = fetch_grades_cached()
tasks_df = fetch_tasks_cached()

base_subjects = ["כללי", "מתמטיקה", "מדעי המחשב", "אנגלית", "פיזיקה", "כתיבה אקדמית", "➕ הוסף מקצוע חדש..."]
db_subjects = df['subject'].unique().tolist() if not df.empty else []
temp_subjects = set(base_subjects + db_subjects)
if "➕ הוסף מקצוע חדש..." in temp_subjects: temp_subjects.remove("➕ הוסף מקצוע חדש...")
if "System_Init" in temp_subjects: temp_subjects.remove("System_Init")
all_subjects = sorted(list(temp_subjects)) + ["➕ הוסף מקצוע חדש..."]
idx_math = all_subjects.index("מתמטיקה") if "מתמטיקה" in all_subjects else 0
idx_general = all_subjects.index("כללי") if "כללי" in all_subjects else 0

# --- תפריט צד ---
with st.sidebar:
    st.markdown(f"<h2>NEXUS OS</h2>", unsafe_allow_html=True)
    
    # החזרת אפשרות השפה
    lang = st.radio("שפת ממשק / Language", ["עברית", "English"], horizontal=True, label_visibility="collapsed")
    if lang != st.session_state.lang: st.session_state.lang = lang; st.rerun()
    
    st.session_state.dark_mode = st.toggle("🌙 מצב לילה" if st.session_state.lang == "עברית" else "🌙 Dark Mode", value=st.session_state.dark_mode)
    st.divider()
    
    # החזרת מצב האנליסט
    analyst_on = st.toggle(cur["analyst"], value=True)
    
    st.markdown("### 📚 ניהול חומר לימודי" if st.session_state.lang == "עברית" else "### 📚 Study Materials")
    upload_sub = st.selectbox("שייך קובץ למקצוע:" if st.session_state.lang == "עברית" else "Assign to subject:", all_subjects[:-1], index=idx_math)
    up = st.file_uploader("העלאת קבצים (כל הסוגים)" if st.session_state.lang == "עברית" else "Upload files", type=None)
    if up and st.button("סרוק לזיכרון הבוט" if st.session_state.lang == "עברית" else "Scan to Memory"):
        st.session_state.file_contexts[upload_sub] = extract_text_from_file(up)
        st.success(f"המידע נטען למקצוע: {upload_sub}" if st.session_state.lang == "עברית" else f"Loaded to: {upload_sub}")

st.markdown(f"<div class='greeting-box'>{greeting_text}</div>", unsafe_allow_html=True)

menu = option_menu(None, [cur["m1"], cur["m2"], cur["m3"], cur["m4"], cur["m5"]], 
                   icons=["bar-chart-fill", "chat-quote-fill", "database-fill", "calendar-check-fill", "gear-fill"], 
                   orientation="horizontal",
                   styles={
                       "container": {"padding": "0!important", "background": "rgba(255,255,255,0.7)" if not st.session_state.dark_mode else "rgba(0,0,0,0.5)", "backdrop-filter": "blur(15px)", "border-radius": "20px", "box-shadow": "0 10px 30px rgba(0,0,0,0.08)", "margin-bottom": "25px"},
                       "nav-link-selected": {"background": "linear-gradient(135deg, #00C9FF, #92FE9D)", "font-weight": "bold", "color": "#0b3d2c", "border-radius": "15px"}
                   })

df_valid = df[df['topic'] != 'System_Init'] if not df.empty else df

# --- התיקון הקריטי לשגיאת ה-NameError ---
total_credits = 0.0
weighted_avg = 0.0

if not df_valid.empty:
    if 'credits' not in df_valid.columns: df_valid['credits'] = 1.0
    total_credits = df_valid['credits'].sum()
    if total_credits > 0:
        weighted_avg = (df_valid['grade'] * df_valid['credits']).sum() / total_credits

# --- עמוד: מרכז אקדמי (הדשבורד) ---
if menu == cur["m1"]:
    c1, c2, c3 = st.columns(3)
    c1.metric(cur["avg"], f"{weighted_avg:.2f}") 
    c2.metric(cur["count"], len(df_valid))
    c3.metric("סה\"כ נ\"ז" if st.session_state.lang == "עברית" else "Total Credits", f"{total_credits:.1f}")
    
    st.divider()
    l, r = st.columns([1, 2.5])
    with l:
        st.markdown("### 📥 הזנת קורס חדש" if st.session_state.lang == "עברית" else "### 📥 Enter Course")
        with st.form("entry", clear_on_submit=True):
            selected_sub = st.selectbox(cur["sub"], all_subjects, index=idx_math)
            new_sub_input = st.text_input("הקלד שם מקצוע חדש:") if selected_sub == "➕ הוסף מקצוע חדש..." else ""
            c = st.number_input(cur["cred"], min_value=0.5, max_value=10.0, value=3.0, step=0.5)
            g = st.number_input(cur["grd"], min_value=0, max_value=100, value=90)
            if st.form_submit_button(cur["sync"]): 
                final_subject = new_sub_input if selected_sub == "➕ הוסף מקצוע חדש..." else selected_sub
                if final_subject: save_grade(final_subject, "", g, c); fetch_grades_cached.clear(); st.rerun()
                else: st.error("חובה להזין שם." if st.session_state.lang == "עברית" else "Name required.")
                
        # מחשבון מה אם
        with st.expander("🤔 מחשבון 'מה אם'" if st.session_state.lang == "עברית" else "🤔 What-If Calculator"):
            st.markdown("בדוק איך ציון ישפיע על הממוצע:" if st.session_state.lang == "עברית" else "Check future grade impact:")
            sim_c = st.number_input("נ\"ז לקורס הבא" if st.session_state.lang == "עברית" else "Next course credits", 1.0, 10.0, 3.0)
            sim_g = st.number_input("ציון צפוי" if st.session_state.lang == "עברית" else "Expected grade", 0, 100, 90)
            if st.button("חשב" if st.session_state.lang == "עברית" else "Calculate"):
                new_tot = total_credits + sim_c
                new_avg = ((weighted_avg * total_credits) + (sim_g * sim_c)) / new_tot if new_tot > 0 else 0
                st.success(f"הממוצע יהיה: {new_avg:.2f}" if st.session_state.lang == "עברית" else f"New Avg: {new_avg:.2f}")

    with r:
        if not df_valid.empty:
            tab1, tab2, tab3 = st.tabs(["גרף ציונים", "עוגת נ\"ז", "מגמת זמן"] if st.session_state.lang == "עברית" else ["Grades Chart", "Credits Pie", "Trend"])
            with tab1:
                fig = px.bar(df_valid, x='subject', y='grade', color='grade', color_continuous_scale='Mint')
                fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color=text_color)
                st.plotly_chart(fig, use_container_width=True)
            with tab2:
                fig2 = px.pie(df_valid, values='credits', names='subject', hole=0.4)
                fig2.update_layout(paper_bgcolor='rgba(0,0,0,0)', font_color=text_color)
                st.plotly_chart(fig2, use_container_width=True)
            with tab3:
                df_time = df_valid.copy().sort_values('created_at')
                df_time['rolling_avg'] = df_time['grade'].expanding().mean()
                fig3 = px.line(df_time, x='created_at', y='rolling_avg', markers=True)
                fig3.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color=text_color)
                st.plotly_chart(fig3, use_container_width=True)

# --- עמוד: בינה מלאכותית ---
elif menu == cur["m2"]:
    st.markdown(f"<h1>{'NEXUS AI MENTOR' if not analyst_on else 'DATA ANALYST AI'}</h1>", unsafe_allow_html=True)
    if not st.session_state.chat_history:
        db_history = get_persistent_chat_history()
        st.session_state.chat_history = [{"role": m["role"], "content": m["content"]} for m in db_history]

    colA, colB = st.columns([3, 1])
    with colA: chat_sub = st.selectbox("נושא השיחה:" if st.session_state.lang == "עברית" else "Subject:", all_subjects[:-1], index=idx_general)
    with colB: 
        if st.button("📝 חולל מבחן (Quiz)" if st.session_state.lang == "עברית" else "📝 Generate Quiz"):
            if chat_sub in st.session_state.file_contexts:
                context_for_bot = st.session_state.file_contexts[chat_sub]
                placeholder = st.empty()
                full_res = ""
                for chunk in get_ai_response_stream(chat_sub, "ייצר לי מבחן." if st.session_state.lang == "עברית" else "Generate a quiz.", [], context_for_bot, st.session_state.lang, analyst_on, is_quiz=True):
                    full_res += chunk
                    placeholder.markdown(f'<div style="text-align: right; direction: rtl; background: rgba(255,255,255,0.8); padding:15px; border-radius:10px; color: black;">{full_res}</div>', unsafe_allow_html=True)
            else:
                st.warning("עליך להעלות קבצים למקצוע זה תחילה." if st.session_state.lang == "עברית" else "Upload files for this subject first.")

    chat_container = st.container(height=450)
    with chat_container:
        for m in st.session_state.chat_history:
            with st.chat_message(m["role"]):
                st.markdown(f'<div style="text-align: right; direction: rtl;">{m["content"]}</div>', unsafe_allow_html=True)

    if p := st.chat_input(cur["ask"]):
        components.html("""<script>window.parent.document.activeElement.blur();</script>""", height=0, width=0)
        st.session_state.chat_history.append({"role": "user", "content": p})
        save_chat_message("user", p)
        with chat_container.chat_message("user"): st.markdown(f'<div style="text-align: right; direction: rtl;">{p}</div>', unsafe_allow_html=True)
        
        with chat_container.chat_message("assistant"):
            placeholder = st.empty()
            full_res = ""
            context_for_bot = st.session_state.file_contexts.get(chat_sub, "")
            for chunk in get_ai_response_stream(chat_sub, p, st.session_state.chat_history[:-1], context_for_bot, st.session_state.lang, analyst_on):
                full_res += chunk
                placeholder.markdown(f'<div style="text-align: right; direction: rtl;">{full_res}</div>', unsafe_allow_html=True)
        st.session_state.chat_history.append({"role": "assistant", "content": full_res})
        save_chat_message("assistant", full_res)

# --- עמוד: מסד נתונים ויצוא לאקסל ---
elif menu == cur["m3"]:
    col1, col2 = st.columns([3, 1])
    with col1: st.markdown("<h1>Vault</h1>", unsafe_allow_html=True)
    with col2:
        if not df_valid.empty:
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                df_valid.to_excel(writer, index=False, sheet_name='Grades')
            st.download_button(label="📥 ייצוא ל-Excel" if st.session_state.lang == "עברית" else "📥 Export Excel", data=buffer.getvalue(), file_name="Nexus_Grades.xlsx", mime="application/vnd.ms-excel")
    st.dataframe(df_valid, use_container_width=True, height=500) 

# --- עמוד: לוח משימות ---
elif menu == cur["m4"]:
    st.markdown("<h1>לוח משימות אקדמי</h1>" if st.session_state.lang == "עברית" else "<h1>Task Board</h1>", unsafe_allow_html=True)
    colA, colB = st.columns([1, 2])
    with colA:
        with st.form("new_task", clear_on_submit=True):
            t_title = st.text_input("תיאור המשימה" if st.session_state.lang == "עברית" else "Task Title")
            t_sub = st.selectbox(cur["sub"], all_subjects[:-1])
            t_date = st.date_input("תאריך הגשה" if st.session_state.lang == "עברית" else "Due Date")
            if st.form_submit_button("הוסף משימה" if st.session_state.lang == "עברית" else "Add Task"):
                save_task(t_title, t_sub, t_date); fetch_tasks_cached.clear(); st.rerun()
    with colB:
        if not tasks_df.empty:
            for index, row in tasks_df.iterrows():
                with st.container():
                    cols = st.columns([4, 1])
                    days_left = (pd.to_datetime(row['due_date']).date() - datetime.date.today()).days
                    status_color = "#ff4b2b" if days_left < 3 else "#92FE9D"
                    days_text = f"נותרו {days_left} ימים" if st.session_state.lang == "עברית" else f"{days_left} days left"
                    cols[0].markdown(f"**{row['title']}** ({row['subject']}) <br> <span style='color:{status_color}; font-weight:bold;'>{days_text}</span>", unsafe_allow_html=True)
                    if cols[1].button("✅ סיום" if st.session_state.lang == "עברית" else "✅ Done", key=f"done_{row['id']}"):
                        delete_task(row['id']); fetch_tasks_cached.clear(); st.rerun()
                    st.divider()
        else:
            st.info("אין משימות קרובות. אתה פנוי!" if st.session_state.lang == "עברית" else "No upcoming tasks. You are free!")

# --- עמוד: הגדרות (Settings) ---
elif menu == cur["m5"]:
    st.markdown(f"<h1>{cur['m5']}</h1>", unsafe_allow_html=True)
    font_size_map = {"קטן": "0.9rem", "רגיל": "1.1rem", "גדול": "1.3rem"} if st.session_state.lang == "עברית" else {"Small": "0.9rem", "Normal": "1.1rem", "Large": "1.3rem"}
    
    current_size_name = [k for k, v in font_size_map.items() if v == st.session_state.font_size]
    if not current_size_name: current_size_name = list(font_size_map.keys())[1] # fallback to normal
    else: current_size_name = current_size_name[0]
    
    new_size_name = st.select_slider("גודל טקסט בצ'אט" if st.session_state.lang == "עברית" else "Chat Font Size", options=list(font_size_map.keys()), value=current_size_name)
    if font_size_map[new_size_name] != st.session_state.font_size: st.session_state.font_size = font_size_map[new_size_name]; st.rerun()
    st.divider()
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("נקה היסטוריית צ'אט" if st.session_state.lang == "עברית" else "Clear Chat", type="primary"): clear_chat_history(); st.session_state.chat_history = []; st.success("נמחק." if st.session_state.lang == "עברית" else "Cleared.")
    with c2:
        if st.button("רוקן זיכרון סורק" if st.session_state.lang == "עברית" else "Clear Scanner", type="primary"): st.session_state.file_contexts = {}; st.success("נוקה." if st.session_state.lang == "עברית" else "Cleared.")
    with c3:
        st.markdown("""<style>div.row-widget.stButton > button[kind="secondary"] {background: linear-gradient(135deg, #ff416c, #ff4b2b) !important; color: white !important;}</style>""", unsafe_allow_html=True)
        if st.button("🚨 אפס מסד נתונים" if st.session_state.lang == "עברית" else "🚨 Reset DB", type="secondary"): clear_db(); fetch_grades_cached.clear(); st.rerun()

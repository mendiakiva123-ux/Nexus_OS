import streamlit as st
import streamlit.components.v1 as components
from streamlit_option_menu import option_menu
import pandas as pd
import plotly.express as px
from database_manager import save_grade, get_all_grades, clear_db, save_chat_message, get_persistent_chat_history, clear_chat_history
from ai_manager import get_ai_response_stream, extract_text_from_file

# --- הגדרות ליבה (Page Config צריכה להיות הפקודה הראשונה) ---
st.set_page_config(page_title="NEXUS CORE", page_icon="💎", layout="wide", initial_sidebar_state="expanded")

# --- 1. מסך נעילה חכם (רק מספרים) ---
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.markdown("""
        <style>
        .stApp {
            background: linear-gradient(-45deg, #4158D0, #C850C0, #FFCC70);
            background-size: 400% 400%;
            animation: gradientBG 10s ease infinite;
            display: flex; align-items: center; justify-content: center;
        }
        @keyframes gradientBG {
            0% {background-position: 0% 50%;}
            50% {background-position: 100% 50%;}
            100% {background-position: 0% 50%;}
        }
        .lock-container {
            background: rgba(255, 255, 255, 0.2);
            backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.5);
            border-radius: 30px; padding: 40px; box-shadow: 0 15px 35px rgba(0,0,0,0.2);
            text-align: center; direction: rtl;
        }
        </style>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<div class='lock-container'>", unsafe_allow_html=True)
        st.markdown("<h1 style='color:white; text-shadow: 0 4px 10px rgba(0,0,0,0.3); font-size:3rem;'>NEXUS OS</h1>", unsafe_allow_html=True)
        st.markdown("<p style='color:white; font-size:1.2rem;'>הכנס קוד גישה מאובטח</p>", unsafe_allow_html=True)
        
        # הקפצת מקלדת מספרים במובייל
        components.html("""
        <script>
            setTimeout(function() {
                var inputs = window.parent.document.querySelectorAll('input[type="password"]');
                for(var i=0; i<inputs.length; i++){
                    inputs[i].setAttribute('inputmode', 'numeric');
                    inputs[i].setAttribute('pattern', '[0-9]*');
                }
            }, 500);
        </script>
        """, height=0)

        pwd = st.text_input("", type="password", placeholder="****", label_visibility="collapsed")
        if st.button("התחברות למערכת 🚀"):
            if pwd == "7707":
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("קוד שגוי. נסה שוב.")
        st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

# ==========================================
# --- מכאן מתחילה האפליקציה (אחרי התחברות) ---
# ==========================================

# אתחול משתני Session State
if 'lang' not in st.session_state: st.session_state.lang = "עברית"
if 'chat_history' not in st.session_state: st.session_state.chat_history = []
if 'file_contexts' not in st.session_state: st.session_state.file_contexts = {} # מילון לשמירת קבצים לפי מקצוע
if 'font_size' not in st.session_state: st.session_state.font_size = "1.1rem" 

T = {
    "עברית": {
        "title": "NEXUS ACADEMY", "m1": "מרכז אקדמי", "m2": "מנטור AI", "m3": "מסד נתונים", "m4": "הגדרות",
        "avg": "ממוצע משוקלל", "count": "קורסים", "sub": "מקצוע", "grd": "ציון", "cred": "נ\"ז", "sync": "הזן ציון",
        "analyst": "מצב דאטה אנליסט 📊", "ask": "הזן שאלה...", "clear": "נקה זיכרון"
    },
    "English": {
        "title": "NEXUS ACADEMY", "m1": "Dashboard", "m2": "AI Mentor", "m3": "Vault", "m4": "Settings",
        "avg": "Weighted GPA", "count": "Courses", "sub": "Subject", "grd": "Grade", "cred": "Credits", "sync": "Save",
        "analyst": "Analyst Mode 📊", "ask": "Message...", "clear": "Clear Memory"
    }
}
cur = T[st.session_state.lang]

# --- CSS מטורף 3D: אנימציות, צבעים חיים, וזכוכית מרחפת ---
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Assistant:wght@300;600;800&display=swap');
    
    header[data-testid="stHeader"] {{ background: transparent !important; }}
    .stAppDeployButton {{display: none;}}
    footer {{visibility: hidden !important;}}
    html, body {{ max-width: 100vw; overflow-x: hidden; }}
    
    .stApp {{ 
        background: linear-gradient(120deg, #e0c3fc 0%, #8ec5fc 100%);
        color: #2c3e50; font-family: 'Assistant', sans-serif; 
    }}
    
    {" .main, [data-testid='stSidebar'], [data-testid='stChatMessageContent'] { direction: rtl !important; text-align: right !important; } " if st.session_state.lang == "עברית" else ""}

    div[data-testid="stMetric"], .stChatMessage, .stForm {{
        background: rgba(255, 255, 255, 0.4) !important;
        backdrop-filter: blur(15px) !important; -webkit-backdrop-filter: blur(15px) !important;
        border: 1px solid rgba(255, 255, 255, 0.6) !important;
        border-radius: 20px !important;
        box-shadow: 0 10px 25px rgba(0,0,0,0.1) !important;
        padding: 15px;
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }}
    div[data-testid="stMetric"]:hover {{
        transform: translateY(-5px); box-shadow: 0 15px 30px rgba(0,0,0,0.15) !important;
    }}
    
    h1 {{ color: #1e3c72; text-align: center; font-weight: 800; text-shadow: 0 2px 5px rgba(0,0,0,0.1); }}
    
    .stButton>button {{
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        color: white !important; font-weight: 800; border: none; border-radius: 50px !important; width: 100%;
        box-shadow: 0 8px 15px rgba(118, 75, 162, 0.4) !important;
        transition: all 0.3s ease !important;
    }}
    .stButton>button:hover {{ 
        transform: translateY(-4px) !important; 
        box-shadow: 0 15px 20px rgba(118, 75, 162, 0.6) !important; 
    }}
    
    [data-testid="stChatMessageContent"] p, [data-testid="stChatMessageContent"] li {{
        font-size: {st.session_state.font_size} !important; color: #1a1a1a;
    }}
    </style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=60)
def fetch_grades_cached():
    return get_all_grades()

df = fetch_grades_cached()

# --- מנגנון המקצועות הדינמי ---
base_subjects = ["מתמטיקה", "אנגלית", "פיזיקה", "כתיבה אקדמית"]
db_subjects = df['subject'].unique().tolist() if not df.empty else []
# איחוד הרשימות ללא כפילויות
all_subjects = sorted(list(set(base_subjects + db_subjects)))

# --- תפריט צד (ניהול מקצועות, העלאת קבצים) ---
with st.sidebar:
    st.markdown(f"<h2 style='color:#1e3c72; text-align:center;'>NEXUS OS</h2>", unsafe_allow_html=True)
    lang = st.radio("שפת ממשק", ["עברית", "English"], horizontal=True, label_visibility="collapsed")
    if lang != st.session_state.lang: st.session_state.lang = lang; st.rerun()
    st.divider()
    analyst_on = st.toggle(cur["analyst"], value=True)
    
    st.markdown("### 📚 ניהול חומר לימודי")
    
    # 1. הוספת מקצוע חדש
    with st.expander("➕ הוסף מקצוע חדש למערכת"):
        new_sub = st.text_input("שם המקצוע:")
        if st.button("שמור מקצוע"):
            if new_sub and new_sub not in all_subjects:
                # שומר רשומה נסתרת ב-DB כדי שהמערכת תזכור את המקצוע לתמיד
                save_grade(new_sub, "System_Init", 0, 0) 
                fetch_grades_cached.clear()
                st.rerun()
                
    st.divider()
    
    # 2. העלאת קבצים למקצוע ספציפי
    upload_sub = st.selectbox("בחר מקצוע עבור הקובץ:", all_subjects)
    up = st.file_uploader("סריקת PDF/DOCX", type=['pdf', 'docx'])
    if up and st.button("סרוק לזיכרון הבוט"):
        # שומר את הטקסט תחת המקצוע הספציפי
        st.session_state.file_contexts[upload_sub] = extract_text_from_file(up)
        st.success(f"המידע נטען ושויך למקצוע: {upload_sub}")

# --- תפריט ניווט עליון צף ---
menu = option_menu(None, [cur["m1"], cur["m2"], cur["m3"], cur["m4"]], 
                   icons=["bar-chart-fill", "chat-quote-fill", "database-fill", "gear-fill"], 
                   orientation="horizontal",
                   styles={
                       "container": {"padding": "0!important", "background": "rgba(255,255,255,0.6)", "backdrop-filter": "blur(10px)", "border-radius": "20px", "box-shadow": "0 8px 20px rgba(0,0,0,0.1)", "margin-bottom": "25px"},
                       "nav-link-selected": {"background": "linear-gradient(135deg, #667eea, #764ba2)", "font-weight": "bold", "color": "white", "border-radius": "15px"}
                   })

# סינון נתוני מערכת נסתרים (כדי שלא ישפיעו על ממוצע/גרפים)
df_valid = df[df['topic'] != 'System_Init'] if not df.empty else df

if not df_valid.empty:
    if 'credits' not in df_valid.columns: df_valid['credits'] = 1.0
    total_credits = df_valid['credits'].sum()
    weighted_avg = (df_valid['grade'] * df_valid['credits']).sum() / total_credits if total_credits > 0 else 0
else:
    weighted_avg = 0.0

# --- עמוד: מרכז בקרה ---
if menu == cur["m1"]:
    st.markdown(f"<h1>{cur['m1']}</h1>", unsafe_allow_html=True)
    
    c1, c2, c3 = st.columns(3)
    c1.metric(cur["avg"], f"{weighted_avg:.2f}") 
    c2.metric(cur["count"], len(df_valid))
    total_cred_display = df_valid['credits'].sum() if not df_valid.empty else 0
    c3.metric("סה\"כ נ\"ז לתואר", f"{total_cred_display:.1f}")
    
    st.divider()
    l, r = st.columns([1, 2.5])
    with l:
        st.markdown("### 📥 הזנת קורס חדש")
        with st.form("entry", clear_on_submit=True):
            s = st.selectbox(cur["sub"], all_subjects) # מסונכרן עם כל המקצועות!
            c = st.number_input(cur["cred"], min_value=0.5, max_value=10.0, value=3.0, step=0.5)
            g = st.number_input(cur["grd"], min_value=0, max_value=100, value=90)
            if st.form_submit_button(cur["sync"]): 
                save_grade(s, "", g, c)
                fetch_grades_cached.clear()
                st.rerun()
    with r:
        if not df_valid.empty:
            fig = px.bar(df_valid, x='subject', y='grade', color='grade', color_continuous_scale='Purp', title="הישגים לפי מקצועות")
            fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="#1e3c72")
            st.plotly_chart(fig, use_container_width=True)

# --- עמוד: בינה מלאכותית ---
elif menu == cur["m2"]:
    st.markdown(f"<h1>{'NEXUS AI MENTOR' if not analyst_on else 'DATA ANALYST AI'}</h1>", unsafe_allow_html=True)
    
    if not st.session_state.chat_history:
        db_history = get_persistent_chat_history()
        st.session_state.chat_history = [{"role": m["role"], "content": m["content"]} for m in db_history]

    # בחירת מקצוע לשיחה - מסונכרן עם הכל!
    chat_sub = st.selectbox("נושא השיחה (הבוט ייגש לקבצים של מקצוע זה):", all_subjects, index=0)
    
    chat_container = st.container(height=500)
    with chat_container:
        for m in st.session_state.chat_history:
            with st.chat_message(m["role"]):
                st.markdown(f'<div style="text-align: right; direction: rtl;">{m["content"]}</div>', unsafe_allow_html=True)

    if p := st.chat_input(cur["ask"]):
        # מעלים את המקלדת מיד עם השליחה במובייל
        components.html("""<script>window.parent.document.activeElement.blur();</script>""", height=0, width=0)
        
        st.session_state.chat_history.append({"role": "user", "content": p})
        save_chat_message("user", p)
        with chat_container.chat_message("user"):
            st.markdown(f'<div style="text-align: right; direction: rtl;">{p}</div>', unsafe_allow_html=True)
        
        with chat_container.chat_message("assistant"):
            placeholder = st.empty()
            full_res = ""
            # שולף את הטקסט הספציפי שנסרק למקצוע הזה!
            context_for_bot = st.session_state.file_contexts.get(chat_sub, "")
            
            for chunk in get_ai_response_stream(chat_sub, p, st.session_state.chat_history[:-1], context_for_bot, st.session_state.lang, analyst_on):
                full_res += chunk
                placeholder.markdown(f'<div style="text-align: right; direction: rtl;">{full_res}</div>', unsafe_allow_html=True)
        
        st.session_state.chat_history.append({"role": "assistant", "content": full_res})
        save_chat_message("assistant", full_res)

# --- עמוד: מסד נתונים ---
elif menu == cur["m3"]:
    st.markdown(f"<h1>{cur['m3']}</h1>", unsafe_allow_html=True)
    st.dataframe(df_valid, use_container_width=True, height=500) # מציג רק את הציונים האמיתיים

# --- עמוד: הגדרות (Settings) ---
elif menu == cur["m4"]:
    st.markdown(f"<h1>{cur['m4']}</h1>", unsafe_allow_html=True)
    
    st.markdown("### ⚙️ תצוגה וממשק")
    font_size_map = {"קטן": "0.9rem", "רגיל": "1.1rem", "גדול": "1.3rem"}
    current_size_name = [k for k, v in font_size_map.items() if v == st.session_state.font_size][0]
    new_size_name = st.select_slider("גודל טקסט בצ'אט", options=["קטן", "רגיל", "גדול"], value=current_size_name)
    if font_size_map[new_size_name] != st.session_state.font_size:
        st.session_state.font_size = font_size_map[new_size_name]; st.rerun()
        
    st.divider()
    st.markdown("### 🧹 ניהול זיכרון ונתונים")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("מחיקת כל השיחות.")
        if st.button("נקה היסטוריית צ'אט", type="primary"):
            clear_chat_history(); st.session_state.chat_history = []; st.success("נמחק.")
    with c2:
        st.markdown("מחיקת קבצים.")
        if st.button("רוקן זיכרון סורק", type="primary"):
            st.session_state.file_contexts = {}; st.success("נוקה.")
    with c3:
        st.markdown("איפוס ציונים מלא.")
        st.markdown("""<style>div.row-widget.stButton > button[kind="secondary"] {background: linear-gradient(135deg, #ff416c, #ff4b2b) !important; color: white !important;}</style>""", unsafe_allow_html=True)
        if st.button("🚨 אפס מסד נתונים", type="secondary"):
            clear_db(); fetch_grades_cached.clear(); st.rerun()

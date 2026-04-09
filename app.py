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

# --- פתרון שורשי לחלונית התרגום של גוגל (לא נוגע בעיצוב) ---
components.html(
    """
    <script>
        window.parent.document.documentElement.lang = 'he';
        if (!window.parent.document.querySelector('meta[name="google"]')) {
            var meta = window.parent.document.createElement('meta');
            meta.name = 'google';
            meta.content = 'notranslate';
            window.parent.document.getElementsByTagName('head')[0].appendChild(meta);
        }
    </script>
    """,
    width=0, height=0
)

# תמונת רקע - 4K High-End
BG_IMAGE_URL = "https://images.unsplash.com/photo-1507842217343-583bb7270b66?q=80&w=2560&auto=format&fit=crop"

# --- מסך נעילה חכם וסינמטי ---
if 'authenticated' not in st.session_state: st.session_state.authenticated = False
if 'dark_mode' not in st.session_state: st.session_state.dark_mode = False

if not st.session_state.authenticated:
    st.markdown(f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Heebo:wght@300;400;700;900&family=Inter:wght@400;700&display=swap');
        html, body {{ font-family: 'Heebo', sans-serif; }}
        .stApp {{ 
            background-image: linear-gradient(rgba(5, 10, 20, 0.7), rgba(0, 0, 0, 0.9)), url('{BG_IMAGE_URL}'); 
            background-size: cover; background-position: center; background-attachment: fixed;
            display: flex; align-items: center; justify-content: center; 
        }}
        @keyframes fadeInLock {{ from {{ opacity: 0; transform: translateY(30px) scale(0.95); }} to {{ opacity: 1; transform: translateY(0) scale(1); }} }}
        @keyframes pulseGlow {{ 0% {{ text-shadow: 0 0 15px rgba(59, 130, 246, 0.5); }} 50% {{ text-shadow: 0 0 30px rgba(139, 92, 246, 0.8), 0 0 10px rgba(59, 130, 246, 0.5); }} 100% {{ text-shadow: 0 0 15px rgba(59, 130, 246, 0.5); }} }}
        .lock-container {{ 
            background: rgba(20, 25, 35, 0.4); 
            backdrop-filter: blur(30px) saturate(150%); 
            -webkit-backdrop-filter: blur(30px) saturate(150%);
            border: 1px solid rgba(255, 255, 255, 0.1); 
            border-radius: 40px; 
            padding: 60px 50px; 
            box-shadow: 0 40px 80px rgba(0,0,0,0.8), inset 0 1px 0 rgba(255,255,255,0.2); 
            text-align: center; 
            direction: rtl;
            animation: fadeInLock 1s cubic-bezier(0.16, 1, 0.3, 1) forwards;
        }}
        h1.nexus-title {{ color: #ffffff; font-size: 4rem; font-weight: 900; letter-spacing: 4px; animation: pulseGlow 4s infinite; margin-bottom: 0; }}
        input[type="password"] {{ 
            font-size: 2.5rem !important; text-align: center !important; letter-spacing: 1rem; 
            background: rgba(255,255,255,0.05) !important; color: #fff !important; 
            border: 2px solid rgba(255,255,255,0.2) !important; border-radius: 20px !important; 
            box-shadow: inset 0 4px 10px rgba(0,0,0,0.5); transition: all 0.3s;
        }}
        input[type="password"]:focus {{ border-color: #8b5cf6 !important; box-shadow: 0 0 20px rgba(139, 92, 246, 0.4), inset 0 4px 10px rgba(0,0,0,0.5) !important; }}
        </style>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<div class='lock-container'><h1 class='nexus-title'>NEXUS</h1><p style='color:#94a3b8; font-size:1.1rem; font-weight:400; margin-top:5px; margin-bottom:30px;'>מערכת ליבה מנותקת</p>", unsafe_allow_html=True)
        components.html("""<script>setTimeout(function() { var inputs = window.parent.document.querySelectorAll('input[type="password"]'); for(var i=0; i<inputs.length; i++){ inputs[i].setAttribute('inputmode', 'numeric'); inputs[i].setAttribute('pattern', '[0-9]*'); } }, 500);</script>""", height=0)
        pwd = st.text_input("", type="password", placeholder="****", max_chars=4, label_visibility="collapsed")
        if pwd == "5050": st.session_state.authenticated = True; st.rerun()
        elif len(pwd) == 4 and pwd != "5050": st.error("קוד שגיאה: הרשאה נדחתה.")
        st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

# ==========================================
# --- מכאן מתחילה האפליקציה ---
# ==========================================

if 'lang' not in st.session_state: st.session_state.lang = "עברית"
if 'chat_history' not in st.session_state: st.session_state.chat_history = []
if 'file_contexts' not in st.session_state: st.session_state.file_contexts = {} 
if 'font_size' not in st.session_state: st.session_state.font_size = "1.1rem" 

# --- ברכת שלום חכמה (מתורגמת) ---
def get_greeting(lang):
    hour = datetime.datetime.now(ZoneInfo("Asia/Jerusalem")).hour
    if lang == "עברית":
        if 5 <= hour < 12: return "בוקר טוב, מנדי עקיבא! ✨"
        elif 12 <= hour < 18: return "צהריים טובים, מנדי עקיבא! ✨"
        elif 18 <= hour < 22: return "ערב טוב, מנדי עקיבא! ✨"
        else: return "לילה טוב, מנדי עקיבא! ✨"
    else:
        if 5 <= hour < 12: return "Good Morning, Mendi Akiva! ✨"
        elif 12 <= hour < 18: return "Good Afternoon, Mendi Akiva! ✨"
        elif 18 <= hour < 22: return "Good Evening, Mendi Akiva! ✨"
        else: return "Good Night, Mendi Akiva! ✨"

greeting_text = get_greeting(st.session_state.lang)

# מילון השפות
T = {
    "עברית": {
        "title": "NEXUS ACADEMY", "m1": "מרכז אקדמי", "m2": "צ'אט AI", "m3": "מסד נתונים", "m4": "לוח משימות 📅", "m5": "הגדרות",
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

# --- משתני עיצוב דינמיים לפי מצב לילה/יום ---
if st.session_state.dark_mode:
    overlay = "rgba(15, 23, 42, 0.85)"
    text_color = "#f8fafc"
    glass_bg = "rgba(30, 41, 59, 0.65)"
    border_color = "rgba(255, 255, 255, 0.1)"
    accent_gradient = "linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%)"
    accent_shadow = "rgba(139, 92, 246, 0.4)"
else:
    overlay = "rgba(240, 245, 255, 0.85)"
    text_color = "#0f172a"
    glass_bg = "rgba(255, 255, 255, 0.75)"
    border_color = "rgba(255, 255, 255, 0.5)"
    accent_gradient = "linear-gradient(135deg, #0ea5e9 0%, #6366f1 100%)"
    accent_shadow = "rgba(99, 102, 241, 0.3)"

bg_css = f"background-image: linear-gradient({overlay}, {overlay}), url('{BG_IMAGE_URL}'); background-size: cover; background-position: center; background-attachment: fixed;"

# --- קוד ה-CSS המקיף והמשודרג ---
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Heebo:wght@300;400;600;800;900&family=Inter:wght@400;700&display=swap');
    
    /* Global Settings & Animations */
    html, body, [class*="css"] {{ font-family: 'Heebo', 'Inter', sans-serif !important; }}
    header[data-testid="stHeader"] {{ background: transparent !important; }}
    .stAppDeployButton {{display: none;}} footer {{visibility: hidden !important;}} 
    html, body {{ max-width: 100vw; overflow-x: hidden; }}
    .stApp {{ {bg_css} color: {text_color}; }}
    
    @keyframes slideUpFade {{ from {{ opacity: 0; transform: translateY(20px); }} to {{ opacity: 1; transform: translateY(0); }} }}
    
    {" .main, [data-testid='stSidebar'], [data-testid='stChatMessageContent'] { direction: rtl !important; text-align: right !important; } " if st.session_state.lang == "עברית" else ""}
    
    /* Scrollbar Premium */
    ::-webkit-scrollbar {{ width: 6px; height: 6px; }}
    ::-webkit-scrollbar-track {{ background: transparent; }}
    ::-webkit-scrollbar-thumb {{ background: {accent_shadow}; border-radius: 10px; }}
    ::-webkit-scrollbar-thumb:hover {{ background: #8b5cf6; }}

    /* Glassmorphism Cards (Metrics, Chat, Forms) */
    div[data-testid="stMetric"], .stChatMessage, .stForm, div[data-testid="stExpander"] {{ 
        background: {glass_bg} !important; 
        backdrop-filter: blur(20px) saturate(180%) !important; 
        -webkit-backdrop-filter: blur(20px) saturate(180%) !important;
        border: 1px solid {border_color} !important; 
        border-radius: 24px !important; 
        box-shadow: 0 10px 30px rgba(0,0,0, 0.1) !important; 
        padding: 20px; 
        transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275); 
        color: {text_color} !important; 
        animation: slideUpFade 0.6s ease-out forwards;
    }}
    
    /* Hover Effects for Cards */
    div[data-testid="stMetric"]:hover, .stForm:hover {{ 
        transform: translateY(-8px) scale(1.01); 
        box-shadow: 0 20px 40px {accent_shadow} !important; 
        border-color: rgba(139, 92, 246, 0.4) !important;
    }}
    
    h1, h2, h3 {{ color: {text_color}; text-align: center; font-weight: 800; letter-spacing: -0.5px; }}
    
    /* Buttons Premium Styling */
    .stButton>button {{ 
        background: {accent_gradient} !important; 
        color: #ffffff !important; 
        font-weight: 800; font-size: 1.1rem;
        border: none; 
        border-radius: 50px !important; 
        width: 100%; 
        padding: 12px;
        box-shadow: 0 8px 20px {accent_shadow} !important; 
        transition: all 0.3s ease !important; 
        text-transform: uppercase; letter-spacing: 1px; 
    }}
    .stButton>button:hover {{ 
        transform: translateY(-4px) scale(1.02) !important; 
        box-shadow: 0 12px 25px rgba(139, 92, 246, 0.6) !important; 
        filter: brightness(1.1);
    }}
    .stButton>button:active {{ transform: translateY(0) scale(0.98) !important; }}
    
    /* Typography inside elements */
    [data-testid="stChatMessageContent"] p, [data-testid="stChatMessageContent"] li {{ font-size: {st.session_state.font_size} !important; color: {text_color}; line-height: 1.6; }}
    [data-testid="stMetricValue"] {{ font-family: 'Inter', sans-serif !important; font-weight: 900 !important; font-size: 2.5rem !important; background: {accent_gradient}; -webkit-background-clip: text; -webkit-text-fill-color: transparent; }}
    
    /* Chat Input Bar */
    .stChatInputContainer {{ background: {glass_bg} !important; border-radius: 30px !important; border: 1px solid {border_color} !important; backdrop-filter: blur(20px) !important; padding: 5px 10px; box-shadow: 0 10px 30px rgba(0,0,0,0.1) !important; }}
    
    .greeting-box {{ text-align: center; font-size: 2.2rem; font-weight: 900; color: {text_color}; margin-top: -20px; margin-bottom: 30px; letter-spacing: -1px; text-shadow: 0px 4px 15px rgba(0,0,0,0.1); animation: slideUpFade 0.8s ease-out forwards; }}
    </style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=60)
def fetch_grades_cached(): return get_all_grades()

@st.cache_data(ttl=60)
def fetch_tasks_cached(): return get_all_tasks()

df = fetch_grades_cached()
tasks_df = fetch_tasks_cached()

# --- מנגנון המקצועות החכם (מתורגם) ---
if st.session_state.lang == "עברית":
    base_subjects = ["כללי", "מתמטיקה", "מדעי המחשב", "אנגלית", "פיזיקה", "כתיבה אקדמית"]
    add_new_str = "➕ הוסף מקצוע חדש..."
else:
    base_subjects = ["General", "Math", "Computer Science", "English", "Physics", "Academic Writing"]
    add_new_str = "➕ Add New Subject..."

db_subjects = df['subject'].unique().tolist() if not df.empty else []
temp_subjects = set(base_subjects + db_subjects)
if "➕ הוסף מקצוע חדש..." in temp_subjects: temp_subjects.remove("➕ הוסף מקצוע חדש...")
if "➕ Add New Subject..." in temp_subjects: temp_subjects.remove("➕ Add New Subject...")
if "System_Init" in temp_subjects: temp_subjects.remove("System_Init")

all_subjects = sorted(list(temp_subjects)) + [add_new_str]

idx_math = all_subjects.index("מתמטיקה") if "מתמטיקה" in all_subjects else (all_subjects.index("Math") if "Math" in all_subjects else 0)
idx_general = all_subjects.index("כללי") if "כללי" in all_subjects else (all_subjects.index("General") if "General" in all_subjects else 0)

# --- תפריט צד משודרג ---
with st.sidebar:
    st.markdown(f"<h2 style='background: {accent_gradient}; -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-size: 2.5rem; font-weight: 900; text-align: center; margin-bottom: 20px;'>NEXUS OS</h2>", unsafe_allow_html=True)
    lang = st.radio("שפת ממשק / Language", ["עברית", "English"], horizontal=True, label_visibility="collapsed")
    if lang != st.session_state.lang: st.session_state.lang = lang; st.rerun()
    st.session_state.dark_mode = st.toggle("🌙 מצב לילה" if st.session_state.lang == "עברית" else "🌙 Night Mode", value=st.session_state.dark_mode)
    st.divider()
    analyst_on = st.toggle(cur["analyst"], value=True)
    st.markdown("### 📚 ניהול חומר לימודי" if st.session_state.lang == "עברית" else "### 📚 Study Materials")
    upload_sub = st.selectbox("בחר מקצוע:" if st.session_state.lang == "עברית" else "Select Subject:", all_subjects[:-1], index=idx_math)
    up = st.file_uploader("העלאה" if st.session_state.lang == "עברית" else "Upload", type=None)
    if up and st.button("סרוק" if st.session_state.lang == "עברית" else "Scan"):
        st.session_state.file_contexts[upload_sub] = extract_text_from_file(up)
        st.success(f"נטען ל: {upload_sub}")

st.markdown(f"<div class='greeting-box'>{greeting_text}</div>", unsafe_allow_html=True)

# --- תפריט ניווט צף ומרכזי (Floating Dock Style) ---
menu = option_menu(None, [cur["m1"], cur["m2"], cur["m3"], cur["m4"], cur["m5"]], 
                   icons=["grid-1x2-fill", "chat-right-quote-fill", "hdd-stack-fill", "calendar2-check-fill", "sliders"], 
                   orientation="horizontal",
                   styles={
                       "container": {
                           "padding": "8px!important", 
                           "background": glass_bg, 
                           "backdrop-filter": "blur(25px)", 
                           "border": f"1px solid {border_color}",
                           "border-radius": "40px", 
                           "box-shadow": "0 15px 35px rgba(0,0,0,0.15)", 
                           "margin-bottom": "40px",
                           "max-width": "900px",
                           "margin-left": "auto",
                           "margin-right": "auto"
                       },
                       "icon": {"color": text_color, "font-size": "1.3rem"}, 
                       "nav-link": {
                           "font-size": "1.1rem", "font-weight": "600",
                           "text-align": "center", "margin":"0px 5px", 
                           "color": text_color, "border-radius": "30px",
                           "transition": "all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1)"
                       },
                       "nav-link-selected": {
                           "background": accent_gradient, 
                           "font-weight": "800", 
                           "color": "#ffffff", 
                           "box-shadow": f"0 8px 20px {accent_shadow}",
                           "transform": "scale(1.05)"
                       }
                   })

df_valid = df[df['topic'] != 'System_Init'] if not df.empty else df
total_credits = 0.0
weighted_avg = 0.0
if not df_valid.empty:
    if 'credits' not in df_valid.columns: df_valid['credits'] = 1.0
    total_credits = df_valid['credits'].sum()
    if total_credits > 0:
        weighted_avg = (df_valid['grade'] * df_valid['credits']).sum() / total_credits

# --- עמוד: מרכז אקדמי ---
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
            new_sub_input = st.text_input("שם מקצוע חדש:" if st.session_state.lang == "עברית" else "New Subject:") if selected_sub == add_new_str else ""
            c = st.number_input(cur["cred"], min_value=0.5, max_value=10.0, value=3.0, step=0.5)
            g = st.number_input(cur["grd"], min_value=0, max_value=100, value=90)
            if st.form_submit_button(cur["sync"]): 
                final_subject = new_sub_input if selected_sub == add_new_str else selected_sub
                if final_subject: save_grade(final_subject, "", g, c); fetch_grades_cached.clear(); st.rerun()
        with st.expander("מחשבון חיזוי ציון" if st.session_state.lang == "עברית" else "Grade Predictor"):
            sim_c = st.number_input("נ\"ז" if st.session_state.lang == "עברית" else "Credits", 1.0, 10.0, 3.0)
            sim_g = st.number_input("ציון" if st.session_state.lang == "עברית" else "Grade", 0, 100, 90)
            if st.button("חשב" if st.session_state.lang == "עברית" else "Calculate"):
                new_tot = total_credits + sim_c
                new_avg = ((weighted_avg * total_credits) + (sim_g * sim_c)) / new_tot if new_tot > 0 else 0
                st.success(f"ממוצע צפוי: {new_avg:.2f}")
    with r:
        if not df_valid.empty:
            tab1, tab2, tab3 = st.tabs(["גרף ציונים", "עוגת נ\"ז", "מגמת זמן"] if st.session_state.lang == "עברית" else ["Grades", "Credits", "Trend"])
            with tab1:
                fig = px.bar(df_valid, x='subject', y='grade', color='grade', color_continuous_scale='Purpor' if st.session_state.dark_mode else 'Blues')
                fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color=text_color, font_family="Heebo")
                st.plotly_chart(fig, use_container_width=True)
            with tab2:
                fig2 = px.pie(df_valid, values='credits', names='subject', hole=0.45, color_discrete_sequence=px.colors.qualitative.Pastel)
                fig2.update_layout(paper_bgcolor='rgba(0,0,0,0)', font_color=text_color, font_family="Heebo")
                st.plotly_chart(fig2, use_container_width=True)
            with tab3:
                df_time = df_valid.copy().sort_values('created_at')
                df_time['rolling_avg'] = df_time['grade'].expanding().mean()
                fig3 = px.line(df_time, x='created_at', y='rolling_avg', markers=True, line_shape='spline')
                fig3.update_traces(line_color='#8b5cf6', marker=dict(size=10, color='#3b82f6'))
                fig3.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color=text_color, font_family="Heebo")
                st.plotly_chart(fig3, use_container_width=True)

# --- עמוד: בינה מלאכותית ---
elif menu == cur["m2"]:
    st.markdown(f"<h1>{'🧠 NEXUS AI MENTOR' if not analyst_on else '💻 DATA ANALYST AI'}</h1>", unsafe_allow_html=True)
    if not st.session_state.chat_history:
        db_history = get_persistent_chat_history()
        st.session_state.chat_history = [{"role": m["role"], "content": m["content"]} for m in db_history]
    colA, colB = st.columns([3, 1])
    with colA: chat_sub = st.selectbox("נושא למיקוד:" if st.session_state.lang == "עברית" else "Focus Subject:", all_subjects[:-1], index=idx_general)
    with colB: 
        if st.button("📝 בחן אותי" if st.session_state.lang == "עברית" else "📝 Quiz Me"):
            if chat_sub in st.session_state.file_contexts:
                context_for_bot = st.session_state.file_contexts[chat_sub]
                placeholder = st.empty()
                full_res = ""
                for chunk in get_ai_response_stream(chat_sub, "ייצר לי מבחן.", [], context_for_bot, st.session_state.lang, analyst_on, is_quiz=True):
                    full_res += chunk
                    placeholder.markdown(f'<div style="text-align: right; direction: rtl; background: {glass_bg}; padding:20px; border-radius:15px; border: 1px solid {accent_shadow};">{full_res}</div>', unsafe_allow_html=True)
    chat_container = st.container(height=500)
    with chat_container:
        for m in st.session_state.chat_history:
            bubble_color = "rgba(59, 130, 246, 0.15)" if m["role"] == "user" else "transparent"
            border_radius = "20px 20px 5px 20px" if m["role"] == "user" else "20px 20px 20px 5px"
            with st.chat_message(m["role"]): 
                st.markdown(f'<div style="text-align: right; direction: rtl; background: {bubble_color}; padding: 15px; border-radius: {border_radius};">{m["content"]}</div>', unsafe_allow_html=True)
    if p := st.chat_input(cur["ask"]):
        components.html("""<script>window.parent.document.activeElement.blur();</script>""", height=0, width=0)
        st.session_state.chat_history.append({"role": "user", "content": p})
        save_chat_message("user", p)
        with chat_container.chat_message("user"): st.markdown(f'<div style="text-align: right; direction: rtl; background: rgba(59, 130, 246, 0.15); padding: 15px; border-radius: 20px 20px 5px 20px;">{p}</div>', unsafe_allow_html=True)
        with chat_container.chat_message("assistant"):
            placeholder = st.empty()
            full_res = ""
            context_for_bot = st.session_state.file_contexts.get(chat_sub, "")
            for chunk in get_ai_response_stream(chat_sub, p, st.session_state.chat_history[:-1], context_for_bot, st.session_state.lang, analyst_on):
                full_res += chunk
                placeholder.markdown(f'<div style="text-align: right; direction: rtl; padding: 15px;">{full_res}</div>', unsafe_allow_html=True)
        st.session_state.chat_history.append({"role": "assistant", "content": full_res})
        save_chat_message("assistant", full_res)

# --- עמוד: מסד נתונים ---
elif menu == cur["m3"]:
    col1, col2 = st.columns([3, 1])
    with col1: st.markdown("<h1>🗄️ System Vault</h1>", unsafe_allow_html=True)
    with col2:
        if not df_valid.empty:
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer: df_valid.to_excel(writer, index=False)
            st.download_button(label="📥 הורד כ-Excel", data=buffer.getvalue(), file_name="NEXUS_Grades.xlsx")
    
    st.markdown(f"""
        <style>
        [data-testid="stDataFrame"] {{ border-radius: 20px; overflow: hidden; border: 1px solid {border_color}; box-shadow: 0 10px 30px rgba(0,0,0,0.1); }}
        </style>
    """, unsafe_allow_html=True)
    st.dataframe(df_valid, use_container_width=True, height=500) 

# --- עמוד: לוח משימות ---
elif menu == cur["m4"]:
    st.markdown("<h1>📌 לוח משימות אקטיבי</h1>" if st.session_state.lang == "עברית" else "<h1>📌 Active Task Board</h1>", unsafe_allow_html=True)
    colA, colB = st.columns([1, 2.5])
    with colA:
        with st.form("new_task", clear_on_submit=True):
            t_title = st.text_input("תיאור המשימה" if st.session_state.lang == "עברית" else "Task Description")
            t_sub = st.selectbox(cur["sub"], all_subjects[:-1])
            t_date = st.date_input("תאריך יעד" if st.session_state.lang == "עברית" else "Due Date")
            if st.form_submit_button("הוסף משימה ➕"): save_task(t_title, t_sub, t_date); fetch_tasks_cached.clear(); st.rerun()
    with colB:
        if not tasks_df.empty:
            for index, row in tasks_df.iterrows():
                days = (pd.to_datetime(row['due_date']).date() - datetime.date.today()).days
                status_color = "#10b981" if days > 3 else ("#f59e0b" if days >= 0 else "#ef4444")
                st.markdown(f"""
                    <div style="background: {glass_bg}; backdrop-filter: blur(15px); border-right: 6px solid {status_color}; border-radius: 15px; padding: 15px 25px; margin-bottom: 15px; box-shadow: 0 5px 15px rgba(0,0,0,0.05); display: flex; justify-content: space-between; align-items: center;">
                        <div style="direction: rtl; text-align: right;">
                            <span style="font-size: 1.2rem; font-weight: 800; color: {text_color};">{row['title']}</span>
                            <br><span style="font-size: 0.9rem; color: #64748b; font-weight: 600;">📚 {row['subject']} • ⏳ נותרו {days} ימים</span>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
                if st.button("סמן כבוצע ✔️", key=f"d_{row['id']}"): delete_task(row['id']); fetch_tasks_cached.clear(); st.rerun()

# --- עמוד: הגדרות ---
elif menu == cur["m5"]:
    st.markdown(f"<h1>⚙️ {cur['m5']} מערכת</h1>", unsafe_allow_html=True)
    font_size_map = {"קטן": "0.9rem", "רגיל": "1.1rem", "גדול": "1.3rem"} if st.session_state.lang == "עברית" else {"Small": "0.9rem", "Normal": "1.1rem", "Large": "1.3rem"}
    cur_size = [k for k, v in font_size_map.items() if v == st.session_state.font_size][0]
    new_size = st.select_slider("גודל טקסט במערכת" if st.session_state.lang == "עברית" else "System Font Size", options=list(font_size_map.keys()), value=cur_size)
    if font_size_map[new_size] != st.session_state.font_size: st.session_state.font_size = font_size_map[new_size]; st.rerun()
    st.divider()
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("🗑️ נקה היסטוריית צ'אט"): clear_chat_history(); st.session_state.chat_history = []; st.rerun()
    with c2:
        if st.button("🧹 נקה קבצים מהסורק"): st.session_state.file_contexts = {}; st.rerun()
    with c3:
        if st.button("🚨 איפוס מסד נתונים מלא (Danger)"): clear_db(); fetch_grades_cached.clear(); st.rerun()

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

# --- הגדרות ליבה (Command Center) ---
st.set_page_config(page_title="NEXUS CORE OS", page_icon="🌌", layout="wide", initial_sidebar_state="collapsed")

# תמונת רקע - חלל/רשת נירונים (SpaceX / Neuralink Vibe)
BG_IMAGE_URL = "https://images.unsplash.com/photo-1451187580459-43490279c0fa?q=80&w=2560&auto=format&fit=crop"

# ==========================================
# --- מסך נעילה ביטחוני סופר-פרימיום ---
# ==========================================
if 'authenticated' not in st.session_state: st.session_state.authenticated = False
if 'dark_mode' not in st.session_state: st.session_state.dark_mode = True # Default to Dark Mode for the Cyber look

if not st.session_state.authenticated:
    st.markdown(f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Heebo:wght@300;400;700;900&family=JetBrains+Mono:wght@400;700&display=swap');
        html, body {{ font-family: 'Heebo', sans-serif; background-color: #000; overflow: hidden; }}
        .stApp {{ 
            background-image: linear-gradient(rgba(0, 5, 15, 0.85), rgba(0, 0, 0, 0.95)), url('{BG_IMAGE_URL}'); 
            background-size: cover; background-position: center; 
            display: flex; align-items: center; justify-content: center; height: 100vh;
        }}
        /* אובייקט סריקה שעובר על המסך */
        .scan-line {{
            position: absolute; width: 100%; height: 4px; background: rgba(0, 255, 255, 0.5);
            box-shadow: 0 0 20px rgba(0, 255, 255, 0.8);
            animation: scan 4s linear infinite; top: 0; left: 0; z-index: 999; pointer-events: none;
        }}
        @keyframes scan {{ 0% {{ top: -10%; opacity: 0; }} 10% {{ opacity: 1; }} 90% {{ opacity: 1; }} 100% {{ top: 110%; opacity: 0; }} }}
        @keyframes bootUp {{ 0% {{ filter: brightness(0) contrast(2); transform: scale(0.9); }} 100% {{ filter: brightness(1) contrast(1); transform: scale(1); }} }}
        
        .terminal-box {{ 
            background: rgba(10, 15, 25, 0.6); 
            backdrop-filter: blur(40px) saturate(200%); -webkit-backdrop-filter: blur(40px);
            border: 1px solid rgba(0, 255, 255, 0.15); border-radius: 20px; 
            padding: 60px; box-shadow: 0 0 50px rgba(0,0,0,0.8), inset 0 0 20px rgba(0, 255, 255, 0.05); 
            text-align: center; direction: rtl; max-width: 500px; margin: auto;
            animation: bootUp 1.5s cubic-bezier(0.16, 1, 0.3, 1) forwards;
            position: relative; overflow: hidden;
        }}
        .terminal-box::before {{ content: ''; position: absolute; top: 0; left: 0; right: 0; height: 2px; background: linear-gradient(90deg, transparent, #00f2fe, transparent); }}
        
        h1.nexus-title {{ font-family: 'JetBrains Mono', monospace; color: #fff; font-size: 3.5rem; font-weight: 700; letter-spacing: 5px; text-shadow: 0 0 20px rgba(0, 242, 254, 0.6); margin-bottom: 5px; }}
        .status-text {{ font-family: 'JetBrains Mono', monospace; color: #00f2fe; font-size: 0.9rem; text-transform: uppercase; letter-spacing: 2px; margin-bottom: 40px; }}
        
        input[type="password"] {{ 
            font-family: 'JetBrains Mono', monospace !important; font-size: 2.5rem !important; text-align: center !important; letter-spacing: 1.5rem; 
            background: rgba(0,0,0,0.5) !important; color: #00f2fe !important; 
            border: 1px solid rgba(0, 242, 254, 0.3) !important; border-radius: 12px !important; 
            box-shadow: inset 0 0 15px rgba(0,0,0,0.8); transition: all 0.3s ease;
        }}
        input[type="password"]:focus {{ border-color: #00f2fe !important; box-shadow: 0 0 30px rgba(0, 242, 254, 0.2), inset 0 0 15px rgba(0,0,0,0.8) !important; outline: none; }}
        </style>
        <div class="scan-line"></div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<div class='terminal-box'><h1 class='nexus-title'>NEXUS_OS</h1><p class='status-text'>Awaiting Authorization_</p>", unsafe_allow_html=True)
        components.html("""<script>setTimeout(function() { var inputs = window.parent.document.querySelectorAll('input[type="password"]'); for(var i=0; i<inputs.length; i++){ inputs[i].setAttribute('inputmode', 'numeric'); inputs[i].setAttribute('pattern', '[0-9]*'); } }, 500);</script>""", height=0)
        pwd = st.text_input("", type="password", placeholder="****", max_chars=4, label_visibility="collapsed")
        if pwd == "5050": 
            st.session_state.authenticated = True; st.rerun()
        elif len(pwd) == 4 and pwd != "5050": 
            st.error("ACCESS DENIED.")
        st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

# ==========================================
# --- מערכת הליבה - NEXUS OS ---
# ==========================================

if 'lang' not in st.session_state: st.session_state.lang = "עברית"
if 'chat_history' not in st.session_state: st.session_state.chat_history = []
if 'file_contexts' not in st.session_state: st.session_state.file_contexts = {} 
if 'font_size' not in st.session_state: st.session_state.font_size = "1.1rem" 

# --- מנוע ברכות סמארט ---
def get_greeting(lang):
    hour = datetime.datetime.now(ZoneInfo("Asia/Jerusalem")).hour
    if lang == "עברית":
        if 5 <= hour < 12: return "בוקר טוב, מנדי עקיבא."
        elif 12 <= hour < 18: return "צהריים טובים, מנדי עקיבא."
        elif 18 <= hour < 22: return "ערב טוב, מנדי עקיבא."
        else: return "לילה טוב, מנדי עקיבא."
    else:
        if 5 <= hour < 12: return "Good Morning, Mendi."
        elif 12 <= hour < 18: return "Good Afternoon, Mendi."
        elif 18 <= hour < 22: return "Good Evening, Mendi."
        else: return "Good Night, Mendi."

greeting_text = get_greeting(st.session_state.lang)

# --- מילון שפות ---
T = {
    "עברית": {
        "m1": "מרכז בקרה", "m2": "בינה מלאכותית", "m3": "מסד נתונים", "m4": "משימות ויעדים", "m5": "הגדרות מערכת",
        "avg": "ממוצע משוקלל", "count": "קורסים הושלמו", "sub": "מקצוע", "grd": "ציון", "cred": "נ\"ז", "sync": "סנכרן נתונים",
        "analyst": "מצב Analyst 📊", "ask": "פקודה חדשה ל-AI...", "clear": "נקה זיכרון"
    },
    "English": {
        "m1": "Command Center", "m2": "AI Terminal", "m3": "Data Vault", "m4": "Objectives", "m5": "System Config",
        "avg": "Weighted GPA", "count": "Courses Completed", "sub": "Subject", "grd": "Grade", "cred": "Credits", "sync": "Sync Data",
        "analyst": "Analyst Mode 📊", "ask": "New AI Command...", "clear": "Clear Memory"
    }
}
cur = T[st.session_state.lang]

# --- משתני עיצוב פרימיום (SpaceX/Tesla Vibe) ---
if st.session_state.dark_mode:
    bg_overlay = "rgba(5, 8, 15, 0.88)"
    glass_bg = "rgba(15, 20, 30, 0.5)"
    text_color = "#e2e8f0"
    accent_color = "#00f2fe"
    accent_grad = "linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)"
    border_color = "rgba(0, 242, 254, 0.15)"
else:
    bg_overlay = "rgba(248, 250, 252, 0.85)"
    glass_bg = "rgba(255, 255, 255, 0.6)"
    text_color = "#0f172a"
    accent_color = "#2563eb"
    accent_grad = "linear-gradient(135deg, #2563eb 0%, #3b82f6 100%)"
    border_color = "rgba(37, 99, 235, 0.2)"

# --- CSS מפלצתי - UI של חללית ---
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Heebo:wght@300;400;500;700;900&family=JetBrains+Mono:wght@400;700;800&display=swap');
    
    html, body, [class*="css"] {{ font-family: 'Heebo', sans-serif !important; }}
    header[data-testid="stHeader"] {{ display: none !important; }}
    .stAppDeployButton {{display: none;}} footer {{display: none !important;}} 
    
    .stApp {{ 
        background-image: linear-gradient({bg_overlay}, {bg_overlay}), url('{BG_IMAGE_URL}'); 
        background-size: cover; background-position: center; background-attachment: fixed; color: {text_color}; 
    }}
    
    {" .main, [data-testid='stSidebar'], [data-testid='stChatMessageContent'] { direction: rtl !important; text-align: right !important; } " if st.session_state.lang == "עברית" else ""}
    
    /* הנדסת גלילה מודרנית */
    ::-webkit-scrollbar {{ width: 4px; height: 4px; }}
    ::-webkit-scrollbar-track {{ background: transparent; }}
    ::-webkit-scrollbar-thumb {{ background: {accent_color}; border-radius: 10px; opacity: 0.5; }}
    
    /* Bento-Box / Glass Cards התאמה מושלמת למכולות */
    div[data-testid="stMetric"], .stChatMessage, .stForm, div[data-testid="stExpander"], div[data-testid="stDataFrame"], .task-card {{ 
        background: {glass_bg} !important; 
        backdrop-filter: blur(25px) saturate(180%) !important; -webkit-backdrop-filter: blur(25px);
        border: 1px solid {border_color} !important; 
        border-radius: 16px !important; 
        box-shadow: 0 8px 32px rgba(0,0,0, 0.2), inset 0 1px 1px rgba(255,255,255,0.05) !important; 
        padding: 24px; transition: all 0.3s ease; color: {text_color} !important; 
    }}
    
    div[data-testid="stMetric"]:hover, .task-card:hover {{ transform: translateY(-4px); border-color: {accent_color} !important; box-shadow: 0 15px 40px rgba(0,0,0,0.4), inset 0 1px 1px rgba(255,255,255,0.1) !important; }}
    
    /* טיפוגרפיה של מדדים - סגנון דאטה אנליסט */
    [data-testid="stMetricValue"] {{ font-family: 'JetBrains Mono', monospace !important; font-weight: 800 !important; font-size: 3.2rem !important; background: {accent_grad}; -webkit-background-clip: text; -webkit-text-fill-color: transparent; }}
    [data-testid="stMetricLabel"] {{ font-size: 1.1rem !important; font-weight: 500 !important; text-transform: uppercase; letter-spacing: 1px; color: #94a3b8 !important; }}
    
    /* כפתורים רובוטיים מדויקים */
    .stButton>button {{ 
        background: rgba(255,255,255,0.05) !important; color: {accent_color} !important; 
        font-family: 'JetBrains Mono', monospace; font-weight: 700; font-size: 1rem;
        border: 1px solid {accent_color} !important; border-radius: 8px !important; 
        padding: 10px 24px; transition: all 0.2s; text-transform: uppercase; letter-spacing: 1px;
    }}
    .stButton>button:hover {{ background: {accent_grad} !important; color: #fff !important; box-shadow: 0 0 20px {border_color} !important; transform: scale(1.02); }}
    
    /* שדות קלט בסגנון טרמינל */
    .stTextInput>div>div>input, .stNumberInput>div>div>input, .stSelectbox>div>div>div {{ 
        background: rgba(0,0,0,0.3) !important; border: 1px solid rgba(255,255,255,0.1) !important; color: {text_color} !important; border-radius: 8px !important; font-family: 'Heebo';
    }}
    .stTextInput>div>div>input:focus {{ border-color: {accent_color} !important; box-shadow: 0 0 10px rgba(0,242,254,0.2) !important; }}
    
    /* תיבת הודעות למעלה */
    .hud-header {{ display: flex; justify-content: space-between; align-items: flex-end; border-bottom: 1px solid {border_color}; padding-bottom: 20px; margin-bottom: 30px; }}
    .hud-title {{ font-family: 'JetBrains Mono', monospace; font-size: 1.8rem; font-weight: 800; margin: 0; color: {text_color}; letter-spacing: 2px; }}
    .hud-subtitle {{ font-size: 1rem; color: #94a3b8; font-weight: 400; margin: 0; }}
    
    /* צ'אט */
    .stChatInputContainer {{ background: {glass_bg} !important; border-radius: 16px !important; border: 1px solid {border_color} !important; backdrop-filter: blur(20px) !important; }}
    [data-testid="stChatMessageContent"] p {{ font-size: {st.session_state.font_size} !important; line-height: 1.7; }}
    
    </style>
""", unsafe_allow_html=True)

# --- שליפת נתונים מקשמון (Cache) ---
@st.cache_data(ttl=60)
def fetch_grades_cached(): return get_all_grades()
@st.cache_data(ttl=60)
def fetch_tasks_cached(): return get_all_tasks()

df = fetch_grades_cached()
tasks_df = fetch_tasks_cached()

# --- מנגנון המקצועות ---
if st.session_state.lang == "עברית":
    base_subjects = ["כללי", "מתמטיקה", "מדעי המחשב", "אנגלית", "פיזיקה", "כתיבה אקדמית", "פייתון", "SQL", "Power BI"]
    add_new_str = "➕ מקצוע חדש..."
else:
    base_subjects = ["General", "Math", "CS", "English", "Physics", "Python", "SQL", "Power BI"]
    add_new_str = "➕ New Subject..."

db_subjects = df['subject'].unique().tolist() if not df.empty else []
temp_subjects = set(base_subjects + db_subjects)
for s in ["➕ מקצוע חדש...", "➕ New Subject...", "System_Init"]: temp_subjects.discard(s)
all_subjects = sorted(list(temp_subjects)) + [add_new_str]
idx_general = all_subjects.index("כללי") if "כללי" in all_subjects else 0

# --- תפריט צדדי חכם (Sidebar Config) ---
with st.sidebar:
    st.markdown(f"<h1 style='font-family: JetBrains Mono; text-align: center; color: {accent_color}; font-size: 2.5rem; text-shadow: 0 0 15px {border_color}; margin-bottom: 30px;'>NEXUS<span style='color: #fff;'>_OS</span></h1>", unsafe_allow_html=True)
    
    lang = st.radio("System Protocol", ["עברית", "English"], horizontal=True, label_visibility="collapsed")
    if lang != st.session_state.lang: st.session_state.lang = lang; st.rerun()
    st.session_state.dark_mode = st.toggle("Tactical Dark Mode", value=st.session_state.dark_mode)
    analyst_on = st.toggle("Analyst Core 📊", value=True)
    st.divider()
    
    st.markdown("<p style='font-family: JetBrains Mono; font-size: 0.9rem; color: #94a3b8; margin-bottom: 5px;'>// DATA_INGESTION</p>", unsafe_allow_html=True)
    upload_sub = st.selectbox("Target Node:", all_subjects[:-1], index=idx_general, label_visibility="collapsed")
    up = st.file_uploader("Drop Files", type=None, label_visibility="collapsed")
    if up and st.button("EXECUTE SCAN", use_container_width=True):
        st.session_state.file_contexts[upload_sub] = extract_text_from_file(up)
        st.success(f"Ingested -> {upload_sub}")

# --- HUD Header (Top Bar) ---
st.markdown(f"""
    <div class="hud-header">
        <div>
            <h1 class="hud-title">{'NEXUS COMMAND' if st.session_state.lang == 'English' else 'מרכז פיקוד NEXUS'}</h1>
            <p class="hud-subtitle">{greeting_text} | System Time: {datetime.datetime.now(ZoneInfo("Asia/Jerusalem")).strftime("%H:%M")}</p>
        </div>
    </div>
""", unsafe_allow_html=True)

# --- תפריט ניווט הולוגרפי עילי ---
menu = option_menu(None, [cur["m1"], cur["m2"], cur["m3"], cur["m4"], cur["m5"]], 
                   icons=["grid-1x2", "cpu", "server", "check2-square", "sliders"], 
                   orientation="horizontal",
                   styles={
                       "container": {"padding": "5px!important", "background": "rgba(0,0,0,0.3)", "backdrop-filter": "blur(10px)", "border": f"1px solid {border_color}", "border-radius": "12px", "margin-bottom": "40px"},
                       "icon": {"color": "#94a3b8", "font-size": "1.1rem"}, 
                       "nav-link": {"font-family": "JetBrains Mono", "font-size": "0.95rem", "font-weight": "600", "text-align": "center", "margin":"0px", "color": "#94a3b8", "border-radius": "8px", "transition": "0.2s"},
                       "nav-link-selected": {"background": "rgba(255,255,255,0.1)", "color": accent_color, "border": f"1px solid {accent_color}", "box-shadow": f"inset 0 0 10px {border_color}"}
                   })

df_valid = df[df['topic'] != 'System_Init'] if not df.empty else df
total_credits = df_valid['credits'].sum() if not df_valid.empty and 'credits' in df_valid.columns else 0.0
weighted_avg = (df_valid['grade'] * df_valid['credits']).sum() / total_credits if total_credits > 0 else 0.0

# ==========================================
# --- MODULE 1: COMMAND CENTER (Bento Box) ---
# ==========================================
if menu == cur["m1"]:
    # שורה 1: מטריקות
    m1, m2, m3, m4 = st.columns(4)
    m1.metric(cur["avg"], f"{weighted_avg:.2f}") 
    m2.metric(cur["count"], len(df_valid))
    m3.metric(cur["cred"], f"{total_credits:.1f}")
    m4.metric("משימות פתוחות" if st.session_state.lang == "עברית" else "Open Tasks", len(tasks_df))
    
    st.write("") # Spacer
    
    # שורה 2: Bento Box Layout
    col_chart, col_tools = st.columns([2.5, 1])
    
    with col_chart:
        st.markdown(f"<div style='background: {glass_bg}; border-radius: 16px; border: 1px solid {border_color}; padding: 20px; height: 100%;'>", unsafe_allow_html=True)
        st.markdown(f"<h3 style='font-family: JetBrains Mono; color: #fff; font-size: 1.2rem; text-align: right; direction: rtl; border-bottom: 1px solid {border_color}; padding-bottom: 10px; margin-bottom: 15px;'>// PERFORMANCE_MATRIX</h3>", unsafe_allow_html=True)
        if not df_valid.empty:
            tab1, tab2 = st.tabs(["📊 Distribution", "📈 Trend"])
            with tab1:
                fig = px.bar(df_valid, x='subject', y='grade', color='grade', color_continuous_scale='Mint' if not st.session_state.dark_mode else 'Teal', text='grade')
                fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color=text_color, font_family="JetBrains Mono", margin=dict(l=0, r=0, t=30, b=0))
                fig.update_traces(textposition='outside')
                st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
            with tab2:
                df_time = df_valid.copy().sort_values('created_at')
                df_time['rolling'] = df_time['grade'].expanding().mean()
                fig2 = px.line(df_time, x='created_at', y='rolling', markers=True, line_shape='spline')
                fig2.update_traces(line_color=accent_color, marker=dict(size=8, color='#fff', line=dict(width=2, color=accent_color)))
                fig2.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color=text_color, font_family="JetBrains Mono", margin=dict(l=0, r=0, t=30, b=0))
                st.plotly_chart(fig2, use_container_width=True, config={'displayModeBar': False})
        else:
            st.info("No data streams detected.")
        st.markdown("</div>", unsafe_allow_html=True)

    with col_tools:
        st.markdown(f"<div style='background: {glass_bg}; border-radius: 16px; border: 1px solid {border_color}; padding: 20px; margin-bottom: 20px;'>", unsafe_allow_html=True)
        st.markdown(f"<h3 style='font-family: JetBrains Mono; color: #fff; font-size: 1.2rem; text-align: right; direction: rtl; border-bottom: 1px solid {border_color}; padding-bottom: 10px; margin-bottom: 15px;'>// DATA_ENTRY</h3>", unsafe_allow_html=True)
        with st.form("entry", clear_on_submit=True):
            sel_sub = st.selectbox(cur["sub"], all_subjects, index=0, label_visibility="collapsed")
            new_sub = st.text_input("New Subject") if sel_sub == add_new_str else ""
            c1, c2 = st.columns(2)
            cred = c1.number_input(cur["cred"], 0.5, 10.0, 3.0, 0.5)
            grd = c2.number_input(cur["grd"], 0, 100, 90)
            if st.form_submit_button(cur["sync"], use_container_width=True): 
                f_sub = new_sub if sel_sub == add_new_str else sel_sub
                if f_sub: save_grade(f_sub, "", grd, cred); fetch_grades_cached.clear(); st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
        
        st.markdown(f"<div style='background: {glass_bg}; border-radius: 16px; border: 1px solid {border_color}; padding: 20px;'>", unsafe_allow_html=True)
        st.markdown(f"<h3 style='font-family: JetBrains Mono; color: #fff; font-size: 1.2rem; text-align: right; direction: rtl; border-bottom: 1px solid {border_color}; padding-bottom: 10px; margin-bottom: 15px;'>// SIMULATION</h3>", unsafe_allow_html=True)
        s_c = st.number_input("Future Credits", 1.0, 10.0, 3.0, key="sc")
        s_g = st.number_input("Expected Grade", 0, 100, 90, key="sg")
        if st.button("RUN SIMULATION", use_container_width=True):
            n_tot = total_credits + s_c
            n_avg = ((weighted_avg * total_credits) + (s_g * s_c)) / n_tot if n_tot > 0 else 0
            st.success(f"Projected GPA: {n_avg:.2f}")
        st.markdown("</div>", unsafe_allow_html=True)

# ==========================================
# --- MODULE 2: AI TERMINAL ---
# ==========================================
elif menu == cur["m2"]:
    if not st.session_state.chat_history:
        db_history = get_persistent_chat_history()
        st.session_state.chat_history = [{"role": m["role"], "content": m["content"]} for m in db_history]
    
    colA, colB = st.columns([4, 1])
    with colA: chat_sub = st.selectbox("Focus Protocol:", all_subjects[:-1], index=idx_general, label_visibility="collapsed")
    with colB: 
        if st.button("INITIATE QUIZ 📝", use_container_width=True):
            if chat_sub in st.session_state.file_contexts:
                ctx = st.session_state.file_contexts[chat_sub]
                placeholder = st.empty()
                res = ""
                for chunk in get_ai_response_stream(chat_sub, "ייצר לי מבחן אקדמי ברמה גבוהה.", [], ctx, st.session_state.lang, analyst_on, is_quiz=True):
                    res += chunk
                    placeholder.markdown(f'<div style="background: rgba(0,255,255,0.05); padding:20px; border-radius:12px; border-left: 4px solid {accent_color}; text-align: right; direction: rtl;">{res}</div>', unsafe_allow_html=True)
    
    chat_container = st.container(height=550)
    with chat_container:
        for m in st.session_state.chat_history:
            bg = "rgba(0, 242, 254, 0.05)" if m["role"] == "user" else "transparent"
            border = f"border-right: 3px solid {accent_color};" if m["role"] == "user" else f"border-left: 3px solid #8b5cf6;"
            with st.chat_message(m["role"]): 
                st.markdown(f'<div style="text-align: right; direction: rtl; background: {bg}; {border} padding: 15px; border-radius: 8px;">{m["content"]}</div>', unsafe_allow_html=True)
                
    if p := st.chat_input(cur["ask"]):
        components.html("""<script>window.parent.document.activeElement.blur();</script>""", height=0, width=0)
        st.session_state.chat_history.append({"role": "user", "content": p})
        save_chat_message("user", p)
        with chat_container.chat_message("user"): 
            st.markdown(f'<div style="text-align: right; direction: rtl; background: rgba(0, 242, 254, 0.05); border-right: 3px solid {accent_color}; padding: 15px; border-radius: 8px;">{p}</div>', unsafe_allow_html=True)
        with chat_container.chat_message("assistant"):
            placeholder = st.empty()
            res = ""
            ctx = st.session_state.file_contexts.get(chat_sub, "")
            for chunk in get_ai_response_stream(chat_sub, p, st.session_state.chat_history[:-1], ctx, st.session_state.lang, analyst_on):
                res += chunk
                placeholder.markdown(f'<div style="text-align: right; direction: rtl; border-left: 3px solid #8b5cf6; padding: 15px;">{res}</div>', unsafe_allow_html=True)
        st.session_state.chat_history.append({"role": "assistant", "content": res})
        save_chat_message("assistant", res)

# ==========================================
# --- MODULE 3: DATA VAULT ---
# ==========================================
elif menu == cur["m3"]:
    st.markdown(f"<h3 style='font-family: JetBrains Mono; color: {accent_color}; margin-bottom: 20px;'>// SECURE_DATA_VAULT</h3>", unsafe_allow_html=True)
    if not df_valid.empty:
        col1, col2 = st.columns([8, 2])
        with col2:
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer: df_valid.to_excel(writer, index=False)
            st.download_button(label="EXPORT .XLSX", data=buffer.getvalue(), file_name="NEXUS_DB.xlsx", use_container_width=True)
        
        st.markdown(f"""<style>[data-testid="stDataFrame"] {{ background: rgba(0,0,0,0.4); border: 1px solid {border_color}; border-radius: 12px; }}</style>""", unsafe_allow_html=True)
        st.dataframe(df_valid, use_container_width=True, height=600) 

# ==========================================
# --- MODULE 4: OBJECTIVES (Task Board) ---
# ==========================================
elif menu == cur["m4"]:
    colA, colB = st.columns([1, 2.5])
    with colA:
        st.markdown(f"<div style='background: {glass_bg}; border-radius: 16px; border: 1px solid {border_color}; padding: 20px;'>", unsafe_allow_html=True)
        st.markdown(f"<h3 style='font-family: JetBrains Mono; color: #fff; font-size: 1.2rem; text-align: right; direction: rtl; border-bottom: 1px solid {border_color}; padding-bottom: 10px; margin-bottom: 15px;'>// ADD_OBJECTIVE</h3>", unsafe_allow_html=True)
        with st.form("new_task", clear_on_submit=True):
            t_title = st.text_input("Objective Detail", label_visibility="collapsed", placeholder="Enter task...")
            t_sub = st.selectbox(cur["sub"], all_subjects[:-1], label_visibility="collapsed")
            t_date = st.date_input("Deadline", label_visibility="collapsed")
            if st.form_submit_button("DEPLOY TASK", use_container_width=True): 
                save_task(t_title, t_sub, t_date); fetch_tasks_cached.clear(); st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
        
    with colB:
        if not tasks_df.empty:
            for index, row in tasks_df.iterrows():
                days = (pd.to_datetime(row['due_date']).date() - datetime.date.today()).days
                status_color = "#00f2fe" if days > 3 else ("#f59e0b" if days >= 0 else "#ef4444")
                pulse_css = "box-shadow: 0 0 15px rgba(239, 68, 68, 0.4);" if days < 0 else ""
                
                st.markdown(f"""
                    <div class="task-card" style="border-right: 4px solid {status_color}; margin-bottom: 15px; display: flex; justify-content: space-between; align-items: center; {pulse_css}">
                        <div style="direction: rtl; text-align: right; width: 100%;">
                            <span style="font-size: 1.3rem; font-weight: 700; color: #fff;">{row['title']}</span>
                            <br><span style="font-family: JetBrains Mono; font-size: 0.85rem; color: {status_color}; text-transform: uppercase;">NODE: {row['subject']} | T-MINUS: {days} DAYS</span>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
                if st.button(f"MARK COMPLETE", key=f"d_{row['id']}"): 
                    delete_task(row['id']); fetch_tasks_cached.clear(); st.rerun()

# ==========================================
# --- MODULE 5: SYSTEM CONFIG ---
# ==========================================
elif menu == cur["m5"]:
    st.markdown(f"<h3 style='font-family: JetBrains Mono; color: {accent_color}; margin-bottom: 20px;'>// SYSTEM_CONFIGURATION</h3>", unsafe_allow_html=True)
    
    st.markdown(f"<div style='background: {glass_bg}; border-radius: 16px; border: 1px solid {border_color}; padding: 30px; margin-bottom: 20px;'>", unsafe_allow_html=True)
    font_size_map = {"Small": "0.9rem", "Standard": "1.1rem", "Large": "1.3rem"}
    cur_size = [k for k, v in font_size_map.items() if v == st.session_state.font_size][0]
    new_size = st.select_slider("UI SCALE", options=list(font_size_map.keys()), value=cur_size)
    if font_size_map[new_size] != st.session_state.font_size: st.session_state.font_size = font_size_map[new_size]; st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)
    
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("PURGE AI MEMORY", use_container_width=True): clear_chat_history(); st.session_state.chat_history = []; st.rerun()
    with c2:
        if st.button("FLUSH INGESTED FILES", use_container_width=True): st.session_state.file_contexts = {}; st.rerun()
    with c3:
        st.markdown("""<style>div.stButton > button:last-child { border-color: #ef4444 !important; color: #ef4444 !important; } div.stButton > button:last-child:hover { background: rgba(239,68,68,0.2) !important; }</style>""", unsafe_allow_html=True)
        if st.button("INITIATE FACTORY RESET", use_container_width=True): clear_db(); fetch_grades_cached.clear(); st.rerun()

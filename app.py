import streamlit as st
from streamlit_option_menu import option_menu
import pandas as pd
import datetime
import plotly.express as px
from database_manager import init_db, save_grade, get_all_grades, clear_db
from ai_manager import get_ai_response_stream, extract_text_from_file

# --- 1. אתחול מערכת ---
st.set_page_config(page_title="Nexus OS | Core", layout="wide", initial_sidebar_state="collapsed")
init_db()

# עברית כברירת מחדל
if 'lang' not in st.session_state: st.session_state.lang = "עברית"
if 'chat_history' not in st.session_state: st.session_state.chat_history = []
if 'file_contexts' not in st.session_state: st.session_state.file_contexts = {}

# --- 2. עיצוב Vivid & Powerful (צבעוני ויוקרתי) ---
st.markdown("""
    <style>
    [data-testid="stAppViewContainer"] {
        background: linear-gradient(135deg, #020024 0%, #090979 35%, #00d4ff 100%) !important;
        color: white;
    }
    [data-testid="collapsedControl"] { display: none !important; }

    /* כרטיסי מדדים ניאון */
    div[data-testid="stMetric"] {
        background: rgba(255, 255, 255, 0.15) !important;
        border-radius: 20px; padding: 25px; backdrop-filter: blur(15px);
        border: 1px solid rgba(255, 255, 255, 0.3);
        box-shadow: 0 8px 32px 0 rgba(0, 212, 255, 0.2);
    }
    div[data-testid="stMetricValue"] { color: #ffffff !important; font-weight: 900 !important; font-size: 3rem !important; }
    div[data-testid="stMetricLabel"] { color: #00d4ff !important; font-weight: bold !important; font-size: 1.1rem !important; }

    /* כפתורי פעולה חזקים */
    .stButton>button {
        background: linear-gradient(45deg, #00f2fe 0%, #4facfe 100%) !important;
        color: #000 !important; border-radius: 12px; font-weight: 900; height: 50px; border: none;
        box-shadow: 0 4px 15px rgba(0, 242, 254, 0.3);
    }
    .stButton>button:hover { transform: translateY(-2px); box-shadow: 0 6px 20px rgba(0, 242, 254, 0.5); }

    /* בועות צ'אט ברורות */
    [data-testid="stChatMessage"] { background: rgba(0, 0, 0, 0.35) !important; border-radius: 15px; border: 1px solid rgba(255,255,255,0.1); }
    [data-testid="stChatMessageContent"] p { color: #ffffff !important; font-size: 1.1rem !important; }

    /* קלט - לבן וחד */
    input, select, textarea, [data-baseweb="select"] {
        background: white !important; color: black !important; font-weight: bold !important; border-radius: 10px !important;
    }
    </style>
    """, unsafe_allow_html=True)

# תמיכה ב-RTL (עברית)
if st.session_state.lang == "עברית":
    st.markdown("<style>div[data-testid='stChatMessageContent'] * { direction: rtl; text-align: right; } textarea { direction: rtl; }</style>", unsafe_allow_html=True)

# כותרת ראשית
st.markdown(f"<h1 style='text-align:center; color:#ffffff; text-shadow: 0 0 20px #00d4ff; margin-bottom:0;'>NEXUS OS | CORE</h1>", unsafe_allow_html=True)
st.markdown(f"<p style='text-align:center; opacity:0.8;'>Student Intelligence Hub | Mendi</p>", unsafe_allow_html=True)

# תפריט אופקי יוקרתי
selected = option_menu(None, ["דאשבורד", "AI Tutor", "היסטוריה", "הגדרות"], 
    icons=["grid-fill", "cpu-fill", "clock-history", "gear-fill"], orientation="horizontal",
    styles={
        "container": {"background-color": "rgba(255,255,255,0.1)", "border-radius": "15px", "padding": "5px"},
        "nav-link": {"color": "white", "font-weight": "bold"},
        "nav-link-selected": {"background-color": "#4facfe", "color": "black"}
    })

df = get_all_grades()

if selected == "דאשבורד":
    # מדדים עליונים
    c1, c2, c3 = st.columns(3)
    val = df['grade'].mean() if not df.empty else 0.0
    c1.metric("ממוצע אקדמי", f"{val:.1f}")
    c2.metric("משימות שבוצעו", len(df))
    c3.metric("מצב מערכת", "Online 🟢")
    
    st.divider()
    
    # אזור הזנה וגרפים
    l, r = st.columns([1, 1.3])
    with l:
        st.markdown("### 📥 הוספת נתונים")
        with st.form("main_form", clear_on_submit=True):
            s = st.selectbox("בחר מקצוע", ["כללי", "מתמטיקה", "פיזיקה", "מדעי המחשב", "אחר"])
            tp = st.text_input("נושא המטלה")
            g = st.number_input("ציון", 0, 100, 90)
            if st.form_submit_button("שמור רשומה"):
                save_grade(s, tp, g); st.rerun()
        
        st.markdown("### 📚 סריקת חומר")
        up = st.file_uploader("PDF/Docx/Image", type=["pdf", "docx", "png", "jpg"])
        if up and st.button("🧠 טען למוח של ה-AI"):
            with st.spinner("Extracting Knowledge..."):
                st.session_state.file_contexts[s] = extract_text_from_file(up)
                st.success("המידע נטען בהצלחה!")

    with r:
        st.markdown("### 📈 ניתוח התקדמות")
        if not df.empty:
            fig = px.line(df.sort_values('date'), x='date', y='grade', color='subject', markers=True)
            fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="white")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("אין עדיין נתונים להצגה בגרף. הזן ציון ראשון!")

elif selected == "AI Tutor":
    st.markdown("### 🧠 AI Academic Tutor")
    sub_sel = st.selectbox("הקשר לימודי:", ["כללי", "מתמטיקה", "פיזיקה", "מדעי המחשב", "אחר"])
    ctx = st.session_state.file_contexts.get(sub_sel, "")
    
    if ctx: st.success("📚 ה-AI משתמש בחומר הלימודי שהעלית עבור מקצוע זה.")
    
    chat_box = st.container(height=480)
    for m in st.session_state.chat_history:
        with chat_box.chat_message(m["role"]): st.markdown(m["content"])
    
    if p := st.chat_input("שאל את Nexus AI כל דבר..."):
        st.session_state.chat_history.append({"role": "user", "content": p})
        with chat_box.chat_message("user"): st.markdown(p)
        with chat_box.chat_message("assistant"):
            # הזרמה ישירה מהמנוע החסין
            full_res = st.write_stream(get_ai_response_stream(sub_sel, p, file_context=ctx))
        st.session_state.chat_history.append({"role": "assistant", "content": full_res})

elif selected == "היסטוריה":
    st.markdown("### 📜 ארכיון ציונים")
    if not df.empty:
        st.dataframe(df.sort_values(by='date', ascending=False), use_container_width=True)
    else:
        st.info("ההיסטוריה ריקה כרגע.")

elif selected == "הגדרות":
    st.markdown("### ⚙️ הגדרות מערכת")
    lang = st.radio("בחר שפת ממשק:", ["עברית", "English"], index=0 if st.session_state.lang == "עברית" else 1, horizontal=True)
    if lang != st.session_state.lang:
        st.session_state.lang = lang; st.rerun()
    
    st.divider()
    if st.button("🗑️ נקה היסטוריית צ'אט"): st.session_state.chat_history = []; st.rerun()
    if st.button("🚨 איפוס מסד נתונים"): clear_db(); st.rerun()

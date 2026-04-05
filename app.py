import streamlit as st
from streamlit_option_menu import option_menu
import pandas as pd
import plotly.express as px
from database_manager import save_grade, get_all_grades, clear_db
from ai_manager import get_ai_response_stream

st.set_page_config(page_title="NEXUS OS | v2.0", layout="wide")

# --- State Management ---
if 'lang' not in st.session_state: st.session_state.lang = "עברית"
if 'chat_history' not in st.session_state: st.session_state.chat_history = []

# --- Custom Theme & RTL ---
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&family=Assistant:wght@300;600&display=swap');
    
    * {{ font-family: 'Assistant', sans-serif; }}
    .stApp {{ background: #050a0f; color: #e0e0e0; }}
    
    /* כרטיסיות בעיצוב זכוכית */
    div[data-testid="stMetric"] {{
        background: rgba(255, 255, 255, 0.03) !important;
        border: 1px solid rgba(0, 209, 255, 0.2) !important;
        border-radius: 15px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.5);
    }}
    
    /* עיצוב כותרות ניאון */
    h1 {{ font-family: 'Orbitron', sans-serif; color: #00d1ff; text-shadow: 0 0 10px #00d1ff; text-align: center; }}
    
    /* כפתורים משודרגים */
    .stButton>button {{
        background: linear-gradient(90deg, #00d1ff, #0072ff) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px;
        font-weight: bold;
        transition: 0.3s all;
    }}
    .stButton>button:hover {{ transform: scale(1.02); box-shadow: 0 0 15px #00d1ff; }}

    /* התאמת RTL לעברית */
    {"[data-testid='stChatMessageContent'] { direction: rtl; text-align: right; }" if st.session_state.lang == "עברית" else ""}
    </style>
""", unsafe_allow_html=True)

# --- Translation System ---
t = {
    "עברית": {
        "title": "NEXUS OS", "dash": "מרכז בקרה", "tutor": "AI אקדמי", "hist": "ארכיון", "set": "מערכת",
        "avg": "ממוצע", "total": "רשומות", "sub": "מקצוע", "grd": "ציון", "save": "שמור נתונים",
        "ask": "שאל את Nexus...", "purge": "ניקוי היסטוריה", "subjects": ["כללי", "מתמטיקה", "מדעי המחשב", "אחר"]
    },
    "English": {
        "title": "NEXUS OS", "dash": "Control Center", "tutor": "Nexus AI", "hist": "Archive", "set": "System",
        "avg": "Average", "total": "Records", "sub": "Subject", "grd": "Grade", "save": "Sync Data",
        "ask": "Ask Nexus...", "purge": "Purge Chat", "subjects": ["General", "Math", "Computer Science", "Other"]
    }
}
cur = t[st.session_state.lang]

# --- Sidebar Navigation ---
with st.sidebar:
    st.markdown(f"<h1>{cur['title']}</h1>", unsafe_allow_html=True)
    lang = st.radio("", ["עברית", "English"], horizontal=True)
    if lang != st.session_state.lang: st.session_state.lang = lang; st.rerun()
    
    selected = option_menu(None, [cur["dash"], cur["tutor"], cur["hist"], cur["set"]], 
                           icons=["cpu", "robot", "database", "gear"], 
                           styles={"container": {"background-color": "transparent"},
                                   "nav-link-selected": {"background-color": "#00d1ff", "color": "black"}})

df = get_all_grades()

if selected == cur["dash"]:
    st.markdown(f"<h1>{cur['dash']}</h1>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    c1.metric(cur["avg"], f"{df['grade'].mean():.1f}" if not df.empty else "0")
    c2.metric(cur["total"], len(df))
    
    st.divider()
    with st.form("input_form"):
        col1, col2 = st.columns(2)
        sub = col1.selectbox(cur["sub"], cur["subjects"])
        grd = col2.number_input(cur["grd"], 0, 100, 90)
        if st.form_submit_button(cur["save"]):
            save_grade(sub, "", grd)
            st.rerun()
            
    if not df.empty:
        fig = px.area(df, x="id", y="grade", color="subject", template="plotly_dark")
        fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig, use_container_width=True)

elif selected == cur["tutor"]:
    st.markdown(f"<h1>{cur['tutor']}</h1>", unsafe_allow_html=True)
    sub_ai = st.selectbox(cur["sub"], cur["subjects"])
    
    # תצוגת צ'אט
    for m in st.session_state.chat_history:
        with st.chat_message(m["role"]): st.markdown(m["content"])

    if p := st.chat_input(cur["ask"]):
        st.session_state.chat_history.append({"role": "user", "content": p})
        with st.chat_message("user"): st.markdown(p)
        
        with st.chat_message("assistant"):
            full_res = st.write_stream(get_ai_response_stream(sub_ai, p, "", st.session_state.lang))
        st.session_state.chat_history.append({"role": "assistant", "content": full_res})

elif selected == cur["hist"]:
    st.markdown(f"<h1>{cur['hist']}</h1>", unsafe_allow_html=True)
    st.dataframe(df, use_container_width=True)

elif selected == cur["set"]:
    if st.button(cur["reset"]): clear_db(); st.rerun()

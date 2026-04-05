import streamlit as st
from streamlit_option_menu import option_menu
from database_manager import save_grade, get_all_grades, clear_db
from ai_manager import get_ai_response_stream, extract_text_from_file

# --- UI Setup ---
st.set_page_config(page_title="NEXUS CORE", layout="wide")

if 'file_context' not in st.session_state: st.session_state.file_context = ""
if 'chat_history' not in st.session_state: st.session_state.chat_history = []

# --- Cyber Design v3.0 ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Rajdhani:wght@500;700&display=swap');
    .stApp { background: linear-gradient(135deg, #0f0c29, #302b63, #24243e); color: #00f2fe; }
    h1 { font-family: 'Rajdhani', sans-serif; background: linear-gradient(to right, #00f2fe, #4facfe); -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-align: center; font-size: 3rem; }
    div[data-testid="stMetric"] { background: rgba(0, 242, 254, 0.1) !important; border: 2px solid #00f2fe !important; border-radius: 15px; padding: 15px; box-shadow: 0 0 20px rgba(0,242,254,0.2); }
    .stButton>button { background: linear-gradient(45deg, #4facfe, #00f2fe) !important; color: white !important; border-radius: 30px; border: none; font-weight: bold; width: 100%; transition: 0.3s; }
    .stButton>button:hover { box-shadow: 0 0 30px #00f2fe; transform: translateY(-2px); }
    /* RTL Fix */
    [data-testid='stChatMessageContent'] { direction: rtl; text-align: right; background: rgba(255,255,255,0.05); border-radius: 15px; }
    </style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("<h1>NEXUS CORE</h1>", unsafe_allow_html=True)
    lang = st.radio("INTERFACE LANG", ["עברית", "English"], horizontal=True)
    st.divider()
    
    # מצב דאטה אנליסט
    analyst_on = st.toggle("ANALYST PROTOCOL 📊", help="מפעיל בינה מלאכותית המתמחה בניתוח נתונים וסטטיסטיקה")
    
    # סריקת קבצים (מה שהיה חסר)
    st.markdown("### 🛰️ NEURAL SCAN")
    up_file = st.file_uploader("Upload Study Material", type=['pdf', 'docx', 'jpg', 'png'])
    if up_file and st.button("PROCESS DATA"):
        with st.spinner("Analyzing..."):
            st.session_state.file_context = extract_text_from_file(up_file)
            st.success("DATA INGESTED")

    menu = option_menu(None, ["Command Center", "Neural Tutor", "Knowledge Vault", "System"], 
                       icons=["cpu", "robot", "database", "gear"], default_index=0)

# --- Logic ---
df = get_all_grades()

if menu == "Command Center":
    st.markdown("<h1>COMMAND CENTER</h1>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    c1.metric("ACADEMIC AVG", f"{df['grade'].mean():.1f}" if not df.empty else "0.0")
    c2.metric("RECORDS", len(df))
    
    with st.expander("📝 MANUAL DATA ENTRY", expanded=True):
        col1, col2 = st.columns(2)
        s = col1.selectbox("SUBJECT", ["General", "Math", "Computer Science", "Physics"])
        g = col2.number_input("GRADE", 0, 100, 90)
        if st.button("SYNC TO CLOUD"):
            save_grade(s, "", g); st.rerun()

elif menu == "Neural Tutor":
    st.markdown(f"<h1>{'ANALYSIS MODE' if analyst_on else 'NEURAL TUTOR'}</h1>", unsafe_allow_html=True)
    
    for m in st.session_state.chat_history:
        with st.chat_message(m["role"]): st.markdown(m["content"])

    if p := st.chat_input("Input query..."):
        st.session_state.chat_history.append({"role": "user", "content": p})
        with st.chat_message("user"): st.markdown(p)
        
        with st.chat_message("assistant"):
            # העברת מצב האנליסט והקונטקסט של הקבצים
            res = st.write_stream(get_ai_response_stream("General", p, st.session_state.file_context, lang, analyst_on))
        st.session_state.chat_history.append({"role": "assistant", "content": res})

elif menu == "Knowledge Vault":
    st.markdown("<h1>KNOWLEDGE VAULT</h1>", unsafe_allow_html=True)
    st.dataframe(df, use_container_width=True)

elif menu == "System":
    if st.button("PURGE ALL DATA"): clear_db(); st.rerun()

import streamlit as st
from streamlit_option_menu import option_menu
import pandas as pd
import datetime
import plotly.express as px
from database_manager import init_db, save_grade, get_all_grades, clear_db
from ai_manager import get_ai_response_stream, extract_text_from_file

# --- 1. הגדרות מערכת ---
# הפעם סגרנו את הסיידבר בצורה בטוחה מתוך ההגדרות של פייתון
st.set_page_config(page_title="Nexus OS | Core", layout="wide", initial_sidebar_state="collapsed")
init_db()

# --- 2. מילון שפות וזיכרון ---
if 'lang' not in st.session_state:
    st.session_state.lang = "עברית"
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'file_contexts' not in st.session_state:
    st.session_state.file_contexts = {}

SUBJECTS_HE = ["General / כללי", "מתמטיקה", "פיזיקה", "כתיבה אקדמאית", "עברית", "מדעי המחשב", "אחר"]
SUBJECTS_EN = ["General", "Math", "Physics", "Academic Writing", "Hebrew", "Computer Science", "Other"]

t = {
    "עברית": {
        "dash": "דאשבורד", "tutor": "AI Tutor 🤖", "history": "היסטוריה", "settings": "הגדרות",
        "avg": "ממוצע אקדמי", "total": "משימות שבוצעו", "add": "הזנת ציונים חדשים", "sub": "מקצוע",
        "topic": "נושא / מטלה", "grade": "ציון", "save": "שמור למסד הנתונים", "upload_title": "סריקת חומרי לימוד (RAG)",
        "ask": "שאל אותי כל דבר...", "subjects": SUBJECTS_HE, "clear_chat": "🗑️ נקה היסטוריית שיחה",
        "purge": "🚨 איפוס כל הנתונים במסד"
    },
    "English": {
        "dash": "Dashboard", "tutor": "AI Tutor 🤖", "history": "History", "settings": "Settings",
        "avg": "Academic Average", "total": "Completed Tasks", "add": "Add New Grades", "sub": "Subject",
        "topic": "Topic / Task", "grade": "Grade", "save": "Save to Database", "upload_title": "Scan Study Materials (RAG)",
        "ask": "Ask me anything...", "subjects": SUBJECTS_EN, "clear_chat": "🗑️ Clear Chat History",
        "purge": "🚨 Purge All Database Records"
    }
}
cur = t[st.session_state.lang]

# --- 3. עיצוב Glassmorphism (בטוח ויציב) ---
st.markdown("""
    <style>
    /* העלמת כפתור הפתיחה של הסיידבר הישן לחלוטין */
    [data-testid="collapsedControl"] { display: none !important; }
    
    [data-testid="stAppViewContainer"] { 
        background: radial-gradient(circle at top, #0f2027, #203a43, #2c5364) !important; color: #ffffff; 
    }
    
    /* קלפי הנתונים */
    div[data-testid="stMetric"] { 
        background: rgba(255, 255, 255, 0.05) !important; border: 1px solid rgba(0, 209, 255, 0.3) !important; 
        border-radius: 20px; padding: 20px; backdrop-filter: blur(10px); 
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
    }
    div[data-testid="stMetricValue"] { color: #00D1FF !important; font-weight: 900 !important; font-size: 3.5rem !important; }
    h1, h2, h3, p, label, span { color: #e0e0e0 !important; text-shadow: 1px 1px 2px black; }
    
    /* תיבות קלט ורשימות - לבן ונקי */
    input, select, textarea, [data-baseweb="select"], .stNumberInput input { 
        background: rgba(255, 255, 255, 0.95) !important; color: #000000 !important; 
        border-radius: 10px !important; font-weight: 900 !important; 
    }
    div[role="listbox"] ul li, div[data-baseweb="popover"] span { color: black !important; font-weight: bold !important; background-color: white !important; }
    
    /* עיצוב כפתורים יוקרתי */
    .stButton>button {
        background: linear-gradient(90deg, #00D1FF 0%, #007BFF 100%); color: white !important;
        border: none; border-radius: 25px; font-weight: bold; border: 1px solid transparent;
    }
    
    div[data-testid="stFileUploader"] section { background-color: rgba(255, 255, 255, 0.9) !important; color: black !important; border-radius: 15px;}
    div[data-testid="stFileUploader"] p, div[data-testid="stFileUploader"] span { color: black !important; text-shadow: none; font-weight: bold;}
    </style>
    """, unsafe_allow_html=True)

if st.session_state.lang == "עברית":
    st.markdown("""
        <style>
        [data-testid="stChatMessageContent"], [data-testid="stChatMessageContent"] * { direction: rtl !important; text-align: right !important; }
        [data-testid="stChatInput"] textarea { direction: rtl !important; text-align: right !important; }
        </style>
    """, unsafe_allow_html=True)

# --- לוגיקת ברכה חכמה לפי שעון ---
hour = datetime.datetime.now().hour
if 5 <= hour < 12:
    greeting = "בוקר טוב" if st.session_state.lang == "עברית" else "Good Morning"
elif 12 <= hour < 17:
    greeting = "צהריים טובים" if st.session_state.lang == "עברית" else "Good Afternoon"
elif 17 <= hour < 21:
    greeting = "ערב טוב" if st.session_state.lang == "עברית" else "Good Evening"
else:
    greeting = "לילה טוב למקצוענים" if st.session_state.lang == "עברית" else "Late Night Hustle"

st.markdown(f"<h1 style='text-align:center; color:#00D1FF; font-size: 3rem;'>NEXUS OS</h1>", unsafe_allow_html=True)
st.markdown(f"<p style='text-align:center; font-size: 1.2rem;'>{greeting}, Mendi 🎓</p>", unsafe_allow_html=True)

# --- 4. תפריט ניווט אופקי חדש! ---
selected = option_menu(
    menu_title=None, 
    options=[cur["dash"], cur["tutor"], cur["history"], cur["settings"]], 
    icons=["grid-1x2-fill", "cpu-fill", "clock-history", "gear-fill"], 
    default_index=0,
    orientation="horizontal", 
    styles={
        "container": {"padding": "0!important", "background-color": "rgba(0,0,0,0.3)", "border-radius": "15px"},
        "icon": {"color": "#00D1FF", "font-size": "20px"}, 
        "nav-link": {"font-size": "18px", "text-align": "center", "margin":"0px", "--hover-color": "rgba(0, 209, 255, 0.1)"},
        "nav-link-selected": {"background-color": "rgba(0, 209, 255, 0.2)", "color": "#00D1FF", "border-bottom": "3px solid #00D1FF"}
    }
)

df = get_all_grades()

# --- 5. מסכי המערכת ---
if selected == cur["dash"]:
    st.markdown("<br>", unsafe_allow_html=True)
    avg_grade = df['grade'].mean() if not df.empty else 0.0
    
    c1, c2, c3 = st.columns(3)
    c1.metric(cur["avg"], f"{avg_grade:.1f}")
    c2.metric(cur["total"], len(df))
    c3.metric("System Engine", "Online 🟢")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    col_left, col_right = st.columns([1, 1.2])
    
    with col_left:
        st.markdown(f"### 📝 {cur['add']}")
        with st.form("grade_form", clear_on_submit=True):
            sub = st.selectbox(cur["sub"], cur["subjects"][1:]) 
            tp = st.text_input(cur["topic"])
            grd = st.number_input(cur["grade"], 0, 100, 90)
            if st.form_submit_button(cur["save"]):
                save_grade(sub, tp, grd)
                st.rerun()
                
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(f"### 📁 {cur['upload_title']}")
        upload_sub = st.selectbox("Assign material to:", cur["subjects"][1:], key="upload_sub")
        uploaded_file = st.file_uploader("PDF / Docx / Images", type=["pdf", "docx", "png", "jpg", "jpeg"])
        
        if uploaded_file is not None:
            if st.button("🧠 Upload to AI Brain"):
                with st.spinner("Extracting knowledge..."):
                    extracted_text = extract_text_from_file(uploaded_file)
                    st.session_state.file_contexts[upload_sub] = extracted_text
                    st.success("Learned successfully! AI is ready.")

    with col_right:
        st.markdown("### 📈 Trend Analysis")
        if not df.empty:
            df_sorted = df.sort_values(by='date')
            fig = px.line(df_sorted, x='date', y='grade', color='subject', markers=True)
            fig.update_layout(
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                font_color="white", legend_title_font_color="white",
                xaxis=dict(showgrid=False), yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)')
            )
            fig.update_traces(line=dict(width=3), marker=dict(size=8))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No data available for trend analysis yet. Add some grades!")

elif selected == cur["tutor"]:
    st.markdown("<br>", unsafe_allow_html=True)
    sub_choice = st.selectbox("Context:", cur["subjects"]) 
    
    current_file_context = st.session_state.file_contexts.get(sub_choice, "")
    if current_file_context:
        st.success("📚 Context Active: The AI is utilizing your uploaded study materials.")

    chat_container = st.container(height=500)
    with chat_container:
        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
                
    if prompt := st.chat_input(cur["ask"]):
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        with chat_container:
            with st.chat_message("user"): 
                st.markdown(prompt)
            with st.chat_message("assistant"):
                res_box = st.empty()
                full_res = ""
                for chunk in get_ai_response_stream(sub_choice, prompt, file_context=current_file_context):
                    full_res += chunk
                    res_box.markdown(full_res + " ▌")
                res_box.markdown(full_res)
                st.session_state.chat_history.append({"role": "assistant", "content": full_res})

elif selected == cur["history"]:
    st.markdown("<br>", unsafe_allow_html=True)
    if df.empty:
        st.info("No records found.")
    else:
        st.dataframe(df.sort_values(by='date', ascending=False), use_container_width=True)

elif selected == cur["settings"]:
    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🌐 Language / שפה")
        lang_choice = st.radio("", ["עברית", "English"], index=0 if st.session_state.lang == "עברית" else 1)
        if lang_choice != st.session_state.lang:
            st.session_state.lang = lang_choice
            st.rerun()
            
    with col2:
        st.markdown("### 🛠️ System Management")
        if st.button(cur["clear_chat"], use_container_width=True):
            st.session_state.chat_history = []
            st.rerun()
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button(cur["purge"], use_container_width=True):
            clear_db()
            st.rerun()

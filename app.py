import streamlit as st
from streamlit_option_menu import option_menu
import datetime

# --- 1. הגדרות כלליות (כאן משנים את שם האפליקציה שמופיע בלשונית) ---
st.set_page_config(page_title="Nexus OS | Mendi's Command Center", layout="wide")

# --- 2. עיצוב יוקרתי (CSS) ---
st.markdown("""
    <style>
    .stApp { background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%); }
    section[data-testid="stSidebar"] { background-color: rgba(255, 255, 255, 0.8) !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. תפריט ניווט (כאן מוסיפים או משנים שמות של דפים!) ---
with st.sidebar:
    st.image("https://via.placeholder.com/150", caption="Nexus Intelligence")  # אפשר להחליף בלוגו שלך
    selected = option_menu(
        menu_title="Nexus Menu",
        options=["Dashboard", "Subjects", "AI Tutor", "Files", "Settings"],  # <--- תוסיף כאן שמות דפים
        icons=["house", "book", "robot", "folder", "gear"],
        default_index=0,
    )

# --- 4. תוכן הדפים (לוגיקה) ---

if selected == "Dashboard":
    st.title("🚀 Welcome, Mendi")
    st.write("System Status: **Active & Secure**")

    # דוגמה למדדים (Metrics)
    c1, c2, c3 = st.columns(3)
    c1.metric("Current Avg", "92.5", "+1.2%")
    c2.metric("Study Hours", "45h", "This Month")
    c3.metric("Tasks", "12", "Pending")

elif selected == "Subjects":
    st.title("📚 Course Inventory")
    # כאן תוכל להוסיף רשימת מקצועות בעתיד
    st.info("Select a subject to view deep analytics and materials.")

elif selected == "AI Tutor":
    st.title("🤖 Nexus AI Assistant")
    user_q = st.chat_input("Ask anything about your studies...")
    if user_q:
        st.write(f"Mendi, you asked: {user_q}. (AI logic will be linked here)")

# --- הוראות להוספת דף חדש ---
# אם הוספת ב-options את השם "Gym", תוסיף כאן:
# elif selected == "Gym":
#     st.title("💪 Fitness Tracker")
#     st.write("Tracking your online fitness course...")
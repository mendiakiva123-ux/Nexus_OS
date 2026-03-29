import os
import streamlit as st
import pandas as pd
from docx import Document
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.documents import Document as LC_Document
from langchain_community.document_loaders import PyPDFLoader


# משיכת המפתח מהכספת של הענן
@st.cache_resource
def get_api_key():
    # המפתח יילקח מהגדרות ה-Secrets בענן
    return st.secrets["GOOGLE_API_KEY"]


@st.cache_resource
def get_embedding_model():
    return GoogleGenerativeAIEmbeddings(model="models/embedding-001", google_api_key=get_api_key())


@st.cache_resource
def get_llm():
    return ChatGoogleGenerativeAI(model="gemini-1.5-flash", google_api_key=get_api_key(), temperature=0.3)


DB_DIR = "ai_data/vector_db"


def process_file_to_db(file_path, subject_name):
    ext = os.path.splitext(file_path)[1].lower()
    docs = []
    try:
        if ext == ".pdf":
            loader = PyPDFLoader(file_path);
            docs = loader.load()
        elif ext == ".docx":
            doc = Document(file_path)
            full_text = "\n".join([p.text for p in doc.paragraphs])
            docs = [LC_Document(page_content=full_text)]
        elif ext in [".csv", ".xlsx"]:
            df = pd.read_csv(file_path) if ext == ".csv" else pd.read_excel(file_path)
            docs = [LC_Document(page_content=df.to_string())]

        if not docs: return False
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        splits = text_splitter.split_documents(docs)

        vectorstore = FAISS.from_documents(documents=splits, embedding=get_embedding_model())
        path = os.path.join(DB_DIR, subject_name)
        os.makedirs(path, exist_ok=True)
        vectorstore.save_local(path)
        return True
    except Exception:
        return False


def get_ai_response_stream(subject_name, query):
    llm = get_llm()
    path = os.path.join(DB_DIR, subject_name)

    if subject_name == "general" or not os.path.exists(path):
        prompt = ChatPromptTemplate.from_messages([
            ("system", "אתה יועץ אקדמי עלית של מנדי אקיבא. ענה בעברית ברורה ומקצועית."),
            ("human", "{input}"),
        ])
        return (prompt | llm).stream({"input": query})

    vectorstore = FAISS.load_local(path, get_embedding_model(), allow_dangerous_deserialization=True)
    retriever = vectorstore.as_retriever()
    context_docs = retriever.get_relevant_documents(query)
    context_text = "\n".join([d.page_content for d in context_docs])

    prompt = ChatPromptTemplate.from_messages([
        ("system", "ענה על בסיס חומר הלימוד בלבד: {context}"),
        ("human", "{input}"),
    ])
    return (prompt | llm).stream({"context": context_text, "input": query})
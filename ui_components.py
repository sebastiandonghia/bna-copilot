import streamlit as st

def apply_custom_styles():
    """Aplica estilos CSS personalizados a la aplicación Streamlit."""
    st.markdown("""
        <style>
        .stApp { background-color: #f4f7f9; }
        .main-header { background-color: #005691; padding: 20px; border-radius: 10px; color: white; text-align: center; margin-bottom: 20px; }
        .stButton>button { background-color: #005691; color: white; border-radius: 10px; font-weight: bold; width: 100%; height: 3em; border: none; }
        .stButton>button:hover { background-color: #004575; color: white; }
        .card { background-color: white; padding: 20px; border-radius: 15px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); border-left: 5px solid #005691; margin-bottom: 20px; }
        .stExpander { background-color: white; border-radius: 10px; border: 1px solid #005691; }
        </style>
        """, unsafe_allow_html=True)

def render_header():
    """Renderiza el encabezado principal de la aplicación."""
    st.markdown("<div class='main-header'><h1>🏦 + Inversiones | Copilot</h1></div>", unsafe_allow_html=True)

def render_card(title, content):
    """Renderiza una tarjeta con estilo personalizado."""
    st.markdown(f"<div class='card'><h3>{title}</h3><p>{content}</p></div>", unsafe_allow_html=True)

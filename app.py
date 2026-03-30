import streamlit as st
import pandas as pd
import plotly.express as px # Para gráficos
import datetime

# --- CONFIGURACIÓN DE MARCA BNA+ ---
st.set_page_config(page_title="BNA+ Inversiones Profundo", page_icon="🏦", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #f4f7f9; }
    .main-header { background-color: #005691; padding: 20px; border-radius: 10px; color: white; text-align: center; margin-bottom: 20px; }
    .stButton>button { background-color: #005691; color: white; border-radius: 10px; font-weight: bold; width: 100%; height: 3em; }
    .card { background-color: white; padding: 20px; border-radius: 15px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); border-left: 5px solid #005691; margin-bottom: 20px; }
    .stExpander { background-color: white; border-radius: 10px; border: 1px solid #005691; }
    </style>
    """, unsafe_allow_html=True)

st.markdown("<div class='main-header'><h1>🏦 BNA+ Inversiones Profundo</h1></div>", unsafe_allow_html=True)

# --- INICIO DEL CUESTIONARIO AVANZADO ---
st.subheader("📋 Perfil Financiero Detallado")
col_g1, col_g2 = st.columns(2)

with col_g1:
    st.markdown("<div class='card'><h3>💰 Ingresos y Depósitos</h3></div>", unsafe_allow_html=True)
    
    with st.expander("Sueldos del Mes", expanded=True):
        n_sueldos = st.number_input("¿Cuántos sueldos recibís?", min_value=1, value=1)
        sueldos = []
        for i in range(n_sueldos):
            c1, c2 = st.columns(2)
            with c1: monto = st.number_input(f"Monto Sueldo {i+1} ($)", value=800000, key=f"s_m_{i}")
            with c2: fecha = st.date_input(f"Fecha cobro {i+1}", datetime.date.today(), key=f"s_f_{i}")
            sueldos.append({"monto": monto, "fecha": fecha})
            
    extra = st.number_input("Depósitos adicionales a analizar ($)", value=200000)

with col_g2:
    st.markdown("<div class='card'><h3>🏠 Gastos Progresivos</h3></div>", unsafe_allow_html=True)
    
    with st.expander("Detalle de Gastos", expanded=True):
        n_gastos = st.number_input("¿Cuántos gastos fijos tenés?", min_value=1, value=2)
        gastos = []
        for i in range(n_gastos):
            c1, c2, c3 = st.columns([2, 1, 1])
            with c1: desc = st.text_input(f"Gasto {i+1} (Alquiler, etc.)", f"Gasto {i+1}", key=f"g_d_{i}")
            with c2: monto = st.number_input(f"Monto {i+1} ($)", value=150000, key=f"g_m_{i}")
            with c3: fecha = st.date_input(f"Vto. {i+1}", datetime.date.today() + datetime.timedelta(days=10), key=f"g_f_{i}")
            gastos.append({"desc": desc, "monto": monto, "fecha": fecha})

with st.container():
    st.markdown("<div class='card'><h3>📈 Tenencias Actuales</h3></div>", unsafe_allow_html=True)
    tiene_pf = st.checkbox("¿Tengo Plazos Fijos actualmente?")
    pfs = []
    if tiene_pf:
        n_pfs = st.number_input("¿Cuántos PF tenés?", min_value=1, value=1)
        for i in range(n_pfs):
            c1, c2, c3 = st.columns(3)
            with c1: monto = st.number_input(f"Monto PF {i+1} ($)", value=500000, key=f"pf_m_{i}")
            with c2: vto = st.date_input(f"Fecha Vto. {i+1}", datetime.date.today() + datetime.timedelta(days=20), key=f"pf_v_{i}")
            with c3: tipo = st.selectbox(f"Tipo PF {i+1}", ["Tradicional", "UVA"], key=f"pf_t_{i}")
            pfs.append({"monto": monto, "fecha": vto, "tipo": tipo})

col_meta, col_extra = st.columns(2)
with col_meta:
    st.markdown("<div class='card'><h3>🎯 Tu Meta</h3></div>", unsafe_allow_html=True)
    meta_nombre = st.text_input("Objetivo de ahorro", "Viaje / Auto")
    meta_monto = st.number_input("Monto total de la meta ($)", value=5000000)
    
with col_extra:
    st.markdown("<div class='card'><h3>⚙️ Preferencias</h3></div>", unsafe_allow_html=True)
    mep = st.checkbox("¿Interés en Dólar MEP?")
    saldo_inicial = st.number_input("Saldo disponible hoy ($)", value=1000000)

# --- BOTÓN DE ACCIÓN ---
if st.button("ANALIZAR Y GENERAR ESTRATEGIA BNA+ PROFUNDA"):
    with st.spinner("Conectando con Gemini (Consultando BCRA, CNV, BNA, BYMA, Tablero Financiero)..."):
        # PASO 3: Aquí irá la lógica de IA y Gráficos Profesionales.
        st.info("Estructura de cuestionario avanzada cargada. En el Paso 3 conectaremos la IA y activaremos los gráficos profesionales.")

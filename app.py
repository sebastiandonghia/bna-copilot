import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go  # CORRECCIÓN: Faltaba esta importación
from google import genai 
import json
import datetime

# --- CONFIGURACIÓN DE IA ---
try:
    # La nueva forma de conectar usa google-genai
    client = genai.Client(api_key=st.secrets["GOOGLE_API_KEY"])
except Exception as e:
    st.error("⚠️ Error en la API KEY. Verificá los Secrets en Streamlit.")
    st.stop()
    
# --- CONFIGURACIÓN DE MARCA BNA+ ---
st.set_page_config(page_title="BNA+ Copilot Profundo", page_icon="🏦", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #f4f7f9; }
    .main-header { background-color: #005691; padding: 20px; border-radius: 10px; color: white; text-align: center; margin-bottom: 20px; }
    .stButton>button { background-color: #005691; color: white; border-radius: 10px; font-weight: bold; width: 100%; height: 3em; }
    .card { background-color: white; padding: 20px; border-radius: 15px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); border-left: 5px solid #005691; margin-bottom: 20px; }
    .stExpander { background-color: white; border-radius: 10px; border: 1px solid #005691; }
    </style>
    """, unsafe_allow_html=True)

st.markdown("<div class='main-header'><h1>🏦 BNA+ Inversiones | Copilot Profundo</h1></div>", unsafe_allow_html=True)

# --- CUESTIONARIO ---
st.subheader("📋 Perfil Financiero Detallado")
col_g1, col_g2 = st.columns(2)

with col_g1:
    st.markdown("<div class='card'><h3>💰 Ingresos y Depósitos</h3></div>", unsafe_allow_html=True)
    with st.expander("Sueldos del Mes", expanded=True):
        n_sueldos = st.number_input("¿Cuántos sueldos recibís?", min_value=1, value=1)
        sueldos = []
        for i in range(n_sueldos):
            c1, c2 = st.columns(2)
            with c1: monto = st.number_input(f"Monto Sueldo {i+1} ($)", value=850000, key=f"s_m_{i}")
            with c2: fecha = st.date_input(f"Fecha cobro {i+1}", datetime.date.today(), key=f"s_f_{i}")
            sueldos.append({"monto": monto, "fecha": fecha.strftime("%Y-%m-%d")})
    extra = st.number_input("Depósitos adicionales ($)", value=300000)

with col_g2:
    st.markdown("<div class='card'><h3>🏠 Gastos Progresivos</h3></div>", unsafe_allow_html=True)
    with st.expander("Detalle de Gastos Fijos", expanded=True):
        n_gastos = st.number_input("¿Cuántos gastos?", min_value=1, value=2)
        gastos = []
        for i in range(n_gastos):
            c1, c2, c3 = st.columns([2, 1, 1])
            with c1: desc = st.text_input(f"Gasto {i+1}", f"Servicio {i+1}", key=f"g_d_{i}")
            with c2: monto = st.number_input(f"Monto {i+1}", value=200000, key=f"g_m_{i}")
            with c3: fecha = st.date_input(f"Vto. {i+1}", datetime.date.today() + datetime.timedelta(days=10), key=f"g_f_{i}")
            gastos.append({"desc": desc, "monto": monto, "fecha": fecha.strftime("%Y-%m-%d")})

tiene_pf = st.checkbox("¿Tengo Plazos Fijos actualmente?")
pfs = []
if tiene_pf:
    n_pfs = st.number_input("¿Cuántos PF?", min_value=1, value=1)
    for i in range(n_pfs):
        c1, c2, c3 = st.columns(3)
        with c1: monto = st.number_input(f"Monto PF {i+1}", value=600000, key=f"pf_m_{i}")
        with c2: vto = st.date_input(f"Vto. {i+1}", datetime.date.today() + datetime.timedelta(days=20), key=f"pf_v_{i}")
        with c3: tipo = st.selectbox(f"Tipo {i+1}", ["Tradicional", "UVA"], key=f"pf_t_{i}")
        pfs.append({"monto": monto, "fecha": vto.strftime("%Y-%m-%d"), "tipo": tipo})

col_meta, col_extra = st.columns(2)
with col_meta:
    meta_nombre = st.text_input("Objetivo", "Cambiar Auto 🚗")
    meta_monto = st.number_input("Meta ($)", value=7500000)
with col_extra:
    mep = st.checkbox("¿Interés en Dólar MEP?")
    saldo_inicial = st.number_input("Saldo hoy ($)", value=1200000)

# --- LÓGICA IA ---
if st.button("ANALIZAR Y GENERAR ESTRATEGIA BNA+ PROFUNDA"):
    datos_completos = {
        "saldo_hoy": saldo_inicial, "sueldos": sueldos, "depositos_extra": extra,
        "gastos": gastos, "pfs": pfs, "meta": {"nombre": meta_nombre, "monto": meta_monto}, "mep": mep
    }
    
    with st.spinner("🤖 Consultando BCRA, BYMA y Tablero Financiero..."):
        prompt_maestro = f"""
        Eres un Senior Wealth Manager del BNA. Analiza: {json.dumps(datos_completos)}
        Considera tasas BCRA, Dólar MEP, e Inflación proyectada de Argentina.
        Responde EXCLUSIVAMENTE en JSON con:
        - "analisis_macro": texto corto.
        - "cartera_sugerida": [{{instrumento, monto, tipo_activo, tna_estimada}}]
        - "evolucion_cartera": [{{mes, monto_pesos, inflacion_acum_estimada}}] (6 meses)
        - "calce_vencimientos": [{{fecha_vto, instrumento_vto, monto_vto, gasto_cubierto}}]
        - "justificacion": texto.
        """
        try:
            # CORRECCIÓN DEFINITIVA: Nombre de modelo simple para google-genai
            response = client.models.generate_content(
                model='gemini-1.5-flash', 
                contents=prompt_maestro
            )
            
            res_text = response.text.replace("```json", "").replace("```", "").strip()
            data = json.loads(res_text)
            
            st.success("✅ Estrategia Generada")
            st.markdown(f"<div class='card'>{data['analisis_macro']}</div>", unsafe_allow_html=True)
            
            # Gráfico 1: Torta
            df_cartera = pd.DataFrame(data['cartera_sugerida'])
            st.plotly_chart(px.pie(df_cartera, values='monto', names='tipo_activo', title='Mix de Activos', 
                                 color_discrete_sequence=['#005691', '#0074c7', '#4da3ff']), use_container_width=True)
            
            col_a, col_b = st.columns(2)
            with col_a:
                # Gráfico 2: Evolución (go.Figure ahora funcionará)
                df_evol = pd.DataFrame(data['evolucion_cartera'])
                fig2 = go.Figure()
                fig2.add_trace(go.Scatter(x=df_evol['mes'], y=df_evol['monto_pesos'], name='Cartera', line=dict(color='#005691')))
                st.plotly_chart(fig2, use_container_width=True)
                
            with col_b:
                # Gráfico 3: Calce
                df_calce = pd.DataFrame(data['calce_vencimientos'])
                st.plotly_chart(px.bar(df_calce, x='fecha_vto', y='monto_vto', color='instrumento_vto', title='Vencimientos'), use_container_width=True)

            st.info(data['justificacion'])
            st.balloons()
            
        except Exception as e:
            st.error(f"Error técnico: {e}. Reintentá en 10 segundos (Cuota Free).")

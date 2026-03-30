import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from google import genai
import json
import datetime

# --- 1. CONFIGURACIÓN DE IA (DRIVER ACTUALIZADO 2026) ---
try:
    # Usamos la nueva SDK google-genai
    client = genai.Client(api_key=st.secrets["GOOGLE_API_KEY"])
except Exception as e:
    st.error("⚠️ Error de configuración: Verificá la GOOGLE_API_KEY en los Secrets de Streamlit.")
    st.stop()

# --- 2. ESTILO VISUAL BNA+ ---
st.set_page_config(page_title="BNA+ Copilot | Inversiones", page_icon="🏦", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #f4f7f9; }
    .main-header { background-color: #005691; padding: 20px; border-radius: 10px; color: white; text-align: center; margin-bottom: 20px; }
    .stButton>button { background-color: #005691; color: white; border-radius: 10px; font-weight: bold; width: 100%; height: 3em; border: none; }
    .stButton>button:hover { background-color: #004575; color: #white; }
    .card { background-color: white; padding: 20px; border-radius: 15px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); border-left: 5px solid #005691; margin-bottom: 20px; }
    .stExpander { background-color: white; border-radius: 10px; border: 1px solid #005691; }
    </style>
    """, unsafe_allow_html=True)

st.markdown("<div class='main-header'><h1>🏦 BNA+ Inversiones | Copilot Profundo</h1></div>", unsafe_allow_html=True)

# --- 3. CUESTIONARIO FINANCIERO ---
st.subheader("📋 Perfil Financiero Detallado")
col_g1, col_g2 = st.columns(2)

with col_g1:
    st.markdown("<div class='card'><h3>💰 Ingresos y Disponibilidad</h3></div>", unsafe_allow_html=True)
    with st.expander("Sueldos y Cobros del Mes", expanded=True):
        n_sueldos = st.number_input("¿Cuántos ingresos recibís al mes?", min_value=1, value=1)
        sueldos = []
        for i in range(n_sueldos):
            c1, c2 = st.columns(2)
            with c1: monto = st.number_input(f"Monto Sueldo {i+1} ($)", value=900000, key=f"s_m_{i}")
            with c2: fecha = st.date_input(f"Fecha de cobro {i+1}", datetime.date.today(), key=f"s_f_{i}")
            sueldos.append({"monto": monto, "fecha": str(fecha)})
    extra = st.number_input("Ahorros/Depósitos adicionales ($)", value=500000)

with col_g2:
    st.markdown("<div class='card'><h3>🏠 Gastos y Vencimientos</h3></div>", unsafe_allow_html=True)
    with st.expander("Detalle de Egresos (Tarjeta, Alquiler, Servicios)", expanded=True):
        n_gastos = st.number_input("¿Cuántos vencimientos tenés?", min_value=1, value=2)
        gastos = []
        for i in range(n_gastos):
            c1, c2, c3 = st.columns([2, 1, 1])
            with c1: desc = st.text_input(f"Descripción {i+1}", f"Gasto {i+1}", key=f"g_d_{i}")
            with c2: monto = st.number_input(f"Monto {i+1} ($)", value=250000, key=f"g_m_{i}")
            with c3: fecha = st.date_input(f"Vencimiento {i+1}", datetime.date.today() + datetime.timedelta(days=15), key=f"g_f_{i}")
            gastos.append({"desc": desc, "monto": monto, "fecha": str(fecha)})

st.markdown("<div class='card'><h3>📈 Inversiones Actuales</h3></div>", unsafe_allow_html=True)
tiene_pf = st.checkbox("Tengo Plazos Fijos activos")
pfs = []
if tiene_pf:
    n_pfs = st.number_input("Cantidad de PFs", min_value=1, value=1)
    for i in range(n_pfs):
        c1, c2, c3 = st.columns(3)
        with c1: monto = st.number_input(f"Monto PF {i+1}", value=1000000, key=f"pf_m_{i}")
        with c2: vto = st.date_input(f"Vencimiento {i+1}", datetime.date.today() + datetime.timedelta(days=10), key=f"pf_v_{i}")
        with c3: tipo = st.selectbox(f"Tipo {i+1}", ["Tradicional", "UVA"], key=f"pf_t_{i}")
        pfs.append({"monto": monto, "vto": str(vto), "tipo": tipo})

# Metas y Preferencias
col_meta, col_pref = st.columns(2)
with col_meta:
    meta_nombre = st.text_input("Tu objetivo", "Cambiar el auto 🚗")
    meta_monto = st.number_input("Monto de la meta ($)", value=10000000)
with col_pref:
    mep = st.checkbox("Me interesa operar Dólar MEP")
    saldo_hoy = st.number_input("Saldo hoy en caja de ahorro ($)", value=1500000)

# --- 4. MOTOR DE ESTRATEGIA (IA + PLOTLY) ---
if st.button("GENERAR ESTRATEGIA PROFESIONAL BNA+"):
    
    # Preparación de datos para la IA
    user_data = {
        "saldo": saldo_hoy, "sueldos": sueldos, "gastos": gastos, 
        "pfs_actuales": pfs, "meta": {"n": meta_nombre, "m": meta_monto}, "mep": mep
    }

    with st.spinner("🤖 Analizando mercado (BCRA, BYMA, BNA, Tablero Financiero)..."):
        
        prompt = f"""
        Como Asesor Senior del BNA, genera una estrategia para este cliente: {json.dumps(user_data)}
        Usa datos reales de Argentina (TNA BNA, Inflación REM, Dólar MEP).
        Responde SOLO un JSON con estas llaves:
        "analisis_macro": texto sobre tasas y MEP.
        "cartera_sugerida": [{{instrumento, monto, tipo_activo, tna_estimada}}]
        "evolucion_cartera": [{{mes, monto_pesos, inflacion_acum_estimada}}] (6 meses)
        "calce_vencimientos": [{{fecha_vto, instrumento_vto, monto_vto, gasto_cubierto}}]
        "justificacion": resumen del porqué.
        """

        try:
            # LLAMADA DEFINITIVA (Sin prefijo models/ para evitar el 404)
            response = client.models.generate_content(model='gemini-1.5-flash', contents=prompt)
            
            # Limpieza de JSON
            raw_text = response.text
            clean_json = raw_text.replace("```json", "").replace("```", "").strip()
            data = json.loads(clean_json)

            st.success("✅ Estrategia calculada con éxito")
            st.balloons()

            # --- RENDERIZADO DE RESULTADOS ---
            st.markdown(f"<div class='card'><b>Resumen de Mercado:</b><br>{data['analisis_macro']}</div>", unsafe_allow_html=True)

            # Gráfico 1: Torta (Distribución)
            df_cartera = pd.DataFrame(data['cartera_sugerida'])
            fig1 = px.pie(df_cartera, values='monto', names='tipo_activo', title='Distribución por Tipo de Activo',
                         color_discrete_sequence=['#005691', '#0074c7', '#4da3ff', '#a3d1ff'])
            st.plotly_chart(fig1, use_container_width=True)

            col_left, col_right = st.columns(2)

            with col_left:
                # Gráfico 2: Evolución vs Inflación
                st.subheader("📈 Proyección a 6 meses")
                df_evol = pd.DataFrame(data['evolucion_cartera'])
                fig2 = go.Figure()
                fig2.add_trace(go.Scatter(x=df_evol['mes'], y=df_evol['monto_pesos'], name='Capital Proyectado', line=dict(color='#005691', width=3)))
                st.plotly_chart(fig2, use_container_width=True)

            with col_right:
                # Gráfico 3: Calce de Vencimientos
                st.subheader("📅 Cronograma de Liquidez")
                df_calce = pd.DataFrame(data['calce_vencimientos'])
                fig3 = px.bar(df_calce, x='fecha_vto', y='monto_vto', color='instrumento_vto', 
                             title='Vencimientos vs Gastos', color_discrete_sequence=['#4da3ff', '#0074c7'])
                st.plotly_chart(fig3, use_container_width=True)

            st.table(df_cartera)
            st.info(f"💡 **Justificación:** {data['justificacion']}")

        except Exception as e:
            if "429" in str(e):
                st.error("⏳ Límite de cuota alcanzado. Esperá 15 segundos y reintentá.")
            else:
                st.error(f"Error en la comunicación con la IA: {e}")

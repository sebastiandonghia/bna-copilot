import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import google.generativeai as genai
import json
import datetime
import re

# Importamos los módulos que funcionan perfecto de forma externa
import ui_components
import data_orchestrator

# --- 1. CONFIGURACIÓN Y ESTILO ---
st.set_page_config(page_title="+ Copilot | Inversiones", page_icon="🏦", layout="wide")
ui_components.apply_custom_styles()
ui_components.render_header()

# CONFIGURACIÓN DE IA (REINTENTOS AUTOMÁTICOS PARA ESTABILIDAD)
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    model = genai.GenerativeModel('models/gemini-1.5-flash')
except Exception as e:
    st.error("⚠️ Error de configuración de IA.")
    st.stop()

# --- 2. CUESTIONARIO FINANCIERO ---
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

col_meta, col_pref = st.columns(2)
with col_meta:
    meta_nombre = st.text_input("Tu objetivo", "Cambiar el auto 🚗")
    meta_monto = st.number_input("Monto de la meta ($)", value=10000000)
with col_pref:
    mep = st.checkbox("Me interesa operar Dólar MEP")
    saldo_hoy = st.number_input("Saldo hoy en caja de ahorro ($)", value=1500000)

# --- 3. PROCESAMIENTO Y ESTRATEGIA ---
if st.button("GENERAR ESTRATEGIA +"):
    
    # Obtenemos todo el contexto de mercado mediante el orquestador (Modularizado)
    market_context = data_orchestrator.get_all_market_context()

    if market_context:
        # Consolidamos datos del usuario
        user_data = {
            "saldo": saldo_hoy, "sueldos": sueldos, "gastos": gastos, 
            "pfs_actuales": pfs, "meta": {"n": meta_nombre, "m": meta_monto}, "mep": mep
        }

        with st.spinner("🤖 El Copilot está analizando tu situación..."):
            try:
                # PROMPT INTEGRADO (Solución de estabilidad para Streamlit Cloud)
                prompt = f"""
                Actúa como un Asesor Financiero Fiduciario Senior del BNA, tu máxima prioridad es la seguridad y el bienestar financiero del cliente. Eres extremadamente claro, didáctico y tus recomendaciones se basan en fundamentos técnicos sólidos y profundos del mercado argentino. El dinero de la gente es una gran responsabilidad.

                Analiza los datos de este cliente: {json.dumps(user_data, indent=2)}
                Considera el siguiente contexto de mercado actualizado: {json.dumps(market_context, indent=2)}

                Tu respuesta DEBE SER EXCLUSIVAMENTE un objeto JSON válido.
                """
                # Agregamos el resto del prompt maestro para asegurar calidad
                prompt += """
                La estructura del JSON debe ser:
                {
                  "analisis_macro": "Texto educativo...",
                  "horizonte_meta": "Cálculo tiempo...",
                  "cartera_sugerida": [{"instrumento": "...", "monto": "...", "tipo_activo": "...", "tna_estimada": "...", "fundamento": "..."}],
                  "estrategia_liquidez": "Plan detallado...",
                  "evolucion_cartera": [{"mes": "Mes 1", "monto_pesos": 1000000, "ingresos_netos_mes": 500000, "egresos_totales_mes": 200000, "inflacion_acum_estimada": "5%"}],
                  "justificacion_general": "Resumen final."
                }
                """

                # Generación directa en el archivo principal
                response = model.generate_content(prompt)
                data = json.loads(response.text[response.text.find('{'):response.text.rfind('}')+1])

                st.success("✅ Estrategia Profesional Generada")
                st.balloons()

                # --- 4. RENDERIZADO DE RESULTADOS (Modularizado) ---
                ui_components.render_card("Resumen de Mercado", data['analisis_macro'])

                col_horiz, col_liq = st.columns(2)
                with col_horiz:
                    ui_components.render_card(f"Horizonte para: {meta_nombre}", data['horizonte_meta'])
                with col_liq:
                    ui_components.render_card("Plan de Liquidez", data['estrategia_liquidez'])

                st.subheader("📊 Cartera de Inversión Sugerida")

                # Procesamiento de montos para gráficos
                processed_cartera = []
                for item in data['cartera_sugerida']:
                    monto_numeric = 0
                    monto_str = str(item.get('monto', '0'))
                    match = re.search(r'(\d[\d.,]*)', monto_str)
                    if match:
                        num_str = match.group(1).replace('.', '').replace(',', '.')
                        try: monto_numeric = float(num_str)
                        except: pass
                    processed_cartera.append({"inst": item['instrumento'], "monto_n": monto_numeric, "tipo": item['tipo_activo'], "fund": item['fundamento'], "tna": item['tna_estimada'], "monto_orig": monto_str})

                df_cartera = pd.DataFrame(processed_cartera)
                if not df_cartera.empty:
                    fig1 = px.pie(df_cartera[df_cartera['monto_n'] > 0], values='monto_n', names='tipo', title='Distribución Propuesta')
                    st.plotly_chart(fig1, use_container_width=True)

                for item in processed_cartera:
                    with st.expander(f"**{item['inst']}** - Monto: {item['monto_orig']}"):
                        st.info(item['fund'])

                st.subheader("📈 Proyección a 6 Meses")
                df_evol = pd.DataFrame(data['evolucion_cartera'])
                fig2 = go.Figure()
                fig2.add_trace(go.Scatter(x=df_evol['mes'], y=df_evol['monto_pesos'], name='Capital Proyectado', line=dict(color='#005691', width=4)))
                st.plotly_chart(fig2, use_container_width=True)

                ui_components.render_card("💡 Justificación General", data['justificacion_general'])

            except Exception as e:
                st.error(f"Error al procesar la estrategia: {e}")

st.info("⚠️ Esta información es educativa y no constituye una recomendación de inversión.")

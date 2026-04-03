import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import google.generativeai as genai
import json
import datetime
import re

# Importamos nuestros módulos modularizados
import ui_components
import ai_engine
import data_orchestrator

# --- 1. CONFIGURACIÓN Y ESTILO ---
st.set_page_config(page_title="+ Copilot | Inversiones", page_icon="🏦", layout="wide")
ui_components.apply_custom_styles()
ui_components.render_header()

st.write(f"google-generativeai version: {genai.__version__}")

# CONFIGURACIÓN DE IA (PATRÓN EXACTO DE LA DEMO)
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    model = genai.GenerativeModel('models/gemini-1.5-flash')
except Exception as e:
    st.error("⚠️ Error de configuración: No se pudo inicializar la IA.")
    st.exception(e)
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
    
    # Obtenemos todo el contexto de mercado mediante el orquestador
    market_context = data_orchestrator.get_all_market_context()

    if market_context:
        # Consolidamos datos del usuario
        user_data = {
            "saldo": saldo_hoy, "sueldos": sueldos, "gastos": gastos, 
            "pfs_actuales": pfs, "meta": {"n": meta_nombre, "m": meta_monto}, "mep": mep
        }

        with st.spinner("🤖 El Copilot está analizando tu situación..."):
            try:
                # Generamos la estrategia usando el motor de IA y el modelo global
                data = ai_engine.generate_strategy(model, user_data, market_context)

                st.success("✅ Estrategia Profesional Generada")
                st.balloons()

                # --- 4. RENDERIZADO DE RESULTADOS ---
                ui_components.render_card("Resumen de Mercado", data['analisis_macro'])

                col_horiz, col_liq = st.columns(2)
                with col_horiz:
                    ui_components.render_card(f"Horizonte para: {meta_nombre}", data['horizonte_meta'])
                with col_liq:
                    ui_components.render_card("Plan de Liquidez", data['estrategia_liquidez'])

                st.subheader("📊 Cartera de Inversión Sugerida")

                # Procesamiento de montos para gráficos (Regex robusto)
                processed_cartera = []
                for item in data['cartera_sugerida']:
                    monto_numeric = 0
                    monto_str = str(item.get('monto', '0'))
                    match = re.search(r'(\d[\d.,]*)', monto_str)
                    if match:
                        num_str = match.group(1).replace('.', '').replace(',', '.')
                        try: monto_numeric = float(num_str)
                        except: pass
                    
                    new_item = item.copy()
                    new_item['monto_num'] = monto_numeric
                    processed_cartera.append(new_item)

                df_cartera = pd.DataFrame(processed_cartera)
                
                if not df_cartera.empty:
                    fig1 = px.pie(df_cartera[df_cartera['monto_num'] > 0], values='monto_num', names='tipo_activo', 
                                 title='Distribución por Tipo de Activo',
                                 color_discrete_sequence=['#005691', '#0074c7', '#4da3ff', '#a3d1ff'])
                    st.plotly_chart(fig1, use_container_width=True)

                st.subheader("📋 Fundamentos de cada Instrumento")
                for item in processed_cartera:
                    with st.expander(f"**{item['instrumento']}** - Monto: {item.get('monto', 'N/A')}"):
                        st.markdown(f"**Rendimiento:** {item['tna_estimada']} | **Tipo:** {item['tipo_activo']}")
                        st.info(item['fundamento'])

                st.subheader("📈 Proyección de Flujo de Efectivo (6 Meses)")
                df_evol = pd.DataFrame(data['evolucion_cartera'])
                fig2 = go.Figure()
                fig2.add_trace(go.Scatter(x=df_evol['mes'], y=df_evol['monto_pesos'], name='Capital Proyectado', line=dict(color='#005691', width=4)))
                fig2.add_trace(go.Scatter(x=df_evol['mes'], y=df_evol['inflacion_acum_estimada'], name='Inflación', line=dict(color='#ff4b4b', dash='dot')))
                st.plotly_chart(fig2, use_container_width=True)

                st.markdown("---")
                ui_components.render_card("💡 Justificación General", data['justificacion_general'])

            except Exception as e:
                st.error(f"Error al procesar la estrategia: {e}")

st.info("⚠️ **Aclaración:** Esta información es educativa y no constituye una recomendación de inversión.")

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import google.generativeai as genai
import json
import datetime
import re

# Importamos módulos modularizados
import ui_components
import data_orchestrator

# --- 1. CONFIGURACIÓN Y ESTILO ---
st.set_page_config(page_title="+ Copilot | Inversiones", page_icon="🏦", layout="wide")
ui_components.apply_custom_styles()
ui_components.render_header()

# AUTO-MODEL DISCOVERY
@st.cache_resource
def get_best_model_name():
    """Busca dinámicamente el nombre del modelo Flash disponible."""
    try:
        genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
        models = [m.name for m in genai.list_models() 
                  if 'generateContent' in m.supported_generation_methods 
                  and 'flash' in m.name.lower()]
        if not models: return None
        flash_15 = [m for m in models if '1.5' in m]
        return flash_15[0] if flash_15 else models[0]
    except: return None

model_name = get_best_model_name()
model = None

if model_name:
    try:
        model = genai.GenerativeModel(model_name)
        st.toast(f"🤖 IA lista ({model_name})")
    except: st.error("Error al inicializar el modelo.")
else:
    st.error("❌ No se pudo conectar con la IA. Verificá tu API KEY.")

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
    market_context = data_orchestrator.get_all_market_context()

    if market_context and model:
        user_data = {
            "saldo": saldo_hoy, "sueldos": sueldos, "gastos": gastos, 
            "pfs_actuales": pfs, "meta": {"n": meta_nombre, "m": meta_monto}, "mep": mep
        }

        with st.spinner("🤖 Generando estrategia financiera personalizada..."):
            try:
                # PROMPT MAESTRO COMPLETO Y DETALLADO
                prompt = f"""
                Actúa como un Asesor Financiero Senior del BNA. Tu prioridad es la seguridad y bienestar del cliente.
                Analiza los datos del cliente: {json.dumps(user_data, indent=2)}
                Analiza el contexto de mercado: {json.dumps(market_context, indent=2)}

                Tu respuesta DEBE SER EXCLUSIVAMENTE un objeto JSON válido con esta estructura:
                {{
                  "analisis_macro": "Explicación del contexto económico de Argentina.",
                  "horizonte_meta": "Cálculo estimado para alcanzar el objetivo.",
                  "cartera_sugerida": [
                    {{
                      "instrumento": "Nombre",
                      "monto": "Monto sugerido",
                      "tipo_activo": "Categoría",
                      "tna_estimada": "Rendimiento",
                      "fundamento": "Por qué se elige."
                    }}
                  ],
                  "estrategia_liquidez": "Plan para el corto plazo.",
                  "evolucion_cartera": [
                    {{
                      "mes": "Mes 1",
                      "monto_pesos": 1000000,
                      "ingresos_netos_mes": 500000,
                      "egresos_totales_mes": 200000,
                      "inflacion_acum_estimada": "5%"
                    }}
                  ],
                  "justificacion_general": "Resumen final."
                }}
                """

                response = model.generate_content(prompt)
                raw_text = response.text
                data = json.loads(raw_text[raw_text.find('{'):raw_text.rfind('}')+1])

                st.success("✅ Estrategia Generada")
                st.balloons()

                # --- 4. RENDERIZADO ---
                ui_components.render_card("Resumen de Mercado", data['analisis_macro'])

                c1, c2 = st.columns(2)
                with c1: ui_components.render_card(f"Horizonte Meta", data['horizonte_meta'])
                with c2: ui_components.render_card("Plan de Liquidez", data['estrategia_liquidez'])

                st.subheader("📊 Cartera de Inversión Sugerida")
                processed_cartera = []
                for item in data['cartera_sugerida']:
                    m_str = str(item.get('monto', '0'))
                    match = re.search(r'(\d[\d.,]*)', m_str)
                    m_num = float(match.group(1).replace('.', '').replace(',', '.')) if match else 0
                    processed_cartera.append({"inst": item['instrumento'], "monto_n": m_num, "tipo": item['tipo_activo'], "fund": item['fundamento'], "tna": item['tna_estimada'], "monto_orig": m_str})

                df = pd.DataFrame(processed_cartera)
                if not df.empty:
                    st.plotly_chart(px.pie(df[df['monto_n'] > 0], values='monto_n', names='tipo', title='Distribución'), use_container_width=True)

                for item in processed_cartera:
                    with st.expander(f"**{item['inst']}** - {item['monto_orig']}"):
                        st.info(item['fund'])

                st.subheader("📈 Proyección de Capital")
                df_evol = pd.DataFrame(data['evolucion_cartera'])
                st.plotly_chart(px.line(df_evol, x='mes', y='monto_pesos', title='Evolución Proyectada'), use_container_width=True)

                ui_components.render_card("💡 Justificación General", data['justificacion_general'])

            except Exception as e:
                st.error(f"Error al procesar la respuesta: {e}")
                if 'raw_text' in locals(): st.code(raw_text)

st.info("⚠️ Esta información es educativa y no constituye asesoramiento financiero.")

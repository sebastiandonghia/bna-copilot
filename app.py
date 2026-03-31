import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import google.generativeai as genai
import json
import datetime
import requests

# --- 0. FUNCIONES DE CAPTURA DE DATOS REALES (Reforzada) ---
def get_market_data():
    """Captura datos reales de APIs financieras de Argentina con Fallbacks técnicos"""
    market_data = {
        "mep": 1280.0, 
        "bna_vendedor": 960.0,
        "tna_pf_bna": 38.0,
        "inflacion_rem": 3.4,
        "letra_ejemplo": {"nombre": "S30A6", "tira": "52%"},
        "fecha": datetime.date.today().strftime("%d/%m/%Y"),
        "banda_inferior": 920.0,
        "banda_superior": 1050.0
    }
    try:
        # 1. Dólar MEP
        res_mep = requests.get("https://dolarapi.com/v1/dolares/mep", timeout=3).json()
        market_data["mep"] = res_mep.get("venta")

        # 2. Dólar Oficial BNA
        res_bna = requests.get("https://dolarapi.com/v1/dolares/oficial", timeout=3).json()
        market_data["bna_vendedor"] = res_bna.get("venta")

        # 3. Tasas de Plazo Fijo (ArgentinaDatos)
        res_pf = requests.get("https://api.argentinadatos.com/v1/finanzas/tasas/plazoFijo", timeout=3).json()
        bna_data = next((x for x in res_pf if "NACION" in x['entidad'].upper()), None)
        if bna_data:
            market_data["tna_pf_bna"] = bna_data['tna']

        # 4. Inflación REM
        res_inf = requests.get("https://api.argentinadatos.com/v1/finanzas/indices/inflacion", timeout=3).json()
        if res_inf:
            market_data["inflacion_rem"] = res_inf[-1]['valor']
            
    except Exception as e:
        st.warning(f"📡 Nota: Se usan estimaciones de mercado por latencia de API.")
    
    return market_data

# --- 1. CONFIGURACIÓN DE IA ---
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    st.error("⚠️ Error de configuración de IA. Verificá los Secrets.")
    st.stop()

# --- 2. ESTILO VISUAL BNA+ (ACTUALIZADO SEGÚN LOGIN DIGITAL.BNA) ---
st.set_page_config(page_title="Copilot Profesional | + Inversiones", page_icon="🏦", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #f8fafc; }
    .main-header { 
        background-color: #007dc5; 
        padding: 25px; border-radius: 12px; color: white; text-align: center; margin-bottom: 25px; 
        box-shadow: 0 4px 6px rgba(0,0,0,0.05); 
    }
    .stButton>button { 
        background-color: #e2e8f0; color: #64748b; border-radius: 12px; font-weight: bold; 
        width: 100%; height: 3.5em; border: none; transition: all 0.3s ease;
    }
    .stButton>button:hover { 
        background-color: #007dc5; color: white; box-shadow: 0 4px 12px rgba(0,125,197,0.2);
    }
    .live-ticker { 
        background-color: #f1f5f9; padding: 12px; border-radius: 8px; text-align: center; 
        font-weight: bold; color: #007dc5; margin-bottom: 25px; border: 1px solid #e2e8f0; 
    }
    .card { 
        background-color: white; padding: 25px; border-radius: 16px; 
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); margin-bottom: 25px; border: 1px solid #e2e8f0; 
    }
    .card h3 { color: #007dc5; font-size: 1.3rem; margin-top: 0; }
    .stExpander { background-color: white; border-radius: 12px; border: 1px solid #e2e8f0; }
    </style>
    """, unsafe_allow_html=True)

st.markdown("<div class='main-header'><h1>🏦 + Inversiones | Copilot Profesional</h1></div>", unsafe_allow_html=True)

m_data = get_market_data()
st.markdown(f"""
    <div class='live-ticker'>
        📡 Terminal Research BNA ({m_data['fecha']}): 
        💵 MEP: ${m_data['mep']} | 🏦 TNA BNA: {m_data['tna_pf_bna']}% | 📈 REM Inf: {m_data['inflacion_rem']}%
    </div>
""", unsafe_allow_html=True)

# --- 3. CUESTIONARIO FINANCIERO ---
st.subheader("📋 Perfil Financiero del Cliente")
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
    with st.expander("Detalle de Egresos", expanded=True):
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
    mep_check = st.checkbox("Me interesa operar Dólar MEP")
    saldo_hoy = st.number_input("Saldo hoy en caja de ahorro ($)", value=1500000)

# --- 4. MOTOR DE ESTRATEGIA ---
if st.button("GENERAR ESTRATEGIA PROFESIONAL +"):
    user_data = {
        "saldo": saldo_hoy, "sueldos": sueldos, "gastos": gastos, 
        "pfs_actuales": pfs, "meta": {"n": meta_nombre, "m": meta_monto}, "mep": mep_check
    }

    with st.spinner("🤖 Nuestro equipo de Research BNA está diseñando su estrategia fiduciaria..."):
        prompt = f"""
        # ROLE: ASESOR FINANCIERO FIDUCIARIO SENIOR - BANCO NACIÓN (BNA+)
        Inversor NO CALIFICADO, adverso al riesgo alto. Tono didáctico y profesional.

        Analiza estos datos: {json.dumps(user_data)}

        # CONTEXTO DE MERCADO REAL:
        - Dólar Oficial BNA: ${m_data['bna_vendedor']} | Dólar MEP: ${m_data['mep']}
        - TNA Plazo Fijo BNA: {m_data['tna_pf_bna']}% | Plazo Fijo UVA: UVA + 1%
        - Inflación REM BCRA: {m_data['inflacion_rem']}% | Letra ref: {m_data['letra_ejemplo']['nombre']} ({m_data['letra_ejemplo']['tira']})

        # INSTRUCCIONES:
        1. Sé explícito con plazos (ej. PF BNA a 30 días).
        2. Usa nombres reales de FCIs PELLEGRINI (Money Market, Renta Pesos, etc).
        3. Para Letras/Bonos, justifica la elección técnica.
        4. Respuesta exclusiva en JSON.

        Estructura:
        {{
          "analisis_macro": "Contexto educativo sobre tasas, inflación y brecha.",
          "cartera_sugerida": [
            {{ "instrumento": "Nombre exacto", "monto": valor, "tipo_activo": "Categoría", "tna_estimada": "valor", "fundamento": "Didáctico" }}
          ],
          "tabla_comparativa_letras": [
            {{ "letra": "Nombre", "plazo_dias": n, "tira_estimada": "X%", "justificacion": "Por qué sí o por qué no" }}
          ],
          "estrategia_liquidez": "Paso a paso usando FCIs Pellegrini.",
          "evolucion_cartera": [{{ "mes": "Mes 1", "monto_pesos": v, "inflacion_acum_estimada": "X%" }}],
          "justificacion_fiduciaria": "Resumen final de seguridad."
        }}
        """

        try:
            response = model.generate_content(prompt)
            data = json.loads(response.text[response.text.find('{'):response.text.rfind('}') + 1])

            st.success("✅ Estrategia Profesional BNA Generada")

            st.markdown(f"<div class='card'><h3>Análisis de Research</h3><p>{data['analisis_macro']}</p></div>", unsafe_allow_html=True)
            
            st.subheader("📊 Cartera de Inversión Sugerida")
            df_cartera = pd.DataFrame(data['cartera_sugerida'])
            st.plotly_chart(px.pie(df_cartera, values='monto', names='instrumento', hole=.4, color_discrete_sequence=px.colors.qualitative.Safe), use_container_width=True)

            # Nueva Tabla Comparativa de Letras
            st.markdown("<div class='card'><h3>📋 Comparativa de Letras del Tesoro (Lecaps/Boncer)</h3>", unsafe_allow_html=True)
            st.table(pd.DataFrame(data['tabla_comparativa_letras']))
            st.markdown("</div>", unsafe_allow_html=True)

            for item in data['cartera_sugerida']:
                with st.expander(f"🔍 {item['instrumento']} - ${item['monto']:,}"):
                    st.write(f"**Rendimiento:** {item['tna_estimada']}")
                    st.info(item['fundamento'])

            st.markdown(f"<div class='card'><h3>💧 Plan de Liquidez y Gastos</h3><p>{data['estrategia_liquidez']}</p></div>", unsafe_allow_html=True)
            
            st.subheader("📈 Proyección vs Inflación")
            df_evol = pd.DataFrame(data['evolucion_cartera'])
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=df_evol['mes'], y=df_evol['monto_pesos'], name='Cartera', line=dict(color='#007dc5', width=4)))
            st.plotly_chart(fig, use_container_width=True)

        except Exception as e:
            st.error(f"Error: {e}")

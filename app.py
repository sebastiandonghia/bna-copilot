import streamlit as st
import subprocess
import json
import pandas as pd
import plotly.express as px
import datetime
import requests
import shlex

# --- API Endpoints Corregidos ---
ARGENTINADATOS_BASE_URL = "https://api.argentinadatos.com/v1"
DATA912_BASE_URL = "https://data912.com"

def fetch_real_time_data():
    """Fetches real-time financial data with filters to avoid buffer overflow."""
    data = {}
    today_str = datetime.date.today().strftime("%Y-%m-%d")

    # 1. Plazo Fijo (URL corregida)
    try:
        pf_response = requests.get(f"{ARGENTINADATOS_BASE_URL}/finanzas/tasas/plazo-fijo", timeout=5)
        pf_response.raise_for_status()
        # Solo enviamos los últimos 5 registros para no saturar el prompt
        data['plazo_fijo_rates'] = pf_response.json()[-5:]
    except Exception as e:
        st.warning(f"⚠️ Error Plazo Fijo: {e}")

    # 2. Inflación (FILTRO CRÍTICO: Solo últimos 6 meses)
    try:
        inflacion_response = requests.get(f"{ARGENTINADATOS_BASE_URL}/finanzas/indices/inflacion", timeout=5)
        inflacion_response.raise_for_status()
        data['inflacion_mensual'] = inflacion_response.json()[-6:] 
    except Exception as e:
        st.warning(f"⚠️ Error Inflación: {e}")

    # 3. Dólar MEP (URL corregida sin /casa/)
    try:
        dolar_response = requests.get(f"{ARGENTINADATOS_BASE_URL}/cotizaciones/dolares/mep", timeout=5)
        if dolar_response.status_code == 200:
            data['dolar_mep'] = dolar_response.json()
        else:
            # Fallback a Data912 si falla ArgentinaDatos
            mep_912 = requests.get(f"{DATA912_BASE_URL}/live/mep", timeout=5)
            data['dolar_mep'] = mep_912.json()
    except Exception as e:
        st.warning(f"⚠️ Error Dólar MEP: {e}")

    return data

# --- CONFIGURACIÓN DE INTERFAZ ---
st.set_page_config(page_title="+ Copilot | BNA", page_icon="🏦", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #f4f7f9; }
    .main-header { background-color: #005691; padding: 20px; border-radius: 10px; color: white; text-align: center; margin-bottom: 20px; }
    .card { background-color: white; padding: 20px; border-radius: 15px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); border-left: 5px solid #005691; margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

st.markdown("<div class='main-header'><h1>🏦 + Inversiones | Copilot Profesional</h1></div>", unsafe_allow_html=True)

# --- FORMULARIO ---
col_g1, col_g2 = st.columns(2)
with col_g1:
    st.markdown("<div class='card'><h3>💰 Ingresos</h3></div>", unsafe_allow_html=True)
    monto_sueldo = st.number_input("Sueldo Neto ($)", value=900000)
    fecha_cobro = st.date_input("Fecha de cobro", datetime.date.today())
    extra = st.number_input("Ahorros adicionales ($)", value=500000)

with col_g2:
    st.markdown("<div class='card'><h3>🏠 Gastos Próximos</h3></div>", unsafe_allow_html=True)
    gasto_monto = st.number_input("Monto total gastos mes ($)", value=500000)
    meta_nombre = st.text_input("Tu objetivo", "Cambiar el auto 🚗")
    meta_monto = st.number_input("Monto de la meta ($)", value=10000000)

# --- LÓGICA DE PROCESAMIENTO ---
if st.button("GENERAR ESTRATEGIA PROFESIONAL"):
    with st.spinner("Analizando mercado..."):
        
        market_data = fetch_real_time_data()
        
        contexto_usuario = {
            "ingresos": [{"monto": monto_sueldo, "fecha": str(fecha_cobro)}],
            "ahorros": extra,
            "gastos": gasto_monto,
            "meta": {"nombre": meta_nombre, "monto": meta_monto},
            "market_snapshot": market_data
        }

        # Prompt simplificado para asegurar estabilidad
        prompt_final = f"""
        Eres un asesor financiero senior del Banco Nación. 
        Analiza estos datos y responde UNICAMENTE con un JSON:
        {json.dumps(contexto_usuario)}
        
        El JSON debe tener: 'analisis_macro', 'horizonte_meta', 'cartera_sugerida' (lista con instrumento, monto, porcentaje_cartera, fundamento), 'estrategia_liquidez' y 'justificacion_general'.
        Importante: La suma de porcentajes debe ser 100.
        """

        try:
            # SOLUCIÓN AL ERROR "ARGUMENT LIST TOO LONG": Usar stdin
            process = subprocess.Popen(
                ["gemini"], 
                stdin=subprocess.PIPE, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE, 
                text=True,
                encoding='utf-8'
            )
            
            resultado_raw, error_output = process.communicate(input=prompt_final)

            if process.returncode != 0:
                st.error("Error en el CLI de Gemini")
                st.code(error_output)
            else:
                # Extraer JSON de la respuesta
                start = resultado_raw.find('{')
                end = resultado_raw.rfind('}') + 1
                data = json.loads(resultado_raw[start:end])

                st.success("✅ Estrategia Generada")
                
                # Renderizado
                st.markdown(f"<div class='card'><b>Análisis:</b> {data['analisis_macro']}</div>", unsafe_allow_html=True)
                
                df = pd.DataFrame(data['cartera_sugerida'])
                fig = px.pie(df, values='porcentaje_cartera', names='instrumento', title='Cartera Recomendada')
                st.plotly_chart(fig, use_container_width=True)
                
                for item in data['cartera_sugerida']:
                    with st.expander(f"{item['instrumento']} - {item['porcentaje_cartera']}%"):
                        st.write(f"**Monto:** ${item['monto']:,.2f}")
                        st.info(item['fundamento'])

        except Exception as e:
            st.error(f"Error inesperado: {e}")

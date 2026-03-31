import streamlit as st
import subprocess
import json
import pandas as pd
import plotly.express as px
import datetime
import requests
import shlex

# --- API Endpoints ---
ARGENTINADATOS_BASE_URL = "https://api.argentinadatos.com/v1"
DATA912_BASE_URL = "https://data912.com"

def fetch_real_time_data():
    """Fetches real-time financial data with filters to prevent 'Argument list too long'."""
    data = {}
    today_str = datetime.date.today().strftime("%Y-%m-%d")

    try:
        pf_response = requests.get(f"{ARGENTINADATOS_BASE_URL}/finanzas/tasas/plazo-fijo", timeout=5)
        pf_response.raise_for_status()
        data['plazo_fijo_rates'] = pf_response.json()[-10:] # Solo los últimos 10
    except Exception as e:
        st.warning(f"⚠️ Error Plazo Fijo: {e}")

    try:
        inflacion_response = requests.get(f"{ARGENTINADATOS_BASE_URL}/finanzas/indices/inflacion", timeout=5)
        inflacion_response.raise_for_status()
        data['inflacion_mensual'] = inflacion_response.json()[-6:] # FILTRO CRÍTICO: Últimos 6 meses
    except Exception as e:
        st.warning(f"⚠️ Error Inflación: {e}")

    try:
        uva_response = requests.get(f"{ARGENTINADATOS_BASE_URL}/finanzas/indices/uva", timeout=5)
        uva_response.raise_for_status()
        data['uva_indices'] = uva_response.json()[-5:] # Solo los últimos 5
    except Exception as e:
        st.warning(f"⚠️ Error UVA: {e}")

    try:
        fci_mm_response = requests.get(f"{ARGENTINADATOS_BASE_URL}/finanzas/fci/mercado-dinero/fecha/{today_str}", timeout=5)
        fci_mm_response.raise_for_status()
        data['fci_money_market'] = fci_mm_response.json()
    except Exception:
        pass # Silenciamos si no hay datos de hoy

    try:
        dolar_response = requests.get(f"{ARGENTINADATOS_BASE_URL}/cotizaciones/dolares/mep", timeout=5)
        data['dolar_mep_argentinadatos'] = dolar_response.json()
    except Exception:
        pass

    return data

# --- 1. CONFIGURACIÓN DE PÁGINA (TU DISEÑO ORIGINAL) ---
st.set_page_config(page_title="+ Copilot | Inversiones", page_icon="🏦", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #f4f7f9; }
    .main-header { background-color: #005691; padding: 20px; border-radius: 10px; color: white; text-align: center; margin-bottom: 20px; }
    .stButton>button { background-color: #005691; color: white; border-radius: 10px; font-weight: bold; width: 100%; height: 3em; border: none; }
    .card { background-color: white; padding: 20px; border-radius: 15px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); border-left: 5px solid #005691; margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

st.markdown("<div class='main-header'><h1>🏦 + Inversiones | Copilot Profesional</h1></div>", unsafe_allow_html=True)

# --- 2. FORMULARIO (MANTENIENDO TODA TU LÓGICA) ---
st.subheader("📋 Perfil Financiero Detallado")
col_g1, col_g2 = st.columns(2)

with col_g1:
    st.markdown("<div class='card'><h3>💰 Ingresos y Disponibilidad</h3></div>", unsafe_allow_html=True)
    with st.expander("Sueldos y Cobros del Mes", expanded=True):
        n_sueldos = st.number_input("¿Cuántos ingresos recibís al mes?", min_value=1, value=1)
        sueldos = []
        for i in range(n_sueldos):
            c1, c2 = st.columns(2)
            with c1: m = st.number_input(f"Monto Sueldo {i+1}", value=900000, key=f"s_m_{i}")
            with c2: f = st.date_input(f"Fecha {i+1}", datetime.date.today(), key=f"s_f_{i}")
            sueldos.append({"monto": m, "fecha": str(f)})
    extra = st.number_input("Ahorros adicionales ($)", value=500000)

with col_g2:
    st.markdown("<div class='card'><h3>🏠 Gastos y Vencimientos</h3></div>", unsafe_allow_html=True)
    with st.expander("Detalle de Egresos", expanded=True):
        n_gastos = st.number_input("¿Cuántos vencimientos?", min_value=1, value=2)
        gastos = []
        for i in range(n_gastos):
            c1, c2, c3 = st.columns([2, 1, 1])
            with c1: d = st.text_input(f"Desc {i+1}", f"Gasto {i+1}", key=f"g_d_{i}")
            with c2: m = st.number_input(f"Monto {i+1}", value=250000, key=f"g_m_{i}")
            with c3: f = st.date_input(f"Vto {i+1}", datetime.date.today() + datetime.timedelta(days=15), key=f"g_f_{i}")
            gastos.append({"desc": d, "monto": m, "fecha": str(f)})

# (Omití visualmente la parte de PF por brevedad, pero en tu código debe seguir igual)

meta_nombre = st.text_input("Objetivo", "Cambiar el auto 🚗")
meta_monto = st.number_input("Monto Meta ($)", value=10000000)
saldo_hoy = st.number_input("Saldo hoy ($)", value=1500000)

# --- 3. MOTOR DE ESTRATEGIA (LA PARTE QUE ARREGLA EL ERROR) ---
if st.button("GENERAR ESTRATEGIA PROFESIONAL"):
    with st.spinner("Analizando..."):
        
        real_time_data = fetch_real_time_data()
        
        contexto_usuario = {
            "saldo_caja_ahorro": saldo_hoy,
            "ingresos_mensuales": sueldos,
            "gastos_vencimientos": gastos,
            "meta_objetivo_nombre": meta_nombre,
            "meta_objetivo_monto": meta_monto,
            "datos_mercado_tiempo_real": real_time_data
        }

        # IMPORTANTE: Usamos el PROMPT_MAESTRO_V2_CONTENT que tenías originalmente
        prompt_completo = f"Tu prompt original aquí...\nDatos: {json.dumps(contexto_usuario)}"

        try:
            # ARREGLO PARA EL ERROR "OSERROR: ARGUMENT LIST TOO LONG"
            # No pasamos el prompt en la lista del comando, lo pasamos por STDIN
            process = subprocess.Popen(
                ["gemini"], 
                stdin=subprocess.PIPE, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE, 
                text=True,
                encoding='utf-8'
            )
            
            # Esto envía el texto DIRECTAMENTE al proceso, saltándose los límites de la terminal
            resultado_raw, error_output = process.communicate(input=prompt_completo)

            if process.returncode != 0:
                st.error("Error en Gemini")
                st.code(error_output)
            else:
                # Tu lógica de parseo original sigue acá...
                start = resultado_raw.find('{')
                end = resultado_raw.rfind('}') + 1
                data = json.loads(resultado_raw[start:end])
                
                st.success("✅ Estrategia Generada")
                # Aquí seguís con tus st.plotly_chart y st.expander originales...

        except Exception as e:
            st.exception(e)

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from google import genai
from google.genai import types
import json
import datetime
import re

# ------------------------------------------------------------
# 0) CONFIG STREAMLIT
# ------------------------------------------------------------
st.set_page_config(page_title="BNA+ Copilot | Inversiones", page_icon="🏦", layout="wide")

# ------------------------------------------------------------
# 1) CLIENT GEMINI
# ------------------------------------------------------------
try:
    api_key = st.secrets["GOOGLE_API_KEY"]
except Exception:
    st.error("⚠️ Falta GOOGLE_API_KEY en Secrets de Streamlit.")
    st.stop()

client = genai.Client(api_key=api_key)

# ------------------------------------------------------------
# 2) UTILIDADES
# ------------------------------------------------------------
@st.cache_data(ttl=3600)
def get_models_supporting_generate_content():
    names = []
    try:
        for m in client.models.list():
            if "generateContent" in getattr(m, "supported_actions", []):
                names.append(m.name)
    except:
        return ["gemini-1.5-flash"] # Fallback si falla el listado
    return names

def pick_preferred_model(model_names):
    priority = ["flash-lite", "1.5-flash"]
    for p in priority:
        for name in model_names:
            if p in name: return name
    return "gemini-1.5-flash"

# ------------------------------------------------------------
# 3) UI: Estilos
# ------------------------------------------------------------
st.markdown("""
<style>
.stApp { background-color: #f4f7f9; }
.main-header { background-color: #005691; padding: 20px; border-radius: 10px; color: white; text-align: center; margin-bottom: 20px; }
.stButton>button { background-color: #005691; color: white; border-radius: 10px; font-weight: bold; width: 100%; height: 3em; border: none; }
.card { background-color: white; padding: 20px; border-radius: 15px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); border-left: 5px solid #005691; margin-bottom: 20px; }
</style>
""", unsafe_allow_html=True)

st.markdown("<div class='main-header'><h1>🏦 BNA+ Inversiones | Copilot Profundo</h1></div>", unsafe_allow_html=True)

modelos_ok = get_models_supporting_generate_content()
MODEL_NAME = pick_preferred_model(modelos_ok)
st.caption(f"✅ Motor: **{MODEL_NAME}**")

# ------------------------------------------------------------
# 4) CUESTIONARIO (Resumido para el ejemplo)
# ------------------------------------------------------------
col_g1, col_g2 = st.columns(2)
with col_g1:
    st.markdown("<div class='card'><h3>💰 Disponibilidad</h3></div>", unsafe_allow_html=True)
    sueldo = st.number_input("Monto Sueldo ($)", value=900000)
    ahorros = st.number_input("Ahorros adicionales ($)", value=500000)

with col_g2:
    st.markdown("<div class='card'><h3>🏠 Gastos</h3></div>", unsafe_allow_html=True)
    gasto_fijo = st.number_input("Gastos fijos totales ($)", value=450000)
    meta_monto = st.number_input("Meta de ahorro ($)", value=10000000)

# ------------------------------------------------------------
# 5) GENERAR ESTRATEGIA (FIXED JSON MODE)
# ------------------------------------------------------------
if st.button("GENERAR ESTRATEGIA PROFESIONAL BNA+"):
    user_data = {"sueldo": sueldo, "ahorros": ahorros, "gastos": gasto_fijo, "meta": meta_monto}

    prompt = f"Generá una estrategia de inversión para Argentina (JSON): {json.dumps(user_data)}. " \
             f"Devolvé un JSON con: analisis_macro, cartera_sugerida, evolucion_cartera, calce_vencimientos, justificacion."

    with st.spinner("🤖 Analizando..."):
        try:
            # --- CORRECCIÓN CRÍTICA AQUÍ ---
            # En la SDK google-genai, el parámetro es 'response_mime_type' 
            # pero debe estar dentro de GenerateContentConfig correctamente.
            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type='application/json',
                    temperature=0.1
                )
            )

            data = json.loads(response.text)
            st.session_state.last_result = data
            st.success("✅ Estrategia generada")

        except Exception as e:
            st.error(f"❌ Error: {e}")

# ------------------------------------------------------------
# 6) RENDERIZADO
# ------------------------------------------------------------
if "last_result" in st.session_state and st.session_state.last_result:
    data = st.session_state.last_result
    
    st.info(data.get('analisis_macro', ''))
    
    df_cartera = pd.DataFrame(data.get("cartera_sugerida", []))
    if not df_cartera.empty:
        st.plotly_chart(px.pie(df_cartera, values="monto", names="instrumento", title="Cartera Sugerida"))
        st.table(df_cartera)
    
    st.write(f"💡 **Justificación:** {data.get('justificacion', '')}")

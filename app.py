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
# 0) CONFIG STREAMLIT (SIEMPRE ARRIBA DE TODO)
# ------------------------------------------------------------
st.set_page_config(page_title="BNA+ Copilot | Inversiones", page_icon="🏦", layout="wide")

# ------------------------------------------------------------
# 1) CLIENT GEMINI (SDK google-genai) + API VERSION V1
# ------------------------------------------------------------
try:
    api_key = st.secrets["GOOGLE_API_KEY"]
except Exception:
    st.error("⚠️ Falta GOOGLE_API_KEY en Secrets de Streamlit.")
    st.stop()

# Forzamos v1 (estable) para evitar sorpresas de v1beta
# (Google documenta que el SDK default es v1beta y se puede cambiar a v1) 
client = genai.Client(
    api_key=api_key,
    http_options={"api_version": "v1"},
)

# ------------------------------------------------------------
# 2) UTILIDADES: listar modelos y elegir 1 que soporte generateContent
# ------------------------------------------------------------
@st.cache_data(ttl=3600)
def get_models_supporting_generate_content():
    names = []
    for m in client.models.list():
        if "generateContent" in getattr(m, "supported_actions", []):
            # m.name normalmente viene como "models/xxxx"
            names.append(m.name)
    return names

def pick_preferred_model(model_names):
    """
    Preferencias:
    - flash-lite (más barato)
    - flash
    - cualquier otro
    """
    if not model_names:
        return None

    priority = [
        "flash-lite",
        "flash",
    ]

    # 1) Primero intentamos match por prioridad
    for p in priority:
        for name in model_names:
            if p in name:
                return name

    # 2) Si no, devolvemos el primero
    return model_names[0]

def parse_json_strict(text: str):
    """
    Si response_mime_type es application/json, debería venir JSON limpio.
    Igual dejamos un parser robusto por si aparece codefence.
    """
    if not text:
        raise ValueError("Respuesta vacía del modelo.")

    # Si vino en ```json ... ```
    m = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
    if m:
        text = m.group(1).strip()

    return json.loads(text)

# ------------------------------------------------------------
# 3) UI: Estilos
# ------------------------------------------------------------
st.markdown("""
<style>
.stApp { background-color: #f4f7f9; }
.main-header { background-color: #005691; padding: 20px; border-radius: 10px; color: white; text-align: center; margin-bottom: 20px; }
.stButton>button { background-color: #005691; color: white; border-radius: 10px; font-weight: bold; width: 100%; height: 3em; border: none; }
.stButton>button:hover { background-color: #004575; }
.card { background-color: white; padding: 20px; border-radius: 15px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); border-left: 5px solid #005691; margin-bottom: 20px; }
.stExpander { background-color: white; border-radius: 10px; border: 1px solid #005691; }
</style>
""", unsafe_allow_html=True)

st.markdown("<div class='main-header'><h1>🏦 BNA+ Inversiones | Copilot Profundo</h1></div>", unsafe_allow_html=True)

# ------------------------------------------------------------
# 4) DEBUG OPCIONAL: mostrar modelos disponibles
# ------------------------------------------------------------
with st.expander("🧪 Debug: ver modelos disponibles para esta API key", expanded=False):
    modelos_ok = get_models_supporting_generate_content()
    if modelos_ok:
        st.write("Modelos que soportan generateContent (según models.list):")
        for n in modelos_ok[:50]:
            st.write(n)
        if len(modelos_ok) > 50:
            st.caption(f"(Mostrando 50 de {len(modelos_ok)} modelos)")
    else:
        st.warning("No se encontraron modelos con generateContent. Tu API key podría no tener acceso habilitado.")

# Elegimos el modelo automáticamente
modelos_ok = get_models_supporting_generate_content()
MODEL_NAME = pick_preferred_model(modelos_ok)

if not MODEL_NAME:
    st.error("No pude seleccionar un modelo válido (models.list no devolvió modelos con generateContent).")
    st.stop()

st.caption(f"✅ Modelo seleccionado automáticamente: **{MODEL_NAME}**")

# ------------------------------------------------------------
# 5) CUESTIONARIO FINANCIERO
# ------------------------------------------------------------
st.subheader("📋 Perfil Financiero Detallado")
col_g1, col_g2 = st.columns(2)

with col_g1:
    st.markdown("<div class='card'><h3>💰 Ingresos y Disponibilidad</h3></div>", unsafe_allow_html=True)
    with st.expander("Sueldos y Cobros del Mes", expanded=True):
        n_sueldos = st.number_input("¿Cuántos ingresos recibís al mes?", min_value=1, value=1)
        sueldos = []
        for i in range(n_sueldos):
            c1, c2 = st.columns(2)
            with c1:
                monto = st.number_input(f"Monto Sueldo {i+1} ($)", value=900000, key=f"s_m_{i}")
            with c2:
                fecha = st.date_input(f"Fecha de cobro {i+1}", datetime.date.today(), key=f"s_f_{i}")
            sueldos.append({"monto": monto, "fecha": str(fecha)})
    extra = st.number_input("Ahorros/Depósitos adicionales ($)", value=500000)

with col_g2:
    st.markdown("<div class='card'><h3>🏠 Gastos y Vencimientos</h3></div>", unsafe_allow_html=True)
    with st.expander("Detalle de Egresos (Tarjeta, Alquiler, Servicios)", expanded=True):
        n_gastos = st.number_input("¿Cuántos vencimientos tenés?", min_value=1, value=2)
        gastos = []
        for i in range(n_gastos):
            c1, c2, c3 = st.columns([2, 1, 1])
            with c1:
                desc = st.text_input(f"Descripción {i+1}", f"Gasto {i+1}", key=f"g_d_{i}")
            with c2:
                monto = st.number_input(f"Monto {i+1} ($)", value=250000, key=f"g_m_{i}")
            with c3:
                fecha = st.date_input(f"Vencimiento {i+1}", datetime.date.today() + datetime.timedelta(days=15), key=f"g_f_{i}")
            gastos.append({"desc": desc, "monto": monto, "fecha": str(fecha)})

st.markdown("<div class='card'><h3>📈 Inversiones Actuales</h3></div>", unsafe_allow_html=True)
tiene_pf = st.checkbox("Tengo Plazos Fijos activos")
pfs = []
if tiene_pf:
    n_pfs = st.number_input("Cantidad de PFs", min_value=1, value=1)
    for i in range(n_pfs):
        c1, c2, c3 = st.columns(3)
        with c1:
            monto = st.number_input(f"Monto PF {i+1}", value=1000000, key=f"pf_m_{i}")
        with c2:
            vto = st.date_input(f"Vencimiento {i+1}", datetime.date.today() + datetime.timedelta(days=10), key=f"pf_v_{i}")
        with c3:
            tipo = st.selectbox(f"Tipo {i+1}", ["Tradicional", "UVA"], key=f"pf_t_{i}")
        pfs.append({"monto": monto, "vto": str(vto), "tipo": tipo})

col_meta, col_pref = st.columns(2)
with col_meta:
    meta_nombre = st.text_input("Tu objetivo", "Cambiar el auto 🚗")
    meta_monto = st.number_input("Monto de la meta ($)", value=10000000)
with col_pref:
    mep = st.checkbox("Me interesa operar Dólar MEP")
    saldo_hoy = st.number_input("Saldo hoy en caja de ahorro ($)", value=1500000)

# ------------------------------------------------------------
# 6) BOTÓN: GENERAR ESTRATEGIA (JSON MODE)
# ------------------------------------------------------------
if "last_result" not in st.session_state:
    st.session_state.last_result = None

if st.button("GENERAR ESTRATEGIA PROFESIONAL BNA+"):

    user_data = {
        "saldo": saldo_hoy,
        "sueldos": sueldos,
        "depositos_extra": extra,
        "gastos": gastos,
        "pfs_actuales": pfs,
        "meta": {"nombre": meta_nombre, "monto": meta_monto},
        "interes_mep": mep
    }

    prompt = f"""
Sos Asesor Senior del BNA (Argentina). Generá una estrategia de inversión para este cliente (JSON):
{json.dumps(user_data, ensure_ascii=False)}

Devolvé EXCLUSIVAMENTE un JSON con estas llaves:
- analisis_macro (string)
- cartera_sugerida (lista de objetos: instrumento, monto, tipo_activo, tna_estimada)
- evolucion_cartera (lista de objetos: mes, monto_pesos, inflacion_acum_estimada) 6 meses
- calce_vencimientos (lista de objetos: fecha_vto, instrumento_vto, monto_vto, gasto_cubierto)
- justificacion (string)
"""

    with st.spinner("🤖 Generando estrategia (IA)..."):
        try:
            # JSON mode: response_mime_type="application/json" (evita backticks y parsing frágil) [3](https://stackoverflow.com/questions/78176807/403-permission-denied-error-when-accessing-google-ai-platform-model)
            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.2
                )
            )

            data = parse_json_strict(response.text)
            st.session_state.last_result = data

            st.success("✅ Estrategia calculada con éxito")
            st.balloons()

        except Exception as e:
            msg = str(e)
            if "429" in msg:
                st.error("⏳ Límite de cuota alcanzado. Probá más tarde o usá un modelo más liviano (flash-lite si aparece en tu lista).")
            else:
                st.error(f"❌ Error en la comunicación con la IA: {e}")
                # Debug: mostrar respuesta cruda si existe
                try:
                    st.code(response.text)
                except Exception:
                    pass

# ------------------------------------------------------------
# 7) RENDER (SIN VOLVER A LLAMAR A LA IA)
# ------------------------------------------------------------
data = st.session_state.last_result

if data:
    st.markdown(f"<div class='card'><b>Resumen de Mercado:</b><br>{data.get('analisis_macro','')}</div>", unsafe_allow_html=True)

    # Tabla + gráfico cartera
    df_cartera = pd.DataFrame(data.get("cartera_sugerida", []))
    if not df_cartera.empty:
        fig1 = px.pie(
            df_cartera, values="monto", names="tipo_activo",
            title="Distribución por Tipo de Activo",
            color_discrete_sequence=["#005691", "#0074c7", "#4da3ff", "#a3d1ff"]
        )
        st.plotly_chart(fig1, use_container_width=True)
        st.table(df_cartera)
    else:
        st.warning("La IA no devolvió 'cartera_sugerida' o vino vacía.")

    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader("📈 Proyección a 6 meses")
        df_evol = pd.DataFrame(data.get("evolucion_cartera", []))
        if not df_evol.empty and "mes" in df_evol and "monto_pesos" in df_evol:
            fig2 = go.Figure()
            fig2.add_trace(go.Scatter(
                x=df_evol["mes"], y=df_evol["monto_pesos"],
                name="Capital Proyectado", line=dict(color="#005691", width=3)
            ))
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.warning("La IA no devolvió 'evolucion_cartera' con campos esperados.")

    with col_right:
        st.subheader("📅 Cronograma de Liquidez")
        df_calce = pd.DataFrame(data.get("calce_vencimientos", []))
        if not df_calce.empty and "fecha_vto" in df_calce and "monto_vto" in df_calce:
            fig3 = px.bar(
                df_calce, x="fecha_vto", y="monto_vto", color="instrumento_vto",
                title="Vencimientos vs Gastos",
                color_discrete_sequence=["#4da3ff", "#0074c7", "#005691"]
            )
            st.plotly_chart(fig3, use_container_width=True)
            st.table(df_calce)
        else:
            st.warning("La IA no devolvió 'calce_vencimientos' con campos esperados.")

    st.info(f"💡 **Justificación:** {data.get('justificacion','')}")


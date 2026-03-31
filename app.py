import streamlit as st
import subprocess
import json
import pandas as pd
import plotly.express as px
import time
import shlex
import datetime # Import datetime for date_input
import requests # New import for API calls
import google.generativeai as genai # Import the Google Generative AI library
import os # Import os to access environment variables

# Configure the Generative AI model
genai.configure(api_key=os.environ.get("GEMINI_API_KEY")) # Use os.environ.get to avoid KeyError if not set
model = genai.GenerativeModel('gemini-pro-latest')

# --- API Endpoints ---
ARGENTINADATOS_BASE_URL = "https://api.argentinadatos.com"
DATA912_BASE_URL = "https://data912.com"

def fetch_real_time_data():
    """Fetches real-time financial data from various APIs."""
    data = {}
    today_str = datetime.date.today().strftime("%Y-%m-%d")

    # ArgentinaDatos API
    try:
        # Plazo Fijo
        pf_response = requests.get(f"{ARGENTINADATOS_BASE_URL}/v1/finanzas/tasas/plazo-fijo", timeout=5)
        pf_response.raise_for_status()
        data['plazo_fijo_rates'] = pf_response.json()
    except requests.exceptions.RequestException as e:
        st.warning(f"⚠️ No se pudieron obtener datos de Plazo Fijo de ArgentinaDatos: {e}")

    try:
        # Inflacion
        inflacion_response = requests.get(f"{ARGENTINADATOS_BASE_URL}/v1/finanzas/indices/inflacion", timeout=5)
        inflacion_response.raise_for_status()
        all_inflacion_data = inflacion_response.json()
        
        # Filter inflation data for the last 12 months
        if all_inflacion_data:
            df_inflacion = pd.DataFrame(all_inflacion_data)
            df_inflacion['fecha'] = pd.to_datetime(df_inflacion['fecha'])
            one_year_ago = datetime.date.today() - datetime.timedelta(days=365)
            df_inflacion = df_inflacion[df_inflacion['fecha'] >= pd.Timestamp(one_year_ago)]
            df_inflacion['fecha'] = df_inflacion['fecha'].dt.strftime('%Y-%m-%d') # Convert Timestamp objects to string
            data['inflacion_mensual'] = df_inflacion.to_dict(orient='records')
        else:
            data['inflacion_mensual'] = []
    except requests.exceptions.RequestException as e:
        st.warning(f"⚠️ No se pudieron obtener datos de Inflación de ArgentinaDatos: {e}")

    try:
        # UVA
        uva_response = requests.get(f"{ARGENTINADATOS_BASE_URL}/v1/finanzas/indices/uva", timeout=5)
        uva_response.raise_for_status()
        data['uva_indices'] = uva_response.json()
    except requests.exceptions.RequestException as e:
        st.warning(f"⚠️ No se pudieron obtener datos UVA de ArgentinaDatos: {e}")

    try:
        # FCI Money Market (using current date)
        fci_mm_response = requests.get(f"{ARGENTINADATOS_BASE_URL}/v1/finanzas/fci/mercado-dinero/fecha/{today_str}", timeout=5)
        fci_mm_response.raise_for_status()
        data['fci_money_market'] = fci_mm_response.json()
    except requests.exceptions.RequestException as e:
        st.warning(f"⚠️ No se pudieron obtener datos de FCI Money Market de ArgentinaDatos: {e}")
        
    try:
        # Letras (LECAP/BONCAP)
        letras_response = requests.get(f"{ARGENTINADATOS_BASE_URL}/v1/finanzas/letras", timeout=5)
        letras_response.raise_for_status()
        data['letras'] = letras_response.json()
    except requests.exceptions.RequestException as e:
        st.warning(f"⚠️ No se pudieron obtener datos de Letras de ArgentinaDatos: {e}")

    try:
        # Dólar MEP (ArgentinaDatos)
        dolar_response = requests.get(f"{ARGENTINADATOS_BASE_URL}/v1/cotizaciones/dolares/mep/{today_str}", timeout=5)
        dolar_response.raise_for_status()
        data['dolar_mep_argentinadatos'] = dolar_response.json()
    except requests.exceptions.RequestException as e:
        st.warning(f"⚠️ No se pudieron obtener datos de Dólar MEP de ArgentinaDatos: {e}")


    # Data912 API
    try:
        # Dólar MEP (live from data912)
        mep_data912_response = requests.get(f"{DATA912_BASE_URL}/live/mep", timeout=5)
        mep_data912_response.raise_for_status()
        data['dolar_mep_data912'] = mep_data912_response.json()
    except requests.exceptions.RequestException as e:
        st.warning(f"⚠️ No se pudieron obtener datos de Dólar MEP de Data912: {e}")

    try:
        # Government Notes (LECAPs/BONCAPs)
        gov_notes_response = requests.get(f"{DATA912_BASE_URL}/live/arg_notes", timeout=5)
        gov_notes_response.raise_for_status()
        data['government_notes'] = gov_notes_response.json()
    except requests.exceptions.RequestException as e:
        st.warning(f"⚠️ No se pudieron obtener datos de Notas de Gobierno de Data912: {e}")

    try:
        # Government Bonds
        gov_bonds_response = requests.get(f"{DATA912_BASE_URL}/live/arg_bonds", timeout=5)
        gov_bonds_response.raise_for_status()
        data['government_bonds'] = gov_bonds_response.json()
    except requests.exceptions.RequestException as e:
        st.warning(f"⚠️ No se pudieron obtener datos de Bonos de Gobierno de Data912: {e}")

    return data


# --- 1. CONFIGURACIÓN DE PÁGINA, ESTILO Y PROMPT ---
st.set_page_config(page_title="+ Copilot | Inversiones", page_icon="🏦", layout="wide")

PROMPT_MAESTRO_V2_CONTENT = """
# ROLE: BNA+ INVESTMENT ENGINE (AGENTIC MODE)
Eres el núcleo de inteligencia artificial del Banco Nación (Argentina), especializado en Estrategia Financiera y Mercado de Capitales. Tu objetivo es transformar datos de un cliente en una hoja de ruta de inversión profesional, didáctica y fundamentada.

# FUENTES DE VERDAD Y NAVEGACIÓN (CRÍTICO):
1. DEBES usar tu conocimiento actualizado sobre el valor del Dólar MEP (AL30/GD30) y CCL.
2. DEBES usar tu conocimiento de las tasas actuales de Plazo Fijo BNA y Tasas de Política Monetaria del BCRA.
3. DEBES verificar si hay nuevas normativas de la CNV sobre "Parking" o restricciones cambiarias.
4. Usa tu conocimiento de portales como El Cronista o Ámbito Financiero para determinar el "Sentimiento de Mercado" (Bullish/Bearish/Cautela).

# LÓGICA DE PROCESAMIENTO:
- PRIORIDAD 1: Liquidez inmediata para gastos próximos (Alquiler, Tarjeta) en instrumentos de muy bajo riesgo y disponibilidad inmediata (T+0), como Cuentas Remuneradas o FCIs Money Market.
- PRIORIDAD 2: Ahorro por Objetivos. Calcula cuánto falta para la meta y sugiere los instrumentos que mejor se alineen a ese objetivo (ej: CER/UVA para metas en pesos, MEP para metas en USD).
- PRIORIDAD 3: Maximización de excedentes. Compara el rendimiento estimado de los instrumentos sugeridos contra la inflación proyectada.

# FORMATO DE SALIDA (ESTRICTO JSON):
Tu respuesta debe ser UNICAMENTE un objeto JSON válido, sin texto antes ni después. La estructura es CRÍTICA y debe seguir este formato exacto:
{
  "analisis_macro": "Un texto claro y educativo sobre el contexto económico actual de Argentina (tasas, inflación, dólar), explicando cómo afecta a las decisiones de inversión. Usa un lenguaje sencillo pero profesional.",
  "horizonte_meta": "Basado en la meta del cliente y su capacidad de ahorro, calcula un horizonte de tiempo estimado para alcanzar el objetivo. Explica el cálculo de forma sencilla.",
  "cartera_sugerida": [
    {
      "instrumento": "Plazo Fijo Tradicional",
      "monto": 100000,
      "porcentaje_cartera": 10,
      "tipo_activo": "Renta Fija conservadora",
      "plazo_sugerido_dias": 30,
      "tasa_especifica": "28% TNA",
      "fundamento": "Explicación técnica y didáctica de por qué este instrumento es adecuado. Detalla riesgos y beneficios. Menciona por qué se eligió ese plazo."
    },
    {
      "instrumento": "Letra del Tesoro S30A6",
      "monto": 200000,
      "porcentaje_cartera": 20,
      "tipo_activo": "Renta Fija soberana",
      "fundamento": "Análisis de por qué se selecciona esta letra en particular (plazo, rendimiento, liquidez).",
      "comparison_table": [
        {"letra": "S30A6", "vencimiento": "30/08/2026", "TIR_estimada": "45%", "volatilidad": "Baja"},
        {"letra": "X15Y7", "vencimiento": "15/09/2027", "TIR_estimada": "48%", "volatilidad": "Media"},
        {"letra": "Z20Z8", "vencimiento": "20/10/2028", "TIR_estimada": "50%", "volatilidad": "Media-Alta"}
      ]
    }
  ],
  "estrategia_liquidez": "Un plan paso a paso y detallado para manejar la liquidez de corto plazo. Por ejemplo: 'Para cubrir el vencimiento de la tarjeta de $350.000 el día 20, invertir $345.000 en un Fondo Común de Inversión Money Market y rescatar el dinero 24hs antes'.",
  "justificacion_general": "Un resumen final que conecte todas las partes de la estrategia, explicando cómo el plan de liquidez, la cartera de inversión y el horizonte de la meta trabajan juntos para cumplir los objetivos del cliente de manera segura y eficiente."
}

# RESTRICCIONES:
- No sugerir Criptomonedas ni Acciones de alta volatilidad.
- Si el usuario menciona Dólar MEP, explicar siempre el concepto de "Parking" y la normativa vigente.
- El campo 'porcentaje_cartera' en cada instrumento de la 'cartera_sugerida' es obligatorio. La suma de todos los porcentajes debe ser 100.
- El campo 'comparison_table' es OBLIGATORIO para Letras y Bonos. Debe contener al menos 3 filas para comparar con otros instrumentos similares.
- Tono: Institucional, claro y confiable, como un asesor senior del Banco Nación.
"""

st.markdown("""
    <style>
    .stApp { background-color: #f4f7f9; }
    .main-header { background-color: #005691; padding: 20px; border-radius: 10px; color: white; text-align: center; margin-bottom: 20px; }
    .stButton>button { background-color: #005691; color: white; border-radius: 10px; font-weight: bold; width: 100%; height: 3em; border: none; }
    .stButton>button:hover { background-color: #004575; color: white; }
    .card { background-color: white; padding: 20px; border-radius: 15px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); border-left: 5px solid #005691; margin-bottom: 20px; }
    .stExpander { background-color: white; border-radius: 10px; border: 1px solid #e0e0e0; }
    </style>
    """, unsafe_allow_html=True)

st.markdown("<div class='main-header'><h1>🏦 + Inversiones | Copilot Profesional</h1></div>", unsafe_allow_html=True)
st.write("Gestioná tus ahorros con la inteligencia y la seguridad del Banco Nación.")


# --- 2. FORMULARIO DE ENTRADA ---
st.subheader("📋 Perfil Financiero Detallado")
col_g1, col_g2 = st.columns(2)

with col_g1:
    st.markdown("<div class='card'><h3>💰 Ingresos y Disponibilidad</h3></div>", unsafe_allow_html=True)
    with st.expander("Sueldos y Cobros del Mes", expanded=True):
        n_sueldos = st.number_input("¿Cuántos ingresos recibís al mes?", min_value=1, value=1, key="n_sueldos")
        sueldos = []
        for i in range(n_sueldos):
            c1, c2 = st.columns(2)
            with c1: monto = st.number_input(f"Monto Sueldo {i+1} ($)", value=900000, key=f"s_m_{i}")
            with c2: fecha = st.date_input(f"Fecha de cobro {i+1}", datetime.date.today(), key=f"s_f_{i}")
            sueldos.append({"monto": monto, "fecha": str(fecha)})
    extra = st.number_input("Ahorros/Depósitos adicionales ($)", value=500000, key="extra_depositos")

with col_g2:
    st.markdown("<div class='card'><h3>🏠 Gastos y Vencimientos</h3></div>", unsafe_allow_html=True)
    with st.expander("Detalle de Egresos (Tarjeta, Alquiler, Servicios)", expanded=True):
        n_gastos = st.number_input("¿Cuántos vencimientos tenés?", min_value=1, value=2, key="n_gastos")
        gastos = []
        for i in range(n_gastos):
            c1, c2, c3 = st.columns([2, 1, 1])
            with c1: desc = st.text_input(f"Descripción {i+1}", f"Gasto {i+1}", key=f"g_d_{i}")
            with c2: monto = st.number_input(f"Monto {i+1} ($)", value=250000, key=f"g_m_{i}")
            with c3: fecha = st.date_input(f"Vencimiento {i+1}", datetime.date.today() + datetime.timedelta(days=15), key=f"g_f_{i}")
            gastos.append({"desc": desc, "monto": monto, "fecha": str(fecha)})

st.markdown("<div class='card'><h3>📈 Inversiones Actuales</h3></div>", unsafe_allow_html=True)
tiene_pf = st.checkbox("Tengo Plazos Fijos activos", key="tiene_pf")
pfs = []
if tiene_pf:
    n_pfs = st.number_input("Cantidad de PFs", min_value=1, value=1, key="n_pfs")
    for i in range(n_pfs):
        c1, c2, c3 = st.columns(3)
        with c1: monto = st.number_input(f"Monto PF {i+1}", value=1000000, key=f"pf_m_{i}")
        with c2: vto = st.date_input(f"Vencimiento {i+1}", datetime.date.today() + datetime.timedelta(days=10), key=f"pf_v_{i}")
        with c3: tipo = st.selectbox(f"Tipo {i+1}", ["Tradicional", "UVA"], key=f"pf_t_{i}")
        pfs.append({"monto": monto, "vto": str(vto), "tipo": tipo})

col_meta, col_pref = st.columns(2)
with col_meta:
    meta_nombre = st.text_input("Tu objetivo", "Cambiar el auto 🚗", key="meta_nombre")
    meta_monto = st.number_input("Monto de la meta ($)", value=10000000, key="meta_monto")
with col_pref:
    mep = st.checkbox("Me interesa operar Dólar MEP", key="mep_interes")
    saldo_hoy = st.number_input("Saldo hoy en caja de ahorro ($)", value=1500000, key="saldo_hoy")


# --- 3. MOTOR DE ESTRATEGIA ---
if st.button("GENERAR ESTRATEGIA PROFESIONAL"):
    with st.spinner("Realizando análisis profundo del mercado y tu perfil..."):
        
        # --- Fetch real-time data ---
        real_time_data = fetch_real_time_data()

        contexto_usuario = {
            "saldo_caja_ahorro": saldo_hoy,
            "ingresos_mensuales": sueldos,
            "depositos_adicionales": extra,
            "gastos_vencimientos": gastos,
            "plazos_fijos_activos": pfs,
            "meta_objetivo_nombre": meta_nombre,
            "meta_objetivo_monto": meta_monto,
            "interes_dolar_mep": mep,
            "datos_mercado_tiempo_real": real_time_data # Inject real-time data
        }
        
        prompt_completo = (
            f"{PROMPT_MAESTRO_V2_CONTENT}\n"
            f"Datos del cliente: {json.dumps(contexto_usuario)}"
        )
        
        # --- LLAMADA A GEMINI CON EL PROMPT INTEGRADO ---
        try:
            response = model.generate_content(prompt_completo)
            resultado_raw = response.text
            
            start = resultado_raw.find('{')
            end = resultado_raw.rfind('}') + 1
            if start == -1 or end == 0:
                st.error("Error de formato: La IA no devolvió un JSON válido.")
                st.code(resultado_raw)
                st.stop()

            clean_json = resultado_raw[start:end]
            data = json.loads(clean_json)
            
            st.success("✅ Estrategia Profesional Generada")
            st.balloons()

            # --- 4. RENDERIZADO DE RESULTADOS MEJORADO ---
            st.markdown(f"<div class='card'><b>Resumen de Mercado (Equipo de Research BNA):</b><br>{data.get('analisis_macro', 'No disponible.')}</div>", unsafe_allow_html=True)
            
            col_horiz, col_liq = st.columns(2)
            with col_horiz:
                st.markdown(f"<div class='card'><h3> Horizonte para tu Meta: {meta_nombre}</h3><p>{data.get('horizonte_meta', 'Calculando...')}</p></div>", unsafe_allow_html=True)
            with col_liq:
                st.markdown(f"<div class='card'><h3> Plan de Liquidez (Corto Plazo)</h3><p>{data.get('estrategia_liquidez', 'No disponible.')}</div>", unsafe_allow_html=True)

            st.subheader("📊 Cartera de Inversión Sugerida")
            
            df_cartera = pd.DataFrame(data['cartera_sugerida'])
            
            # Gráfico de Torta
            fig = px.pie(df_cartera, values='porcentaje_cartera', names='instrumento', title='Distribución Propuesta por Instrumento',
                         color_discrete_sequence=px.colors.sequential.Agsunset)
            fig.update_layout(legend_title_text='Instrumentos')
            st.plotly_chart(fig, use_container_width=True)

            st.subheader("📋 Fundamentos y Detalles de cada Instrumento")
            for index, row in df_cartera.iterrows():
                # Formateo del título del expander
                titulo = f"**{row['instrumento']}** ({row['porcentaje_cartera']}%) - Monto: ${int(row['monto']):,}"
                
                with st.expander(titulo):
                    st.markdown(f"**Tipo de Activo:** {row.get('tipo_activo', 'N/A')}")
                    
                    if 'tasa_especifica' in row:
                        st.markdown(f"**Tasa Específica:** {row['tasa_especifica']}")
                    if 'plazo_sugerido_dias' in row:
                        st.markdown(f"**Plazo Sugerido:** {row['plazo_sugerido_dias']} días")
                    
                    st.markdown(f"---")
                    st.markdown(f"**Fundamento Técnico de la Recomendación:**")
                    st.info(row.get('fundamento', 'Sin fundamento específico.'))

                    # Renderizar la tabla de comparación si existe
                    if 'comparison_table' in row and row['comparison_table']:
                        st.markdown(f"**Tabla Comparativa de Instrumentos Similares:**")
                        df_comp = pd.DataFrame(row['comparison_table'])
                        st.dataframe(df_comp, use_container_width=True)

            st.markdown("---")
            st.markdown(f"<div class='card'><h3>💡 Justificación General de la Estrategia</h3><p>{data.get('justificacion_general', 'No disponible.')}</div>", unsafe_allow_html=True)

        except subprocess.CalledProcessError as e:
            st.error("Ocurrió un error al ejecutar el comando de la IA.")
            st.code(e.output)
        except json.JSONDecodeError:
            st.error("Error de formato: La IA no devolvió un JSON válido. Esto puede ocurrir por un fallo temporal.")
            st.code(resultado_raw)
        except Exception as e:
            st.error(f"Ocurrió un error inesperado.")
            st.exception(e)

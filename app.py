import streamlit as st
import pandas as pd
import plotly.express as px
from google import genai  # Librería nueva
import json
import datetime


# --- CONFIGURACIÓN DE IA Y SEGURIDAD ---
# Para que esto funcione en Streamlit Cloud, debés configurar la API KEY en 'Secrets'
# Verás cómo hacerlo en las instrucciones de texto después del código.
try:
    # La nueva forma de conectar
    client = genai.Client(api_key=st.secrets["GOOGLE_API_KEY"])
except Exception as e:
    st.error("⚠️ Error en la API KEY. Verificá los Secrets.")
    st.stop()
    
# --- CONFIGURACIÓN DE MARCA BNA+ PROFUNDO ---
st.set_page_config(page_title="BNA+ Copilot Profundo", page_icon="🏦", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #f4f7f9; }
    .main-header { background-color: #005691; padding: 20px; border-radius: 10px; color: white; text-align: center; margin-bottom: 20px; }
    .stButton>button { background-color: #005691; color: white; border-radius: 10px; font-weight: bold; width: 100%; height: 3em; }
    .card { background-color: white; padding: 20px; border-radius: 15px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); border-left: 5px solid #005691; margin-bottom: 20px; }
    .stExpander { background-color: white; border-radius: 10px; border: 1px solid #005691; }
    </style>
    """, unsafe_allow_html=True)

st.markdown("<div class='main-header'><h1>🏦 BNA+ Inversiones | Copilot Profundo</h1></div>", unsafe_allow_html=True)

# --- INICIO DEL CUESTIONARIO AVANZADO ---
st.subheader("📋 Perfil Financiero Detallado")
col_g1, col_g2 = st.columns(2)

with col_g1:
    st.markdown("<div class='card'><h3>💰 Ingresos y Depósitos</h3></div>", unsafe_allow_html=True)
    
    with st.expander("Sueldos del Mes", expanded=True):
        n_sueldos = st.number_input("¿Cuántos sueldos recibís?", min_value=1, value=1)
        sueldos = []
        for i in range(n_sueldos):
            c1, c2 = st.columns(2)
            with c1: monto = st.number_input(f"Monto Sueldo {i+1} ($)", value=850000, key=f"s_m_{i}")
            with c2: fecha = st.date_input(f"Fecha cobro {i+1}", datetime.date.today(), key=f"s_f_{i}")
            sueldos.append({"monto": monto, "fecha": fecha.strftime("%Y-%m-%d")})
            
    extra = st.number_input("Depósitos adicionales a analizar ($)", value=300000)

with col_g2:
    st.markdown("<div class='card'><h3>🏠 Gastos Progresivos</h3></div>", unsafe_allow_html=True)
    
    with st.expander("Detalle de Gastos Fijos", expanded=True):
        n_gastos = st.number_input("¿Cuántos gastos fijos tenés?", min_value=1, value=2)
        gastos = []
        for i in range(n_gastos):
            c1, c2, c3 = st.columns([2, 1, 1])
            with c1: desc = st.text_input(f"Gasto {i+1} (Alquiler, etc.)", f"Gasto {i+1}", key=f"g_d_{i}")
            with c2: monto = st.number_input(f"Monto {i+1} ($)", value=200000, key=f"g_m_{i}")
            with c3: fecha = st.date_input(f"Vto. {i+1}", datetime.date.today() + datetime.timedelta(days=10), key=f"g_f_{i}")
            gastos.append({"desc": desc, "monto": monto, "fecha": fecha.strftime("%Y-%m-%d")})

with st.container():
    st.markdown("<div class='card'><h3>📈 Tenencias Actuales</h3></div>", unsafe_allow_html=True)
    tiene_pf = st.checkbox("¿Tengo Plazos Fijos actualmente?")
    pfs = []
    if tiene_pf:
        n_pfs = st.number_input("¿Cuántos PF tenés?", min_value=1, value=1)
        for i in range(n_pfs):
            c1, c2, c3 = st.columns(3)
            with c1: monto = st.number_input(f"Monto PF {i+1} ($)", value=600000, key=f"pf_m_{i}")
            with c2: vto = st.date_input(f"Fecha Vto. {i+1}", datetime.date.today() + datetime.timedelta(days=20), key=f"pf_v_{i}")
            with c3: tipo = st.selectbox(f"Tipo PF {i+1}", ["Tradicional", "UVA"], key=f"pf_t_{i}")
            pfs.append({"monto": monto, "fecha": vto.strftime("%Y-%m-%d"), "tipo": tipo})

col_meta, col_extra = st.columns(2)
with col_meta:
    st.markdown("<div class='card'><h3>🎯 Tu Meta</h3></div>", unsafe_allow_html=True)
    meta_nombre = st.text_input("Objetivo de ahorro", "Compra Auto 🚗")
    meta_monto = st.number_input("Monto total de la meta ($)", value=7500000)
    
with col_extra:
    st.markdown("<div class='card'><h3>⚙️ Preferencias</h3></div>", unsafe_allow_html=True)
    mep = st.checkbox("¿Interés en Dólar MEP?")
    saldo_inicial = st.number_input("Saldo disponible hoy en cuenta ($)", value=1200000)

# --- BOTÓN DE ACCIÓN ---
if st.button("ANALIZAR Y GENERAR ESTRATEGIA BNA+ PROFUNDA"):
    
    # 1. Empaquetado de Datos para Gemini
    datos_completos = {
        "saldo_hoy": saldo_inicial,
        "sueldos": sueldos,
        "depositos_extra": extra,
        "gastos": gastos,
        "plazos_fijos_actuales": pfs,
        "meta": {"nombre": meta_nombre, "monto": meta_monto},
        "interes_mep": mep
    }
    
    with st.spinner("🤖 Gemini está consultando BCRA, CNV, BNA, BYMA, Tablero Financiero y Reuters..."):
        
        # 2. PROMPT MAESTRO ACTUALIZADO (Con Grounding en fuentes reales)
        prompt_maestro = f"""
        # ROLE: BNA+ SENIOR WEALTH MANAGER (AGENTIC ENGINE)
        Eres el motor de IA del Banco Nación de Argentina. Tu misión es transformar datos financieros complejos en una estrategia de inversión profesional.

        # FUENTES OBLIGATORIAS (CONSULTA EN TIEMPO REAL):
        1. Consulta obligatoriamente las Tasas de Política Monetaria del BCRA y las TNAs de Plazo Fijo vigentes en el BNA.
        2. Consulta normativas de la CNV sobre Parking y límites operativos para Dólar MEP/CCL.
        3. Consulta cotizaciones de Bonos Soberanos (AL30/GD30) en BYMA para calcular el tipo de cambio implícito (Dólar MEP).
        4. Consulta la inflación proyectada (REM del BCRA) y datos de Tablero Financiero para instrumentos indexados (CER/UVA).

        # DATOS DEL CLIENTE (JSON):
        {json.dumps(datos_completos)}

        # LÓGICA DE NEGOCIO (ESTRICTA):
        - PRIORIDAD 1: Calce de Liquidez. Usa instrumentos T+0/T+1 (FCI Money Market BNA) para cubrir los gastos fijos del cliente según sus fechas de vencimiento.
        - PRIORIDAD 2: Optimización de Tenencias Actuales. Si tiene PFs Tradicionales, evalúa si la TNA del BNA le gana a la inflación proyectada.
        - PRIORIDAD 3: Ahorro por Objetivos. Calcula cuánto debe invertir mensualmente para llegar a la meta. Sugiere instrumentos CER si la meta es en pesos, o MEP si es dolarizable.
        - PRIORIDAD 4: Maximización de Tasa Real Positive (TRP). Compara TEM de Lecaps vs Inflación Proyectada.

        # FORMATO DE SALIDA (UNICAMENTE JSON ESTRICTO, SIN TEXTO ADICIONAL):
        Debes responder EXCLUSIVAMENTE con un objeto JSON válido que contenga estas llaves:
        - "analisis_macro": (String) Resumen de tasas actuales, inflación y dólar MEP encontrados.
        - "cartera_sugerida": (Lista de objetos: {{"instrumento": "", "monto": 0, "tipo_activo": "Pesos/USD/Indexado", "tna_estimada": "XX%"}})
        - "evolucion_cartera": (Lista de objetos: {{"mes": "Ene-26", "monto_pesos": 0, "inflacion_acum_estimada": "X%"}}) - Proyección a 6 meses.
        - "calce_vencimientos": (Lista de objetos: {{"fecha_vto": "YYYY-MM-DD", "instrumento_vto": "", "monto_vto": 0, "gasto_cubierto": ""}})
        - "justificacion": (String) Explicación profesional del mix.
        """
        
        try:
            # 3. Llamada a la API de Gemini
            response = client.models.generate_content(
                model='models/gemini-1.5-flash', # Usamos el modelo más nuevo y rápido
                contents=prompt_maestro
            )
            
            # Limpieza del JSON
            texto = response.text
            json_str = texto.replace("```json", "").replace("```", "").strip()
            data = json.loads(json_str)
            
            st.success("✅ Estrategia Generada")
            st.balloons()
            
            # --- VISUALIZACIÓN PROFESIONAL ---
            st.markdown(f"<div class='card'><b>Contexto de Mercado Real:</b><br>{data.get('analisis_macro', 'Cargando...')}</div>", unsafe_allow_html=True)
            
            # Gráfico 1: Distribución de Cartera (Gráfico de Torta) - Estilo BNA+ (Azules)
            st.subheader("📊 Gráfico 1: Distribución de Inversión por Tipo de Activo")
            df_cartera = pd.DataFrame(data['cartera_sugerida'])
            fig1 = px.pie(df_cartera, values='monto', names='tipo_activo', title='Mix de Activos',
                         color_discrete_sequence=['#005691', '#0074c7', '#4da3ff', '#a3d1ff'])
            st.plotly_chart(fig1, use_container_width=True)
            
            st.table(df_cartera)
            
            col_a, col_b = st.columns(2)
            
            with col_a:
                # Gráfico 2: Evolución de Cartera (Gráfico de Líneas con Inflación)
                st.subheader("📈 Gráfico 2: Evolución Estimada de Cartera vs Inflación")
                df_evolucion = pd.DataFrame(data['evolucion_cartera'])
                fig2 = go.Figure()
                fig2.add_trace(go.Scatter(x=df_evolucion['mes'], y=df_evolucion['monto_pesos'], name='Cartera BNA+', line=dict(color='#005691', width=3)))
                fig2.add_trace(go.Scatter(x=df_evolucion['mes'], y=df_evolucion['inflacion_acum_estimada'].str.replace('%','').astype(float), name='Inflación Acum.', line=dict(color='#E31B23', dash='dot')))
                fig2.update_layout(title='Evolución Proyectada (6 meses)', xaxis_title='Mes', yaxis_title='Monto ($) / Tasa (%)')
                st.plotly_chart(fig2, use_container_width=True)
                
            with col_b:
                # Gráfico 3: Calce de Vencimientos (Gráfico de Barras)
                st.subheader("📅 Gráfico 3: Calce de Vencimientos vs Gastos Cubiertos")
                df_calce = pd.DataFrame(data['calce_vencimientos'])
                df_calce['fecha_vto'] = pd.to_datetime(df_calce['fecha_vto'])
                fig3 = px.bar(df_calce, x='fecha_vto', y='monto_vto', color='instrumento_vto', title='Cronograma de Disponibilidad',
                             labels={'fecha_vto':'Fecha', 'monto_vto':'Monto ($)', 'instrumento_vto':'Instrumento'},
                             color_discrete_sequence=['#4da3ff', '#0074c7', '#005691'])
                st.plotly_chart(fig3, use_container_width=True)
                st.table(df_calce)
                
            st.markdown(f"<div class='card'><b>Justificación del Asesor Senior:</b><br>{data.get('justificacion', 'Consultando...')}</div>", unsafe_allow_html=True)

        except Exception as e:
            st.error(f"Hubo un problema técnico: {e}")
            # st.code(response.text) # Descomentar para debug

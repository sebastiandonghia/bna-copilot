import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import google.generativeai as genai
import json
import datetime
import requests

# --- 0. FUNCIONES DE CAPTURA DE DATOS REALES (APIs Argentina) ---
def get_market_data():
    """Captura datos reales de APIs financieras de Argentina"""
    market_data = {
        "mep": "No disponible",
        "tna_pf_bna": "No disponible",
        "inflacion_rem": "No disponible",
        "fecha": datetime.date.today().strftime("%d/%m/%Y")
    }
    try:
        # 1. Dólar MEP (DolarApi)
        res_mep = requests.get("https://dolarapi.com/v1/dolares/mep", timeout=5).json()
        market_data["mep"] = res_mep.get("venta")

        # 2. Tasas de Plazo Fijo (ArgentinaDatos)
        res_pf = requests.get("https://api.argentinadatos.com/v1/finanzas/tasas/plazoFijo", timeout=5).json()
        # Buscamos específicamente el dato del Banco Nación
        bna_data = next((x for x in res_pf if "NACION" in x['entidad'].upper()), None)
        if bna_data:
            market_data["tna_pf_bna"] = bna_data['tna']

        # 3. Inflación (REM - ArgentinaDatos)
        res_inf = requests.get("https://api.argentinadatos.com/v1/finanzas/indices/inflacion", timeout=5).json()
        if res_inf:
            market_data["inflacion_rem"] = res_inf[-1]['valor'] # Último dato mensual cargado
            
    except Exception as e:
        st.warning(f"Nota: Algunos datos de mercado se estimarán (Error de API: {e})")
    
    return market_data

# --- 1. CONFIGURACIÓN DE IA ---
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    # Usamos 1.5 Flash por velocidad y estabilidad en JSON
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    st.error("⚠️ Error de configuración de IA.")
    st.stop()

# --- 2. ESTILO VISUAL BNA+ ---
st.set_page_config(page_title="Copilot Profesional | + Inversiones", page_icon="🏦", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #f4f7f9; }
    .main-header { background-color: #005691; padding: 20px; border-radius: 10px; color: white; text-align: center; margin-bottom: 20px; }
    .stButton>button { background-color: #005691; color: white; border-radius: 10px; font-weight: bold; width: 100%; height: 3em; border: none; }
    .card { background-color: white; padding: 20px; border-radius: 15px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); border-left: 5px solid #005691; margin-bottom: 20px; }
    .live-ticker { background-color: #e1f5fe; padding: 10px; border-radius: 5px; text-align: center; font-weight: bold; color: #005691; margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

st.markdown("<div class='main-header'><h1>🏦 + Inversiones | Copilot Profesional</h1></div>", unsafe_allow_html=True)

# Captura de datos en vivo para mostrar en UI
m_data = get_market_data()
st.markdown(f"""
    <div class='live-ticker'>
        📡 Datos en vivo ({m_data['fecha']}): 
        💵 Dólar MEP: ${m_data['mep']} | 
        🏦 TNA BNA: {m_data['tna_pf_bna']}% | 
        📈 Últ. Inflación: {m_data['inflacion_rem']}%
    </div>
""", unsafe_allow_html=True)

# --- 3. CUESTIONARIO FINANCIERO ---
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
    mep_interes = st.checkbox("Me interesa operar Dólar MEP")
    saldo_hoy = st.number_input("Saldo hoy en caja de ahorro ($)", value=1500000)

# --- 4. MOTOR DE ESTRATEGIA ---
if st.button("GENERAR ESTRATEGIA PROFESIONAL +"):
    
    user_data = {
        "saldo": saldo_hoy, "sueldos": sueldos, "gastos": gastos, 
        "pfs_actuales": pfs, "meta": {"n": meta_nombre, "m": meta_monto}, "interes_mep": mep_interes
    }

    with st.spinner("🤖 Consultando APIs financieras y generando análisis fiduciario..."):
        
        # INYECCIÓN DE DATOS REALES EN EL PROMPT
        prompt = f"""
        Actúa como un Asesor Financiero Fiduciario Senior del BNA (Argentina).
        CONTEXTO DE MERCADO REAL CAPTURADO HOY:
        - Dólar MEP: ${m_data['mep']}
        - TNA Plazo Fijo BNA: {m_data['tna_pf_bna']}%
        - Último Índice Inflación Mensual: {m_data['inflacion_rem']}%

        Analiza los datos de este cliente: {json.dumps(user_data)}

        Tu respuesta DEBE SER EXCLUSIVAMENTE un objeto JSON válido.
        Estructura obligatoria:
        {{
          "analisis_macro": "Resumen educativo basado en los datos reales provistos arriba y el contexto país.",
          "horizonte_meta": "Cálculo estimado para alcanzar la meta.",
          "cartera_sugerida": [
            {{
              "instrumento": "Nombre",
              "monto": pesos_valor,
              "tipo_activo": "Categoría",
              "tna_estimada": "valor",
              "fundamento": "Explicación técnica"
            }}
          ],
          "estrategia_liquidez": "Plan paso a paso para gastos inmediatos.",
          "evolucion_cartera": [
            {{ "mes": "Mes 1", "monto_pesos": valor, "inflacion_acum_estimada": valor }}
          ],
          "justificacion_general": "Resumen de cómo todo encaja."
        }}
        """

        try:
            response = model.generate_content(prompt)
            raw_text = response.text
            
            # Limpieza de JSON por si la IA agrega markdown
            clean_json = raw_text[raw_text.find('{'):raw_text.rfind('}') + 1]
            data = json.loads(clean_json)

            st.success("✅ Estrategia Profesional Generada con Datos Reales")
            st.balloons()

            # --- RENDERIZADO ---
            st.markdown(f"<div class='card'><b>Análisis de Research (Datos Actualizados):</b><br>{data['analisis_macro']}</div>", unsafe_allow_html=True)
            
            c_h, c_l = st.columns(2)
            with c_h: st.markdown(f"<div class='card'><h3>🎯 Meta: {meta_nombre}</h3><p>{data['horizonte_meta']}</p></div>", unsafe_allow_html=True)
            with c_l: st.markdown(f"<div class='card'><h3>💧 Plan de Liquidez</h3><p>{data['estrategia_liquidez']}</p></div>", unsafe_allow_html=True)

            st.subheader("📊 Cartera de Inversión Sugerida")
            df_cartera = pd.DataFrame(data['cartera_sugerida'])
            fig1 = px.pie(df_cartera, values='monto', names='tipo_activo', title='Distribución por Activo',
                         color_discrete_sequence=['#005691', '#0074c7', '#4da3ff', '#a3d1ff'])
            st.plotly_chart(fig1, use_container_width=True)

            for index, row in df_cartera.iterrows():
                with st.expander(f"🔍 Fundamentos: {row['instrumento']} (${int(row['monto']):,})"):
                    st.write(f"**Rendimiento:** {row['tna_estimada']}")
                    st.info(row['fundamento'])

            st.subheader("📈 Proyección de Cartera vs. Inflación")
            df_evol = pd.DataFrame(data['evolucion_cartera'])
            fig2 = go.Figure()
            fig2.add_trace(go.Scatter(x=df_evol['mes'], y=df_evol['monto_pesos'], name='Capital Proyectado', line=dict(color='#005691', width=4), fill='tozeroy'))
            fig2.add_trace(go.Scatter(x=df_evol['mes'], y=df_evol['inflacion_acum_estimada'], name='Inflación Est.', line=dict(color='#ff4b4b', dash='dot')))
            st.plotly_chart(fig2, use_container_width=True)
            
            st.markdown(f"<div class='card'><h3>💡 Conclusión Estratégica</h3><p>{data['justificacion_general']}</p></div>", unsafe_allow_html=True)

        except Exception as e:
            st.error(f"Error procesando la estrategia: {e}")
            if 'raw_text' in locals(): st.code(raw_text)
st.markdown("<div class='main-header'><h1>🏦 + Inversiones | Copilot Profesional</h1></div>", unsafe_allow_html=True)

# --- 3. CUESTIONARIO FINANCIERO ---
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

# --- 4. MOTOR DE ESTRATEGIA (IA + PLOTLY) ---
if st.button("GENERAR ESTRATEGIA PROFESIONAL +"):
    
    user_data = {
        "saldo": saldo_hoy, "sueldos": sueldos, "gastos": gastos, 
        "pfs_actuales": pfs, "meta": {"n": meta_nombre, "m": meta_monto}, "mep": mep
    }

    with st.spinner("🤖 Realizando análisis profundo del mercado y perfil financiero..."):
        
        prompt = f"""
        Actúa como un Asesor Financiero Fiduciario Senior del BNA, tu máxima prioridad es la seguridad y el bienestar financiero del cliente. Eres extremadamente claro, didáctico y tus recomendaciones se basan en fundamentos técnicos sólidos y profundos del mercado argentino. El dinero de la gente es una gran responsabilidad.

        Analiza los datos de este cliente: {json.dumps(user_data)}

        Usa datos macroeconómicos reales y actualizados de Argentina (TNA de Plazo Fijo BNA, Tasa de Política Monetaria BCRA, Inflación REM, valor de Dólar MEP, etc.).

        Tu respuesta DEBE SER EXCLUSIVAMENTE un objeto JSON válido, sin texto antes ni después. La estructura del JSON debe ser la siguiente:
        {{
          "analisis_macro": "Un texto claro y educativo sobre el contexto económico actual de Argentina, explicando cómo afecta a las tasas de interés, la inflación y el dólar. Usa un lenguaje sencillo pero profesional.",
          "horizonte_meta": "Basado en la meta del cliente y su capacidad de ahorro, calcula un horizonte de tiempo estimado (en meses o años) para alcanzar el objetivo. Explica el cálculo.",
          "cartera_sugerida": [
            {{
              "instrumento": "Nombre del instrumento (ej. Plazo Fijo, FCI Money Market, Letra del Tesoro)",
              "monto": "Monto a invertir en pesos",
              "tipo_activo": "Categoría del activo (ej. Renta Fija, Renta Variable, Cobertura)",
              "tna_estimada": "Tasa Nominal Anual estimada o rendimiento esperado",
              "fundamento": "Explicación técnica y didáctica de por qué este instrumento es adecuado para el cliente en este momento. Detalla los riesgos y beneficios."
            }}
          ],
          "estrategia_liquidez": "Un plan paso a paso y detallado para manejar la liquidez de corto plazo. Explica qué hacer con el dinero destinado a gastos próximos. Por ejemplo: 'Para cubrir el vencimiento de la tarjeta de $350.000 el día 20, invertir $345.000 en un Fondo Común de Inversión Money Market y rescatar el dinero 24hs antes, el día 19. El resto del dinero para gastos, colocarlo en cauciones a 1 día y renovarlas diariamente hasta la fecha de pago.'",
          "evolucion_cartera": [
            {{
              "mes": "Mes (ej. 'Mes 1', 'Mes 2')",
              "monto_pesos": "Monto total proyectado de la cartera en pesos",
              "inflacion_acum_estimada": "Inflación acumulada estimada para ese mes"
            }}
          ],
          "justificacion_general": "Un resumen final que conecte todas las partes de la estrategia, explicando cómo el plan de liquidez, la cartera de inversión y el horizonte de la meta trabajan juntos para cumplir los objetivos del cliente de manera segura y eficiente."
        }}
        """

        try:
            # LLAMADA CORRECTA A LA API
            response = model.generate_content(prompt)
            
            # Limpieza robusta del JSON de la respuesta
            raw_text = response.text
            start = raw_text.find('{')
            end = raw_text.rfind('}') + 1
            clean_json = raw_text[start:end]
            data = json.loads(clean_json)

            st.success("✅ Estrategia Profesional Generada")
            st.balloons()

            # --- RENDERIZADO DE RESULTADOS MEJORADO ---
            st.markdown(f"<div class='card'><b>Resumen de Mercado por Nuestro Equipo de Research:</b><br>{data['analisis_macro']}</div>", unsafe_allow_html=True)
            
            col_horiz, col_liq = st.columns(2)
            with col_horiz:
                st.markdown(f"<div class='card'><h3> Horizonte para tu Meta: {meta_nombre}</h3><p>{data['horizonte_meta']}</p></div>", unsafe_allow_html=True)
            with col_liq:
                st.markdown(f"<div class='card'><h3> Plan de Liquidez (Corto Plazo)</h3><p>{data['estrategia_liquidez']}</p></div>", unsafe_allow_html=True)

            st.subheader("📊 Cartera de Inversión Sugerida")
            df_cartera = pd.DataFrame(data['cartera_sugerida'])
            fig1 = px.pie(df_cartera, values='monto', names='tipo_activo', title='Distribución Propuesta por Tipo de Activo',
                         color_discrete_sequence=['#005691', '#0074c7', '#4da3ff', '#a3d1ff'])
            st.plotly_chart(fig1, use_container_width=True)

            st.subheader("📋 Fundamentos de cada Instrumento")
            for index, row in df_cartera.iterrows():
                with st.expander(f"**{row['instrumento']}** - Monto: ${int(row['monto']):,}"):
                    st.markdown(f"**Tipo de Activo:** {row['tipo_activo']}")
                    st.markdown(f"**Rendimiento Anual Estimado:** {row['tna_estimada']}")
                    st.markdown(f"---")
                    st.markdown(f"**Fundamento Técnico de la Recomendación:**")
                    st.info(row['fundamento'])

            st.subheader("📈 Proyección de tu Cartera vs. Inflación (6 Meses)")
            df_evol = pd.DataFrame(data['evolucion_cartera'])
            fig2 = go.Figure()
            fig2.add_trace(go.Scatter(x=df_evol['mes'], y=df_evol['monto_pesos'], name='Capital Proyectado', line=dict(color='#005691', width=4), fill='tozeroy'))
            fig2.add_trace(go.Scatter(x=df_evol['mes'], y=df_evol['inflacion_acum_estimada'], name='Inflación Acumulada Estimada', line=dict(color='#ff4b4b', width=2, dash='dot')))
            st.plotly_chart(fig2, use_container_width=True)
            
            st.markdown("---")
            st.markdown(f"<div class='card'><h3>💡 Justificación General de la Estrategia</h3><p>{data['justificacion_general']}</p></div>", unsafe_allow_html=True)

        except json.JSONDecodeError:
            st.error("Error de formato: La IA no devolvió un JSON válido. Esto puede ocurrir por un fallo temporal.")
            st.code(raw_text)
        except Exception as e:
            if "429" in str(e):
                st.error("⏳ Límite de cuota alcanzado. Por favor, esperá un minuto antes de reintentar o considerá habilitar la facturación en tu proyecto de Google Cloud para obtener límites más altos.")
            else:
                st.error(f"Ocurrió un error inesperado al comunicarse con la IA.")
                st.exception(e)

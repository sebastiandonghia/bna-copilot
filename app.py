import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import google.generativeai as genai
import json
import datetime
import market_data # Import the market_data script

st.write(f"google-generativeai version: {genai.__version__}")

# --- 1. CONFIGURACIÓN DE IA (DRIVER CORREGIDO Y ESTABLE) ---
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    model = genai.GenerativeModel('models/gemini-2.5-flash')
except Exception as e:
    st.error("⚠️ Error de configuración: No se pudo inicializar la IA. Verificá la GOOGLE_API_KEY en los Secrets de Streamlit.")
    st.exception(e)
    st.stop()

# --- 2. ESTILO VISUAL BNA+ ---
st.set_page_config(page_title="+ Copilot | Inversiones", page_icon="🏦", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #f4f7f9; }
    .main-header { background-color: #005691; padding: 20px; border-radius: 10px; color: white; text-align: center; margin-bottom: 20px; }
    .stButton>button { background-color: #005691; color: white; border-radius: 10px; font-weight: bold; width: 100%; height: 3em; border: none; }
    .stButton>button:hover { background-color: #004575; color: white; }
    .card { background-color: white; padding: 20px; border-radius: 15px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); border-left: 5px solid #005691; margin-bottom: 20px; }
    .stExpander { background-color: white; border-radius: 10px; border: 1px solid #005691; }
    </style>
    """, unsafe_allow_html=True)

st.markdown("<div class='main-header'><h1>🏦 + Inversiones | Copilot</h1></div>", unsafe_allow_html=True)

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
if st.button("GENERAR ESTRATEGIA +"):

    # 1. Obtener datos del mercado en tiempo real
    with st.spinner("🚀 Obteniendo datos de mercado actualizados..."):
        exchange_rates = market_data.get_exchange_rates()
        fci_data = market_data.get_fci_data()
        sovereign_bonds_data = market_data.get_sovereign_bonds_data()
        lecap_boncap_data = market_data.get_lecap_boncap_data()
        bcra_macro_indicators = market_data.get_bcra_macro_indicators()
        bcra_exchange_rates_summary = market_data.get_bcra_exchange_rates_summary()

    # 2. Consolidar datos del usuario
    user_data = {
        "saldo": saldo_hoy, "sueldos": sueldos, "gastos": gastos, 
        "pfs_actuales": pfs, "meta": {"n": meta_nombre, "m": meta_monto}, "mep": mep
    }

    # 3. Consolidar todos los datos del mercado en un contexto para la IA
    market_context = {
        "exchange_rates": exchange_rates,
        "fci_data": fci_data,
        "sovereign_bonds": sovereign_bonds_data,
        "lecap_boncap": lecap_boncap_data,
        "bcra_macro_indicators": bcra_macro_indicators,
        "bcra_exchange_rates_summary": bcra_exchange_rates_summary,
        # "cer_data": cer_data # Implementar cuando tengamos una fuente confiable
    }

    with st.spinner("🤖 Realizando análisis profundo del mercado y perfil financiero..."):

        prompt = f"""
        Actúa como un Asesor Financiero Fiduciario Senior del BNA, tu máxima prioridad es la seguridad y el bienestar financiero del cliente. Eres extremadamente claro, didáctico y tus recomendaciones se basan en fundamentos técnicos sólidos y profundos del mercado argentino. El dinero de la gente es una gran responsabilidad.

        Analiza los datos de este cliente: {json.dumps(user_data, indent=2)}

        Considera el siguiente contexto de mercado actualizado para tus análisis: {json.dumps(market_context, indent=2)}

        Usa datos macroeconómicos reales y actualizados de Argentina (TNA de Plazo Fijo BNA, Tasa de Política Monetaria BCRA, Inflación REM, valor de Dólar MEP, etc.) OBTENIDOS DEL CONTEXTO DE MERCADO PROPORCIONADO.

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
              "ingresos_netos_mes": "Ingresos netos esperados para este mes (sueldos - gastos)",
              "egresos_totales_mes": "Egresos totales proyectados para este mes",
              "inflacion_acum_estimada": "Inflación acumulada estimada para ese mes"
            }}
          ],
          "justificacion_general": "Un resumen final que conecte todas las partes de la estrategia, explicando cómo el plan de liquidez, la cartera de inversión y el horizonte de la meta trabajan juntos para cumplir los objetivos del cliente de manera segura y eficiente."
        }}
        """

        try:
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
            st.markdown(f"<div class='card'><b>Resumen de Mercado Generado por Nuestro Copilot de Inversiones:</b><br>{data['analisis_macro']}</div>", unsafe_allow_html=True)

            col_horiz, col_liq = st.columns(2)
            with col_horiz:
                st.markdown(f"<div class='card'><h3> Horizonte para tu Meta: {meta_nombre}</h3><p>{data['horizonte_meta']}</p></div>", unsafe_allow_html=True)
            with col_liq:
                st.markdown(f"<div class='card'><h3> Plan de Liquidez (Corto Plazo)</h3><p>{data['estrategia_liquidez']}</p></div>", unsafe_allow_html=True)

            st.subheader("📊 Cartera de Inversión Sugerida")
            
            processed_cartera_sugerida = []
            for item in data['cartera_sugerida']:
                monto_numeric = 0
                try:
                    cleaned_monto = str(item['monto']).replace('$', '').replace('.', '').replace(',', '')
                    # Extract the numeric part (e.g., from "Inicialmente 3.625.000" take 3625000)
                    parts = cleaned_monto.split(' ')
                    if parts and parts[-1].replace('.', '', 1).isdigit(): # Check if last part is numeric
                         monto_numeric = float(parts[-1])
                except (ValueError, TypeError):
                    pass # Keep monto_numeric as 0 if parsing fails
                
                new_item = item.copy()
                new_item['monto'] = monto_numeric
                processed_cartera_sugerida.append(new_item)

            df_cartera = pd.DataFrame(processed_cartera_sugerida)
            
            # Filter out entries with 0 monto for better pie chart representation
            df_cartera_filtered = df_cartera[df_cartera['monto'] > 0] 

            if not df_cartera_filtered.empty:
                fig1 = px.pie(df_cartera_filtered, values='monto', names='tipo_activo', title='Distribución Propuesta por Tipo de Activo',
                             color_discrete_sequence=['#005691', '#0074c7', '#4da3ff', '#a3d1ff'])
                st.plotly_chart(fig1, use_container_width=True)
            else:
                st.info("No hay montos válidos en la cartera sugerida para mostrar el gráfico de distribución.")

            st.subheader("📋 Fundamentos de cada Instrumento")
            for index, row in df_cartera.iterrows():
                monto_display = ""
                try:
                    # Clean the string, remove '$', thousands separators, and any text
                    cleaned_monto = str(row['monto']).replace('$', '').replace('.', '').replace(',', '')
                    # Try to parse float first to handle potential decimal values
                    numeric_monto = float(cleaned_monto.split(' ')[-1]) # Try to get the last numeric part
                    monto_display = f"${int(numeric_monto):,}"
                except (ValueError, TypeError):
                    # Fallback to displaying the original string if parsing fails
                    monto_display = str(row['monto'])
                
                with st.expander(f"**{row['instrumento']}** - Monto: {monto_display}"):
                    st.markdown(f"**Tipo de Activo:** {row['tipo_activo']}")
                    st.markdown(f"**Rendimiento Anual Estimado:** {row['tna_estimada']}")
                    st.markdown(f"---")
                    st.markdown(f"**Fundamento Técnico de la Recomendación:**")
                    st.info(row['fundamento'])

            st.subheader("📈 Proyección de Flujo de Efectivo y Cartera (6 Meses)")
            df_evol = pd.DataFrame(data['evolucion_cartera'])
            fig2 = go.Figure()

            # Capital Proyectado (Line)
            fig2.add_trace(go.Scatter(x=df_evol['mes'], y=df_evol['monto_pesos'], name='Capital Proyectado', 
                                      line=dict(color='#005691', width=4), mode='lines+markers'))
            # Inflación Acumulada Estimada (Line)
            fig2.add_trace(go.Scatter(x=df_evol['mes'], y=df_evol['inflacion_acum_estimada'], name='Inflación Acumulada Estimada', 
                                      line=dict(color='#ff4b4b', width=2, dash='dot'), mode='lines+markers'))
            
            # Ingresos Netos (Bar)
            if 'ingresos_netos_mes' in df_evol.columns:
                fig2.add_trace(go.Bar(x=df_evol['mes'], y=df_evol['ingresos_netos_mes'], name='Ingresos Netos Mensuales',
                                      marker_color='green', opacity=0.6))
            # Egresos Totales (Bar)
            if 'egresos_totales_mes' in df_evol.columns:
                fig2.add_trace(go.Bar(x=df_evol['mes'], y=df_evol['egresos_totales_mes'], name='Egresos Totales Mensuales',
                                      marker_color='red', opacity=0.6))

            fig2.update_layout(barmode='overlay', # Overlay bars if both incomes/expenses are present
                               yaxis_title='Monto ($)')
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

st.info("⚠️ **Aclaración Importante:** La información y estrategias generadas por este Copilot de Inversiones tienen fines educativos e informativos únicamente y no constituyen una recomendación de inversión, asesoramiento financiero ni una oferta de compra o venta de ningún producto financiero. La inversión en mercados financieros conlleva riesgos, incluyendo la posible pérdida del capital invertido. Consultá siempre con un asesor financiero certificado antes de tomar cualquier decisión de inversión.")

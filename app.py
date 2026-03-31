import streamlit as st
import subprocess
import json
import pandas as pd
import plotly.express as px
import time

# --- 1. CONFIGURACIÓN DE PÁGINA Y ESTILO ---
st.set_page_config(page_title="+ Copilot | Inversiones", page_icon="🏦", layout="wide")

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
st.subheader("📋 Perfil Financiero")
with st.container():
    col1, col2 = st.columns(2)
    with col1:
        saldo = st.number_input("Saldo actual en cuenta ($)", value=1500000, step=50000)
        tarjeta = st.number_input("Próximo resumen de Tarjeta ($)", value=350000)
    with col2:
        gasto_fijo = st.number_input("Gastos fijos mensuales (aprox.) ($)", value=450000)
        fecha_pago = st.slider("Día del mes para estos pagos", 1, 31, 10)

    st.subheader("🎯 Tu Meta Principal")
    col3, col4 = st.columns(2)
    with col3:
        meta_nombre = st.text_input("¿Cuál es tu objetivo?", "Cambiar el auto 🚗")
        quiere_mep = st.selectbox("¿Te interesa operar Dólar MEP?", ["No", "Sí, como opción de ahorro"])
    with col4:
        meta_monto = st.number_input("Monto estimado de la meta ($)", value=10000000, step=100000)


# --- 3. MOTOR DE ESTRATEGIA ---
if st.button("GENERAR ESTRATEGIA PROFESIONAL"):
    with st.spinner("Realizando análisis profundo del mercado y tu perfil..."):
        
        contexto_usuario = {
            "saldo_disponible": saldo,
            "gastos_fijos_mes": gasto_fijo,
            "dia_pago_gastos": fecha_pago,
            "pago_tarjeta": tarjeta,
            "meta_nombre": meta_nombre,
            "meta_monto": meta_monto,
            "interes_mep": quiere_mep
        }
        
        # --- LLAMADA A GEMINI CLI CON EL NUEVO PROMPT ---
        comando = f'gemini "Actúa según @PROMPT_MAESTRO_v2.txt. Datos del cliente: {json.dumps(contexto_usuario)}"'
        
        try:
            resultado_raw = subprocess.check_output(comando, shell=True, text=True, stderr=subprocess.STDOUT)
            
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
                st.markdown(f"<div class='card'><h3> Plan de Liquidez (Corto Plazo)</h3><p>{data.get('estrategia_liquidez', 'No disponible.')}</p></div>", unsafe_allow_html=True)

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
            st.markdown(f"<div class='card'><h3>💡 Justificación General de la Estrategia</h3><p>{data.get('justificacion_general', 'No disponible.')}</p></div>", unsafe_allow_html=True)

        except subprocess.CalledProcessError as e:
            st.error("Ocurrió un error al ejecutar el comando de la IA.")
            st.code(e.output)
        except json.JSONDecodeError:
            st.error("Error de formato: La IA no devolvió un JSON válido. Esto puede ocurrir por un fallo temporal.")
            st.code(resultado_raw)
        except Exception as e:
            st.error(f"Ocurrió un error inesperado.")
            st.exception(e)

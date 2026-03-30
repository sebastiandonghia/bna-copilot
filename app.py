import streamlit as st
import pandas as pd

# 1. Configuración de Marca BNA+
st.set_page_config(page_title="BNA+ Inversiones", page_icon="🏦", layout="centered")

# Estilo CSS para que parezca la App del Nación
st.markdown("""
    <style>
    .stApp { background-color: #f4f7f9; }
    .main-header { background-color: #005691; padding: 20px; border-radius: 10px; color: white; text-align: center; margin-bottom: 20px; }
    .stButton>button { background-color: #005691; color: white; border-radius: 10px; font-weight: bold; width: 100%; height: 3em; }
    .card { background-color: white; padding: 20px; border-radius: 15px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); border-left: 5px solid #005691; margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

st.markdown("<div class='main-header'><h1>🏦 BNA+ Inversiones</h1></div>", unsafe_allow_html=True)

# 2. Captura de Datos (Interfaz Amigable)
with st.container():
    st.subheader("📋 Datos del Cliente")
    col1, col2 = st.columns(2)
    with col1:
        saldo = st.number_input("Saldo disponible ($)", value=1500000)
        meta_nombre = st.text_input("¿Cuál es tu objetivo de ahorro?", "Viaje a Italia")
    with col2:
        gastos = st.number_input("Gastos del mes (Tarjeta/Servicios) ($)", value=600000)
        meta_monto = st.number_input("Monto para cumplir tu objetivo ($)", value=5000000)

mep = st.checkbox("¿Te interesa comprar Dólar MEP?")

if st.button("GENERAR ESTRATEGIA DE INVERSIÓN"):
    st.balloons() # Efecto visual de éxito
    
    # Simulación de respuesta de IA (Datos reales Marzo 2026)
    st.markdown("<div class='card'><h3>🚀 Estrategia Recomendada</h3>"
                "<p>Basado en la inflación proyectada del 2.4% y las tasas vigentes del BCRA.</p></div>", unsafe_allow_html=True)
    
    # Tabla de Resultados
    resultados = pd.DataFrame({
        "Instrumento": ["FCI Pellegrini (T+0)", "Lecap S15Y6", "Boncer TX26", "Dólar MEP"],
        "Asignación": [f"$ {gastos}", f"$ {(saldo-gastos)*0.5:.0f}", f"$ {(saldo-gastos)*0.3:.0f}", "Opcional"],
        "Objetivo": ["Liquidez Gastos", "Tasa Real +", "Cobertura Inflación", "Resguardo Valor"]
    })
    st.table(resultados)
    
    # Barra de Progreso de Meta
    st.subheader(f"🎯 Progreso para: {meta_nombre}")
    progreso = (saldo / meta_monto)
    st.progress(progreso if progreso <= 1.0 else 1.0)
    st.write(f"Llevás el **{progreso*100:.1f}%** de tu meta alcanzado.")

    if mep:
        st.warning("⚠️ **Aviso BNA:** La compra de MEP requiere 24hs de parking antes de la liquidación.")
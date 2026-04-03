import google.generativeai as genai
import json
import streamlit as st

def configure_ai():
    """Configura el modelo generativo de Google."""
    try:
        genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
        # Cambiamos 'models/gemini-1.5-flash' por 'gemini-1.5-flash' (más compatible)
        return genai.GenerativeModel('gemini-1.5-flash')
    except Exception as e:
        st.error("⚠️ Error de configuración de IA: Verificá tu API KEY.")
        st.stop()

def generate_strategy(model, user_data, market_context):
    """
    Envía los datos a la IA y procesa la respuesta para obtener la estrategia final.
    """
    prompt = f"""
    Actúa como un Asesor Financiero Fiduciario Senior del BNA, tu máxima prioridad es la seguridad y el bienestar financiero del cliente. Eres extremadamente claro, didáctico y tus recomendaciones se basan en fundamentos técnicos sólidos y profundos del mercado argentino. El dinero de la gente es una gran responsabilidad.

    Analiza los datos de este cliente: {json.dumps(user_data, indent=2)}

    Considera el siguiente contexto de mercado actualizado para tus análisis: {json.dumps(market_context, indent=2)}

    Usa datos macroeconómicos reales y actualizados de Argentina (TNA de Plazo Fijo BNA, Tasa de Política Monetaria BCRA, Inflación REM, valor de Dólar MEP, etc.) OBTENIDOS DEL CONTEXTO DE MERCADO PROPORCIONADO. Presta especial atención a la nueva información sobre el rendimiento de las cuentas del propio banco (`bna_account_remuneration`) para dar recomendaciones de liquidez diaria.

    Tu respuesta DEBE SER EXCLUSIVAMENTE un objeto JSON válido, sin texto antes ni después. La estructura del JSON debe ser la siguiente:
    {{
      "analisis_macro": "Un texto claro y educativo sobre el contexto económico actual de Argentina...",
      "horizonte_meta": "Basado en la meta del cliente...",
      "cartera_sugerida": [
        {{
          "instrumento": "Nombre del instrumento",
          "monto": "Monto a invertir en pesos",
          "tipo_activo": "Categoría del activo",
          "tna_estimada": "Tasa Nominal Anual estimada",
          "fundamento": "Explicación técnica..."
        }}
      ],
      "estrategia_liquidez": "Un plan paso a paso y detallado...",
      "evolucion_cartera": [
        {{
          "mes": "Mes 1",
          "monto_pesos": 1000000,
          "ingresos_netos_mes": 500000,
          "egresos_totales_mes": 200000,
          "inflacion_acum_estimada": "5%"
        }}
      ],
      "justificacion_general": "Resumen final conectando todas las partes."
    }}
    """
    
    try:
        response = model.generate_content(prompt)
        raw_text = response.text
        
        # Limpieza robusta del JSON
        start = raw_text.find('{')
        end = raw_text.rfind('}') + 1
        clean_json = raw_text[start:end]
        return json.loads(clean_json)
    except Exception as e:
        raise Exception(f"Error al generar la estrategia con la IA: {str(e)}")

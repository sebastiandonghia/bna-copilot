import market_data
from bna_scraper import main as scrape_bna_accounts
import streamlit as st

def get_all_market_context():
    """
    Orquesta la obtención de todos los datos de mercado necesarios 
    para la estrategia, incluyendo datos del BCRA, FCI, Bonos y el scraper del BNA.
    """
    try:
        with st.spinner("🚀 Obteniendo datos de mercado en tiempo real..."):
            exchange_rates = market_data.get_exchange_rates()
            fci_data = market_data.get_fci_data()
            sovereign_bonds_data = market_data.get_sovereign_bonds_data()
            lecap_boncap_data = market_data.get_lecap_boncap_data()
            bcra_macro_indicators = market_data.get_bcra_macro_indicators()
            bcra_exchange_rates_summary = market_data.get_bcra_exchange_rates_summary()
            
            # Datos específicos de remuneración del BNA
            bna_remuneration_data = scrape_bna_accounts()

        return {
            "exchange_rates": exchange_rates,
            "fci_data": fci_data,
            "sovereign_bonds": sovereign_bonds_data,
            "lecap_boncap": lecap_boncap_data,
            "bcra_macro_indicators": bcra_macro_indicators,
            "bcra_exchange_rates_summary": bcra_exchange_rates_summary,
            "bna_account_remuneration": bna_remuneration_data
        }
    except Exception as e:
        st.error(f"Error al obtener datos de mercado: {e}")
        return None

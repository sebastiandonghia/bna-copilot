import requests
import datetime
from concurrent.futures import ThreadPoolExecutor

# Fuentes de datos basadas en el análisis de https://github.com/arisbdar/rendimientos-ar
YAHOO_FINANCE_URL = "https://query1.finance.yahoo.com/v8/finance/chart/ARS=X?interval=1d&range=5d"
DATA912_BONDS_URL = "https://data912.com/live/arg_bonds"
DATA912_NOTES_URL = "https://data912.com/live/arg_notes"
ARGENTINA_DATOS_RIESGO_URL = "https://api.argentinadatos.com/v1/finanzas/indices/riesgo-pais/ultimo"
ARGENTINA_DATOS_FCI_MM_ULTIMO_URL = "https://api.argentinadatos.com/v1/finanzas/fci/mercadoDinero/ultimo"
ARGENTINA_DATOS_FCI_MM_PENULTIMO_URL = "https://api.argentinadatos.com/v1/finanzas/fci/mercadoDinero/penultimo"
ARGENTINA_DATOS_FCI_RM_ULTIMO_URL = "https://api.argentinadatos.com/v1/finanzas/fci/rentaMixta/ultimo"
ARGENTINA_DATOS_FCI_RM_PENULTIMO_URL = "https://api.argentinadatos.com/v1/finanzas/fci/rentaMixta/penultimo"
BCRA_API_BASE_URL = "https://api.bcra.gob.ar/estadisticas/v4.0/Monetarias"
BCRA_CAMBIARIAS_API_BASE_URL = "https://api.bcra.gob.ar/estadisticascambiarias/v1.0/Cotizaciones"

# --- Constantes para BCRA (copiadas de server.js) ---
BCRA_VARS = [
  { "id": 1,  "key": "reservas",              "nombre": "Reservas Internacionales",          "unidad": "MM USD", "categoria": "Cambiario", "formato": "numero" },
  { "id": 4,  "key": "usd_minorista",         "nombre": "Dólar Minorista (vendedor)",        "unidad": "$/USD",  "categoria": "Cambiario", "formato": "numero" },
  { "id": 5,  "key": "usd_mayorista",         "nombre": "Dólar Mayorista (referencia)",      "unidad": "$/USD",  "categoria": "Cambiario", "formato": "numero" },
  { "id": 7,  "key": "badlar_tna",            "nombre": "BADLAR Privados (TNA)",             "unidad": "% TNA",  "categoria": "Tasas",     "formato": "pct" },
  { "id": 35, "key": "badlar_tea",            "nombre": "BADLAR Privados (TEA)",             "unidad": "% TEA",  "categoria": "Tasas",     "formato": "pct" },
  { "id": 8,  "key": "tm20",                  "nombre": "TM20 Privados",                     "unidad": "% TNA",  "categoria": "Tasas",     "formato": "pct" },
  { "id": 44, "key": "tamar_tna",             "nombre": "TAMAR Privados (TNA)",              "unidad": "% TNA",  "categoria": "Tasas",     "formato": "pct" },
  { "id": 45, "key": "tamar_tea",             "nombre": "TAMAR Privados (TEA)",              "unidad": "% TEA",  "categoria": "Tasas",     "formato": "pct" },
  { "id": 11, "key": "baibar",                "nombre": "BAIBAR (interbancaria)",            "unidad": "% TNA",  "categoria": "Tasas",     "formato": "pct" },
  { "id": 12, "key": "tasa_depositos_30d",    "nombre": "Depósitos 30 días",                 "unidad": "% TNA",  "categoria": "Tasas",     "formato": "pct" },
  { "id": 13, "key": "tasa_adelantos",        "nombre": "Adelantos Cta Cte",                 "unidad": "% TNA",  "categoria": "Tasas",     "formato": "pct" },
  { "id": 14, "key": "tasa_prestamos",        "nombre": "Préstamos Personales",              "unidad": "% TNA",  "categoria": "Tasas",     "formato": "pct" },
  { "id": 43, "key": "tasa_justicia",         "nombre": "Tasa Uso de Justicia (P 14.290)",   "unidad": "% anual","categoria": "Tasas",     "formato": "pct" },
  { "id": 15, "key": "base_monetaria",        "nombre": "Base Monetaria",                    "unidad": "MM $",   "categoria": "Monetario", "formato": "numero" },
  { "id": 16, "key": "circulacion",           "nombre": "Circulación Monetaria",             "unidad": "MM $",   "categoria": "Monetario", "formato": "numero" },
  { "id": 17, "key": "billetes_publico",      "nombre": "Billetes en poder del Público",     "unidad": "MM $",   "categoria": "Monetario", "formato": "numero" },
  { "id": 18, "key": "efectivo_entidades",    "nombre": "Efectivo en Entidades",             "unidad": "MM $",   "categoria": "Monetario", "formato": "numero" },
  { "id": 19, "key": "dep_cta_cte_bcra",     "nombre": "Depósitos Cta Cte en BCRA",         "unidad": "MM $",   "categoria": "Monetario", "formato": "numero" },
  { "id": 21, "key": "depositos_total",       "nombre": "Depósitos en EF (total)",           "unidad": "MM $",   "categoria": "Monetario", "formato": "numero" },
  { "id": 22, "key": "depositos_cc",          "nombre": "Depósitos en Cta Cte",              "unidad": "MM $",   "categoria": "Monetario", "formato": "numero" },
  { "id": 23, "key": "depositos_ca",          "nombre": "Depósitos en Caja de Ahorro",      "unidad": "MM $",   "categoria": "Monetario", "formato": "numero" },
  { "id": 24, "key": "depositos_plazo",       "nombre": "Depósitos a Plazo",                "unidad": "MM $",   "categoria": "Monetario", "formato": "numero" },
  { "id": 25, "key": "m2_var_ia",             "nombre": "M2 Privado (var. interanual)",      "unidad": "%",      "categoria": "Monetario", "formato": "pct" },
  { "id": 26, "key": "prestamos_privado",     "nombre": "Préstamos al Sector Privado",      "unidad": "MM $",   "categoria": "Monetario", "formato": "numero" },
  { "id": 27, "key": "inflacion_mensual",     "nombre": "Inflación Mensual (IPC)",           "unidad": "%",      "categoria": "Inflación", "formato": "pct" },
  { "id": 28, "key": "inflacion_interanual",  "nombre": "Inflación Interanual (IPC)",        "unidad": "%",      "categoria": "Inflación", "formato": "pct" },
  { "id": 29, "key": "inflacion_esperada",    "nombre": "Inflación Esperada (próx. 12m)",    "unidad": "%",      "categoria": "Inflación", "formato": "pct" },
  { "id": 30, "key": "cer",                   "nombre": "CER",                               "unidad": "índice", "categoria": "Índices",   "formato": "numero" },
  { "id": 31, "key": "uva",                   "nombre": "UVA",                               "unidad": "$",      "categoria": "Índices",   "formato": "numero" },
  { "id": 32, "key": "uvi",                   "nombre": "UVI",                               "unidad": "$",      "categoria": "Índices",   "formato": "numero" },
  { "id": 40, "key": "icl",                   "nombre": "ICL (Contratos de Locación)",       "unidad": "índice", "categoria": "Índices",   "formato": "numero" },
]

MONEDAS_DESTACADAS = ['USD', 'EUR', 'BRL', 'GBP', 'CHF', 'JPY', 'CNY', 'CLP', 'UYU', 'PYG', 'BOB', 'MXN', 'COP', 'CAD', 'AUD', 'XAU', 'XAG']

BCRA_HEADERS = { 'Accept': 'application/json', 'User-Agent': 'rendimientos.co' }

def _fetch_bcra_api(url):
    """Helper function to fetch data from BCRA API with common headers."""
    try:
        response = requests.get(url, headers=BCRA_HEADERS)
        response.raise_for_status() # Raise an exception for HTTP errors
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching from BCRA API ({url}): {e}")
        return None

def get_exchange_rates():
    """
    Obtiene las cotizaciones del Dólar Oficial, MEP, CCL y el Riesgo País.
    La lógica replica la implementación del endpoint /api/cotizaciones del repositorio de referencia.
    """
    """
    Obtiene las cotizaciones del Dólar Oficial, MEP, CCL y el Riesgo País.
    La lógica replica la implementación del endpoint /api/cotizaciones del repositorio de referencia.
    """
    oficial = None
    mep = None
    ccl = None
    riesgo_pais = None
    
    try:
        # 1. Dólar Oficial desde Yahoo Finance
        headers = {'User-Agent': 'Mozilla/5.0'}
        yahoo_resp = requests.get(YAHOO_FINANCE_URL, headers=headers)
        if yahoo_resp.status_code == 200:
            yahoo_data = yahoo_resp.json()
            meta = yahoo_data.get("chart", {}).get("result", [{}])[0].get("meta", {})
            if meta.get("regularMarketPrice"):
                oficial = {
                    "price": meta["regularMarketPrice"],
                    "prevClose": meta.get("chartPreviousClose") or meta.get("previousClose") or 0
                }
    except Exception as e:
        print(f"Error fetching Dolar Oficial from Yahoo Finance: {e}")

    try:
        # 2. Dólar MEP y CCL desde data912 (basado en AL30)
        bonds_resp = requests.get(DATA912_BONDS_URL)
        if bonds_resp.status_code == 200:
            bonds_data = bonds_resp.json()
            if isinstance(bonds_data, list):
                al30 = next((b for b in bonds_data if b.get("symbol") == "AL30"), None)
                al30d = next((b for b in bonds_data if b.get("symbol") == "AL30D"), None)
                al30c = next((b for b in bonds_data if b.get("symbol") == "AL30C"), None)
                
                ars_price = float(al30.get("c", 0)) if al30 else 0
                
                if ars_price > 0:
                    if al30d:
                        mep_usd_price = float(al30d.get("c", 0))
                        if mep_usd_price > 0:
                            mep = {"price": round(ars_price / mep_usd_price, 2)}
                    if al30c:
                        ccl_usd_price = float(al30c.get("c", 0))
                        if ccl_usd_price > 0:
                            ccl = {"price": round(ars_price / ccl_usd_price, 2)}
    except Exception as e:
        print(f"Error fetching MEP/CCL from data912: {e}")

    try:
        # 3. Riesgo País desde ArgentinaDatos
        riesgo_resp = requests.get(ARGENTINA_DATOS_RIESGO_URL)
        if riesgo_resp.status_code == 200:
            riesgo_data = riesgo_resp.json()
            if riesgo_data.get("valor") is not None:
                riesgo_pais = {"value": riesgo_data["valor"]}
    except Exception as e:
        print(f"Error fetching Riesgo Pais from ArgentinaDatos: {e}")

    return {
        "oficial": oficial, "mep": mep, "ccl": ccl,
        "riesgo_pais": riesgo_pais, "updated": datetime.datetime.now().isoformat()
    }

def get_fci_data():
    """
    Obtiene datos de Fondos Comunes de Inversión (Money Market y Renta Mixta)
    y calcula su TNA basado en los últimos dos días de datos.
    """
    urls = [
        ARGENTINA_DATOS_FCI_MM_ULTIMO_URL,
        ARGENTINA_DATOS_FCI_MM_PENULTIMO_URL,
        ARGENTINA_DATOS_FCI_RM_ULTIMO_URL,
        ARGENTINA_DATOS_FCI_RM_PENULTIMO_URL
    ]
    
    with ThreadPoolExecutor() as executor:
        responses = list(executor.map(lambda url: requests.get(url).json(), urls))
    
    mm_latest, mm_previous, rm_latest, rm_previous = responses

    def filter_valid(data):
        return [d for d in data if d.get("fecha") and d.get("vcp")]

    all_latest = filter_valid(mm_latest) + filter_valid(rm_latest)
    all_previous = filter_valid(mm_previous) + filter_valid(rm_previous)

    prev_map = {f["fondo"]: f for f in all_previous}
    results = []

    for fund in all_latest:
        prev = prev_map.get(fund["fondo"])
        if not prev or not prev.get("vcp") or not fund.get("vcp"):
            continue

        try:
            days = abs(round((datetime.datetime.fromisoformat(fund["fecha"]) - datetime.datetime.fromisoformat(prev["fecha"])).total_seconds() / 86400))
            if days <= 0:
                continue
            
            tna = round(((fund["vcp"] - prev["vcp"]) / prev["vcp"] / days) * 365 * 100, 2)
            results.append({
                "nombre": fund["fondo"],
                "tna": tna,
                "patrimonio": fund.get("patrimonio"),
                "fechaDesde": prev["fecha"],
                "fechaHasta": fund["fecha"]
            })
        except (ValueError, TypeError):
            continue # Ignorar si hay error en parseo de fechas o valores

    return sorted(results, key=lambda x: x['tna'], reverse=True)

def get_sovereign_bonds_data():
    """
    Obtiene los precios de bonos soberanos en USD de data912.
    La lógica replica la implementación del endpoint /api/soberanos del repositorio de referencia.
    """
    TICKERS_USD = ['BPD7D','AO27D','AN29D','AL29D','AL30D','AL35D','AE38D','AL41D','GD29D','GD30D','GD35D','GD38D','GD41D']
    results = []
    try:
        response = requests.get(DATA912_BONDS_URL)
        response.raise_for_status() # Raise an exception for HTTP errors
        data = response.json()
        
        if not isinstance(data, list):
            raise ValueError('Invalid data912 API response format for bonds')

        for bond in data:
            if bond.get("symbol") in TICKERS_USD:
                price_usd = float(bond.get("c", 0))
                if price_usd <= 0:
                    continue
                base_symbol = bond["symbol"].replace('D', '') # Remove 'D' for base symbol
                results.append({
                    "symbol": base_symbol,
                    "price_usd": price_usd,
                    "bid": float(bond.get("px_bid", 0)),
                    "ask": float(bond.get("px_ask", 0)),
                    "volume": bond.get("v", 0),
                    "pct_change": bond.get("pct_change", 0),
                })
    except requests.exceptions.RequestException as e:
        print(f"Error fetching sovereign bonds data: {e}")
    except ValueError as e:
        print(f"Error processing sovereign bonds data: {e}")
    except Exception as e:
        print(f"An unexpected error occurred with sovereign bonds: {e}")
            
    return results

def get_lecap_boncap_data():
    """
    Obtiene los precios de LECAPs y BONCAPs de data912.
    La lógica replica la implementación del endpoint /api/lecaps del repositorio de referencia.
    """
    LECAP_TICKERS = ['S17A6','S30A6','S15Y6','S29Y6','S31L6','S31G6','S30S6','S30O6','S30N6']
    BONCAP_TICKERS = ['T30J6','T15E7','T30A7','T31Y7','T30J7']
    results = []

    try:
        with ThreadPoolExecutor() as executor:
            notes_resp, bonds_resp = executor.map(requests.get, [DATA912_NOTES_URL, DATA912_BONDS_URL])

        notes_resp.raise_for_status()
        bonds_resp.raise_for_status()

        notes_data = notes_resp.json()
        bonds_data = bonds_resp.json()

        for item in notes_data:
            if item.get("symbol") in LECAP_TICKERS and float(item.get("c", 0)) > 0:
                results.append({ 
                    "symbol": item["symbol"], 
                    "price": float(item["c"]), 
                    "bid": float(item.get("px_bid", 0)), 
                    "ask": float(item.get("px_ask", 0)), 
                    "type": "LECAP" 
                })
        for item in bonds_data:
            if item.get("symbol") in BONCAP_TICKERS and float(item.get("c", 0)) > 0:
                results.append({ 
                    "symbol": item["symbol"], 
                    "price": float(item["c"]), 
                    "bid": float(item.get("px_bid", 0)), 
                    "ask": float(item.get("px_ask", 0)), 
                    "type": "BONCAP" 
                })
    except requests.exceptions.RequestException as e:
        print(f"Error fetching LECAP/BONCAP data: {e}")
    except ValueError as e:
        print(f"Error processing LECAP/BONCAP data: {e}")
    except Exception as e:
        print(f"An unexpected error occurred with LECAP/BONCAP: {e}")

    return results

if __name__ == '__main__':
    print("Obteniendo datos del mercado...")
    
    # --- Test get_exchange_rates ---
    exchange_data = get_exchange_rates()
    print("\n--- Cotizaciones ---")
    if exchange_data["oficial"]:
        print(f"Dólar Oficial: ${exchange_data['oficial']['price']:.2f}")
    else:
        print("Dólar Oficial: No disponible")

    if exchange_data["mep"]:
        print(f"Dólar MEP (calculado con AL30): ${exchange_data['mep']['price']:.2f}")
    else:
        print("Dólar MEP: No disponible")

    if exchange_data["ccl"]:
        print(f"Dólar CCL (calculado con AL30): ${exchange_data['ccl']['price']:.2f}")
    else:
        print("Dólar CCL: No disponible")
        
    if exchange_data["riesgo_pais"]:
        print(f"Riesgo País: {exchange_data['riesgo_pais']['value']} puntos")
    else:
        print("Riesgo País: No disponible")
    
    print(f"Actualizado: {exchange_data['updated']}")

    # --- Test get_fci_data ---
    print("\n--- Rendimiento FCIs (Money Market y Renta Mixta) ---")
    fci_data = get_fci_data()
    if fci_data:
        for fci in fci_data[:5]: # Imprimir los 5 de mayor rendimiento
            patrimonio = fci.get('patrimonio') or 0
            print(f"- {fci['nombre']}: TNA {fci['tna']:.2f}% (Patrimonio: ${patrimonio:,.2f})")
        if len(fci_data) > 5:
            print(f"... y {len(fci_data) - 5} más.")
    else:
        print("No se pudieron obtener datos de FCIs.")

    # --- Test get_sovereign_bonds_data ---
    print("\n--- Bonos Soberanos en USD ---")
    soberanos_data = get_sovereign_bonds_data()
    if soberanos_data:
        for bond in soberanos_data[:5]: # Imprimir los 5 primeros bonos
            print(f"- {bond['symbol']} (USD): Precio {bond['price_usd']:.2f} (Cambio: {bond['pct_change']:.2f}%)")
        if len(soberanos_data) > 5:
            print(f"... y {len(soberanos_data) - 5} más.")
    else:
        print("No se pudieron obtener datos de Bonos Soberanos en USD.")
    
    # --- Test get_lecap_boncap_data ---
    print("\n--- LECAPs y BONCAPs ---")
    lecap_boncap_data = get_lecap_boncap_data()
    if lecap_boncap_data:
        for item in lecap_boncap_data[:5]:
            print(f"- {item['symbol']} ({item['type']}): Precio {item['price']:.2f} (Bid: {item['bid']:.2f}, Ask: {item['ask']:.2f})")
        if len(lecap_boncap_data) > 5:
            print(f"... y {len(lecap_boncap_data) - 5} más.")
    else:
        print("No se pudieron obtener datos de LECAPs y BONCAPs.")

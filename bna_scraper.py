import requests
from bs4 import BeautifulSoup
import re
import json
from concurrent.futures import ThreadPoolExecutor

# --- CONFIGURACIÓN DE CUENTAS A SCRAPEAR ---
ACCOUNTS_TO_SCRAPE = {
    "cuenta_sueldo_pesos": {
        "name": "Cuenta Sueldo (Pesos)",
        "url": "https://bna.com.ar/Personas/cuentasueldo"
    },
    "cuenta_previsional_pesos": {
        "name": "Cuenta Previsional (Pesos)",
        "url": "https://bna.com.ar/Personas/CuentaPrevisional"
    },
    "caja_ahorro_dolares": {
        "name": "Caja de Ahorro (Dólares)",
        "url": "https://www.bna.com.ar/home/cuentaremunerada"
    }
}

def parse_remuneration_details(soup):
    """
    Parses the HTML soup to find remuneration details using a primary
    and a fallback strategy.
    """
    data = {
        "tna": None,
        "tea": None,
        "monto_maximo": None,
        "moneda": "ARS", # Default a Pesos
        "vigencia": None,
    }

    # --- Estrategia de Búsqueda de Texto ---
    terms_text = None
    # Estrategia Primaria: Buscar en el div específico.
    primary_div = soup.find('div', class_='text-xs-bna-custom')
    if primary_div:
        terms_text = primary_div.get_text(" ", strip=True)
    else:
        # Estrategia Secundaria (Fallback): Buscar en todo el cuerpo del documento.
        # Esto es útil para páginas con estructura diferente, como la de Cuenta Previsional.
        terms_text = soup.get_text(" ", strip=True)

    if not terms_text:
        return {"error": "No se pudo extraer texto de la página para analizar."}

    # --- Patrones de Regex (más flexibles) ---
    # Captura TNA, ej: "TASA NOMINAL ANUAL (TNA): 18,00%" o "A UNA TASA NOMINAL ANUAL DE 18,00% (TNA)"
    tna_pattern = re.compile(r"TASA NOMINAL ANUAL(?:\s*DE)?\s*([\d,.]+%?)(?:\s*\(TNA\))?", re.IGNORECASE)
    # Captura TEA
    tea_pattern = re.compile(r"TASA EFECTIVA ANUAL\s*([\d,.]+%?)(?:\s*\(TEA\))?", re.IGNORECASE)
    # Captura Monto, ej: "hasta $2.000.000,00" o "SUMA MÁXIMA DE $500.000,00"
    monto_pattern = re.compile(r"(?:HASTA LA SUMA MÁXIMA DE|hasta|Up to|monto máximo de)\s+((?:U\$S|\$)\s*[\d.,]+)", re.IGNORECASE)
    # Captura Vigencia, ej: "VIGENCIA DEL BENEFICIO DESDE EL 26/03/2026 AL 31/12/2026"
    vigencia_pattern = re.compile(r"VIGENCIA(?: DEL BENEFICIO)?\s*(?:DESDE EL|DESDE)?\s*([\d/]+\s*(?:hasta el|al)\s*[\d/]+)", re.IGNORECASE)
    # Captura Moneda
    moneda_pattern = re.compile(r"(Dólares|Dólares Estadounidenses|U\$S)", re.IGNORECASE)

    # --- Extracción de Datos ---
    tna_match = tna_pattern.search(terms_text)
    if tna_match:
        data["tna"] = tna_match.group(1)

    tea_match = tea_pattern.search(terms_text)
    if tea_match:
        # El TEA de la cuenta previsional no tiene '%' en el texto original, lo agregamos si falta.
        tea_value = tea_match.group(1)
        if not tea_value.endswith('%'):
            tea_value += '%'
        data["tea"] = tea_value

    monto_match = monto_pattern.search(terms_text)
    if monto_match:
        data["monto_maximo"] = monto_match.group(1)

    vigencia_match = vigencia_pattern.search(terms_text)
    if vigencia_match:
        data["vigencia"] = vigencia_match.group(1).strip()
    
    moneda_match = moneda_pattern.search(terms_text)
    if moneda_match:
        data["moneda"] = "USD"

    return data

def scrape_single_account(name, url):
    """
    Scrapes a single BNA account page for remuneration info.
    """
    result = {
        "nombre_cuenta": name,
        "fuente": url,
        "error": None
    }
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        remuneration_data = parse_remuneration_details(soup)
        
        if remuneration_data.get("error"):
            result["error"] = remuneration_data["error"]
        # El TNA es el dato clave, si no está, consideramos que no hay info de remuneración
        elif not remuneration_data.get("tna"):
            result["error"] = "No se encontraron detalles de remuneración (TNA) en la página."
        
        result.update(remuneration_data)

    except requests.exceptions.RequestException as e:
        result["error"] = f"Error al acceder a la URL: {e}"
    except Exception as e:
        result["error"] = f"Ocurrió un error inesperado: {e}"
        
    return result

def main():
    """
    Main function to scrape all defined BNA accounts and return the data.
    """
    all_results = {}
    
    with ThreadPoolExecutor(max_workers=len(ACCOUNTS_TO_SCRAPE)) as executor:
        future_to_key = {
            executor.submit(scrape_single_account, acc_info["name"], acc_info["url"]): key
            for key, acc_info in ACCOUNTS_TO_SCRAPE.items()
        }
        
        for future in future_to_key:
            key = future_to_key[future]
            try:
                data = future.result()
                if data.get("tna") and "error" in data:
                    data["error"] = None
                all_results[key] = data
            except Exception as e:
                all_results[key] = {
                    "nombre_cuenta": ACCOUNTS_TO_SCRAPE[key]["name"],
                    "fuente": ACCOUNTS_TO_SCRAPE[key]["url"],
                    "error": f"La tarea de scraping falló: {e}"
                }
    return all_results

if __name__ == '__main__':
    scraped_data = main()
    print(json.dumps(scraped_data, indent=2, ensure_ascii=False))

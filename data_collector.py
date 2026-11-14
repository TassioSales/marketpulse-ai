import urllib.request
import json
import os
from datetime import datetime, timedelta

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
CACHE_FILE = os.path.join(DATA_DIR, "market_data.json")

# Series do Banco Central do Brasil (SGS - Sistema Gerenciador de Series Temporais)
SERIES_MAP = {
    "dolar": {
        "code": 1,
        "name": "Dólar Comercial (USD/BRL)",
        "unit": "R$",
        "category": "Câmbio"
    },
    "ipca": {
        "code": 433,
        "name": "IPCA (Inflação Mensal)",
        "unit": "%",
        "category": "Preços"
    },
    "selic": {
        "code": 432,
        "name": "Meta Taxa Selic",
        "unit": "% a.a.",
        "category": "Juros"
    },
    "ic_br_geral": {
        "code": 27741,
        "name": "Índice de Commodities Brasil (IC-Br)",
        "unit": "Índice",
        "category": "Commodities"
    },
    "ic_br_agro": {
        "code": 27742,
        "name": "IC-Br Agropecuária (Grãos/Carnes)",
        "unit": "Índice",
        "category": "Agronegócio"
    }
}

def fetch_bacen_series(code: int, days_back: int = 365):
    """Obtém dados históricos de uma série temporal do Banco Central do Brasil."""
    end_date = datetime.now().strftime("%d/%m/%Y")
    start_date = (datetime.now() - timedelta(days=days_back)).strftime("%d/%m/%Y")
    
    url = f"https://api.bcb.gov.br/dados/serie/bcdata.sgs.{code}/dados?formato=json&dataInicial={start_date}&dataFinal={end_date}"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) MarketPulseAI/1.0"}
    
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=12) as response:
            if response.status == 200:
                raw_data = json.loads(response.read().decode("utf-8"))
                cleaned = []
                for item in raw_data:
                    try:
                        val = float(item["valor"].replace(",", "."))
                        cleaned.append({
                            "date": item["data"],
                            "value": val
                        })
                    except (ValueError, KeyError):
                        continue
                return cleaned
    except Exception as e:
        print(f"Erro ao buscar série BACEN #{code}: {e}")
        return []

def update_all_market_data(days_back: int = 365, force: bool = False):
    """Atualiza todas as séries e grava o cache local."""
    os.makedirs(DATA_DIR, exist_ok=True)
    
    # Checar se cache e recente (menos de 6 horas)
    if not force and os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                cached = json.load(f)
            last_updated = datetime.fromisoformat(cached.get("last_updated", "2000-01-01T00:00:00"))
            if datetime.now() - last_updated < timedelta(hours=6):
                return cached
        except Exception:
            pass

    print("[MarketPulse Data] Atualizando indicadores econômicos do Banco Central...")
    dataset = {
        "last_updated": datetime.now().isoformat(),
        "series": {}
    }
    
    for key, info in SERIES_MAP.items():
        data = fetch_bacen_series(info["code"], days_back=days_back)
        dataset["series"][key] = {
            "name": info["name"],
            "unit": info["unit"],
            "category": info["category"],
            "code": info["code"],
            "count": len(data),
            "data": data
        }
    
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(dataset, f, indent=2, ensure_ascii=False)
        
    print(f"[MarketPulse Data] Sucesso! {len(dataset['series'])} séries sincronizadas.")
    return dataset

if __name__ == "__main__":
    data = update_all_market_data(force=True)
    print("Séries carregadas:")
    for k, v in data["series"].items():
        print(f" - {v['name']}: {v['count']} pontos históricos")

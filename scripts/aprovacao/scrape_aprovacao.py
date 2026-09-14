"""
Scraper para dados de aprovação/desaprovação do governo Lula 3
Fonte: widget "Compara Pesquisas" do site Meio (canalmeio.com.br), aba "Aprovação de governo"

O widget carrega os dados de um endpoint público do Google Apps Script que
retorna JSON com a lista de pesquisas por instituto (campo "institutos").
Este é um endpoint distinto do usado pela aba "Avaliação de governo"
(que traz Ótimo/Bom vs Ruim/Péssimo, uma pergunta diferente da pesquisa).

Gera: data/aprovacao/pesquisas_aprovacao.json
"""
import json
from datetime import datetime, timedelta
from pathlib import Path

import requests

DATA_URL = "https://script.google.com/macros/s/AKfycbzS0rv0-qtQNaAOkR5foudC4RXh8XCOh47tkv4HpAGR61FLh-dG7gAKLmS_LZjh3Zu7jw/exec"
OUT_FILE = Path("data/aprovacao/pesquisas_aprovacao.json")

MIN_DATE = datetime(2023, 1, 1)


def parse_date(date_str):
    """Parseia datas no formato YYYY-MM-DD, descartando valores malformados."""
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str.strip()[:10], "%Y-%m-%d")
    except ValueError:
        return None


def main():
    print("Baixando dados de aprovação de governo...")
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

    try:
        response = requests.get(DATA_URL, headers=headers, timeout=30)
        response.raise_for_status()
        payload = response.json()
    except Exception as e:
        print(f"Erro ao baixar dados: {e}")
        return

    institutos = payload.get("institutos", [])
    print(f"Registros brutos recebidos: {len(institutos)}")

    today = datetime.now()
    max_allowed_date = today + timedelta(days=1)

    registros = []
    descartados = 0
    for item in institutos:
        data_parsed = parse_date(item.get("Date"))
        aprova = item.get("Positive")
        desaprova = item.get("Negative")
        instituto = item.get("Institute")

        if data_parsed is None or data_parsed < MIN_DATE or data_parsed > max_allowed_date:
            descartados += 1
            continue
        if not instituto:
            descartados += 1
            continue

        try:
            aprova = float(aprova)
            desaprova = float(desaprova)
        except (TypeError, ValueError):
            descartados += 1
            continue

        registros.append({
            "instituto": instituto,
            "data": data_parsed.strftime("%Y-%m-%d"),
            "candidatos": {
                "Aprova": aprova,
                "Desaprova": desaprova,
            }
        })

    # Ordena por data (mais recente primeiro, igual aos demais datasets do projeto)
    registros.sort(key=lambda r: r["data"], reverse=True)

    print(f"Registros válidos: {len(registros)} (descartados: {descartados})")

    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(registros, f, ensure_ascii=False, indent=2)

    print(f"✓ Dados salvos em '{OUT_FILE}'")


if __name__ == "__main__":
    main()

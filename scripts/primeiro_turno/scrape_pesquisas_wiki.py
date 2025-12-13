"""
Scraper para pesquisas eleitorais de 2026 no Brasil a partir da Wikipedia (EN):
https://en.wikipedia.org/wiki/Opinion_polling_for_the_2026_Brazilian_presidential_election

Gera: data/pesquisas_2026.json
"""
import requests
from bs4 import BeautifulSoup
import pandas as pd
import json
from pathlib import Path
import re

WIKI_URL = "https://en.wikipedia.org/wiki/Opinion_polling_for_the_2026_Brazilian_presidential_election"
OUT_FILE = Path("data/primeiro_turno/pesquisas_2026.json")

# Função utilitária para limpar nomes de candidatos
def clean_candidate(name):
    name = re.sub(r"\[.*?\]", "", name)
    name = re.sub(r"\(.*?\)", "", name)
    return name.strip()

def extract_year(date_str):
    """Extrai o ano de uma string de data"""
    if not date_str:
        return None
    match = re.search(r'\d{4}', date_str)
    return int(match.group()) if match else None

def main():
    print("Baixando página...")
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
    html = requests.get(WIKI_URL, headers=headers).text
    soup = BeautifulSoup(html, "lxml")
    pesquisas = []
    seen = set()  # Track (instituto, data) pairs to avoid duplicates
    tables = soup.find_all("table")
    print(f"Tabelas encontradas: {len(tables)}")
    for table in tables:
        rows = table.find_all("tr")
        if not rows or len(rows) < 2:
            continue
        # Extrair cabeçalhos reais dos candidatos
        header_cells = rows[0].find_all(["td", "th"])
        header_texts = [clean_candidate(c.get_text(strip=True)) for c in header_cells]
        for row in rows[1:]:
            cells = row.find_all(["td", "th"])
            if len(cells) < 2:
                continue
            # Use minimum of header count and cell count to handle variable row lengths
            cell_count = min(len(header_texts), len(cells))
            cell_texts = [c.get_text(strip=True) for c in cells]
            instituto = cell_texts[0]
            data = cell_texts[1]
            
            # Skip rows with invalid dates (must contain month name or be in proper date format)
            # Valid patterns: "6–9 Nov 2025", "29 Sep – 6 Oct 2025", etc.
            if not data or len(data) < 5:
                continue
            valid_date = False
            months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec',
                     'January', 'February', 'March', 'April', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
            for month in months:
                if month in data:
                    valid_date = True
                    break
            if not valid_date:
                continue
            
            # Filtrar apenas pesquisas de 2025 em diante
            year = extract_year(data)
            if not year or year < 2025:
                continue
            
            # Skip duplicate (instituto, data) pairs
            poll_key = (instituto, data)
            if poll_key in seen:
                continue
            seen.add(poll_key)
            
            candidatos = {}
            for i in range(2, cell_count):
                if i >= len(cell_texts):
                    continue
                cand_name = header_texts[i]
                val = cell_texts[i]
                try:
                    pct = float(str(val).replace('%','').replace(',','.'))
                    if cand_name:
                        candidatos[cand_name] = pct
                except Exception:
                    continue
            if candidatos:
                pesquisa = {
                    "instituto": instituto,
                    "data": data,
                    "candidatos": candidatos
                }
                pesquisas.append(pesquisa)
    print(f"Registros extraídos: {len(pesquisas)}")
    OUT_FILE.write_text(json.dumps(pesquisas, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Arquivo gerado: {OUT_FILE}")

if __name__ == "__main__":
    main()

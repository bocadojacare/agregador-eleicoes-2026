"""
Scraper para pesquisas eleitorais de 2026 no Brasil a partir da Wikipedia (EN):
https://en.wikipedia.org/wiki/Opinion_polling_for_the_2026_Brazilian_presidential_election

Gera: public/pesquisas_2026.json
"""
import requests
from bs4 import BeautifulSoup
import pandas as pd
import json
from pathlib import Path

WIKI_URL = "https://en.wikipedia.org/wiki/Opinion_polling_for_the_2026_Brazilian_presidential_election"
OUT_FILE = Path("pesquisas_2026.json")

# Função utilitária para limpar nomes de candidatos
import re
def clean_candidate(name):
    name = re.sub(r"\[.*?\]", "", name)
    name = re.sub(r"\(.*?\)", "", name)
    return name.strip()

def main():
    print("Baixando página...")
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
    html = requests.get(WIKI_URL, headers=headers).text
    soup = BeautifulSoup(html, "lxml")
    pesquisas = []
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
            if len(cells) != len(header_texts):
                continue
            if len(cells) < 2:
                continue
            cell_texts = [c.get_text(strip=True) for c in cells]
            instituto = cell_texts[0]
            data = cell_texts[1]
            candidatos = {}
            for i in range(2, len(header_texts)):
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

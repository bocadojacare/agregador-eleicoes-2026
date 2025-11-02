"""
Scraper para pesquisas do segundo turno (Lula vs Tarcísio) de 2026 no Brasil
Fonte: https://en.wikipedia.org/wiki/Opinion_polling_for_the_2026_Brazilian_presidential_election

Gera: data/segundo_turno/pesquisas_segundo_turno.json
"""
import requests
from bs4 import BeautifulSoup
import pandas as pd
import json
from pathlib import Path
import re

WIKI_URL = "https://en.wikipedia.org/wiki/Opinion_polling_for_the_2026_Brazilian_presidential_election"
OUT_FILE = Path("data/segundo_turno/pesquisas_segundo_turno.json")

def parse_percentage(s):
    """Converte string de percentual para float"""
    if not s or s.strip() == '–' or s.strip() == '' or s.strip() == '—':
        return None
    try:
        return float(s.strip().replace('%', '').replace(',', '.'))
    except:
        return None

def extract_year(date_str):
    """Extrai o ano de uma string de data"""
    if not date_str or date_str.strip() == '—' or date_str.strip() == '–':
        return None
    match = re.search(r'\d{4}', date_str)
    return int(match.group()) if match else None

def is_valid_poll_row(cells_text):
    """
    Checks if a row contains valid poll data with both candidates.
    Returns True only if it has proper instituto, date, and two numeric values (Lula and Tarcísio).
    """
    if len(cells_text) < 4:
        return False
    
    instituto = cells_text[0].strip()
    data = cells_text[1].strip()
    
    # Instituto should not be a number or empty
    if not instituto or instituto.replace('.', '').replace(',', '').replace('–', '').replace('—', '').replace('-', '').isdigit():
        return False
    
    # Data should contain a year
    if not data or '—' in data or (data.isdigit() and len(data) < 4):
        return False
    
    # Should have at least 2 numeric values after instituto and data
    numeric_count = 0
    for i in range(2, len(cells_text)):
        val = parse_percentage(cells_text[i])
        if val is not None:
            numeric_count += 1
    
    return numeric_count >= 2

print("SCRAPING DADOS DO SEGUNDO TURNO (Lula vs Tarcísio)")
print("=" * 80)

try:
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    response = requests.get(WIKI_URL, timeout=10, headers=headers)
    response.raise_for_status()
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Procurar pela seção "Second round"
    tables = soup.find_all('table', {'class': 'wikitable'})
    print(f"✓ Encontradas {len(tables)} tabelas na página")
    
    pesquisas = []
    found_tables = []
    
    # Buscar apenas PRIMEIRA tabela do segundo turno com dados válidos de 2026
    for table_idx, table in enumerate(tables):
        # Verificar se é a tabela do segundo turno
        # Procurar por "Second round" ou "Runoff" nas headers
        table_headers = [th.get_text(strip=True).lower() for th in table.find_all('th')]
        
        if any(term in str(table_headers).lower() for term in ['second', 'runoff', 'lula', 'tarcísio', 'freitas']):
            print(f"\n  Processando tabela {table_idx} (possível segunda volta)")
            
            rows = table.find_all('tr')
            table_pesquisas = []
            table_years = []
            seen_polls = set()  # Track (instituto, data) pairs to avoid duplicates
            
            for row in rows:
                cols = row.find_all('td')
                if len(cols) < 3:
                    continue
                
                # Extrair informações
                cells_text = [col.get_text(strip=True) for col in cols]
                
                # Validate that this is a proper poll row (not a subrow)
                if not is_valid_poll_row(cells_text):
                    continue
                
                # Tentar identificar: data, instituto, Lula, Tarcísio
                if len(cells_text) >= 4:
                    instituto = cells_text[0]
                    data = cells_text[1]
                    
                    # Skip if we've already seen this instituto/data combination (avoiding subrows)
                    poll_key = (instituto, data)
                    if poll_key in seen_polls:
                        continue
                    
                    # Procurar valores de Lula e Tarcísio
                    lula = None
                    tarcisio = None
                    
                    # Tentar encontrar os valores nas colunas seguintes
                    for i in range(2, len(cells_text)):
                        val = parse_percentage(cells_text[i])
                        if val is not None:
                            if lula is None:
                                lula = val
                            elif tarcisio is None:
                                tarcisio = val
                                break
                    
                    # Validar dados - só pegar dados de 2025 e 2026
                    year = extract_year(data)
                    if data and instituto and lula is not None and tarcisio is not None and year and year >= 2025:
                        pesquisa = {
                            "data": data,
                            "instituto": instituto,
                            "candidatos": {
                                "Lula": lula,
                                "Freitas": tarcisio
                            }
                        }
                        table_pesquisas.append(pesquisa)
                        table_years.append(year)
                        seen_polls.add(poll_key)
                        print(f"    ✓ {instituto}: {data} - Lula {lula}% | Tarcísio {tarcisio}%")
            
            if table_pesquisas:
                found_tables.append((table_idx, table_pesquisas, table_years))
    
    # Usar apenas a primeira tabela com dados válidos de 2026
    if found_tables:
        # Use table 1 if it exists (it has the correct second round data with higher Lula numbers)
        # Otherwise use table 0
        table_to_use = 1 if len(found_tables) > 1 else 0
        table_idx, table_data, years = found_tables[table_to_use]
        pesquisas = table_data
        print(f"\n✓ Usando tabela {table_idx} (contém dados de 2026+)")
        print(f"✓ {len(pesquisas)} pesquisas extraídas do segundo turno")
        
        # Salvar JSON
        with open(OUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(pesquisas, f, ensure_ascii=False, indent=2)
        print(f"✓ Salvo em: {OUT_FILE}")
    else:
        print("⚠ Nenhuma pesquisa válida do segundo turno de 2026 encontrada.")
        # Criar arquivo vazio como fallback
        OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(OUT_FILE, 'w', encoding='utf-8') as f:
            json.dump([], f)

except Exception as e:
    print(f"❌ Erro ao fazer scraping: {e}")
    import traceback
    traceback.print_exc()

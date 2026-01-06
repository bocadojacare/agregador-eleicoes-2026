"""
Scraper para pesquisas do segundo turno (Lula vs Tarcísio) de 2026 no Brasil
Fonte: https://en.wikipedia.org/wiki/Opinion_polling_for_the_2026_Brazilian_presidential_election

Gera: data/segundo_turno/pesquisas_segundo_turno.json
"""
import sys
import io
import requests
from bs4 import BeautifulSoup
import pandas as pd
import json
from pathlib import Path
import re

# Fix Unicode output on Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

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
            seen_polls = set()  # Track (instituto, data) pairs after finding Lula vs Freitas
            
            # Get header row to find column indices for Lula and Freitas
            header_cols = table.find_all('th')
            lula_idx = None
            freitas_idx = None
            
            for idx, th in enumerate(header_cols):
                th_text = th.get_text(strip=True).lower()
                if 'lula' in th_text:
                    lula_idx = idx
                elif 'freitas' in th_text or 'tarcísio' in th_text or 'tarcisio' in th_text:
                    freitas_idx = idx
            
            # Group rows by instituto+data (each poll has multiple rows for different matchups)
            current_instituto = None
            current_data = None
            
            for row in rows:
                cols = row.find_all('td')
                if len(cols) < 3:
                    continue
                
                # Extrair informações
                cells_text = [col.get_text(strip=True) for col in cols]
                
                # Check if this is a new poll (has instituto and data in first two cells)
                # or a continuation row (empty first cells, or numeric/N/a values)
                first_cell = cells_text[0]
                second_cell = cells_text[1]
                
                # A new poll row has both instituto name (text, not just numbers) and a date
                # Continuation rows have empty cells, or numeric values, or just "N/a"
                is_new_poll = (first_cell and second_cell and 
                              not first_cell.replace('.', '').replace(',', '').replace('–', '').replace('N/a', '').strip().isdigit() and
                              not first_cell in ['–N/a', 'N/a'] and
                              len(first_cell) > 3)  # Instituto names are longer than 3 chars
                
                if is_new_poll:
                    current_instituto = first_cell
                    current_data = second_cell
                # Otherwise, this is a continuation row using previous instituto/data
                
                if not current_instituto or not current_data:
                    continue
                
                # Extract Lula and Freitas by their column indices if found
                # ONLY extract if BOTH columns have valid data (to skip Lula vs Bolsonaro rows)
                lula = None
                tarcisio = None
                
                # For continuation rows (where first cells are empty or numeric),
                # the columns are shifted left by 2 (no instituto/date columns)
                lula_col = lula_idx
                freitas_col = freitas_idx
                
                if not is_new_poll and lula_idx is not None and lula_idx >= 2:
                    lula_col = lula_idx - 2
                    freitas_col = freitas_idx - 2 if freitas_idx else None
                
                # If we found column indices, use them directly
                if lula_col is not None and lula_col < len(cells_text):
                    lula = parse_percentage(cells_text[lula_col])
                if freitas_col is not None and freitas_col < len(cells_text):
                    tarcisio = parse_percentage(cells_text[freitas_col])
                
                # CRITICAL: Only proceed if BOTH Lula and Freitas columns have values
                # This ensures we skip rows that are Lula vs Bolsonaro or other matchups
                if lula is None or tarcisio is None:
                    continue
                
                # Skip if we've already found Lula vs Freitas for this poll
                poll_key = (current_instituto, current_data)
                if poll_key in seen_polls:
                    continue
                
                # Validar dados - só pegar dados de 2025 e 2026
                year = extract_year(current_data)
                if current_instituto and current_data and year and year >= 2025:
                    pesquisa = {
                        "data": current_data,
                        "instituto": current_instituto,
                        "candidatos": {
                            "Lula": lula,
                            "Freitas": tarcisio
                        }
                    }
                    table_pesquisas.append(pesquisa)
                    table_years.append(year)
                    seen_polls.add(poll_key)
                    print(f"    ✓ {current_instituto}: {current_data} - Lula {lula}% | Tarcísio {tarcisio}%")
            
            if table_pesquisas:
                found_tables.append((table_idx, table_pesquisas, table_years))
    
    # Use only the proper second round/runoff table (Table 2)
    # Table 0 and 1 have first round multi-candidate scenarios, not head-to-head runoffs
    if found_tables:
        # Find the table with highest average Lula+Freitas combined percentage (indicates runoff, not first round)
        best_table_idx = None
        highest_avg = 0
        
        for table_idx, table_data, years in found_tables:
            if len(table_data) > 0:
                avg_combined = sum(p['candidatos']['Lula'] + p['candidatos']['Freitas'] for p in table_data) / len(table_data)
                print(f"\n✓ Tabela {table_idx}: {len(table_data)} pesquisas, média combinada: {avg_combined:.1f}%")
                if avg_combined > highest_avg:
                    highest_avg = avg_combined
                    best_table_idx = table_idx
        
        # Get the data from the best table
        pesquisas = []
        for table_idx, table_data, years in found_tables:
            if table_idx == best_table_idx:
                pesquisas = table_data
                break
        
        print(f"\n✓ Usando tabela {best_table_idx} (dados de segundo turno válidos)")
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

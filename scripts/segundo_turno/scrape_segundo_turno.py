"""
Scraper para pesquisas do segundo turno (Lula vs Flávio) de 2026 no Brasil
Fonte: https://pt.wikipedia.org/wiki/Pesquisas_de_opinião_para_a_eleição_presidencial_no_Brasil_em_2026

Especificamente extrai as tabelas da seção "Segundo Turno > Lula e Flávio Bolsonaro"
Gera: data/segundo_turno/pesquisas_segundo_turno.json
"""
import requests
from bs4 import BeautifulSoup
import pandas as pd
import json
from pathlib import Path
import re
import io
from datetime import datetime, timedelta

WIKI_URL = "https://pt.wikipedia.org/wiki/Pesquisas_de_opinião_para_a_eleição_presidencial_no_Brasil_em_2026"
OUT_FILE = Path("data/segundo_turno/pesquisas_segundo_turno.json")

CANDIDATE_WHITELIST = {"Lula", "Flávio"}

def clean_candidate(name):
    """Remove brackets, parties, and extra text from candidate names"""
    name = str(name)
    name = name.replace('ß', 'á').replace('├', 'a').replace('Û', 'u').replace('Ý', 'i')
    name = name.replace('þ', 'p').replace('·', '').replace('Ø', 'o')
    name = re.sub(r"\[.*?\]", "", name)
    name = re.sub(r"\(.*?\)", "", name)
    name = re.sub(r'(PT|PL|PSD|PSB|PSDB|PSOL|PSC|PRB|PDT|PP|PCdoB|DEM|Cidadania|PCO|PSTU|NOVO|MDB|Solidariedade|Patriota|UP|PRTB|MIS|MISSÃ|MISSÃO|UNIÃO|DC|Republicans|Republicanos|UNIAO)$', '', name)
    return name.strip()

def normalize_percentage(val):
    """Convert percentage string to float"""
    if val is None or val == '':
        return None
    if isinstance(val, str):
        val = val.replace('%', '').strip()
        if not val or val == '-':
            return None
        val = val.replace(',', '.')
    try:
        return float(val)
    except:
        return None


def extract_institute_date(row_text):
    """Extract institute name and date from text"""
    match = re.search(r'^([^(\[]+)(?:\[\d+\])?\s*(?:\()?(\d{1,2}\s+\w+\s*(?:–|-)\s*\d{1,2}\s+\w+(?:\s+\d{4})?)\)?', str(row_text))
    if match:
        institute = match.group(1).strip()
        date = match.group(2).strip()
        return institute, date
    return None, None

def parse_date_with_year(date_str, fallback_year=None):
    """Parse date string and infer year, preferring subsection year when available."""
    today = datetime.now()

    month_abbrev = {
        'jan': 1, 'fev': 2, 'mar': 3, 'abr': 4, 'mai': 5, 'jun': 6,
        'jul': 7, 'ago': 8, 'set': 9, 'out': 10, 'nov': 11, 'dez': 12,
        'janeiro': 1, 'fevereiro': 2, 'março': 3, 'abril': 4, 'maio': 5, 'junho': 6,
        'julho': 7, 'agosto': 8, 'setembro': 9, 'outubro': 10, 'novembro': 11, 'dezembro': 12
    }
    
    year_match = re.search(r'(\d{4})', date_str)
    if year_match:
        year = int(year_match.group(1))
    elif fallback_year is not None:
        year = int(fallback_year)
    else:
        month_lower = date_str.lower()
        found_month = None
        for month_name, month_num in month_abbrev.items():
            if month_name in month_lower:
                found_month = month_num
                break
        
        if not found_month:
            return None, None
        
        # Infer year relative to current month with year rollover.
        year = today.year
        if found_month > today.month + 1:
            year -= 1
    
    date_with_year = f"{date_str} {year}" if not re.search(r'\d{4}', date_str) else date_str
    
    month_names_full = {
        'janeiro': 'January', 'fevereiro': 'February', 'março': 'March', 'abril': 'April',
        'maio': 'May', 'junho': 'June', 'julho': 'July', 'agosto': 'August',
        'setembro': 'September', 'outubro': 'October', 'novembro': 'November', 'dezembro': 'December',
        'jan': 'Jan', 'fev': 'Feb', 'mar': 'Mar', 'abr': 'Apr', 'mai': 'May', 'jun': 'Jun',
        'jul': 'Jul', 'ago': 'Aug', 'set': 'Sep', 'out': 'Oct', 'nov': 'Nov', 'dez': 'Dec'
    }
    
    date_for_parsing = date_with_year
    for pt_month, en_month in month_names_full.items():
        date_for_parsing = re.sub(rf'\b{pt_month}\b', en_month, date_for_parsing, flags=re.IGNORECASE)
    
    # Extract END date from range
    date_parts_match = re.search(r'(?:–|-)\s*(\d{1,2})\s+(\w+)(?:\s+(\d{4}))?', date_for_parsing)
    if date_parts_match:
        day_str = date_parts_match.group(1)
        month_str = date_parts_match.group(2)
        
        year_in_range = date_parts_match.group(3)
        if year_in_range:
            year = int(year_in_range)
        else:
            year_in_str = re.search(r'(\d{4})', date_for_parsing)
            if year_in_str:
                year = int(year_in_str.group(1))
        
        try:
            parsed_date = datetime.strptime(f"{day_str} {month_str} {year}", "%d %b %Y")
        except ValueError:
            try:
                parsed_date = datetime.strptime(f"{day_str} {month_str.title()} {year}", "%d %B %Y")
            except ValueError:
                return None, None
        
        max_allowed_date = today + timedelta(days=1)
        min_date = datetime(2025, 11, 10)
        
        if parsed_date > max_allowed_date or parsed_date < min_date:
            return None, None
        
        return date_with_year, parsed_date
    
    return None, None

def main():
    print("Baixando página...")
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    
    try:
        response = requests.get(WIKI_URL, headers=headers)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')
    except Exception as e:
        print(f"Erro ao baixar página: {e}")
        return
    
    # Find the "Segundo Turno" section heading
    segundo_turno_heading = None
    for heading in soup.find_all(['h2']):
        if 'Segundo turno' in heading.get_text():
            segundo_turno_heading = heading
            break
    
    if not segundo_turno_heading:
        print("❌ Seção 'Segundo Turno' não encontrada")
        return
    
    print("✓ Seção 'Segundo Turno' encontrada")
    
    # Find the "Lula e Flávio Bolsonaro" subsection
    lula_flavio_heading = None
    current = segundo_turno_heading.find_next()
    while current:
        if current.name and current.name in ['h3', 'h2']:
            text = current.get_text()
            if 'Lula' in text and 'Flávio' in text:
                lula_flavio_heading = current
                break
            elif current.name == 'h2':
                # Reached next major section
                break
        current = current.find_next()
    
    if not lula_flavio_heading:
        print("❌ Seção 'Lula e Flávio' não encontrada")
        return
    
    print("✓ Seção 'Lula e Flávio' encontrada")
    
    # Extract tables between this heading and the next h3/h2, while tracking the year subsection.
    tables_content = []
    current_subsection_year = None
    current = lula_flavio_heading.find_next()
    while current:
        if current.name in ['h3', 'h2']:
            break
        if current.name == 'h4':
            heading_text = current.get_text(strip=True)
            if re.fullmatch(r'\d{4}', heading_text):
                current_subsection_year = int(heading_text)
        if current.name == 'table':
            tables_content.append((str(current), current_subsection_year))
        current = current.find_next()
    
    if not tables_content:
        print("❌ Nenhuma tabela encontrada na seção")
        return
    
    print(f"✓ {len(tables_content)} tabelas encontradas na seção 'Lula e Flávio'")
    
    # Process each table
    polls_by_date = {}
    
    for table_idx, table_info in enumerate(tables_content):
        table_html, subsection_year = table_info
        try:
            dfs = pd.read_html(io.StringIO(table_html), match="Contratante")
            
            for df in dfs:
                if len(df) < 3 or len(df.columns) < 6:
                    continue
                
                print(f"\n  Tabela {table_idx}: {df.shape[0]} rows x {df.shape[1]} cols")
                
                # Handle MultiIndex columns
                if isinstance(df.columns, pd.MultiIndex):
                    headers_list = []
                    for col in df.columns:
                        if isinstance(col, tuple) and len(col) > 1:
                            headers_list.append(str(col[1]))
                        else:
                            headers_list.append(str(col[0] if isinstance(col, tuple) else col))
                else:
                    headers_list = list(df.columns)
                
                # Find candidate columns
                candidate_cols = {}
                for col_idx, col_name in enumerate(headers_list):
                    col_clean = clean_candidate(str(col_name))
                    for candidate in CANDIDATE_WHITELIST:
                        if candidate.lower() in col_clean.lower() or col_clean.lower() in candidate.lower():
                            candidate_cols[col_idx] = candidate
                            break
                
                if not candidate_cols or len(candidate_cols) < 2:
                    continue
                
                print(f"    Candidatos: {list(candidate_cols.values())}")
                
                # Process data rows
                for row_idx, row in df.iterrows():
                    inst_col = row.iloc[0] if len(row) > 0 else None
                    date_col = row.iloc[1] if len(row) > 1 else None
                    
                    if not inst_col or pd.isna(inst_col):
                        continue
                    
                    institute, date = extract_institute_date(inst_col)
                    
                    if not institute or not date:
                        if str(date_col) and not pd.isna(date_col):
                            institute, date = extract_institute_date(f"{inst_col} {date_col}")
                    
                    if not institute or not date:
                        continue
                    
                    # Extract candidate percentages
                    candidatos = {}
                    for col_idx, candidate in candidate_cols.items():
                        if col_idx < len(row):
                            val = normalize_percentage(row.iloc[col_idx])
                            if val is not None:
                                candidatos[candidate] = val
                    
                    if not candidatos:
                        continue
                    
                    data_with_year, parsed_date = parse_date_with_year(date, fallback_year=subsection_year)
                    
                    if not data_with_year:
                        continue
                    
                    # Must have BOTH Lula and Flávio.
                    if not ("Lula" in candidatos and "Flávio" in candidatos):
                        continue
                    
                    poll_key = (institute, data_with_year)
                    
                    if poll_key not in polls_by_date:
                        polls_by_date[poll_key] = {
                            "instituto": institute,
                            "data": data_with_year,
                            "candidatos": candidatos
                        }
                        print(f"      [OK] {institute} ({data_with_year})")
        
        except Exception as e:
            print(f"  ⚠ Erro processando tabela {table_idx}: {e}")
            continue
    
    pesquisas = list(polls_by_date.values())
    
    print(f"\n✓ Registros extraídos: {len(pesquisas)}")
    OUT_FILE.write_text(json.dumps(pesquisas, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✓ Arquivo gerado: {OUT_FILE}")

if __name__ == "__main__":
    main()

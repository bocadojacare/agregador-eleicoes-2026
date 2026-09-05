"""
Scraper para pesquisas eleitorais de 2026 no Brasil a partir da Wikipedia (PT).
Reescrito para usar pandas.read_html que lida corretamente com colspan/rowspan.
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
OUT_FILE = Path("data/primeiro_turno/pesquisas_2026.json")

CANDIDATE_WHITELIST = {"Lula", "Flávio", "Caiado", "Zema", "Renan", "Cury", "Samara"}

def clean_candidate(name):
    """Remove brackets, parties, and extra text from candidate names"""
    name = str(name)
    
    # Fix encoding issues common in Wikipedia scraping
    name = name.replace('ß', 'á').replace('├', 'a').replace('Û', 'u').replace('Ý', 'i')
    name = name.replace('þ', 'p').replace('·', '').replace('Ø', 'o')
    
    name = re.sub(r"\[.*?\]", "", name)
    name = re.sub(r"\(.*?\)", "", name)
    # Remove party suffixes
    name = re.sub(r'(PT|PL|PSD|PSB|PSDB|PSOL|PSC|PRB|PDT|PP|PCdoB|DEM|Cidadania|PCO|PSTU|NOVO|MDB|Solidariedade|Patriota|UP|PRTB|MIS|MISSÃ|MISSÃO|UNIÃO|DC|Republicans|Republicanos|UNIAO)$', '', name)
    return name.strip()

def normalize_percentage(val):
    """Convert percentage string to float"""
    if val is None or val == '':
        return None
    if isinstance(val, str):
        # Brazilian format: 40,5% or 40,5
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
    # Format: "Instituto[XX] (DD Mês - DD Mês YYYY)" or "Instituto DD Mês - DD Mês"
    row_text = re.sub(r"\[\d+\]", "", str(row_text))
    match = re.search(r'^([^(\[]+)(?:\[\d+\])?\s*(?:\()?(\d{1,2}\s+\w+\s*(?:–|-)\s*\d{1,2}\s+\w+(?:\s+\d{4})?)\)?', str(row_text))
    if match:
        institute = match.group(1).strip()
        date = match.group(2).strip()
        return institute, date
    return None, None

def extract_institute_date(row_text):
    row_text = re.sub(r"\[[0-9]+\]", "", str(row_text))
    match = re.search(r'^([^()]+?)[ ]*[(]?([0-9]{1,2}[ ]+[A-Za-zÀ-ÿ]+[ ]*(?:–|-)[ ]*[0-9]{1,2}[ ]+[A-Za-zÀ-ÿ]+(?:[ ]+[0-9]{4})?)[)]?', row_text)
    if match:
        return match.group(1).strip(), match.group(2).strip()
    return None, None

def parse_date_with_year(date_str):
    """
    Parse date string and infer year. Returns (date_str_with_year, parsed_date) or (None, None) if invalid.
    Only includes polls from November 10, 2025 onwards.
    """
    today = datetime.now()

    # If already has year, use it
    year_match = re.search(r'(\d{4})', date_str)
    if year_match:
        year = int(year_match.group(1))
    else:
        # Infer year based on month
        month_abbrev = {
            'jan': 1, 'fev': 2, 'mar': 3, 'abr': 4, 'mai': 5, 'jun': 6,
            'jul': 7, 'ago': 8, 'set': 9, 'out': 10, 'nov': 11, 'dez': 12,
            'janeiro': 1, 'fevereiro': 2, 'março': 3, 'abril': 4, 'maio': 5, 'junho': 6,
            'julho': 7, 'agosto': 8, 'setembro': 9, 'outubro': 10, 'novembro': 11, 'dezembro': 12
        }
        
        date_lower = date_str.lower()
        found_month = None
        for month_name, month_num in month_abbrev.items():
            if month_name in date_lower:
                found_month = month_num
                break
        
        if not found_month:
            return None, None
        
        # Infer year relative to current month with year rollover.
        # Example: if today is April and we see "Nov" without year, it likely refers to previous year.
        year = today.year
        if found_month > today.month + 1:
            year -= 1
    
    # Now try to parse the full date
    date_with_year = f"{date_str} {year}" if not re.search(r'\d{4}', date_str) else date_str
    
    # Try to parse with common Brazilian date formats
    month_names_full = {
        'janeiro': 'January', 'fevereiro': 'February', 'março': 'March', 'abril': 'April',
        'maio': 'May', 'junho': 'June', 'julho': 'July', 'agosto': 'August',
        'setembro': 'September', 'outubro': 'October', 'novembro': 'November', 'dezembro': 'December',
        'jan': 'Jan', 'fev': 'Feb', 'mar': 'Mar', 'abr': 'Apr', 'mai': 'May', 'jun': 'Jun',
        'jul': 'Jul', 'ago': 'Aug', 'set': 'Sep', 'out': 'Oct', 'nov': 'Nov', 'dez': 'Dec'
    }
    
    # Convert Portuguese month names to English for parsing
    date_for_parsing = date_with_year
    for pt_month, en_month in month_names_full.items():
        date_for_parsing = re.sub(rf'\b{pt_month}\b', en_month, date_for_parsing, flags=re.IGNORECASE)
    
    # Try to extract the END date (last date in range like "6 Nov - 9 Nov 2026" -> use 9 Nov 2026)
    # This ensures we include polls that end after the minimum date, even if they start before
    date_parts_match = re.search(r'(?:–|-)\s*(\d{1,2})\s+(\w+)(?:\s+(\d{4}))?', date_for_parsing)
    if date_parts_match:
        day_str = date_parts_match.group(1)
        month_str = date_parts_match.group(2)
        
        # Extract year if present in the date range, otherwise from full string
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
                # Try full month names
                parsed_date = datetime.strptime(f"{day_str} {month_str.title()} {year}", "%d %B %Y")
            except ValueError:
                return None, None
        
        # Reject dates too far in the future or before the supported window start.
        max_allowed_date = today + timedelta(days=1)
        min_date = datetime(2025, 11, 10)  # Start from Nov 10, 2025 (first poll with both Lula and Flávio)
        
        if parsed_date > max_allowed_date or parsed_date < min_date:
            return None, None  # Reject future dates or dates before Nov 8, 2025
        
        return date_with_year, parsed_date
    
    return None, None

def main():
    print("Baixando página...")
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    
    # Use pandas to read HTML tables
    try:
        # Fetch HTML directly with proper encoding
        response = requests.get(WIKI_URL, headers=headers)
        response.encoding = 'utf-8'
        
        # Read tables from HTML string
        dfs = pd.read_html(io.StringIO(response.text), match="Contratante")
    except Exception as e:
        print(f"Erro ao ler tabelas: {e}")
        import traceback
        traceback.print_exc()
        return
    
    print(f"Tabelas encontradas: {len(dfs)}")
    
    # Collect all polls by (institute, date) and keep only those with BOTH Lula and Flávio
    # If multiple scenarios for same date, keep the one with most candidates
    polls_by_date = {}  # key: (institute, data_with_year) -> best poll with Lula+Flávio

    # Preserve the local history because Wikipedia now exposes only recent monthly tables.
    if OUT_FILE.exists():
        try:
            existing_polls = json.loads(OUT_FILE.read_text(encoding="utf-8"))
            for poll in existing_polls:
                candidatos = poll.get("candidatos", {})
                if poll.get("instituto") and poll.get("data") and candidatos:
                    poll_key = (poll["instituto"], poll["data"])
                    polls_by_date[poll_key] = {
                        "instituto": poll["instituto"],
                        "data": poll["data"],
                        "candidatos": candidatos,
                        "num_candidates": len(candidatos)
                    }
            print(f"Histórico local preservado: {len(polls_by_date)} registros")
        except (json.JSONDecodeError, OSError) as e:
            print(f"Aviso: não foi possível carregar o histórico local: {e}")
    
    for table_idx, df in enumerate(dfs):
        # Skip very small tables
        if len(df) < 3 or len(df.columns) < 6:
            continue
        
        print(f"\nTabela {table_idx}: {df.shape[0]} rows x {df.shape[1]} cols")
        
        # Handle MultiIndex columns (from colspan in HTML tables)
        if isinstance(df.columns, pd.MultiIndex):
            # Flatten multi-index by taking the second level (usually has candidate names)
            headers_list = []
            for col in df.columns:
                # col is a tuple like ('Unnamed: 5_level_0', 'Flávio PL', 'Unnamed: 5_level_2')
                # Take the second element which is usually the candidate name
                if isinstance(col, tuple) and len(col) > 1:
                    headers_list.append(str(col[1]))
                else:
                    headers_list.append(str(col[0] if isinstance(col, tuple) else col))
        else:
            headers_list = list(df.columns)
        
        print(f"  Headers: {headers_list[:6]}...")
        
        # Find candidate columns by matching header names
        candidate_cols = {}
        for col_idx, col_name in enumerate(headers_list):
            col_clean = clean_candidate(str(col_name))
            for candidate in CANDIDATE_WHITELIST:
                # Match by exact name or by similarity
                if candidate.lower() in col_clean.lower() or col_clean.lower() in candidate.lower():
                    # Store the canonical name from whitelist
                    candidate_cols[col_idx] = candidate
                    break
        
        if not candidate_cols:
            print(f"  Pulando - nenhum candidato encontrado")
            continue
        
        print(f"  Candidatos encontrados: {list(candidate_cols.values())}")
        
        # Process data rows - collect scenarios for each (institute, date)
        for row_idx, row in df.iterrows():
            # First column should be institute name or date
            inst_col = row.iloc[0] if len(row) > 0 else None
            date_col = row.iloc[1] if len(row) > 1 else None
            
            if not inst_col or pd.isna(inst_col):
                continue
            
            institute, date = extract_institute_date(inst_col)
            
            if not institute or not date:
                # Try alternate format
                if str(date_col) and not pd.isna(date_col):
                    institute, date = extract_institute_date(f"{inst_col} {date_col}")
            
            if not institute or not date:
                continue
            
            # Extract candidate percentages for this scenario
            candidatos = {}
            for col_idx, candidate in candidate_cols.items():
                if col_idx < len(row):
                    val = normalize_percentage(row.iloc[col_idx])
                    if val is not None:
                        candidatos[candidate] = val
            
            if candidatos:
                # Parse and validate date (reject future dates)
                data_with_year, parsed_date = parse_date_with_year(date)
                
                if not data_with_year:
                    # Skip if date is invalid or in the future
                    continue
                
                # ONLY accept scenarios with BOTH Lula AND Flávio
                has_lula = "Lula" in candidatos
                has_flavio = "Flávio" in candidatos
                
                if not (has_lula and has_flavio):
                    # Reject scenario without both candidates
                    continue
                
                # Also reject if this looks like a segundo turno (second round) scenario
                # Check if candidate names include "bolsonaro" or reject Lula-only vs Flávio-only matchups
                candidate_str = str(candidatos.keys()).lower()
                if "bolsonaro" in candidate_str or "segundo" in institute.lower():
                    # Skip second round polls
                    continue
                
                # Reject polls with only 2 candidates (likely head-to-head matchups)
                if len(candidatos) < 3:
                    continue
                
                poll_key = (institute, data_with_year)
                num_candidates = len(candidatos)
                
                if poll_key not in polls_by_date:
                    # First scenario for this date (and it has Lula+Flávio)
                    polls_by_date[poll_key] = {
                        "instituto": institute,
                        "data": data_with_year,
                        "candidatos": candidatos,
                        "num_candidates": num_candidates
                    }
                    print(f"    [OK] {institute} ({data_with_year}): {list(candidatos.keys())} ({num_candidates} cand)")
                else:
                    # Replace if this scenario has more candidates
                    if num_candidates > polls_by_date[poll_key]["num_candidates"]:
                        polls_by_date[poll_key] = {
                            "instituto": institute,
                            "data": data_with_year,
                            "candidatos": candidatos,
                            "num_candidates": num_candidates
                        }
                        print(f"    [REPLACE] {institute} ({data_with_year}): {list(candidatos.keys())} ({num_candidates} cand)")
    
    # Convert to final pesquisas list (remove temp fields)
    pesquisas = []
    for poll_data in polls_by_date.values():
        pesquisas.append({
            "instituto": poll_data["instituto"],
            "data": poll_data["data"],
            "candidatos": poll_data["candidatos"]
        })
    
    print(f"\nRegistros extraídos: {len(pesquisas)}")
    OUT_FILE.write_text(json.dumps(pesquisas, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Arquivo gerado: {OUT_FILE}")

if __name__ == "__main__":
    main()

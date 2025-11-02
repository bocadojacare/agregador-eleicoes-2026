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

WIKI_URL = "https://en.wikipedia.org/wiki/Opinion_polling_for_the_2026_Brazilian_presidential_election"
OUT_FILE = Path("data/segundo_turno/pesquisas_segundo_turno.json")

def parse_percentage(s):
    """Converte string de percentual para float"""
    if not s or s.strip() == '–' or s.strip() == '':
        return None
    try:
        return float(s.strip().replace('%', '').replace(',', '.'))
    except:
        return None

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
    
    # Buscar a tabela do segundo turno
    for table_idx, table in enumerate(tables):
        # Verificar se é a tabela do segundo turno
        # Procurar por "Second round" ou "Runoff" nas headers
        headers = [th.get_text(strip=True).lower() for th in table.find_all('th')]
        
        if any(term in str(headers).lower() for term in ['second', 'runoff', 'lula', 'tarcísio', 'freitas']):
            print(f"\n  Processando tabela {table_idx} (possível segunda volta)")
            
            rows = table.find_all('tr')
            
            for row in rows:
                cols = row.find_all('td')
                if len(cols) < 3:
                    continue
                
                # Extrair informações
                cells_text = [col.get_text(strip=True) for col in cols]
                
                # Tentar identificar: data, instituto, Lula, Tarcísio
                if len(cells_text) >= 4:
                    # CORRIGIDO: A ordem está invertida na impressão, mas no JSON quer data primeiro
                    instituto = cells_text[0]
                    data = cells_text[1]
                    
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
                    
                    # Validar dados
                    if data and instituto and lula is not None and tarcisio is not None:
                        pesquisa = {
                            "data": data,
                            "instituto": instituto,
                            "candidatos": {
                                "Lula": lula,
                                "Freitas": tarcisio
                            }
                        }
                        pesquisas.append(pesquisa)
                        print(f"    ✓ {instituto}: {data} - Lula {lula}% | Tarcísio {tarcisio}%")
    
    if pesquisas:
        print(f"\n✓ {len(pesquisas)} pesquisas extraídas do segundo turno")
        
        # Salvar JSON
        with open(OUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(pesquisas, f, ensure_ascii=False, indent=2)
        print(f"✓ Salvo em: {OUT_FILE}")
    else:
        print("⚠ Nenhuma pesquisa do segundo turno encontrada. Verifique a estrutura da tabela.")
        # Criar arquivo vazio como fallback
        OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(OUT_FILE, 'w', encoding='utf-8') as f:
            json.dump([], f)

except Exception as e:
    print(f"❌ Erro ao fazer scraping: {e}")
    import traceback
    traceback.print_exc()

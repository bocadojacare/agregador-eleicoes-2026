"""
Normaliza dados do segundo turno (Lula vs Tarcísio)
- Lê data/segundo_turno/pesquisas_segundo_turno.json
- Formata datas consistentemente
- Salva data/segundo_turno/pesquisas_segundo_turno_normalizado.json
"""
import json
from pathlib import Path
import re

IN_FILE = Path("data/segundo_turno/pesquisas_segundo_turno.json")
OUT_FILE = Path("data/segundo_turno/pesquisas_segundo_turno_normalizado.json")

def normalize_date(date_str):
    """Normaliza formato de data"""
    if not date_str:
        return None
    
    # Remover caracteres especiais de travessão
    date_str = date_str.replace('–', '-').replace('−', '-').replace('–', '-')
    
    # Formato: "15-19 Oct 2025"
    m = re.match(r'(\d{1,2})\s*-\s*(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})', date_str)
    if m:
        return f"{m.group(2)} {m.group(3)} {m.group(4)}"
    
    # Formato: "29 Sep - 6 Oct 2025"
    m = re.match(r'(\d{1,2})\s+([A-Za-z]+)\s*-\s*(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})', date_str)
    if m:
        return f"{m.group(3)} {m.group(4)} {m.group(5)}"
    
    # Formato: "29 Sep 2025"
    m = re.match(r'(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})', date_str)
    if m:
        return f"{m.group(1)} {m.group(2)} {m.group(3)}"
    
    return date_str

print("NORMALIZANDO DADOS DO SEGUNDO TURNO")
print("=" * 80)

try:
    with open(IN_FILE, 'r', encoding='utf-8') as f:
        dados = json.load(f)
    
    print(f"✓ Carregados {len(dados)} registros")
    
    # Normalizar datas
    for pesquisa in dados:
        if 'data' in pesquisa:
            data_original = pesquisa['data']
            pesquisa['data'] = normalize_date(data_original)
    
    # Salvar
    with open(OUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)
    
    print(f"✓ {len(dados)} pesquisas normalizadas")
    print(f"✓ Salvo em: {OUT_FILE}")

except FileNotFoundError:
    print(f"⚠ Arquivo não encontrado: {IN_FILE}")
    print("  Execute scrape_segundo_turno.py primeiro")
except Exception as e:
    print(f"❌ Erro: {e}")
    import traceback
    traceback.print_exc()

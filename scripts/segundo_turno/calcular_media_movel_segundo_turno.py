"""
Calcula médias móveis pré-calculadas para o segundo turno (Lula vs Tarcísio)
- Lê data/segundo_turno/pesquisas_segundo_turno_normalizado.json
- Calcula média móvel com janela de 31 dias
- Salva data/segundo_turno/media_movel_segundo_turno_precalculada.json
"""
import json
import pandas as pd
import numpy as np
from datetime import datetime
import re
from pathlib import Path

def parseDate(str_data):
    """Parse dates in different formats"""
    if not str_data:
        return None
    
    str_data = str_data.replace('–', '-').replace('−', '-').replace('–', '-')
    
    # Formato: "15-19 Oct 2025"
    m = re.match(r'(\d{1,2})\s*-\s*(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})', str_data)
    if m:
        return pd.to_datetime(f"{m.group(3)} {m.group(2)}, {m.group(4)}")
    
    # Formato: "29 Sep - 6 Oct 2025"
    m = re.match(r'(\d{1,2})\s+([A-Za-z]+)\s*-\s*(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})', str_data)
    if m:
        return pd.to_datetime(f"{m.group(4)} {m.group(3)}, {m.group(5)}")
    
    # Formato: "29 Sep 2025"
    m = re.match(r'(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})', str_data)
    if m:
        return pd.to_datetime(f"{m.group(2)} {m.group(1)}, {m.group(3)}")
    
    return None

def calcular_media_movel(valores, datas, window_days=31):
    """Calcula média móvel com interpolação linear"""
    media_movel = []
    msWindow = window_days * 24 * 60 * 60 * 1000
    
    for i, val in enumerate(valores):
        if val is None or datas[i] is None:
            media_movel.append(None)
            continue
        
        base = datas[i]
        sum_val = 0
        cnt = 0
        
        for j in range(len(valores)):
            if valores[j] is None or datas[j] is None:
                continue
            
            if abs((datas[j] - base).total_seconds() * 1000) <= msWindow:
                sum_val += valores[j]
                cnt += 1
        
        media_movel.append(float(sum_val / cnt) if cnt > 0 else None)
    
    # Interpolação linear
    for i in range(len(media_movel)):
        if media_movel[i] is None:
            prev_idx = -1
            next_idx = -1
            
            for j in range(i - 1, -1, -1):
                if media_movel[j] is not None:
                    prev_idx = j
                    break
            
            for j in range(i + 1, len(media_movel)):
                if media_movel[j] is not None:
                    next_idx = j
                    break
            
            if prev_idx != -1 and next_idx != -1:
                ratio = (i - prev_idx) / (next_idx - prev_idx)
                media_movel[i] = media_movel[prev_idx] + (media_movel[next_idx] - media_movel[prev_idx]) * ratio
            elif prev_idx != -1:
                media_movel[i] = media_movel[prev_idx]
            elif next_idx != -1:
                media_movel[i] = media_movel[next_idx]
    
    return media_movel

print("CALCULANDO MÉDIAS MÓVEIS DO SEGUNDO TURNO")
print("=" * 80)

try:
    with open('data/segundo_turno/pesquisas_segundo_turno_normalizado.json', 'r', encoding='utf-8') as f:
        dados = json.load(f)
    
    if not dados:
        print("⚠ Nenhum dado do segundo turno encontrado")
        # Criar estrutura vazia
        resultado = {
            "datas": [],
            "institutos": [],
            "candidatos": {
                "Lula": {"media_movel": [], "pesquisas_brutos": []},
                "Freitas": {"media_movel": [], "pesquisas_brutos": []}
            }
        }
    else:
        print(f"✓ Carregadas {len(dados)} pesquisas")
        
        # Extrair e ordenar por data
        registros = []
        for pesquisa in dados:
            data_parsed = parseDate(pesquisa['data'])
            if data_parsed:
                registros.append({
                    'data': pesquisa['data'],
                    'data_parsed': data_parsed,
                    'instituto': pesquisa['instituto'],
                    'candidatos': pesquisa.get('candidatos', {})
                })
        
        registros.sort(key=lambda x: x['data_parsed'])
        print(f"✓ {len(registros)} pesquisas com datas válidas")
        
        # Preparar dados para cálculo
        datas = [r['data_parsed'] for r in registros]
        institutos = [r['instituto'] for r in registros]
        
        resultado = {
            "datas": [d.isoformat() for d in datas],
            "institutos": institutos,
            "candidatos": {}
        }
        
        # Calcular para cada candidato
        for candidato in ['Lula', 'Freitas']:
            valores = [r['candidatos'].get(candidato) for r in registros]
            mm = calcular_media_movel(valores, datas, window_days=31)
            
            resultado['candidatos'][candidato] = {
                'media_movel': mm,
                'pesquisas_brutos': valores
            }
            
            num_pesquisas = sum(1 for v in valores if v is not None)
            print(f"  {candidato}: {num_pesquisas} pesquisas")
    
    # Salvar
    output_path = 'data/segundo_turno/media_movel_segundo_turno_precalculada.json'
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(resultado, f, ensure_ascii=False, indent=2)
    
    print(f"✓ Salvo em: {output_path}")

except FileNotFoundError as e:
    print(f"❌ Arquivo não encontrado: {e}")
except Exception as e:
    print(f"❌ Erro: {e}")
    import traceback
    traceback.print_exc()

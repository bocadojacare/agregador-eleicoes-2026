import json
import pandas as pd
import numpy as np
from datetime import datetime
import re

def parseDate(str_data):
    """Parse dates in different formats from Wikipedia"""
    if not str_data:
        return None
    
    # Normalizar caracteres de travessão para hífen
    str_data = str_data.replace('–', '-').replace('−', '-').replace('–', '-')
    
    # Formato: "15-19 Oct 2025" (range de dias)
    m = re.match(r'(\d{1,2})\s*-\s*(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})', str_data)
    if m:
        return pd.to_datetime(f"{m.group(3)} {m.group(2)}, {m.group(4)}")
    
    # Formato: "29 Sep - 6 Oct 2025" (range entre meses)
    m = re.match(r'(\d{1,2})\s+([A-Za-z]+)\s*-\s*(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})', str_data)
    if m:
        return pd.to_datetime(f"{m.group(4)} {m.group(3)}, {m.group(5)}")
    
    # Formato: "28 Aug 2025" (data simples)
    m = re.match(r'(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})', str_data)
    if m:
        return pd.to_datetime(f"{m.group(2)} {m.group(1)}, {m.group(3)}")
    
    return None

def calcular_media_movel(valores, datas, window_days=31):
    """
    Calcula m├®dia m├│vel baseada em janela de dias
    Apenas para dados do candidato espec├¡fico (ignora nulos)
    """
    ms_window = window_days * 24 * 60 * 60 * 1000
    media_movel = []
    
    for i, data_ref in enumerate(datas):
        if pd.isna(valores[i]):
            media_movel.append(None)
            continue
        
        # Encontrar todas as pesquisas do candidato dentro de 31 dias
        mascara = np.abs((datas - data_ref).dt.total_seconds() * 1000) <= ms_window
        valores_janela = valores[mascara].dropna()
        
        if len(valores_janela) > 0:
            media_movel.append(float(valores_janela.mean()))
        else:
            media_movel.append(None)
    
    # Interpola├º├úo linear para preencher valores None
    media_movel_interpolado = []
    for i, val in enumerate(media_movel):
        if val is not None:
            media_movel_interpolado.append(val)
        else:
            # Procurar valor anterior e pr├│ximo
            prev_val = None
            next_val = None
            prev_idx = -1
            next_idx = -1
            
            for j in range(i - 1, -1, -1):
                if media_movel[j] is not None:
                    prev_val = media_movel[j]
                    prev_idx = j
                    break
            
            for j in range(i + 1, len(media_movel)):
                if media_movel[j] is not None:
                    next_val = media_movel[j]
                    next_idx = j
                    break
            
            # Interpolar
            if prev_val is not None and next_val is not None:
                ratio = (i - prev_idx) / (next_idx - prev_idx)
                media_movel_interpolado.append(prev_val + (next_val - prev_val) * ratio)
            elif prev_val is not None:
                media_movel_interpolado.append(prev_val)
            elif next_val is not None:
                media_movel_interpolado.append(next_val)
            else:
                media_movel_interpolado.append(None)
    
    return media_movel_interpolado

class NaNEncoder(json.JSONEncoder):
    def encode(self, obj):
        if isinstance(obj, float) and np.isnan(obj):
            return "null"
        return super().encode(obj)
    
    def iterencode(self, obj, _one_shot=False):
        for chunk in super().iterencode(obj, _one_shot):
            yield chunk.replace("NaN", "null")

# Carregar dados
print("=" * 80)
print("CALCULANDO M├ëDIAS M├ôVEIS PR├ë-CALCULADAS")
print("=" * 80)

with open('pesquisas_2026_normalizado.json', 'r', encoding='utf-8') as f:
    dados = json.load(f)

df = pd.DataFrame(dados)

# Expandir candidatos
candidatos_df = pd.json_normalize(df['candidatos'])
df = pd.concat([df.drop('candidatos', axis=1), candidatos_df], axis=1)

# Parsear datas
df['data_parsed'] = df['data'].apply(parseDate)
df = df.sort_values('data_parsed').reset_index(drop=True)

# Filtrar linhas com datas nulas
df = df[df['data_parsed'].notna()].reset_index(drop=True)

print(f"\nDados carregados: {df.shape[0]} pesquisas")
if df.shape[0] > 0:
    print(f"Periodo: {df['data'].iloc[-1]} a {df['data'].iloc[0]}")
else:
    print("ERRO: Nenhuma data foi parseada com sucesso!")
    exit(1)

# Candidatos principais
candidatos_principais = ['Lula', 'Freitas', 'Gomes', 'Caiado', 'Zema', 'Ratinho']

# Estrutura para salvar
resultado = {
    'datas': [],
    'institutos': [],
    'candidatos': {}
}

# Adicionar datas e institutos
for _, row in df.iterrows():
    resultado['datas'].append(row['data_parsed'].isoformat())
    resultado['institutos'].append(row['instituto'])

# Calcular m├®dia m├│vel para cada candidato
print("\nCalculando m├®dias m├│veis...")
for candidato in candidatos_principais:
    if candidato in df.columns:
        valores = pd.Series(df[candidato].values)
        datas = pd.Series(df['data_parsed'].values)
        
        media_movel = calcular_media_movel(valores, datas, window_days=31)
        
        # Substituir NaN por None
        media_movel = [None if (isinstance(x, float) and np.isnan(x)) else x for x in media_movel]
        pesquisas_brutos = [None if (isinstance(x, float) and np.isnan(x)) else x for x in df[candidato].values.tolist()]
        
        resultado['candidatos'][candidato] = {
            'media_movel': media_movel,
            'pesquisas_brutos': pesquisas_brutos
        }
        
        # Contar pesquisas
        num_pesquisas = df[candidato].notna().sum()
        print(f"  {candidato}: {num_pesquisas} pesquisas")

# Salvar como JSON
output_path = 'media_movel_precalculada.json'
with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(resultado, f, ensure_ascii=False, indent=2)

print(f"\nÔ£ô M├®dias m├│veis pr├®-calculadas salvas em '{output_path}'")
print(f"Ô£ô Total de registros: {len(resultado['datas'])}")
print(f"Ô£ô Candidatos: {', '.join(candidatos_principais)}")

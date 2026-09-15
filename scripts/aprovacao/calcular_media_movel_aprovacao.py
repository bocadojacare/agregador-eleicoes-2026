"""
Calcula médias móveis pré-calculadas para os dados de aprovação/desaprovação do governo.
Gera: data/aprovacao/media_movel_aprovacao_precalculada.json
"""
import json

import numpy as np
import pandas as pd


def calcular_media_movel(valores, datas, window_days=30):
    """Média móvel baseada em janela de dias (apenas dados anteriores/backward-looking)."""
    ms_window = window_days * 24 * 60 * 60 * 1000
    media_movel = []

    for i, data_ref in enumerate(datas):
        if pd.isna(valores[i]):
            media_movel.append(None)
            continue

        diff_ms = (datas - data_ref).dt.total_seconds() * 1000
        mascara = (diff_ms <= 0) & (diff_ms >= -ms_window)
        valores_janela = valores[mascara].dropna()

        if len(valores_janela) > 0:
            media_movel.append(float(valores_janela.mean()))
        else:
            media_movel.append(None)

    # Interpolação linear para preencher valores None
    media_movel_interpolado = []
    for i, val in enumerate(media_movel):
        if val is not None:
            media_movel_interpolado.append(val)
            continue

        prev_val = prev_idx = next_val = next_idx = None
        for j in range(i - 1, -1, -1):
            if media_movel[j] is not None:
                prev_val, prev_idx = media_movel[j], j
                break
        for j in range(i + 1, len(media_movel)):
            if media_movel[j] is not None:
                next_val, next_idx = media_movel[j], j
                break

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


print("=" * 80)
print("CALCULANDO MÉDIAS MÓVEIS PRÉ-CALCULADAS - APROVAÇÃO DE GOVERNO")
print("=" * 80)

with open('data/aprovacao/pesquisas_aprovacao.json', 'r', encoding='utf-8') as f:
    dados = json.load(f)

df = pd.DataFrame(dados)
candidatos_df = pd.json_normalize(df['candidatos'])
df = pd.concat([df.drop('candidatos', axis=1), candidatos_df], axis=1)

df['data_parsed'] = pd.to_datetime(df['data'])
df = df.sort_values('data_parsed').reset_index(drop=True)

print(f"\nDados carregados: {df.shape[0]} pesquisas")
if df.shape[0] > 0:
    print(f"Periodo: {df['data'].iloc[0]} a {df['data'].iloc[-1]}")
else:
    print("ERRO: Nenhum dado carregado!")
    raise SystemExit(1)

series_alvo = ['Aprova', 'Desaprova']

resultado = {
    'datas': [],
    'institutos': [],
    'candidatos': {}
}

for _, row in df.iterrows():
    resultado['datas'].append(row['data_parsed'].isoformat())
    resultado['institutos'].append(row['instituto'])

print("\nCalculando médias móveis...")
for nome in series_alvo:
    if nome in df.columns:
        valores = pd.Series(df[nome].values)
        datas = pd.Series(df['data_parsed'].values)

        media_movel = calcular_media_movel(valores, datas, window_days=30)
        media_movel = [None if (isinstance(x, float) and np.isnan(x)) else x for x in media_movel]
        pesquisas_brutos = [None if (isinstance(x, float) and np.isnan(x)) else x for x in df[nome].values.tolist()]

        resultado['candidatos'][nome] = {
            'media_movel': media_movel,
            'pesquisas_brutos': pesquisas_brutos
        }

        num_pesquisas = df[nome].notna().sum()
        print(f"  {nome}: {num_pesquisas} pesquisas")

output_path = 'data/aprovacao/media_movel_aprovacao_precalculada.json'
with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(resultado, f, ensure_ascii=False, indent=2)

print(f"\n✓ Médias móveis pré-calculadas salvas em '{output_path}'")
print(f"✓ Total de registros: {len(resultado['datas'])}")

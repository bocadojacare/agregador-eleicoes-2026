import pandas as pd
import json

# Carregar o JSON
with open('public/pesquisas_2026_normalizado.json', 'r', encoding='utf-8') as f:
    dados = json.load(f)

# Converter para DataFrame
df = pd.DataFrame(dados)

# Exibir informações básicas
print("=" * 80)
print("CARREGAMENTO DO JSON CONCLUÍDO")
print("=" * 80)
print(f"\nForma do DataFrame: {df.shape}")
print(f"Colunas: {df.columns.tolist()}")
print(f"\nPrimeiras linhas:\n{df.head()}")
print(f"\nÚltimas linhas:\n{df.tail()}")
print(f"\nTipos de dados:\n{df.dtypes}")
print(f"\nValores nulos:\n{df.isnull().sum()}")

# Expandir coluna 'candidatos' para colunas separadas
if 'candidatos' in df.columns:
    candidatos_df = pd.json_normalize(df['candidatos'])
    df = pd.concat([df.drop('candidatos', axis=1), candidatos_df], axis=1)
    print(f"\nDataFrame após expandir candidatos:")
    print(f"Forma: {df.shape}")
    print(f"Colunas: {df.columns.tolist()}")
    print(f"\nPrimeiras linhas:\n{df.head()}")

# Salvar como CSV para facilitar análises
df.to_csv('pesquisas_2026.csv', index=False, encoding='utf-8')
print("\n✓ DataFrame salvo em 'pesquisas_2026.csv'")

# Estatísticas básicas por candidato
print("\n" + "=" * 80)
print("ESTATÍSTICAS POR CANDIDATO")
print("=" * 80)
candidatos = [col for col in df.columns if col not in ['instituto', 'data']]
for candidato in candidatos:
    if candidato in df.columns:
        media = df[candidato].mean()
        minimo = df[candidato].min()
        maximo = df[candidato].max()
        print(f"\n{candidato}:")
        print(f"  Média: {media:.2f}%")
        print(f"  Mínimo: {minimo:.2f}%")
        print(f"  Máximo: {maximo:.2f}%")
        print(f"  Pesquisas: {df[candidato].notna().sum()}")

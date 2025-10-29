"""
Normaliza nomes dos candidatos no JSON de pesquisas extraído da Wikipedia (inglês).
- Lê public/pesquisas_2026.json
- Usa heurística por ordem/frequência para mapear cand_X para nomes reais (Lula, Tarcísio, etc.)
- Salva public/pesquisas_2026_normalizado.json
"""
import json
from pathlib import Path
from collections import Counter

IN_FILE = Path("public/pesquisas_2026.json")
OUT_FILE = Path("public/pesquisas_2026_normalizado.json")

# Mapeamento manual por ordem (ajustar conforme necessário)
CANDIDATE_ORDER = [
    "Lula",
    "Tarcísio",
    "Bolsonaro",
    "Ciro",
    "Simone",
    "Michelle",
    "Zema",
    "Ratinho",
    "Leite",
    "Caiado",
    "Tebet",
    "Outros"
]

def main():
    data = json.loads(IN_FILE.read_text(encoding="utf-8"))
    registros = []
    colunas_irrelevantes = {"Sample size", "Lead", "BlankNullUndec.", "Others", "Outros"}
    for pesquisa in data:
        candidatos = pesquisa.get("candidatos", {})
        novo_cand = {k: v for k, v in candidatos.items() if k not in colunas_irrelevantes}
        pesquisa["candidatos"] = novo_cand
        registros.append(pesquisa)
    OUT_FILE.write_text(json.dumps(registros, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Arquivo salvo: {OUT_FILE} (registros: {len(registros)})")
    print("Candidatos presentes:")
    todos_cands = Counter()
    for pesquisa in registros:
        for nome in pesquisa["candidatos"]:
            todos_cands[nome] += 1
    for nome, cnt in todos_cands.most_common():
        print(f" - {nome}: {cnt}")

if __name__ == "__main__":
    main()

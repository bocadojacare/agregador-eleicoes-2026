"""
Normaliza nomes dos candidatos no JSON de pesquisas extraído da Wikipedia (português).
- Lê data/pesquisas_2026.json
- Mapeia nomes brutos (com siglas de partidos) para nomes limpos
- Salva data/pesquisas_2026_normalizado.json
"""
import json
from pathlib import Path
from collections import Counter
import re

IN_FILE = Path("data/primeiro_turno/pesquisas_2026.json")
OUT_FILE = Path("data/primeiro_turno/pesquisas_2026_normalizado.json")

# Mapeamento de nomes brutos (do Wikipedia PT) para nomes limpos
CANDIDATE_NAME_MAPPING = {
    # Lula
    "LulaPT": "Lula",
    # Flávio Bolsonaro
    "FláviopL": "Flávio",
    "FlávioPL": "Flávio",
    "FlÃ¡vioPL": "Flávio",  # Encoding issue variant
    # Caiado
    "CaiadoPSD": "Caiado",
    "CaiadoUNIÃO": "Caiado",
    # Zema
    "ZemaNOVO": "Zema",
    # Renan Santos
    "RenanMISSÃO": "Renan",
    "RenanMISSÃO": "Renan",  # Encoding issue variant
    # Aldo Rebelo
    "RebeloDC": "Rebelo",
    # Tarcísio (if found)
    "TarcísioRepublicanos": "Tarcísio",
    "TarcIsioRepublicanos": "Tarcísio",
    # Other candidates that might appear (to filter out)
    "HaddadPT": "Haddad",
    "RatinhoPSD": "Ratinho",
    "LeitePSD": "Leite",
}

def normalize_candidate_name(raw_name):
    """Converte nome bruto para nome normalizado"""
    if raw_name in CANDIDATE_NAME_MAPPING:
        return CANDIDATE_NAME_MAPPING[raw_name]
    # Try to match by partial name (case-insensitive)
    raw_lower = raw_name.lower()
    for raw, normalized in CANDIDATE_NAME_MAPPING.items():
        if raw.lower() in raw_lower:
            return normalized
    return raw_name  # Return unchanged if no mapping found

def main():
    data = json.loads(IN_FILE.read_text(encoding="utf-8"))
    registros = []
    
    # Candidates to keep (whitelist)
    CANDIDATES_TO_KEEP = {"Lula", "Flávio", "Caiado", "Zema", "Renan", "Rebelo"}
    
    colunas_irrelevantes = {"Sample size", "Lead", "BlankNullUndec.", "Others", "Outros"}
    
    for pesquisa in data:
        candidatos = pesquisa.get("candidatos", {})
        
        # Map candidate names and filter
        novo_cand = {}
        for raw_name, value in candidatos.items():
            if raw_name in colunas_irrelevantes:
                continue
            
            # Normalize the name
            normalized_name = normalize_candidate_name(raw_name)
            
            # Only keep whitelisted candidates
            if normalized_name in CANDIDATES_TO_KEEP:
                novo_cand[normalized_name] = value
        
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

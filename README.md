# Agregador de Pesquisas Eleitorais 2026

Um agregador de pesquisas eleitorais brasileiras que consolida dados de múltiplas institutos de pesquisa para oferecer uma visão clara e atualizada das intenções de voto para as eleições presidenciais de 2026.

## 🎯 Funcionalidades

- **Gráficos Interativos**: Visualização de evolução de intenções de voto com Chart.js
- **Médias Móveis**: Cálculo de média móvel de 31 dias para suavizar flutuações
- **Dois Turnos Independentes**: 
  - Primeiro turno: Lula, Tarcísio, Ciro Gomes, Caiado, Zema e Ratinho
  - Segundo turno: Lula vs Tarcísio
- **Timeline Interativa**: Filtre dados por período específico com controles deslizantes
- **Toggle de Pesquisas**: Mostrar ou ocultar pontos de pesquisa individuais para visualizar apenas a média móvel
- **Modo Escuro/Claro**: Alterne entre temas para melhor conforto visual
- **Responsivo**: Design adaptável para desktop, tablet e mobile
- **Tooltips Detalhados**: Informações completas ao passar o mouse sobre os dados

## 📋 Estrutura do Projeto

```
.
├── index.html              # Arquivo HTML principal
├── style.css               # Estilos CSS com suporte a modo escuro
├── script.js               # Lógica JavaScript com Chart.js
├── README.md               # Este arquivo
├── backlog.md              # Lista de tarefas futuras
├── .gitignore              # Arquivo de exclusão Git
└── data/
    ├── changelog.json      # Histórico de versões
    ├── primeiro_turno/     # Dados do primeiro turno
    │   ├── pesquisas_*.json
    │   ├── pesquisas_normalizado.json
    │   └── media_movel_precalculada.json
    └── segundo_turno/      # Dados do segundo turno
        ├── pesquisas_*.json
        ├── pesquisas_normalizado.json
        └── media_movel_precalculada.json
```

## 🚀 Como Usar

### Localmente

1. Clone o repositório:
```bash
git clone https://github.com/bocadojacare/agregador-eleicoes-2026.git
cd agregador-eleicoes-2026
```

2. Inicie um servidor local:
```bash
python -m http.server 8000
```

3. Abra no navegador:
```
http://localhost:8000
```

### Online

Acesse a versão hospedada no GitHub Pages:
```
https://bocadojacare.github.io/agregador-eleicoes-2026/
```

## 📊 Navegação

- **Abas de Turno**: Clique em "1º Turno" ou "2º Turno" para alternar entre as visualizações
- **Toggle de Pesquisas**: Use o checkbox "Mostrar Pesquisas" para exibir ou ocultar os pontos individuais
- **Timeline**: Arraste os controles para filtrar um período específico
- **Modo Escuro**: Clique no ícone 🌙 no cabeçalho
- **Changelog**: Clique no botão de versão (v1.2.0) para ver histórico de mudanças

## 🔄 Atualização Automática de Dados

Os dados são atualizados automaticamente via GitHub Actions todos os dias às 12:00 UTC. O fluxo:

1. **Scraping**: Coleta dados de institutos de pesquisa
2. **Normalização**: Padroniza os dados coletados
3. **Média Móvel**: Calcula média móvel de 30 dias
4. **Push Automático**: Envia dados para o repositório

## 📈 Dados e Fontes

Os dados agregados vêm de múltiplos institutos de pesquisa de opinião. Os arquivos são organizados por turno e incluem:

- **pesquisas_*.json**: Dados brutos por data de coleta
- **pesquisas_normalizado.json**: Dados normalizados e validados
- **media_movel_precalculada.json**: Média móvel pré-calculada para melhor performance

## 🛠️ Tecnologias Utilizadas

- **Frontend**: HTML5, CSS3, JavaScript ES6+
- **Gráficos**: Chart.js
- **Dados**: JSON
- **Hospedagem**: GitHub Pages
- **Automação**: GitHub Actions
- **Versionamento**: Git

## 📝 Versões

### v1.2.0 (2026-04-04)
- Exibição de partidos políticos nas caixas de Média Atual
- Melhoria no comportamento do toggle 'Mostrar Pesquisas'
- Correção do seletor de candidatos via legenda para respeitar estado do toggle
- Atualização dos candidatos para refletir entrada de Flávio Bolsonaro como pré-candidato
- Inclusão de Renan e Rebelo nos candidatos principais

### v1.1.0 (2025-11-01)
- Implementação do segundo turno completo e independente
- Adição do Ciro Gomes aos candidatos
- Toggle para mostrar/ocultar pontos de pesquisa
- Navegação por abas com efeito "pull" elegante
- Refinamentos no modo escuro e responsividade mobile

### v1.0.0 (2025-10-27)
- Lançamento inicial
- Visualização de 5 candidatos principais
- Gráficos com médias móveis
- Timeline interativa
- Modo escuro/claro

## ✉️ Contato

Dúvidas ou sugestões? Entre em contato através do [GitHub](https://github.com/bocadojacare).

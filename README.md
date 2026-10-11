# ⚔️ Yu-Gi-Oh! AI Card Analyzer & Database

> **Classificação inteligente de efeitos e estratégias de cartas de Yu-Gi-Oh! em tempo real utilizando Processamento de Linguagem Natural (NLP) e Zero-Shot Classification com o modelo BART-Large-MNLI.**

---

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![PyTorch](https://img.shields.io/badge/PyTorch-EE4C2C?style=for-the-badge&logo=pytorch&logoColor=white)](https://pytorch.org/)
[![Hugging Face](https://img.shields.io/badge/Hugging%20Face-Transformers-FFD21E?style=for-the-badge&logo=huggingface&logoColor=black)](https://huggingface.co/facebook/bart-large-mnli)
[![Pandas](https://img.shields.io/badge/Pandas-Data%20Analysis-150458?style=for-the-badge&logo=pandas&logoColor=white)](https://pandas.pydata.org/)
[![CustomTkinter](https://img.shields.io/badge/GUI-CustomTkinter-24292E?style=for-the-badge&logo=tkinter&logoColor=white)](https://github.com/TomSchimansky/CustomTkinter)

---

## 📖 Visão Geral

O **Yu-Gi-Oh! AI Card Analyzer** é uma aplicação desktop desenvolvida para analisar, catalogar e classificar o efeito textual de cartas do jogo Yu-Gi-Oh! utilizando inteligência artificial de ponta.

Através de **Zero-Shot Sequence Classification**, o sistema avalia a descrição de qualquer carta e determina sua finalidade estratégica (ex.: destruição de monstros, negação de efeitos, invocação especial, compra de cartas ou busca no deck) sem a necessidade de fine-tuning específico para o jogo, aproveitando a capacidade semântica profunda do modelo **BART-Large-MNLI**.

O projeto conta com:
- **Dashboard Intuitivo**: Resumo de métricas da base com mais de 40.000 cartas, distribuição de cartas por tipo (Monstros, Magias e Armadilhas) e status da IA.
- **Analisador de Efeito (IA em Background)**: Entrada manual ou carregamento instantâneo de cartas, execução assíncrona que não congela a interface, ordenação automática de probabilidades relativas e destaque da categoria vencedora com barras de progresso visuais.
- **Banco de Cartas Completo**: Tabela moderna, responsiva e paginada, permitindo busca textual rápida (nome, nome oficial, descrição, Index, Index Market, Join ID e Set ID) e filtros por Tipo, Subtipo, Atributo, Raridade e Coleção.
- **Painel de Detalhes e Transferência**: Exibição detalhada de atributos, preços, coleções e texto completo do efeito com quebra de linha e rolagem, incluindo botões para copiar identificadores e transferir a carta diretamente para análise da IA com 1 clique.
- **Configurações Flexíveis**: Validação automática de arquivos CSV, seleção de dispositivo de execução (CPU ou GPU via CUDA) e personalização das categorias de classificação.

---

## ⚖️ Avisos Legais, Isenção de Responsabilidade e Créditos

### 🎓 Fins Educacionais e Acadêmicos
Este software foi desenvolvido **estritamente para fins educacionais, de pesquisa, aprendizado e demonstração técnica** nas áreas de Processamento de Linguagem Natural (NLP), Engenharia de Software e Interfaces Gráficas Desktop com Python. Não há qualquer finalidade comercial, monetização ou intenção de exploração econômica associada a este repositório.

### 🛡️ Propriedade Intelectual da KONAMI
Todos os direitos autorais, marcas registradas, nomes de cartas, termos do jogo, imagens, mecânicas, regras e textos associados ao universo **Yu-Gi-Oh!** pertencem exclusivamente à **KONAMI Digital Entertainment Co., Ltd.** e ao criador original **Kazuki Takahashi**. 
> *Yu-Gi-Oh! é uma marca registrada da KONAMI Digital Entertainment. Todos os direitos reservados.* Este projeto não é afiliado, patrocinado, associado ou endossado pela KONAMI.

### 📊 Créditos da Base de Dados (Dataset CSV)
A base de dados de cartas utilizada neste projeto foi obtida a partir do dataset público disponibilizado pela comunidade no Kaggle:
- **Autor / Mantenedor**: [hammadus](https://www.kaggle.com/hammadus)
- **Dataset Oficial**: [Yu-Gi-Oh! Full Card Database & Index (August 2025)](https://www.kaggle.com/datasets/hammadus/yugioh-full-card-database-index](https://www.kaggle.com/datasets/hammadus/yugioh-full-card-database-index-august-1st-2025?resource=download))

### 🧠 Créditos do Modelo de Inteligência Artificial
A classificação zero-shot é viabilizada pelo modelo pré-treinado de última geração fornecido pela equipe do **Hugging Face** e desenvolvido pela **Meta AI (Facebook)**:
- **Modelo**: `facebook/bart-large-mnli`
- **Repositório Hugging Face**: [facebook/bart-large-mnli](https://huggingface.co/facebook/bart-large-mnli)
- **Tipo de Modelo**: Bidirectional and Auto-Regressive Transformers (BART) ajustado para Inferência de Linguagem Natural (Multi-Genre Natural Language Inference - MNLI).

---

## 👥 Créditos de Desenvolvimento e Ferramentas

- **Front-End & Interface Gráfica (GUI)**:
  A arquitetura visual da interface desktop, o design temático escuro (*Obsidian & Millennium Gold*), a paginação de alto desempenho, os componentes customizados e a integração responsiva em CustomTkinter/Tkinter foram projetados e estruturados com o auxílio do assistente de engenharia de software **Google Antigravity**.
- **Back-End, Manipulação de Dados & Pipeline de IA**:
  O tratamento da base de dados com Pandas, a estruturação dos dados tabulares, a lógica de extração semântica e a integração inicial do pipeline de Machine Learning com Transformers e PyTorch foram desenvolvidos do modo tradicional em Python pelo autor do projeto.

---

## 🏗️ Arquitetura do Sistema e Como Tudo Funciona

O projeto é estruturado em uma arquitetura modular que desacopla a camada de dados, o mecanismo de inferência de NLP e a camada de apresentação visual:

```
┌───────────────────────────────────────────────────────────────┐
│                       INTERFACE GRÁFICA                       │
│                     (CustomTkinter / GUI)                     │
│   [Dashboard]   [Analisar Carta]   [Banco de Cartas]   [Config]│
└───────────────▲───────────────────────────────▲───────────────┘
                │ Interação do Usuário          │ Renderização Segura
                │ Eventos (Clique / Busca)      │ (root.after Callback)
┌───────────────▼───────────────────────────────┴───────────────┐
│                    GERENCIADOR DE ESTADO &                    │
│                      THREADING ASSÍNCRONO                     │
└───────────────┬───────────────────────────────┬───────────────┘
                │ Leitura em Memória            │ Processamento em
                │ (Sub-10ms)                    │ Background
┌───────────────▼───────────────┐ ┌─────────────▼───────────────┐
│       CAMADA DE DADOS         │ │      PIPELINE DE IA         │
│     (Pandas DataFrame)        │ │  (Hugging Face BART-Large)  │
│  yugioh-ccd-*.csv (40.792 lin)│ │   facebook/bart-large-mnli  │
└───────────────────────────────┘ └─────────────────────────────┘
```

### 1. Extração e Consulta de Dados em Memória (Pandas)
- Ao iniciar a aplicação, o arquivo CSV com 40.792 registros é carregado de forma vetorizada em um `pandas.DataFrame`.
- Com consumo de memória enxuto (~48 MB de RAM), as pesquisas e filtros não tocam o disco rígido novamente durante o uso.
- A busca textual realiza operações vetorizadas com `.str.contains(case=False)` simultaneamente nas colunas `name`, `name_official`, `description`, `index`, `index_market`, `join_id` e `set_id`, entregando resultados em poucos milissegundos.
- A exibição na tabela utiliza **paginação virtualizada**, garantindo 60 FPS e evitando engasgos comuns ao renderizar milhares de itens de uma só vez no Tkinter.

### 2. O Mecanismo do Modelo BART (Zero-Shot NLI)
O modelo `facebook/bart-large-mnli` não foi treinado com dados específicos de regras de Yu-Gi-Oh!, mas consegue interpretar os textos com precisão através do princípio de **Inferência de Linguagem Natural (NLI - Natural Language Inference)**:
- **Premissa**: O efeito real da carta (exemplo: *"Target 1 monster on the field; destroy it."*).
- **Hipótese**: Um modelo de frase gerado dinamicamente para cada categoria candidata (exemplo: *"This text is about destroy monster on field"*).
- **Classificação de Relação**: A rede neural avalia a relação lógica entre Premissa e Hipótese através de três estados fundamentais:
  1. *Entailment* (A premissa implica diretamente a hipótese);
  2. *Contradiction* (A premissa contradiz a hipótese);
  3. *Neutral* (A premissa é neutra em relação à hipótese).
- **Cálculo dos Scores**: A probabilidade do estado *Entailment* é normalizada via função softmax sobre todas as categorias candidatas (*candidate labels*), resultando em um percentual de afinidade relativa ordenado do maior para o menor.

### 3. Integração Assíncrona Back-End ↔ Front-End
- **Padrão Singleton de IA**: O modelo é carregado apenas uma vez na memória RAM/VRAM. Análises subsequentes reutilizam o pipeline já instanciado, eliminando atrasos repetidos de inicialização.
- **Multi-Threading Sem Travamentos**: Como a inferência de um modelo de ~1.6 GB exige alto uso computacional do processador ou placa de vídeo, a execução da predição ocorre em uma `threading.Thread` em segundo plano (*daemon thread*).
- **Atualização Segura de Interface**: Ao finalizar o cálculo, a thread em segundo plano despacha os resultados para a thread principal da interface através do método seguro `root.after()`, atualizando as barras de progresso, percentuais e badges sem nunca congelar ou travar a janela para o usuário.

---

## 💻 Requisitos do Sistema

- **Sistema Operacional**: Windows 10/11 (ou Linux / macOS com suporte a Tkinter).
- **Python**: Versão **3.10** ou superior.
- **Memória RAM**: Mínimo de 4 GB recomendados (8 GB recomendados para carregamento simultâneo do modelo e dataset).
- **Placa de Vídeo (Opcional)**: GPU NVIDIA com suporte a CUDA para inferência acelerada (se não houver GPU dedicada, a aplicação executa automaticamente em modo CPU de maneira estável).

---

## 🚀 Instalação e Execução

### 1. Clonar o Repositório
```bash
git clone https://github.com/seu-usuario/yugioh-ai-card-analyzer.git
cd yugioh-ai-card-analyzer
```

### 2. Criar e Ativar um Ambiente Virtual (Recomendado)
```bash
# Criar ambiente virtual
python -m venv venv

# Ativar no Windows (PowerShell)
.\venv\Scripts\Activate.ps1

# Ativar no Linux/macOS
source venv/bin/activate
```

### 3. Instalar as Dependências
Instale as bibliotecas necessárias com o comando:
```bash
pip install torch transformers pandas customtkinter darkdetect pillow
```

### 4. Executar a Aplicação

#### ▶️ Modo Interface Gráfica Desktop (Recomendado):
Para iniciar a experiência visual completa com dashboard, busca avançada de cartas e análise em tempo real:
```bash
python app.py
```

#### ⌨️ Modo Script Terminal (Original):
Para executar a classificação direta de exemplo no console:
```bash
python estudoIA.py
```

---

## 📁 Estrutura de Arquivos do Projeto

```
yugioh-ai-card-analyzer/
│
├── app.py                           # Aplicação gráfica principal em CustomTkinter
├── estudoIA.py                      # Módulo central de IA, funções de análise e teste CLI
├── yugioh-ccd-2025SEP12-163128.csv   # Base de dados oficial com 40.792 cartas
└── README.md                        # Documentação completa do projeto
```

---

## 🏷️ Categorias de Classificação Padrão

As categorias avaliadas pela IA podem ser personalizadas diretamente na tela de **Configurações** da aplicação ou no arquivo `estudoIA.py`:

| Categoria Candidata (*Label*) | Descrição da Intenção Estratégica |
| :--- | :--- |
| `ATK or DEF modification / debuff` | Modificação de valores de ataque/defesa ou enfraquecimento de monstros. |
| `battle protection or trap card` | Proteção contra destruição em batalha ou ativação defensiva. |
| `negate effect or activation` | Negação de efeitos ou ativações de cartas do oponente. |
| `destroy monster on field` | Remoção e destruição de monstros presentes no campo. |
| `special summon monster` | Invocação especial de monstros a partir de qualquer zona. |
| `draw cards from deck` | Compra direta de cartas do topo do Deck. |
| `add from deck to hand` | Busca e adição de cartas específicas do Deck para a mão (*searchers*). |

---

## 📄 Licença

Este projeto é disponibilizado sob a licença **MIT** para fins estritamente educacionais e acadêmicos. Consulte o arquivo `LICENSE` para mais detalhes.

*Yu-Gi-Oh! e todos os materiais relacionados são marcas e propriedades intelectuais da KONAMI Digital Entertainment.*

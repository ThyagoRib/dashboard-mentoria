# 📊 Dashboard de Mentoria — Estude com Danilo

Dashboard analítico construído com **Streamlit** para acompanhamento de desempenho de alunos em atividades e simulados. Os dados são lidos em tempo real de planilhas no **Google Sheets** e toda a autenticação é feita via `streamlit-authenticator`.

---

## Sumário

1. [Visão Geral](#visão-geral)
2. [Estrutura do Projeto](#estrutura-do-projeto)
3. [Pré-requisitos](#pré-requisitos)
4. [Instalação e Configuração](#instalação-e-configuração)
5. [Estrutura das Planilhas](#estrutura-das-planilhas)
6. [Módulos e Funcionalidades](#módulos-e-funcionalidades)
   - [Avaliação Individual](#avaliação-individual)
   - [Simulados](#simulados)
7. [Secrets e Autenticação](#secrets-e-autenticação)
8. [Deploy no Streamlit Cloud](#deploy-no-streamlit-cloud)
9. [Cache e Performance](#cache-e-performance)

---

## Visão Geral

O dashboard foi projetado para mentores que acompanham múltiplos alunos em diferentes frentes de estudo (atividades diárias e simulados do ENEM). A aplicação permite:

- Filtrar desempenho por **aluno**, **matéria** e **período**.
- Visualizar indicadores de **consistência, tendência e retenção**.
- Comparar resultados individuais com a **média da turma**.
- Acompanhar o **ranking** entre os alunos nos simulados.

---

## Estrutura do Projeto

```
.
├── app.py                  # Ponto de entrada: config, autenticação e roteamento
├── estilos.py              # CSS global injetado no Streamlit
├── utils.py                # Conexão com Google Sheets e carregamento de dados
├── modulo_individual.py    # Módulo de Avaliação Individual
├── modulo_simulados.py     # Módulo de Simulados
├── requirements.txt        # Dependências Python
├── logo.png                # Logo exibida na sidebar e telas de login
└── .streamlit/
    └── secrets.toml        # Credenciais (NÃO versionar este arquivo)
```

---

## Pré-requisitos

- Python 3.11+
- Conta Google com acesso à planilha de dados
- Projeto no Google Cloud com a **Google Sheets API** e **Google Drive API** habilitadas
- Chave de serviço (Service Account) com permissão de leitura na planilha

---

## Instalação e Configuração

### 1. Clone o repositório

```bash
git clone https://github.com/seu-usuario/dashboard-mentoria.git
cd dashboard-mentoria
```

### 2. Crie e ative um ambiente virtual

```bash
python -m venv .venv
source .venv/bin/activate      # Linux / macOS
.venv\Scripts\activate         # Windows
```

### 3. Instale as dependências

```bash
pip install -r requirements.txt
```

### 4. Configure os Secrets

Crie o arquivo `.streamlit/secrets.toml` com o conteúdo abaixo (veja a seção [Secrets e Autenticação](#secrets-e-autenticação) para detalhes):

```toml
[auth]
  [auth.credentials.usernames.seu_usuario]
    name = "Nome Completo"
    password = "$2b$12$hash_gerado_pelo_stauth"

  [auth.cookie]
    name   = "dashboard_cookie"
    key    = "chave_secreta_aleatoria"
    expiry_days = 7

[gcp_service_account]
  type                        = "service_account"
  project_id                  = "seu-projeto"
  private_key_id              = "..."
  private_key                 = "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
  client_email                = "sua-conta@seu-projeto.iam.gserviceaccount.com"
  client_id                   = "..."
  auth_uri                    = "https://accounts.google.com/o/oauth2/auth"
  token_uri                   = "https://oauth2.googleapis.com/token"
  auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
  client_x509_cert_url        = "..."
```

### 5. Execute localmente

```bash
streamlit run app.py
```

---

## Estrutura das Planilhas

O ID da planilha está definido em `utils.py` (`_SHEET_ID`). A planilha deve conter **três abas**:

### Aba `Alunos`

| Coluna       | Tipo    | Descrição                                      |
|-------------|---------|------------------------------------------------|
| `id_aluno`  | inteiro | Identificador único do aluno                   |
| `nome`      | texto   | Nome completo do aluno                         |
| `id_mentoria` | inteiro | `1` = Estude com Danilo · `2` = Projeto Medicina |

### Aba `Atividades`

| Coluna     | Tipo    | Descrição                                          |
|-----------|---------|-----------------------------------------------------|
| `id_aluno` | inteiro | FK para a aba Alunos                               |
| `data`     | data    | Data da atividade (formato `DD/MM/AAAA`)           |
| `materia`  | texto   | Uma das 8 matérias: `Linguagens`, `História`, `Geografia`, `Filo / Socio`, `Biologia`, `Física`, `Química`, `Matemática` |
| `conteudo` | texto   | Tópico ou conteúdo específico estudado             |
| `acertos`  | inteiro | Número de questões acertadas                       |
| `total`    | inteiro | Total de questões realizadas                       |

### Aba `Simulados`

| Coluna     | Tipo    | Descrição                                          |
|-----------|---------|-----------------------------------------------------|
| `id_aluno` | inteiro | FK para a aba Alunos                               |
| `data`     | data    | Data do simulado (formato `DD/MM/AAAA`)            |
| `tipo`     | texto   | Tipo do simulado (ex: `ENEM`, `Extensivo`)         |
| `numero`   | inteiro | Número sequencial do simulado                      |
| `ano`      | inteiro | Ano de referência do simulado                      |
| `area`     | texto   | Uma das 4 áreas: `Linguagens`, `Humanas`, `Natureza`, `Matemática` |
| `acertos`  | inteiro | Número de questões acertadas na área               |
| `total`    | inteiro | Total de questões da área (padrão ENEM: 45 por área) |

> **Simulado Completo:** Um simulado é considerado completo quando o aluno registra as 4 áreas com exatamente 180 questões no total para o mesmo `tipo + numero + ano`.

---

## Módulos e Funcionalidades

### Avaliação Individual

**Arquivo:** `modulo_individual.py`  
**Acesso:** Sidebar → *Avaliação Individual*

Este módulo oferece uma visão completa do desempenho de um aluno em suas atividades diárias.

#### Filtros disponíveis (sidebar)

| Filtro         | Descrição                                        |
|---------------|--------------------------------------------------|
| Mentoria       | Filtra alunos por grupo de mentoria             |
| Aluno          | Seleciona o aluno a ser analisado               |
| Matéria        | Exibe dados gerais ("Todas") ou por disciplina  |
| Data Inicial   | Início do período de análise (padrão: 30 dias)  |
| Data Final     | Fim do período de análise (padrão: hoje)        |

#### Aba — Performance & Equilíbrio

**Cards de métricas gerais:**

| Métrica     | Descrição                                                      |
|------------|----------------------------------------------------------------|
| Questões    | Total de questões realizadas no período                        |
| Acertos     | Total de questões acertadas                                    |
| Média       | Percentual geral de acertos                                    |
| Volatilidade | Desvio padrão do rendimento diário — indica consistência      |
| Atividades  | Número de registros de atividade no período                    |

> **Interpretação da Volatilidade:**
> - `< 15%` → Consistência saudável
> - `15% – 30%` → Alerta: variação elevada
> - `> 30%` → Instabilidade: recomenda-se revisão da estratégia de estudos

**Radar de Competências:** Gráfico polar comparando o rendimento do aluno em cada matéria contra a média de toda a turma.

**Evolução Diária:** Gráfico de linha com marcadores mostrando o rendimento diário. Inclui uma linha de tendência linear e um indicador colorido (🟢 Crescente / 🔴 Decrescente / ⚫ Estável).

#### Aba — Diagnóstico Tático

**Streak de Constância:** Quantos dias consecutivos o aluno registrou pelo menos uma atividade. Incentiva a regularidade nos estudos.

**Alerta de Hiato:** Identifica automaticamente a matéria com o maior intervalo sem registros. O card fica vermelho quando o hiato supera 7 dias.

**Conteúdos Críticos:** Lista os até 5 conteúdos com pior rendimento no período filtrado:
- 🚨 **Crítico** (rendimento < 50%)
- 🟡 **Atenção** (rendimento entre 50% e 70%)

**Retenção Estimada por Conteúdo:** Aplica a **Curva de Esquecimento de Ebbinghaus** para estimar o quanto de cada conteúdo o aluno ainda retém. A fórmula utilizada é:

```
Retenção = acertos_% × e^(-0.03 × dias_desde_último_registro)
```

Os 15 conteúdos com menor retenção estimada são exibidos em um gráfico de barras horizontal com escala de cores do vermelho ao verde.

**Histórico Completo:** Expander com a tabela de todas as atividades do aluno no período, ordenada da mais recente para a mais antiga.

---

### Simulados

**Arquivo:** `modulo_simulados.py`  
**Acesso:** Sidebar → *Simulados*

Este módulo analisa o desempenho nos simulados do formato ENEM (4 áreas × 45 questões = 180 questões).

#### Filtros disponíveis (sidebar)

| Filtro     | Descrição                                                    |
|-----------|--------------------------------------------------------------|
| Aluno      | `Todos os Alunos` para visão coletiva, ou um aluno específico |
| Área       | Filtra os gráficos para uma área específica ou `Todas`       |

#### Aba — Performance de Simulados

**Cards de Recordes** *(visíveis apenas com ao menos 1 simulado completo)*:

| Card            | Descrição                                              |
|----------------|--------------------------------------------------------|
| Melhor Área     | Área com maior média de acertos (em números)           |
| Pior Área       | Área com menor média de acertos (em números)           |
| Recorde         | Maior pontuação total obtida em um único simulado      |
| Provas Total    | Quantidade de simulados completos realizados           |

**Diagnóstico de Treino — Visão Geral (todas as áreas):**
- **Radar** com média de rendimento por área.
- **Gráfico de barras horizontal** com volume acumulado de questões por área — permite identificar onde o aluno concentra mais treino.

**Diagnóstico de Treino — Área Específica:**
- **Gauge** com a média geral de rendimento na área selecionada.
- **Gráfico de linha** com evolução temporal do rendimento na área + linha de tendência.

**Histórico Completo:** Tabela expansível com todos os registros de simulados. No modo "Todos os Alunos", inclui a coluna de nome.

#### Aba — Ranking e Comparativo

**Modo "Todos os Alunos":**
Permite selecionar um simulado específico (`tipo + número + ano`) e exibe o ranking de todos os alunos que completaram as 180 questões, com emojis de medalha (🥇🥈🥉) para os três primeiros.

**Modo individual (aluno selecionado):**
Exibe uma tabela com o histórico de posicionamento do aluno em cada simulado completo que realizou, mostrando: posição, acertos por área e total.

---

## Secrets e Autenticação

A autenticação usa a biblioteca `streamlit-authenticator`. As senhas devem ser armazenadas como **hashes bcrypt**.

### Como gerar o hash de uma senha

```python
import streamlit_authenticator as stauth
hashed = stauth.Hasher(["sua_senha"]).generate()
print(hashed[0])
```

Cole o hash gerado no campo `password` do `secrets.toml`.

---

## Deploy no Streamlit Cloud

1. Faça push do projeto para um repositório GitHub (sem o `secrets.toml`).
2. Acesse [share.streamlit.io](https://share.streamlit.io) e crie um novo app apontando para `app.py`.
3. No painel do app, vá em **Settings → Secrets** e cole o conteúdo do `secrets.toml`.
4. Certifique-se de que o e-mail da Service Account tem **permissão de leitor** na planilha Google Sheets.

---

## Cache e Performance

Os dados são carregados via `@st.cache_data(ttl=600)`, o que significa que a aplicação consulta o Google Sheets **no máximo uma vez a cada 10 minutos** por sessão de servidor. Para forçar a atualização imediata dos dados, o usuário pode recarregar a página com `Ctrl+Shift+R` (limpa o cache do navegador, forçando nova busca na próxima execução).

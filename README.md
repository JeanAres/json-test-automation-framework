# E-pro Test Framework

Framework Data-Driven em Python para automacao de testes E2E e validacao de interface web. Construido com Playwright e orquestrado por arquivos JSON, o grande diferencial deste projeto e a sua integracao nativa com Inteligencia Artificial (Google Gemini) e Azure DevOps para analise e reporte automatizado de falhas.


Este framework vai alem da simples execucao de passos. Ele atua como um Analista de QA autonomo. Quando um teste falha (ex: quebra de layout, erro 500, seletor nao encontrado):
1. Captura de Evidencia: O motor tira um screenshot instantaneo do exato momento da falha.
2. Analise de Causa Raiz: O log de erro e o passo executado sao enviados para a API do Google Gemini (IA), que deduz o problema tecnico.
3. Reporte Automatico: O sistema consome a API REST do Azure DevOps e abre um card de Bug silenciosamente no board do time.
4. Contexto Visual: O card e criado com a analise tecnica da IA e a imagem do erro e anexada e renderizada diretamente no corpo da descricao.

---

## Quick Start

### 1. Pre-requisitos
- Python 3.8 ou superior
- Playwright
- Conta com acesso ao Azure DevOps (Personal Access Token)
- Chave de API do Google Gemini (GenAI)

### 2. Instalacao

pip install -r requirements.txt
python -m playwright install chromium


### 3. Configuracao de Ambiente

O projeto utiliza variaveis de ambiente para gerenciar credenciais e chaves de API, evitando a exposicao de dados sensiveis. Crie um arquivo .env na raiz do projeto com a seguinte estrutura:

# Credenciais do Sistema E-pro
EPROD_USERNAME=seu_usuario
EPROD_PASSWORD=sua_senha

# Integracao IA (Google Gemini)
GEMINI_API_KEY=sua_chave_api_aqui

# Integracao Azure DevOps
AZURE_ORGANIZATION=agapebuild
AZURE_PROJECT=Fabrica
AZURE_AREA_PATH=Fabrica\Time DEV (2.0) - ALERGS
AZURE_TOKEN=seu_personal_access_token_aqui

Aviso: Nunca versione o arquivo .env.

### 4. Executando os Testes

Utilize o executor central na raiz do projeto:

# Executar todos os testes de uma suite (pasta)
python run.py --suite tests/contas_de_usuarios/grupos

# Executar um teste especifico (arquivo JSON)
python run.py --test tests/contas_de_usuarios/grupos/grupos.json


---

## Estrutura do Projeto

A arquitetura isola configuracoes, massa de dados e o motor de execucao principal:

web-test-framework/
├── config/environments/ # Configuracoes e URLs por ambiente (Dev, HML, Stage)
├── evidence/            # Output de testes (Screenshots, Videos e Logs)
├── src/testador/        # Motor principal (Playwright + parser JSON + IA/Azure)
├── tests/               # Suites de testes separadas por modulo (Arquivos JSON)
├── .env                 # Variaveis locais e chaves de API (Ignorado pelo Git)
└── run.py               # Ponto de entrada unico para execucao


---

## Escrevendo Testes (Configuracao JSON)

Os testes sao definidos estritamente em arquivos JSON, permitindo escalabilidade sem necessidade de programar nova logica no motor. Variaveis do .env podem ser injetadas utilizando a sintaxe ${VARIAVEL}.

Exemplo Basico (happy_path.json):

{
  "nome": "Login e Validacao",
  "descricao": "Testa o login no sistema",
  "configuracoes": {
    "timeout": 30000,
    "largura": 1366,
    "altura": 768
  },
  "passos": [
    { "acao": "goto", "url": "https://eprod.al.rs.gov.br/", "descricao": "Acessar sistema" },
    { "acao": "fill", "seletor": "[name='userName']", "valor": "${EPROD_USERNAME}", "descricao": "Preencher Usuario" },
    { "acao": "fill", "seletor": "[name='password']", "valor": "${EPROD_PASSWORD}", "descricao": "Preencher Senha" },
    { "acao": "click", "seletor": "button[type='submit']", "descricao": "Clicar em Entrar" },
    { "acao": "assert", "tipo": "elemento_visivel", "seletor": ".dashboard-header", "descricao": "Validar login" }
  ]
}


### Dicionario de Acoes Disponiveis

| Acao | Parametros | Descricao |
| --- | --- | --- |
| goto | url | Navega para a pagina especificada |
| fill | seletor, valor | Preenche um input com texto |
| click | seletor | Clica em um elemento |
| wait | tempo ou seletor | Aguarda ms fixos ou um elemento aparecer no DOM |
| select | seletor, valor | Seleciona opcao em dropdown |
| busca_fracionada| seletor, tentativas| Injeta fragmentos de string em sequencia para validar inputs e exceptions |
| screenshot | nome (opcional) | Captura a tela atual manualmente |
| assert | tipo, seletor/valor | Valida uma condicao (veja abaixo) |

### Tipos de Validacao (Assert)

| Tipo | Parametros | Descricao |
| --- | --- | --- |
| url_contem | valor | Verifica se a string esta na URL atual |
| elemento_visivel | seletor | Valida se o seletor esta renderizado e visivel na tela |
| texto_visivel | texto | Valida se um texto especifico esta renderizado na tela |
| valor_igual | seletor, esperado | Checa se o conteudo de um input corresponde ao esperado |

---

## Evidencias e Logs

Apos a execucao, as evidencias sao salvas automaticamente na pasta evidence/:

* Screenshots: evidence/screenshots/{ambiente}/{modulo}/
* Videos: evidence/videos/{ambiente}/{modulo}/ (se configurado no JSON do teste)
* Logs: evidence/logs/ (Historico de passos executados, sucesso e erros capturados)

---

## Troubleshooting Rapido

* Timeout exceeded: O site demorou a responder ou o seletor mudou. Aumente o timeout global no JSON ou adicione um passo wait apontando para o seletor antes da acao.
* Variavel de ambiente nao encontrada: Verifique se o .env esta na raiz do projeto e se a nomenclatura das chaves coincide exatamente com o JSON ou com a configuracao do Azure/Gemini.
* Elemento nao clicavel: Pode estar fora da area visivel ou oculto por um modal. Experimente usar uma acao de scroll antes do clique ou verifique as dimensoes do viewport nas configuracoes.

---

Autor: Jean Soares
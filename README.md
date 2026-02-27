
```markdown
# E-pro Test Framework

Framework em Python para automação de testes de regressão e validação de interface web do sistema E-pro. Utiliza Playwright e configurações declarativas em JSON, gerando evidências de forma automática.

## Quick Start

### 1. Pré-requisitos
- Python 3.8 ou superior
- Playwright

### 2. Instalação
```bash
pip install -r requirements.txt
python -m playwright install chromium

```

### 3. Configuração de Ambiente

O projeto utiliza variáveis de ambiente para gerenciar credenciais, evitando a exposição de dados sensíveis.

```bash
cp .env.example .env

```

Edite o arquivo `.env` gerado com suas credenciais de acesso (`EPROD_USERNAME` e `EPROD_PASSWORD`). Nunca versione este arquivo.

### 4. Executando os Testes

Utilize o executor central na raiz do projeto:

```bash
# Executar todos os testes de uma suíte (pasta)
python run.py --suite tests/contas_de_usuarios/grupos

# Executar um teste específico (arquivo JSON)
python run.py --test tests/contas_de_usuarios/grupos/grupos.json

```

---

## Estrutura do Projeto

A arquitetura isola configurações, massa de dados e o motor de execução principal:

```text
web-test-framework/
├── config/environments/ # Configurações e URLs por ambiente (Dev, HML, Stage)
├── evidence/            # Output de testes (Screenshots, Vídeos e Logs)
├── src/testador/        # Motor principal (Playwright + parser de JSON)
├── tests/               # Suítes de testes separadas por módulo (Arquivos JSON)
├── .env                 # Variáveis locais (Ignorado pelo Git)
└── run.py               # Ponto de entrada único para execução

```

---

## Escrevendo Testes (Configuração JSON)

Os testes são definidos estritamente em arquivos JSON. Variáveis do `.env` podem ser injetadas utilizando a sintaxe `${VARIAVEL}`.

**Exemplo Básico (`happy_path.json`):**

```json
{
  "nome": "Login e Validação",
  "descricao": "Testa o login no sistema",
  "configuracoes": {
    "timeout": 30000,
    "largura": 1366,
    "altura": 768
  },
  "passos": [
    { "acao": "goto", "url": "[https://eprod.al.rs.gov.br/](https://eprod.al.rs.gov.br/)", "descricao": "Acessar sistema" },
    { "acao": "fill", "seletor": "[name='userName']", "valor": "${EPROD_USERNAME}", "descricao": "Preencher Usuário" },
    { "acao": "fill", "seletor": "[name='password']", "valor": "${EPROD_PASSWORD}", "descricao": "Preencher Senha" },
    { "acao": "click", "seletor": "button[type='submit']", "descricao": "Clicar em Entrar" },
    { "acao": "assert", "tipo": "elemento_visivel", "seletor": ".dashboard-header", "descricao": "Validar login" }
  ]
}

```

### Dicionário de Ações Disponíveis

| Ação | Parâmetros | Descrição |
| --- | --- | --- |
| `goto` | `url` | Navega para a página especificada |
| `fill` | `seletor`, `valor` | Preenche um input com texto |
| `click` | `seletor` | Clica em um elemento |
| `wait` | `tempo` ou `seletor` | Aguarda ms fixos ou um elemento aparecer no DOM |
| `select` | `seletor`, `valor` | Seleciona opção em dropdown |
| `screenshot` | `nome` (opcional) | Captura a tela atual manualmente |
| `assert` | `tipo`, `seletor`/`valor` | Valida uma condição (veja abaixo) |

### Tipos de Validação (Assert)

| Tipo | Parâmetros | Descrição |
| --- | --- | --- |
| `url_contem` | `valor` | Verifica se a string está na URL atual |
| `elemento_visivel` | `seletor` | Valida se o seletor está renderizado e visível na tela |
| `texto_visivel` | `texto` | Valida se um texto específico está renderizado na tela |
| `valor_igual` | `seletor`, `esperado` | Checa se o conteúdo de um input corresponde ao esperado |

---

## Evidências e Logs

Após a execução, as evidências são salvas automaticamente na pasta `evidence/`:

* **Screenshots:** `evidence/screenshots/{ambiente}/{modulo}/`
* **Vídeos:** `evidence/videos/{ambiente}/{modulo}/` (se configurado no JSON do teste)
* **Logs:** `evidence/logs/` (Histórico de passos executados, sucesso e erros capturados)

---

## Troubleshooting Rápido

* **`Timeout exceeded`:** O site demorou a responder ou o seletor mudou. Aumente o `timeout` global no JSON ou adicione um passo `wait` apontando para o seletor antes da ação.
* **`Variável de ambiente não encontrada`:** Verifique se o `.env` está na raiz do projeto e se a nomenclatura das chaves coincide exatamente com o JSON.
* **Elemento não clicável:** Pode estar fora da área visível ou oculto por um modal. Experimente usar uma ação de `scroll` antes do clique ou verifique as dimensões do viewport nas configurações.

---

**Autor:** Jean Soares

```

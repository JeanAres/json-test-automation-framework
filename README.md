# Sistema de Testes Automatizados - E-pro

Sistema de testes automatizados para aplicação web do E-pro, utilizando Playwright e configuração baseada em JSON com suporte a múltiplos ambientes.

## Descrição

Este sistema permite criar e executar testes automatizados de interface web de forma simples e configurável. Cada teste é definido através de um arquivo JSON que descreve os passos a serem executados, sem necessidade de programação complexa. Agora com suporte a múltiplos ambientes (dev, homolog, stage) e executor único.

## Estrutura do Projeto
```
web-test-framework/
│
├── .env                          # Credenciais reais (NÃO versionar)
├── .env.example                  # Template de credenciais
├── .gitignore                   # Arquivos ignorados
├── requirements.txt             # Dependências
├── run.py                       # Executor único de testes
│
├── src/
│   └── testador/
│       ├── __init__.py
│       └── testador_json.py     # Motor principal
│
├── tests/
│   └── exemplos/               # Seus arquivos JSON
│       ├── teste_abertura_PL.json
│       ├── teste_cargos.json
│       └── ...
│
├── evidence/                   # Evidências
│   ├── screenshots/
│   │   ├── dev/
│   │   ├── homolog/
│   │   └── stage/
│   ├── videos/
│   │   ├── dev/
│   │   ├── homolog/
│   │   └── stage/
│   └── textos_teste/          # Arquivos .txt para preenchimento
│
├── config/
│   └── environments/          # URLs por ambiente
│       ├── dev.json
│       ├── homolog.json
│       └── stage.json
│
└── scripts/                   # Scripts auxiliares (opcional)
```

## Requisitos

### Software Necessário
- Python 3.8 ou superior
- Playwright
- python-dotenv (para gerenciamento de variáveis de ambiente)
- Navegador Brave (opcional, usa Chromium se não disponível)

### Instalação
```bash
# Instalar dependências
pip install playwright
pip install python-dotenv

# Instalar navegadores do Playwright
python -m playwright install chromium
```

### Configuração Inicial

O sistema utiliza variáveis de ambiente para armazenar credenciais e outras informações sensíveis, evitando que sejam expostas no código ou arquivos JSON versionados.

1. **Copie o arquivo de exemplo:**
  
   cp .env.example .env
   2. **Edite o arquivo `.env`** com suas credenciais:
   EPROD_USERNAME=seu_usuario@email.com
   EPROD_PASSWORD=sua_senha_aqui
   3. **Importante:** O arquivo `.env` não deve ser versionado no Git. Ele já está incluído no `.gitignore`.

### Usando Variáveis de Ambiente nos Testes

Nos arquivos JSON de teste, você pode usar variáveis de ambiente através da sintaxe `${NOME_DA_VARIAVEL}`:
son
{
  "acao": "fill",
  "seletor": "[name='userName']",
  "valor": "${EPROD_USERNAME}",
  "descricao": "Preencher usuário"
},
{
  "acao": "fill",
  "seletor": "[name='password']",
  "valor": "${EPROD_PASSWORD}",
  "descricao": "Preencher senha"
}**Nota:** O sistema substitui automaticamente `${VARIAVEL}` pelo valor correspondente do arquivo `.env` durante a execução do teste.

### Boas Práticas de Segurança

- **Nunca commite** o arquivo `.env` no Git
-  Use nomes específicos para variáveis (ex: `EPROD_USERNAME` em vez de `USERNAME`)
-  Mantenha o arquivo `.env.example` atualizado (sem valores reais)
-  Use diferentes arquivos `.env` para ambientes diferentes (dev, staging, prod)

## Componentes do Sistema

### testador.py
Motor principal que executa os testes. Responsável por:
- Interpretar configurações JSON
- Controlar o navegador
- Executar ações e validações
- Capturar screenshots e gravar vídeos
- Gerar relatórios

### Arquivo JSON de Teste
Define os passos do teste de forma declarativa:
```json
{
  "nome": "Nome do Teste",
  "descricao": "Descrição do que o teste faz",
  "configuracoes": {
    "timeout": 30000,
    "slow_motion": 1000,
    "largura": 1366,
    "altura": 768,
    "idioma": "pt-BR"
  },
  "passos": [
    {
      "acao": "goto",
      "url": "https://exemplo.com",
      "descricao": "Acessar página"
    },
    {
      "acao": "fill",
      "seletor": "#campo",
      "valor": "texto",
      "descricao": "Preencher campo"
    }
  ]
}
```

### Script de Execução
Script Python que inicializa o testador e executa o teste específico:
```python
from testador import TestadorJSON

testador = TestadorJSON(
    pasta_screenshots="screenshots_nomedoteste",
    pasta_videos="videos_nomedoteste"
)

resultado = testador.executar_teste(
    arquivo_json="teste_nomedoteste.json",
    headless=False,
    navegador="brave",
    gravar_video=True
)
```

## Ações Disponíveis

| Ação | Descrição | Parâmetros Obrigatórios | Parâmetros Opcionais |
|------|-----------|------------------------|---------------------|
| `goto` | Navega para URL | `url` | - |
| `fill` | Preenche campo | `seletor`, `valor` | - |
| `click` | Clica em elemento | `seletor` | - |
| `wait` | Aguarda tempo/elemento | `tempo` OU `seletor` | - |
| `press` | Pressiona tecla | `seletor`, `tecla` | - |
| `select` | Seleciona opção em dropdown | `seletor`, `valor` | - |
| `check` | Marca checkbox | `seletor` | - |
| `uncheck` | Desmarca checkbox | `seletor` | - |
| `hover` | Passa mouse sobre elemento | `seletor` | - |
| `screenshot` | Captura tela | - | `nome` |
| `assert` | Valida condição | `tipo`, [varia por tipo] | - |
| `scroll` | Rola página | - | `posicao` |
| `javascript` | Executa código JS | `codigo` | - |

**Nota:** Todos os passos devem ter o campo `descricao` para documentação.

## Tipos de Validação (Assert)

| Tipo | Descrição | Parâmetros | Exemplo de Uso |
|------|-----------|------------|----------------|
| `url_contem` | Verifica se URL contém texto | `valor` | Confirmar redirecionamento |
| `titulo_contem` | Verifica se título contém texto | `valor` | Validar página carregada |
| `texto_visivel` | Verifica se texto está visível | `texto` | Confirmar mensagem exibida |
| `elemento_visivel` | Verifica se elemento está visível | `seletor` | Validar botão apareceu |
| `elemento_existe` | Verifica se elemento existe no DOM | `seletor` | Checar presença de campo |
| `valor_igual` | Verifica valor de input | `seletor`, `esperado` | Validar campo preenchido |
| `pagina_contem` | Verifica se página contém texto | `texto` | Buscar conteúdo específico |

## Criando um Novo Teste

### Passo 1: Identificar categoria e subcategoria

Determine onde seu teste se encaixa na estrutura:
- **Categoria:** Item da sidebar do sistema (ex: "Contas de Usuário", "Gestão Documental")
- **Subcategoria:** Funcionalidade específica (ex: "Grupos", "Usuários")

### Passo 2: Criar estrutura de diretórios
# Exemplo: teste de editar grupo
cd testeAutomatizado/contasDeUsuario/Grupos
mkdir testeEditarGrupo
cd testeEditarGrupo
mkdir screenshots_editar
mkdir videos_editar

### Passo 3: Copiar testador.py
# Copie o testador.py de um teste existente da mesma categoria
cp ../testeCriarGrupo/testador.py .

### Passo 4: Criar arquivo JSON do teste

Crie `teste_editar_grupo.json`:
{
  "nome": "Teste de Editar Grupo",
  "descricao": "Valida fluxo de edição de grupo",
  "configuracoes": {
    "timeout": 20000,
    "slow_motion": 800,
    "largura": 1366,
    "altura": 768,
    "idioma": "pt-BR"
  },
  "passos": [
    {
      "acao": "goto",
      "url": "https://eprod.al.rs.gov.br/",
      "descricao": "Acessar sistema"
    },
    {
      "acao": "fill",
      "seletor": "[name='userName']",
      "valor": "${EPROD_USERNAME}",
      "descricao": "Preencher usuário"
    },
    {
      "acao": "fill",
      "seletor": "[name='password']",
      "valor": "${EPROD_PASSWORD}",
      "descricao": "Preencher senha"
    }
  ]
}**Importante:** Use variáveis de ambiente (`${EPROD_USERNAME}`, `${EPROD_PASSWORD}`) em vez de valores hardcoded para credenciais.

### Passo 5: Criar script de execução

Crie `rodar_editar_grupo.py`:
"""
Script de Execução de Teste - Editar Grupo
===========================================

Executa teste automatizado de edição de grupo no sistema eProd.

Uso:
    python rodar_editar_grupo.py

Autor: Jean Soares
Data: Janeiro 2026
"""

from testador import TestadorJSON


def main():
    testador = TestadorJSON(
        pasta_screenshots="screenshots_editar",
        pasta_videos="videos_editar"
    )
    
    print("="*60)
    print("TESTE AUTOMATIZADO: EDITAR GRUPO")
    print("="*60)
    
    resultado = testador.executar_teste(
        arquivo_json="teste_editar_grupo.json",
        headless=False,
        navegador="brave",
        gravar_video=True
    )
    
    if resultado['sucesso']:
        print("\nTESTE PASSOU COM SUCESSO")
    else:
        print(f"\nTESTE FALHOU: {resultado['erro']}")
    
    input("\nPressione ENTER para fechar...")


if __name__ == "__main__":
    main()### Passo 6: Executar o teste
python rodar_editar_grupo.py## Descobrindo Seletores

Para identificar seletores CSS corretos dos elementos:

1. Abra o site no navegador
2. Pressione `F12` para abrir DevTools
3. Clique no ícone de seleção (seta no canto superior esquerdo)
4. Clique no elemento desejado
5. No código HTML destacado, procure por:
   - `id="..."` → Use `#id`
   - `name="..."` → Use `[name="..."]`
   - `class="..."` → Use `.classe`

**Exemplos:**
<input id="usuario" />           → "#usuario"
<input name="password" />        → "[name='password']"
<button class="btn-primary" />   → ".btn-primary"
<button>Entrar</button>          → "button:has-text('Entrar')"## Saídas do Teste

### Screenshots
- **Localização:** Pasta `screenshots_[nome]/`
- **Formato:** `{contador}_{timestamp}_{nome}.png`
- **Quando:** Capturados em passos com `"acao": "screenshot"` ou com `"screenshot": true`
- **Conteúdo:** Página completa (full page)

### Vídeos
- **Localização:** Pasta `videos_[nome]/`
- **Formato:** `{timestamp}_{nome_teste}.webm`
- **Quando:** Durante toda a execução do teste (se `gravar_video=True`)
- **Qualidade:** Resolução configurada em `configuracoes.largura` e `altura`

### Relatório Console
Exibido ao final da execução contendo:
- Nome do teste
- Status (PASSOU/FALHOU)
- Passos executados vs total
- Tempo de execução
- Mensagens de erro (se houver)
- Localização de screenshots e vídeos

### Logs
- Armazenados internamente no objeto `testador.logs`
- Contém timestamp, mensagem e tipo de cada evento
- Acessíveis programaticamente após execução do teste

## Manutenção

### Adicionar Nova Ação

1. Abra `testador.py`
2. Localize o método `_executar_passo()`
3. Adicione novo bloco `elif` com a ação:
elif acao == 'nova_acao':
    # Implemente a lógica da ação
    page.metodo_playwright(passo['parametro'])4. Documente a nova ação neste README
5. Atualize a tabela de "Ações Disponíveis"
6. **Importante:** Propague a atualização para todos os `testador.py` existentes

### Corrigir Seletores

Se um teste falhar devido a mudanças na interface:

1. Abra o screenshot do erro na pasta `screenshots_[nome]/`
2. Identifique o novo seletor usando DevTools (F12) no navegador
3. Atualize o seletor no arquivo JSON do teste
4. Execute novamente o teste para validar

### Ajustar Timeouts

Se testes falharem por timeout:

1. **Ajuste global:** Edite `configuracoes.timeout` no JSON (valor em milissegundos)
2. **Ajuste pontual:** Adicione passo `wait` com tempo específico antes da ação problemática
3. **Diminuir velocidade:** Aumente `configuracoes.slow_motion` para execução mais lenta

Exemplo:
{
  "acao": "wait",
  "tempo": 5000,
  "descricao": "Aguardar carregamento pesado"
}## Troubleshooting

### Variável de ambiente não encontrada
**Sintoma:** Erro `Variável de ambiente 'VARIAVEL' não encontrada no arquivo .env`

**Soluções:**
- Verifique se o arquivo `.env` existe na raiz do projeto
- Confirme que a variável está escrita corretamente (case-sensitive)
- Certifique-se de que não há espaços extras: `VARIAVEL=valor` (sem espaços ao redor do `=`)
- Verifique se o arquivo `.env` está na mesma pasta onde você executa o teste

### Navegador não abre
**Sintoma:** Erro ao tentar iniciar navegador

**Soluções:**
- Verifique instalação: `python -m playwright install chromium`
- Confirme caminho do Brave em `testador.py` (método `_inicializar_navegador`)
- Tente com navegador padrão alterando `navegador="chromium"` no script

### Seletor não encontrado
**Sintoma:** `Timeout exceeded` ao aguardar elemento

**Soluções:**
- Use DevTools (F12) para verificar se seletor está correto
- Adicione `wait` antes da ação para dar tempo de carregamento
- Aumente timeout nas configurações do teste
- Verifique se elemento não está dentro de iframe

### Vídeo não gravado
**Sintoma:** Teste executa mas vídeo não aparece

**Soluções:**
- Verifique se pasta `videos_[nome]/` existe e tem permissões de escrita
- Confirme que `gravar_video=True` no script de execução
- Verifique logs de erro no console

### Screenshots em branco
**Sintoma:** Screenshots capturados mas exibem página em branco

**Soluções:**
- Aumente tempo de espera antes do screenshot
- Verifique se página carregou completamente com `wait`
- Confirme que não há overlays ou modals bloqueando conteúdo

### Elementos não clicáveis
**Sintoma:** Erro "element is not visible" ou "element is outside viewport"

**Soluções:**
- Adicione `scroll` antes do `click`
- Use `wait` para garantir que elemento está pronto
- Verifique se elemento não está coberto por outro

### Teste funciona manualmente mas falha automatizado
**Sintoma:** Ações que funcionam manualmente falham no teste

**Soluções:**
- Reduza `slow_motion` para velocidade mais próxima da manual
- Adicione `wait` entre ações que dependem de animações/transições
- Verifique se não há detecção de automação bloqueando ações

## Boas Práticas

### Nomenclatura
1. **Categorias:** Nome do item da sidebar: `contasDeUsuario`, `documentos`
2. **Subcategorias:** Funcionalidade específica: `Grupos`, `Usuarios`
3. **Testes:** Ação + contexto: `testeCriarGrupo`, `testeEditarUsuario`
4. **Arquivos JSON:** Prefixe com `teste_`: `teste_criar_grupo.json`
5. **Scripts:** Prefixe com `rodar_`: `rodar_criar_grupo.py`
6. **Pastas de output:** Use sufixo descritivo: `screenshots_grupo/`, `videos_login/`

### Estruturação de Testes
1. **Modularize:** Separe testes longos em múltiplos testes menores
2. **Reutilize:** Crie testes de setup (login) que outros testes podem importar
3. **Documente:** Sempre preencha campo `descricao` em cada passo
4. **Screenshots estratégicos:** Capture telas em pontos críticos, não em todos os passos

### Organização
1. **Um teste por funcionalidade:** Não misture múltiplos fluxos em um teste
2. **Versionamento:** Use Git para controlar versões de testes
3. **Dados sensíveis:** **NUNCA** commite credenciais em arquivos JSON. Use sempre variáveis de ambiente (`${VARIAVEL}`)
4. **Arquivo .env:** Mantenha o `.env` no `.gitignore` e use `.env.example` como template
5. **Limpeza:** Delete screenshots/vídeos antigos periodicamente
6. **Hierarquia clara:** Mantenha categoria → subcategoria → teste

### Segurança
1. **Credenciais:** Use sempre variáveis de ambiente, nunca valores hardcoded
2. **Nomes de variáveis:** Use nomes específicos (ex: `EPROD_USERNAME`) para evitar conflitos com variáveis do sistema
3. **Gitignore:** Certifique-se de que `.env` está no `.gitignore`
4. **Compartilhamento:** Compartilhe apenas o `.env.example`, nunca o `.env` real

### Performance
1. **Headless quando possível:** Use `headless=True` para testes em CI/CD
2. **Timeouts adequados:** Não use timeouts muito altos desnecessariamente
3. **Vídeos opcionais:** Desative gravação (`gravar_video=False`) para testes rápidos
4. **Seletores eficientes:** Prefira IDs e atributos únicos a classes genéricas

### Manutenibilidade
1. **Comente alterações:** Documente mudanças significativas nos testes
2. **Versionamento semântico:** Use tags Git para releases de testes
3. **Changelog:** Mantenha histórico de alterações importantes
4. **Testes de regressão:** Mantenha testes antigos funcionando após mudanças
5. **Atualize testador.py:** Ao melhorar o motor, propague para todos os testes

## Configurações Avançadas

### Slow Motion
Controla atraso entre ações (em milissegundos):
"configuracoes": {
  "slow_motion": 1000  // 1 segundo entre cada ação
}**Recomendações:**
- Desenvolvimento/Debug: 800-1500ms
- Execução normal: 300-500ms
- CI/CD automatizado: 0ms

### Viewport (Resolução)
Define tamanho da janela do navegador:
"configuracoes": {
  "largura": 1920,  // Largura em pixels
  "altura": 1080    // Altura em pixels
}**Resoluções comuns:**
- Desktop: 1920x1080, 1366x768
- Tablet: 768x1024
- Mobile: 375x667

### Timeout Global
Tempo máximo de espera para ações (em milissegundos):
"configuracoes": {
  "timeout": 30000  // 30 segundos
}**Recomendações:**
- Páginas rápidas: 10000-15000ms
- Páginas com carregamento pesado: 30000-60000ms
- APIs lentas: até 120000ms

## Integração Contínua

### GitHub Actions

Crie `.github/workflows/testes.yml`:
name: Testes Automatizados

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Setup Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.10'
      
      - name: Install dependencies
        run: |
          pip install playwright python-dotenv
          python -m playwright install chromium
      
      - name: Setup environment variables
        run: |
          cp .env.example .env
          # Configure as variáveis de ambiente via secrets do GitHub
          echo "EPROD_USERNAME=${{ secrets.EPROD_USERNAME }}" >> .env
          echo "EPROD_PASSWORD=${{ secrets.EPROD_PASSWORD }}" >> .env
      
      - name: Run tests
        run: |
          cd contasDeUsuario/Grupos/testeCriarGrupo
          python rodar_criar_grupo.py
      
      - name: Upload screenshots
        if: failure()
        uses: actions/upload-artifact@v2
        with:
          name: screenshots
          path: contasDeUsuario/Grupos/testeCriarGrupo/screenshots_grupo/## Histórico de Versões

### v1.1.0 (Janeiro 2026)
- Adicionado suporte a variáveis de ambiente via arquivo `.env`
- Implementada substituição automática de variáveis nos arquivos JSON
- Adicionado arquivo `.env.example` como template
- Melhorias na segurança: credenciais não são mais hardcoded
- Documentação atualizada com seção de configuração de variáveis de ambiente

### v1.0.0 (Janeiro 2026)
- Versão inicial do sistema
- Suporte a testes baseados em JSON
- Gravação automática de vídeo
- Captura de screenshots
- Suporte a múltiplos navegadores (Chromium, Firefox, WebKit, Brave)
- Documentação completa
- Sistema de logs
- Relatórios detalhados
- Estrutura hierárquica (Categoria → Subcategoria → Teste)

## Suporte

Para questões ou problemas:

1. **Consulte primeiro:**
   - Seção Troubleshooting deste README
   - Logs de erro no console
   - Screenshots/vídeos do teste falhado

2. **Debug:**
   - Execute teste com `slow_motion` alto para visualizar
   - Adicione screenshots extras em pontos problemáticos
   - Verifique seletores no DevTools
   - Verifique se as variáveis de ambiente estão configuradas corretamente

3. **Documente:**
   - Anote mensagem de erro completa
   - Capture screenshot do problema
   - Liste passos para reproduzir

## Autor

**Jean Soares**
- Email: jean06soares@gmail.com

## Licença

Uso interno - Jean Soares
"""
Sistema de Testes Automatizados Baseado em JSON
================================================

Este módulo fornece uma classe TestadorJSON que permite executar testes
automatizados de interface web usando Playwright, configurados através de
arquivos JSON.

Características:
- Execução de testes baseados em JSON
- Suporte a múltiplos navegadores (Chromium, Firefox, WebKit, Brave)
- Gravação automática de vídeo
- Captura de screenshots
- Geração de relatórios detalhados
- Sistema de logs
- Suporte a variáveis de ambiente via arquivo .env
- Suporte a variáveis dinâmicas capturadas durante a execução
- Suporte a múltiplas abas do navegador
- Suporte avançado para PDFs e Shadow DOM
- Interceptação de APIs para capturar PDFs
- Suporte a múltiplos ambientes (dev, homolog, stage)

Dependências:
    pip install playwright python-dotenv
    python -m playwright install chromium

Autor: Jean Soares
Data: Março 2026
Versão: 1.8.0 (com suporte a ambientes)
"""

import json
import os
import random
import time
import psycopg2
import re
import copy
import sys
from datetime import datetime
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
from dotenv import load_dotenv


load_dotenv()


class TestadorJSON:
    """
    Classe responsável por executar testes automatizados de interface web
    baseados em configurações JSON.
    
    A classe gerencia a execução de testes, captura de screenshots, gravação
    de vídeos e geração de relatórios.
    
    Attributes:
        screenshots_dir (str): Diretório para armazenar screenshots
        videos_dir (str): Diretório para armazenar vídeos
        logs (list): Lista de logs da execução
        screenshot_count (int): Contador de screenshots capturados
        variaveis (dict): Dicionário para armazenar variáveis dinâmicas capturadas
    """
    
    def __init__(self, pasta_screenshots="test_screenshots", pasta_videos="videos"):
        """
        Inicializa o testador com diretórios para screenshots e vídeos.
        
        Args:
            pasta_screenshots (str): Nome do diretório para screenshots.
                                    Padrão: "test_screenshots"
            pasta_videos (str): Nome do diretório para vídeos.
                               Padrão: "videos"
        
        Nota:
            Os diretórios são criados automaticamente se não existirem.
        """
        self.screenshots_dir = pasta_screenshots
        self.videos_dir = pasta_videos
        self.logs = []
        self.screenshot_count = 0
        self.variaveis = {}  # Armazena variáveis capturadas durante a execução
        self.pdf_viewers_detected = []  # Para armazenar tipos de visualizadores PDF detectados
        self.cenario_atual = None  # Nome do cenário atual sendo executado
        self.ambiente_atual = None  # Ambiente atual (dev, homolog, stage)
        
        # Cria diretórios se não existirem
        os.makedirs(self.screenshots_dir, exist_ok=True)
        os.makedirs(self.videos_dir, exist_ok=True)

    def validar_ordenacao_coluna(self, page, seletor_coluna, seletor_itens, parametro_url="name", modo_debug=False):
        """
        Clica em uma coluna para ordenar, valida a URL e se a ordem dos itens foi invertida.

        Args:
            page: Objeto page do Playwright.
            seletor_coluna: Seletor CSS do botão/cabeçalho da coluna para clicar
            seletor_itens: Seletor CSS para capturar a lista de itens na coluna.
            parametro_url: O valor da parametro 'orderProperty' esperando na URL 
            modo_debug: Se True, imprime detalhes da validação.

        Returns:
            bool: Retorna True se a ordenação (URL e dados) funcionou corretamente.
        """
        if modo_debug:
            print(f"[Ordenação] Primeiro clique em: {seletor_coluna}")
        
        page.click(seletor_coluna)
        page.wait_for_timeout(500)

        url_atual = page.url
        if f"orderDir=desc" not in url_atual and f"orderDir=asc" not in url_atual:
            print("[Ordenação] URL não reflete a ordenação após o primeiro clique.")
            if modo_debug: 
                print(f"URL atual: {url_atual}")

        primeira_lista = page.evaluate(f"""
            () => {{
                const itens = [...document.querySelectorAll('{seletor_itens}')].map(el => el.textContent.trim()).filter(item => item);
                return itens;
            }}
        """)
        
        if modo_debug:
            print(f"[Ordenação] Primeira lista capturada ({len(primeira_lista)} itens): {primeira_lista[:5]}...")

        if len(primeira_lista) == 0:
            print("[Ordenação] Nenhum item encontrado na primeira captura.")
            return False

        if modo_debug:
            print(f"[Ordenação] Segundo clique em: {seletor_coluna}")

        page.click(seletor_coluna)
        page.wait_for_timeout(500)

        url_atual = page.url
        if f"orderDir=desc" not in url_atual and f"orderDir=asc" not in url_atual:
            print("[Ordenação] URL não reflete a ordenação após o segundo clique.")
            if modo_debug: 
                print(f"URL atual: {url_atual}")
            return False

        segunda_lista = page.evaluate(f"""
            () => {{
                const itens = [...document.querySelectorAll('{seletor_itens}')].map(el => el.textContent.trim()).filter(item => item);
                return itens; 
            }}
        """)
        
        if modo_debug:
            print(f"[Ordenação] Segunda lista capturada ({len(segunda_lista)} itens): {segunda_lista[:5]}...")

        if len(segunda_lista) == 0:
            print("[Ordenação] Nenhum item encontrado na segunda captura.")
            return False
        
        lista_invertida_esperada = list(reversed(primeira_lista))
        if segunda_lista == lista_invertida_esperada:
            print("[Ordenação] Ordenação validada com sucesso (dados invertidos).")
            return True
        else:
            print("[Ordenação] Falha na validação dos dados. A ordem dos itens não foi invertida.")
            if modo_debug:
                print(f" Primeira lista: {primeira_lista[:5]}...")
                print(f" Segunda lista: {segunda_lista[:5]}...")
                print(f" Esperado (invertido): {lista_invertida_esperada[:5]}...")
            return False

    def carregar_ambiente(self, ambiente=None):
        """
        Carrega configurações do ambiente especificado.
        Ambientes disponíveis: dev, homolog, stage
    
        A URL vem do arquivo JSON em config/environments/
        As credenciais vêm do .env
        """
        import json
        import os
    
        if not ambiente:
            ambiente = os.getenv('AMBIENTE_PADRAO', 'dev')
    
        self.ambiente_atual = ambiente
        ambiente_upper = ambiente.upper()
    
        # ===== 1. CARREGA URL DO ARQUIVO JSON (config/environments/) =====
        caminho_url = f"config/environments/{ambiente}.json"
        if os.path.exists(caminho_url):
            with open(caminho_url, 'r', encoding='utf-8') as f:
                config = json.load(f)
                self.variaveis['URL_BASE'] = config['url_base'].rstrip('/')
                self.variaveis['NOME_AMBIENTE'] = config['nome']
        else:
            print(f"ERRO: Arquivo de ambiente não encontrado: {caminho_url}")
            self.variaveis['URL_BASE'] = 'https://homologacao.al.rs.gov.br'
    
        # ===== 2. CARREGA CREDENCIAIS DO .env =====
        # Admin
        self.variaveis['ADMIN_USER'] = os.getenv(f'{ambiente_upper}_ADMIN_USER')
        self.variaveis['ADMIN_PASS'] = os.getenv(f'{ambiente_upper}_ADMIN_PASS')
    
        # Deputado
        self.variaveis['DEPUTADO_USER'] = os.getenv(f'{ambiente_upper}_DEPUTADO_USER')
        self.variaveis['DEPUTADO_PASS'] = os.getenv(f'{ambiente_upper}_DEPUTADO_PASS')
    
        # Diretor
        self.variaveis['DIRETOR_USER'] = os.getenv(f'{ambiente_upper}_DIRETOR_USER')
        self.variaveis['DIRETOR_PASS'] = os.getenv(f'{ambiente_upper}_DIRETOR_PASS')
    
        print(f"\n{'='*50}")
        print(f"AMBIENTE: {self.variaveis.get('NOME_AMBIENTE', ambiente)}")
        print(f"URL BASE: {self.variaveis['URL_BASE']}")
        print(f"{'='*50}\n")
    
        return self.variaveis.get('URL_BASE')
    
    def executar_teste(self, arquivo_json=None, config_json=None, headless=False, 
                      navegador="chromium", caminho_navegador=None, gravar_video=True,
                      modo_debug=False, ambiente=None):
        """
        Executa um teste automatizado baseado em configuração JSON.
        
        Args:
            arquivo_json (str, optional): Caminho para arquivo JSON de configuração
            config_json (dict, optional): Dicionário com configuração do teste
            headless (bool): Se True, executa navegador em modo headless (sem interface)
            navegador (str): Navegador a ser usado. Opções: "chromium", "firefox", 
                           "webkit", "brave". Padrão: "chromium"
            caminho_navegador (str, optional): Caminho completo para executável do navegador
            gravar_video (bool): Se True, grava vídeo da execução. Padrão: True
            modo_debug (bool): Se True, exibe mais informações de debug. Padrão: False
            ambiente (str, optional): Ambiente a ser carregado (dev, homolog, stage)
        
        Returns:
            dict: Dicionário contendo resultados do teste
        
        Raises:
            ValueError: Se nem arquivo_json nem config_json forem fornecidos
        """
        # Carrega ambiente se especificado
        if ambiente:
            self.carregar_ambiente(ambiente)
        
        # Carrega configuração do teste
        if arquivo_json:
            with open(arquivo_json, 'r', encoding='utf-8') as f:
                config = json.load(f)
        elif config_json:
            config = config_json
        else:
            raise ValueError("Forneça arquivo_json ou config_json")
        
        # Substitui variáveis de ambiente nos passos
        config = self._substituir_variaveis_ambiente(config)
        
        # Exibe informações do teste
        print(f"\n{'='*60}")
        print(f"EXECUTANDO TESTE: {config.get('nome', 'Sem nome')}")
        print(f"{'='*60}\n")
        
        if config.get('descricao'):
            print(f"Descricao: {config['descricao']}\n")
        
        if modo_debug:
            print(f"MODO DEBUG ATIVADO")
            if gravar_video:
                print(f"Gravando video em: {self.videos_dir}/")
        
        # ===== Suporte a estrutura com cenários =====
        # Prepara lista de passos baseado na estrutura do JSON
        if "cenarios" in config:
            # Nova estrutura com cenários
            todos_passos = []
            total_passos = 0
            cenario_ativo_encontrado = False
            
            for cenario in config["cenarios"]:
                # Verifica se o cenário está ativo
                if not cenario.get("ativa", True):
                    if modo_debug:
                        print(f"Cenario '{cenario['nome']}' desativado - Pulando")
                    continue
                
                # Verifica pré-condições
                pre_condicao = cenario.get('pre_condicao')
                if pre_condicao:
                    # Substitui variáveis na pré-condição
                    pre_condicao_avaliada = self._substituir_texto(pre_condicao)
                    # Avalia pré-condição simples
                    if not self._avaliar_pre_condicao(pre_condicao_avaliada):
                        if modo_debug:
                            print(f"Pre-condicao nao atendida para '{cenario['nome']}': {pre_condicao}")
                        continue
                
                cenario_ativo_encontrado = True
                print(f"\nEXECUTANDO CENARIO: {cenario['nome']}")
                print(f"Papel: {cenario.get('papel', 'Nao especificado')}")
                print("-" * 50)
                
                # Adiciona passo de comentário para marcar início do cenário
                todos_passos.append({
                    "acao": "comentario",
                    "mensagem": f"========== CENARIO: {cenario['nome']} ==========",
                    "tipo": "separador",
                    "descricao": f"Inicio do cenario: {cenario['nome']}"
                })
                
                # Adiciona passo de papel
                if 'papel' in cenario:
                    todos_passos.append({
                        "acao": "comentario",
                        "mensagem": f"Papel: {cenario['papel']}",
                        "tipo": "papel",
                        "descricao": f"Definir papel: {cenario['papel']}"
                    })
                
                # Adiciona passos do cenário à lista geral
                if 'passos' in cenario:
                    for passo in cenario['passos']:
                        # Marca o passo com o cenário de origem para logs
                        passo['_cenario'] = cenario['nome']
                        todos_passos.append(passo)
                        total_passos += 1
                
                # Adiciona passo de fim de cenário
                todos_passos.append({
                    "acao": "comentario",
                    "mensagem": f"FIM DO CENARIO: {cenario['nome']}",
                    "tipo": "fim_cenario",
                    "descricao": f"Fim do cenario: {cenario['nome']}"
                })
            
            if not cenario_ativo_encontrado:
                print("ATENCAO: Nenhum cenario ativo encontrado no arquivo JSON")
                todos_passos = []
                total_passos = 0
        else:
            # Estrutura antiga (backward compatibility)
            todos_passos = config.get('passos', [])
            total_passos = len(todos_passos)
        
        # Inicializa estrutura de resultados
        resultado = {
            "nome": config.get('nome', 'Teste'),
            "sucesso": False,
            "passos_executados": 0,
            "passos_total": total_passos,
            "erro": None,
            "screenshots": [],
            "video": None,
            "tempo_execucao": None,
            "variaveis": {},
            "pdf_viewers": self.pdf_viewers_detected,
            "cenario_atual": None,
            "ambiente": self.ambiente_atual
        }
        
        inicio = datetime.now()
        
        try:
            with sync_playwright() as p:
                # Obtém configurações do navegador do JSON
                browser_config = config.get('configuracoes', {})
                
                # Seleciona e inicializa o navegador
                browser = self._inicializar_navegador(
                    p, navegador, caminho_navegador, 
                    headless, browser_config
                )
                
                # Configura contexto do navegador com suporte a PDFs
                context_options = self._configurar_contexto(
                    browser_config, gravar_video
                )
                
                context = browser.new_context(**context_options)
                page = context.new_page()
                page.set_default_timeout(browser_config.get('timeout', 60000))
                
                # Executa cada passo do teste
                for i, passo in enumerate(todos_passos, 1):
                    # Atualiza cenário atual se necessário
                    if '_cenario' in passo and passo['_cenario'] != self.cenario_atual:
                        self.cenario_atual = passo['_cenario']
                        resultado["cenario_atual"] = self.cenario_atual
                    
                    # Captura o retorno para suportar troca de abas
                    page_retornada = self._executar_passo(page, passo, i, resultado, modo_debug)
                    if page_retornada is not None:
                        page = page_retornada
                    resultado["passos_executados"] = i
                
                resultado["sucesso"] = True
                resultado["variaveis"] = self.variaveis.copy()
                resultado["pdf_viewers"] = self.pdf_viewers_detected.copy()
                
                # Finaliza gravação de vídeo
                if gravar_video:
                    video_path = page.video.path()
                    resultado["video"] = video_path
                
                context.close()
                browser.close()
                
                # Renomeia vídeo com timestamp e nome do teste
                if gravar_video and resultado["video"]:
                    resultado["video"] = self._renomear_video(
                        resultado["video"], config.get('nome', 'teste')
                    )
                
        except Exception as e:
            resultado["erro"] = str(e)
            resultado["variaveis"] = self.variaveis.copy()
            resultado["pdf_viewers"] = self.pdf_viewers_detected.copy()
            self._log(f"Erro: {e}", "error")
            if modo_debug:
                print(f"ERRO CRITICO: {e}")
        
        # Calcula tempo total de execução
        resultado["tempo_execucao"] = (datetime.now() - inicio).total_seconds()
        resultado["screenshots"] = self._listar_screenshots()
        
        # Gera relatório final
        self._gerar_relatorio(resultado)
        return resultado
    
    def _avaliar_pre_condicao(self, pre_condicao):
        """
        Avalia uma pré-condição simples.
        
        Args:
            pre_condicao (str): Pré-condição a ser avaliada, ex: "{{numero_processo}} != null"
        
        Returns:
            bool: True se pré-condição for atendida, False caso contrário
        """
        try:
            # Avalia condições simples
            if "!=" in pre_condicao:
                partes = pre_condicao.split("!=")
                if len(partes) == 2:
                    esquerda = partes[0].strip()
                    direita = partes[1].strip()
                    
                    # Remove aspas
                    if (direita.startswith("'") and direita.endswith("'")) or \
                       (direita.startswith('"') and direita.endswith('"')):
                        direita = direita[1:-1]
                    
                    # Avalia
                    valor_esquerda = self._obter_valor_condicao(esquerda)
                    return valor_esquerda != direita
            
            # Condição padrão: se existe e não é vazio
            valor = self._obter_valor_condicao(pre_condicao.strip())
            return bool(valor)
            
        except Exception as e:
            print(f"Erro ao avaliar pre-condicao '{pre_condicao}': {e}")
            return False
    
    def _obter_valor_condicao(self, expressao):
        """
        Obtém valor de uma expressão para avaliação de condições.
        
        Args:
            expressao (str): Expressão a ser avaliada
        
        Returns:
            Valor da expressão
        """
        # Remove chaves se for referência a variável
        if expressao.startswith("{{") and expressao.endswith("}}"):
            var_nome = expressao[2:-2].strip()
            return self.variaveis.get(var_nome)
        else:
            return expressao
    
    def _substituir_variaveis_ambiente(self, config):
        """
        Substitui placeholders ${VARIAVEL} por valores do arquivo .env nos passos do teste.
        
        Agora suporta tanto estrutura antiga (passos) quanto nova (cenarios).
        """
        def substituir_em_passos(passos_lista):
            """Substitui variáveis em uma lista de passos."""
            for passo in passos_lista:
                # Substitui em campos 'valor'
                if 'valor' in passo and isinstance(passo['valor'], str):
                    valor = passo['valor']
                    if valor.startswith('${') and valor.endswith('}'):
                        var_name = valor[2:-1]  # Remove ${ e }
                        env_value = os.getenv(var_name)
                        if env_value:
                            passo['valor'] = env_value
                        else:
                            raise ValueError(
                                f"Variavel de ambiente '{var_name}' nao encontrada no arquivo .env. "
                                f"Certifique-se de que o arquivo .env existe e contem a variavel {var_name}."
                            )
                
                # Substitui em campos 'url' também (caso necessário)
                if 'url' in passo and isinstance(passo['url'], str):
                    url = passo['url']
                    if '${' in url and '}' in url:
                        # Substitui múltiplas variáveis na URL se necessário
                        def substituir_var(match):
                            var_name = match.group(1)
                            env_value = os.getenv(var_name)
                            if env_value:
                                return env_value
                            else:
                                raise ValueError(
                                    f"Variavel de ambiente '{var_name}' nao encontrada no arquivo .env."
                                )
                        passo['url'] = re.sub(r'\$\{(\w+)\}', substituir_var, url)
        
        # Verifica estrutura e substitui variáveis
        if 'passos' in config:
            # Estrutura antiga
            substituir_em_passos(config['passos'])
        elif 'cenarios' in config:
            # Estrutura nova
            for cenario in config['cenarios']:
                if 'passos' in cenario:
                    substituir_em_passos(cenario['passos'])
        
        return config
    
    def _inicializar_navegador(self, playwright, navegador, caminho_navegador, 
                              headless, browser_config):
        """
        Inicializa o navegador especificado com as configurações fornecidas.
        """
        slow_mo = browser_config.get('slow_motion', 0)
        
        # Configuração para Brave
        if navegador == "brave" or caminho_navegador:
            if not caminho_navegador:
                # Caminhos padrão do Brave no Windows
                caminhos_brave = [
                    r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe",
                    r"C:\Program Files (x86)\BraveSoftware\Brave-Browser\Application\brave.exe",
                    os.path.expanduser(r"~\AppData\Local\BraveSoftware\Brave-Browser\Application\brave.exe")
                ]
                for caminho in caminhos_brave:
                    if os.path.exists(caminho):
                        caminho_navegador = caminho
                        break
            
            if caminho_navegador and os.path.exists(caminho_navegador):
                print(f"Usando Brave: {caminho_navegador}\n")
                return playwright.chromium.launch(
                    headless=headless,
                    slow_mo=slow_mo,
                    executable_path=caminho_navegador
                )
            else:
                print("Aviso: Brave nao encontrado, usando Chromium padrao\n")
                return playwright.chromium.launch(headless=headless, slow_mo=slow_mo)
        
        # Outros navegadores
        elif navegador == "firefox":
            return playwright.firefox.launch(headless=headless, slow_mo=slow_mo)
        elif navegador == "webkit":
            return playwright.webkit.launch(headless=headless, slow_mo=slow_mo)
        else:  # chromium padrão
            return playwright.chromium.launch(headless=headless, slow_mo=slow_mo)
    
    def _configurar_contexto(self, browser_config, gravar_video):
        """
        Configura opções do contexto do navegador otimizadas para PDFs.
        """
        context_options = {
            "viewport": {
                "width": browser_config.get('largura', 1280),
                "height": browser_config.get('altura', 720)
            },
            "locale": browser_config.get('idioma', 'pt-BR'),
            "permissions": ["clipboard-read", "clipboard-write"],
            "bypass_csp": True,  # Importante para PDFs
            "accept_downloads": True,  # Permite download de PDFs
            "ignore_https_errors": True
        }
        
        if gravar_video:
            context_options["record_video_dir"] = self.videos_dir
            context_options["record_video_size"] = {
                "width": browser_config.get('largura', 1280),
                "height": browser_config.get('altura', 720)
            }
        
        return context_options
    
    def _executar_passo(self, page, passo, numero, resultado, modo_debug=False):
        """
        Executa um passo individual do teste.
        
        Returns:
            Page ou None: Retorna objeto Page se houve troca de aba, senão None
        """
        acao = passo['acao']
        
        # CORREÇÃO: Para passos de comentário sem descrição, gera uma descrição baseada na mensagem
        if acao == 'comentario' and 'descricao' not in passo:
            mensagem = passo.get('mensagem', '')
            tipo = passo.get('tipo', 'info')
            
            # Remove caracteres de separação (=) e espaços extras
            mensagem_limpa = mensagem.strip('= ').strip()
            
            if tipo == 'separador':
                # Extrai o texto entre os separadores "=========="
                if '==========' in mensagem:
                    partes = mensagem.split('==========')
                    if len(partes) >= 3:
                        # Texto entre os separadores
                        texto_central = partes[1].strip()
                        if texto_central:
                            descricao = texto_central
                        else:
                            descricao = "Separador de secao"
                    else:
                        descricao = "Inicio de secao"
                else:
                    descricao = "Separador"
            elif tipo == 'papel':
                descricao = "Definir papel"
            elif tipo == 'sucesso':
                descricao = "Mensagem de sucesso"
            elif tipo == 'fim_cenario':
                descricao = "Fim do cenario"
            else:
                # Para outros tipos, usa a mensagem (limitada a 40 caracteres)
                if mensagem_limpa:
                    if len(mensagem_limpa) > 40:
                        descricao = mensagem_limpa[:37] + "..."
                    else:
                        descricao = mensagem_limpa
                else:
                    descricao = f"Comentario {numero}"
        else:
            # Usa a descrição fornecida no passo, ou padrão
            descricao = passo.get('descricao', f'Passo {numero}')
        
        # Adiciona informação do cenário se disponível
        cenario_info = ""
        if '_cenario' in passo:
            cenario_info = f" [{passo['_cenario']}]"
        
        if modo_debug:
            print(f"\nPasso {numero}{cenario_info}: {descricao}")
        else:
            print(f"Passo {numero}{cenario_info}: {descricao}")
        
        self._log(f"Executando: {descricao}", "info")
        
        try:
            # Substitui variáveis dinâmicas antes de executar
            passo = self._substituir_variaveis_passo(passo)
            
            # Executa a ação correspondente
            if acao == 'comentario':
                mensagem = self._substituir_texto(passo.get('mensagem', ''))
                tipo = passo.get('tipo', 'info')
                
                if tipo == 'separador':
                    print(f"   --- {mensagem} ---")
                elif tipo == 'papel':
                    print(f"   Papel: {mensagem}")
                elif tipo == 'sucesso':
                    print(f"   [SUCESSO] {mensagem}")
                elif tipo == 'fim_cenario':
                    print(f"   [FIM DO CENARIO] {mensagem}")
                else:
                    print(f"   [COMENTARIO] {mensagem}")
                
                # Adiciona uma pequena pausa para visualização
                page.wait_for_timeout(100)
            
            elif acao == 'log':
                mensagem = self._substituir_texto(passo.get('mensagem', ''))
                nivel = passo.get('nivel', 'INFO')
                print(f"   [{nivel}] {mensagem}")
            
            elif acao == 'goto':
                page.goto(passo['url'])

            elif acao == 'validar_indexacao_api':
                seletor_input = passo['seletor']
                ano_pesquisa = str(passo['ano'])
                url_parcial = passo['url_api_contem']
                chave_total = passo['chave_json_total']

                ambiente = "dev"
                for arg in sys.argv:
                    if arg.startswith("--env="):
                        ambiente = arg.split("=")[1]
                        
                arquivo_historico = f"evidence/logs/{ambiente}/quant_prop_ano.json"
            
                # 1. Escuta a rede AGUARDANDO a requisição disparar, e ENTÃO preenche o campo
                with page.expect_response(lambda response: url_parcial in response.url) as response_info:
                    page.fill(seletor_input, ano_pesquisa)
            
                # 2. Pega o objeto da resposta e já converte o corpo direto para um dicionário Python
                corpo_json = response_info.value.json()
            
                # 3. Extrai o número total de dentro do JSON
                total_atual = int(corpo_json[chave_total])
                
                # 4. Lógica de comparação com execuções anteriores
                historico = {}
                if os.path.exists(arquivo_historico):
                    with open(arquivo_historico, 'r', encoding='utf-8') as f:
                        historico = json.load(f)
                
                if ano_pesquisa in historico and len(historico[ano_pesquisa]) > 0:
                    ultima_execucao = historico[ano_pesquisa][-1]
                    total_anterior = ultima_execucao['total']
                    
                    if total_atual < total_anterior:
                        raise AssertionError(
                            f"Falha na indexação! O ano {ano_pesquisa} tinha {total_anterior} proposições, "
                            f"mas a API retornou apenas {total_atual}."
                        )
                    
                # 5. Salva o novo registro
                novo_registro = {
                    "data_execucao": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "total": total_atual
                }
                
                if ano_pesquisa not in historico:
                    historico[ano_pesquisa] = []

                historico[ano_pesquisa].append(novo_registro)
                    
                os.makedirs(os.path.dirname(arquivo_historico), exist_ok=True)
                with open(arquivo_historico, 'w', encoding='utf-8') as f:
                    json.dump(historico, f, indent=4)

            elif acao == 'fill':
                valor = passo['valor']
                
                # Se o valor começar com "@arquivo:" ou "@file:", carrega o texto do arquivo
                if valor.startswith('@arquivo:') or valor.startswith('@file:'):
                    # Remove o prefixo
                    caminho_arquivo = valor.replace('@arquivo:', '').replace('@file:', '').strip()

                    # Usa a raiz do projeto como base (sobe 2 níveis: testador/ -> src/ -> raiz)
                    raiz_projeto = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                    caminho_completo = os.path.join(raiz_projeto, caminho_arquivo)
                    caminho_completo = os.path.normpath(caminho_completo)

                    if modo_debug:
                        print(f"Procurando arquivo: {caminho_completo}")

                    if not os.path.exists(caminho_completo):
                        # Tenta subir mais um nível (caso esteja em subpasta)
                        raiz_projeto = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                        caminho_completo = os.path.join(raiz_projeto, caminho_arquivo)
                        caminho_completo = os.path.normpath(caminho_completo)

                        if not os.path.exists(caminho_completo):
                            raise FileNotFoundError(f"Arquivo nao encontrado: {caminho_completo}")

                    with open(caminho_completo, 'r', encoding='utf-8') as f:
                        valor = f.read()

                    if modo_debug:
                        print(f"Arquivo carregado: {caminho_completo}")
                        print(f"Tamanho: {len(valor)} caracteres")
                
                # Preenche o campo com o texto
                page.fill(passo['seletor'], valor)
            
            elif acao == 'fill_devexpress':
                """
                Preenche campo DevExpress que abre em modal.
                """
                valor = passo['valor']
                
                # Se o valor começar com "@arquivo:" ou "@file:", carrega o texto do arquivo
                if valor.startswith('@arquivo:') or valor.startswith('@file:'):
                    caminho_arquivo = valor.replace('@arquivo:', '').replace('@file:', '').strip()
                    
                    # Usa a raiz do projeto como base (sobe 2 níveis)
                    raiz_projeto = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                    caminho_completo = os.path.join(raiz_projeto, caminho_arquivo)
                    caminho_completo = os.path.normpath(caminho_completo)
                    
                    if modo_debug:
                        print(f"Procurando arquivo: {caminho_completo}")
                    
                    if not os.path.exists(caminho_completo):
                        # Tenta subir mais um nível
                        raiz_projeto = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                        caminho_completo = os.path.join(raiz_projeto, caminho_arquivo)
                        caminho_completo = os.path.normpath(caminho_completo)
                        
                        if not os.path.exists(caminho_completo):
                            raise FileNotFoundError(f"Arquivo nao encontrado: {caminho_completo}")
                    
                    with open(caminho_completo, 'r', encoding='utf-8') as f:
                        valor = f.read()
                    
                    if modo_debug:
                        print(f"Arquivo carregado: {caminho_completo}")
                        print(f"Tamanho: {len(valor)} caracteres")
                
                # Aguarda o elemento principal aparecer na modal
                seletor_base = passo['seletor']
                page.wait_for_selector(seletor_base, timeout=10000)
                page.wait_for_timeout(500)
                
                # Tenta focar no elemento editável (dxrePage) dentro do container
                seletor_editavel = f"{seletor_base} .dxrePage"
                
                try:
                    page.wait_for_selector(seletor_editavel, timeout=2000)
                    seletor_final = seletor_editavel
                    if modo_debug:
                        print(f"Usando elemento editavel: {seletor_editavel}")
                except:
                    seletor_final = seletor_base
                    if modo_debug:
                        print(f"Usando seletor base: {seletor_base}")
                
                # Foca no elemento
                elemento = page.locator(seletor_final)
                elemento.click()
                page.wait_for_timeout(500)
                
                # Limpa o campo se necessário
                if passo.get('limpar_antes', True):
                    page.keyboard.press('Control+A')
                    page.wait_for_timeout(200)
                    page.keyboard.press('Delete')
                    page.wait_for_timeout(200)
                
                # Digita o texto
                delay = passo.get('delay', 0)
                page.keyboard.type(valor, delay=delay)
                
                if modo_debug:
                    print(f"Texto digitado no DevExpress ({len(valor)} caracteres)")

            elif acao == 'click':
                page.click(passo['seletor'])
            
            elif acao == 'executar_script':
                resultado_script = page.evaluate(passo['script'])
                if 'variavel' in passo:
                    self.variaveis[passo['variavel']] = resultado_script
                    
                    # Print simplificado para variáveis de debug de ordenação
                    nome_var = passo['variavel']
                    if nome_var == 'resultado_completo':
                        # Só mostra se falhou
                        if isinstance(resultado_script, dict) and not resultado_script.get('match', True):
                            print(f"\n{'='*60}")
                            print(f"⚠️  ORDENAÇÃO FALHOU - Debug")
                            print(f"{'='*60}")
                            print(f"Total ASC: {resultado_script.get('totalASC', 'N/A')} | Total DESC: {resultado_script.get('totalDESC', 'N/A')}")
                            
                            asc = resultado_script.get('primeiros5ASC', [])
                            desc = resultado_script.get('primeiros5DESC', [])
                            
                            print(f"\nPrimeiros 5 ASC inicial: {asc}")
                            print(f"Primeiros 5 DESC:        {desc}")
                            print(f"Últimos 5 DESC:          {resultado_script.get('ultimos5DESC', [])}")
                            print(f"\n💡 DESC deve ser o inverso alfabético de ASC")
                            print(f"{'='*60}\n")
                        elif isinstance(resultado_script, dict) and resultado_script.get('match', False):
                            print(f"✓ Ordenação validada: ASC ↔ DESC funcionando corretamente")
                    
                    elif nome_var in ['itens_asc', 'itens_iniciais', 'itens_apos_primeiro_clique', 'itens_desc']:
                        # Mostra primeiros 5 itens
                        if isinstance(resultado_script, list):
                            primeiros_5 = resultado_script[:5]
                            print(f"  → {nome_var}: {len(resultado_script)} itens")
                            for i, item in enumerate(primeiros_5, 1):
                                print(f"     {i}. {item}")
                    
                    elif modo_debug:
                        valor_truncado = str(resultado_script)[:100]
                        if len(str(resultado_script)) > 100:
                            valor_truncado += "..."
                        print(f"Variavel '{passo['variavel']}' = {valor_truncado}")
            
            elif acao == 'wait':
                if 'seletor' in passo:
                    page.wait_for_selector(passo['seletor'])
                elif 'tempo' in passo:
                    page.wait_for_timeout(passo['tempo'])
            
            elif acao == 'press':
                page.press(passo['seletor'], passo['tecla'])
            
            elif acao == 'select':
                page.select_option(passo['seletor'], passo['valor'])
            
            elif acao == 'check':
                page.check(passo['seletor'])
            
            elif acao == 'uncheck':
                page.uncheck(passo['seletor'])
            
            elif acao == 'hover':
                page.hover(passo['seletor'])
            
            elif acao == 'screenshot':
                nome_screenshot = passo.get('nome', f'passo_{numero}')
                if self.cenario_atual:
                    nome_screenshot = f"{self.cenario_atual}_{nome_screenshot}"
                nome_screenshot = self._substituir_texto(nome_screenshot)
                self._tirar_screenshot(page, nome_screenshot)
            
            elif acao == 'assert':
                self._executar_assert(page, passo)
            
            elif acao == 'scroll':
                page.evaluate(f"window.scrollTo(0, {passo.get('posicao', 'document.body.scrollHeight')})")
            
            elif acao == 'scroll_elemento':
                seletor = passo['seletor']
                pixels = passo.get('pixels', 500)
                suave = passo.get('suave', False)
                
                if suave:
                    page.locator(seletor).evaluate(f"""
                        element => {{
                            element.scrollBy({{
                                top: {pixels},
                                behavior: 'smooth'
                            }});
                        }}
                    """)
                else:
                    page.locator(seletor).evaluate(f"""
                        element => {{
                            element.scrollTop += {pixels};
                        }}
                    """)
                
                if modo_debug:
                    print(f"Scroll de {pixels}px no elemento: {seletor}")
            
            elif acao == 'scroll_pdf':
                seletor = passo.get('seletor', "embed[type='application/x-google-chrome-pdf']")
                page.locator(seletor).click()
                page.wait_for_timeout(500)
                
                repeticoes = passo.get('repeticoes', 1)
                intervalo = passo.get('intervalo', 800)
                
                for i in range(repeticoes):
                    page.keyboard.press('PageDown')
                    page.wait_for_timeout(intervalo)
                    if modo_debug:
                        print(f"PageDown {i+1}/{repeticoes}")
            
            elif acao == 'aguardar_nova_aba':
                abas_antes = len(page.context.pages)
                timeout = passo.get('timeout', 15000)
                tempo_decorrido = 0
                intervalo = 100
                
                if modo_debug:
                    print(f"Abas antes: {abas_antes}")
                    print(f"Timeout: {timeout}ms")
                
                while len(page.context.pages) == abas_antes and tempo_decorrido < timeout:
                    page.wait_for_timeout(intervalo)
                    tempo_decorrido += intervalo
                
                if len(page.context.pages) > abas_antes:
                    nova_aba = page.context.pages[-1]
                    nova_aba.bring_to_front()
                    
                    try:
                        nova_aba.wait_for_load_state('networkidle', timeout=10000)
                        page.wait_for_timeout(3000)
                        
                        url_curta = nova_aba.url[:80] if len(nova_aba.url) > 80 else nova_aba.url
                        titulo = nova_aba.title()[:50] if len(nova_aba.title()) > 50 else nova_aba.title()
                        
                        if modo_debug:
                            print(f"Nova aba detectada!")
                            print(f"URL: {url_curta}")
                            print(f"Titulo: {titulo}")
                        
                        self._detectar_tipo_viewer_pdf(nova_aba, modo_debug)
                        
                        if self._is_pdf_url(nova_aba.url):
                            if modo_debug:
                                print(f"E um PDF - aguardando renderizacao...")
                            page.wait_for_timeout(5000)
                        
                        return nova_aba
                        
                    except Exception as e:
                        if modo_debug:
                            print(f"Aviso ao verificar nova aba: {e}")
                        return nova_aba
                else:
                    if modo_debug:
                        print(f"Nenhuma nova aba detectada apos {timeout}ms")
                    return None
            
            elif acao == 'scroll_aba_atual':
                repeticoes = passo.get('repeticoes', 1)
                intervalo = passo.get('intervalo', 800)
                
                page.bring_to_front()
                page.wait_for_timeout(300)
                
                for i in range(repeticoes):
                    page.keyboard.press('PageDown')
                    page.wait_for_timeout(intervalo)
                    if modo_debug:
                        print(f"PageDown {i+1}/{repeticoes}")
            
            elif acao == 'fechar_aba_atual':
                paginas = page.context.pages
                if len(paginas) > 1:
                    url_fechada = page.url[:60] if len(page.url) > 60 else page.url
                    if modo_debug:
                        print(f"Fechando aba: {url_fechada}...")
                    
                    page.close()
                    page.wait_for_timeout(1000)
                    
                    aba_principal = paginas[0]
                    aba_principal.bring_to_front()
                    aba_principal.wait_for_load_state('load', timeout=5000)
                    
                    if modo_debug:
                        print(f"Retornou para aba principal")
                        print(f"URL atual: {aba_principal.url[:60]}...")
                    
                    return aba_principal
                else:
                    if modo_debug:
                        print(f"Apenas uma aba aberta - nao fechar")
                    return page
            
            elif acao == 'pressionar_tecla':
                tecla = passo.get('tecla', 'Escape')
                page.keyboard.press(tecla)
                if modo_debug:
                    print(f"Tecla pressionada: {tecla}")
            
            elif acao == 'click_shadow':
                pagina = passo.get('pagina', 2)
                
                if modo_debug:
                    print(f"Tentando clicar na miniatura da pagina {pagina}")
                
                estrategias = [
                    self._estrategia_chrome_pdf_viewer,
                    self._estrategia_firefox_pdf_viewer,
                    self._estrategia_generic_thumbnails,
                    self._estrategia_by_class_names
                ]
                
                for estrategia in estrategias:
                    try:
                        resultado_estrategia = estrategia(page, pagina, modo_debug)
                        if resultado_estrategia and resultado_estrategia.get('success'):
                            if modo_debug:
                                print(f"Sucesso com estrategia: {resultado_estrategia.get('method')}")
                            page.wait_for_timeout(2000)
                            return None
                    except Exception as e:
                        if modo_debug:
                            print(f"Estrategia falhou: {str(e)[:100]}")
                        continue
                
                if modo_debug:
                    print(f"Tentando metodo direto...")
                
                try:
                    page.evaluate(f"""
                        (function() {{
                            const allElements = document.querySelectorAll('*');
                            for (let element of allElements) {{
                                if (element.shadowRoot) {{
                                    const thumbnails = element.shadowRoot.querySelectorAll('[role="option"], .thumbnail, .pageThumbnail, viewer-thumbnail');
                                    if (thumbnails.length >= {pagina}) {{
                                        thumbnails[{pagina - 1}].click();
                                        return {{ success: true, method: 'shadow_direct' }};
                                    }}
                                }}
                            }}
                            
                            const clickable = document.querySelectorAll('div[role="button"], div[tabindex="0"], button, .thumb');
                            for (let el of clickable) {{
                                const text = el.textContent || '';
                                if (text.includes('{pagina}') || text.includes('Page {pagina}')) {{
                                    el.click();
                                    return {{ success: true, method: 'text_match' }};
                                }}
                            }}
                            
                            return {{ success: false, error: 'Nenhum elemento encontrado' }};
                        }})();
                    """)
                    
                    if modo_debug:
                        print(f"Metodo direto executado")
                    
                    page.wait_for_timeout(2000)
                    
                except Exception as e:
                    if modo_debug:
                        print(f"Metodo direto falhou: {e}")
            
            elif acao == 'javascript':
                page.evaluate(passo['codigo'])
            
            elif acao == 'capturar_pdf_da_api':
                return self._capturar_pdf_da_api(page, passo, modo_debug)
            
            elif acao == 'interceptar_url_pdf':
                return self._interceptar_url_pdf(page, passo, modo_debug)
            
            elif acao == 'monitorar_requisicoes':
                return self._monitorar_requisicoes(page, passo, modo_debug)
            
            elif acao == 'gerar_pdf_direto':
                return self._gerar_pdf_direto(page, passo, modo_debug)
            
            elif acao == 'abrir_pdf_via_blob':
                return self._abrir_pdf_via_blob(page, passo, modo_debug)
            
            else:
                raise ValueError(f"Acao desconhecida: {acao}")
            
            if passo.get('screenshot', False):
                self._tirar_screenshot(page, f'passo_{numero}')
            
            if modo_debug:
                print(f"Concluido")
            else:
                print(f"Concluido\n")
            
            return None
            
        except Exception as e:
            print(f"Falhou: {e}\n")
            self._tirar_screenshot(page, f'erro_passo_{numero}')
            if modo_debug:
                print(f"DEBUG - Stack trace: {e.__traceback__}")
            raise Exception(f"Erro no passo {numero} ({descricao}): {e}")
    
    # ===== MÉTODOS PARA INTERCEPTAÇÃO DA API =====
    
    def _capturar_pdf_da_api(self, page, passo, modo_debug=False):
        if modo_debug:
            print(f"Configurando interceptacao da API NoPaper...")
        
        pdf_blob_url = None
        api_response_data = None
        
        def handle_response(response):
            nonlocal pdf_blob_url, api_response_data
            
            url = response.url
            if 'api-nopaperd.al.rs.gov.br/api/v1/documents/preview' in url:
                if modo_debug:
                    print(f"API do PDF detectada: {url}")
                    print(f"Status: {response.status}")
                
                try:
                    if response.status == 200:
                        content_type = response.headers.get('content-type', '')
                        if 'application/pdf' in content_type or 'application/octet-stream' in content_type:
                            response_body = response.body()
                            
                            if response_body:
                                if modo_debug:
                                    print(f"PDF recebido ({len(response_body)} bytes)")
                                
                                blob_url = page.evaluate("""
                                    async (pdfData) => {
                                        try {
                                            const byteArray = new Uint8Array(pdfData);
                                            const blob = new Blob([byteArray], { 
                                                type: 'application/pdf' 
                                            });
                                            
                                            const blobUrl = URL.createObjectURL(blob);
                                            console.log('Blob URL criada:', blobUrl);
                                            
                                            window._capturedPdfBlobUrl = blobUrl;
                                            
                                            return blobUrl;
                                        } catch (error) {
                                            console.error('Erro ao criar blob:', error);
                                            return null;
                                        }
                                    }
                                """, list(response_body))
                                
                                if blob_url:
                                    pdf_blob_url = blob_url
                                    if modo_debug:
                                        print(f"Blob URL gerada: {blob_url[:80]}...")
                        else:
                            try:
                                api_response_data = response.json()
                                if modo_debug:
                                    print(f"Resposta JSON: {api_response_data}")
                            except:
                                pass
                except Exception as e:
                    if modo_debug:
                        print(f"Erro ao processar resposta: {e}")
        
        page.on("response", handle_response)
        page.click(passo['seletor'])
        
        timeout = passo.get('timeout', 20000)
        start_time = datetime.now()
        
        while not pdf_blob_url and (datetime.now() - start_time).total_seconds() * 1000 < timeout:
            page.wait_for_timeout(500)
            if not pdf_blob_url:
                result = page.evaluate("window._capturedPdfBlobUrl || null")
                if result:
                    pdf_blob_url = result
        
        page.remove_listener("response", handle_response)
        
        if pdf_blob_url:
            print(f"PDF capturado da API: {pdf_blob_url[:80]}...")
            self.variaveis['pdf_api_blob_url'] = pdf_blob_url
            
            if api_response_data:
                self.variaveis['api_response_data'] = api_response_data
            
            nova_aba = page.context.new_page()
            nova_aba.goto(pdf_blob_url)
            nova_aba.wait_for_load_state('networkidle')
            nova_aba.bring_to_front()
            nova_aba.wait_for_timeout(3000)
            
            return nova_aba
        else:
            print(f"Nenhum PDF capturado da API apos {timeout}ms")
            if api_response_data:
                print(f"Mas recebeu resposta da API: {api_response_data}")
            return None
    
    def _interceptar_url_pdf(self, page, passo, modo_debug=False):
        if modo_debug:
            print(f"Interceptando requisicoes da API...")
        
        pdf_url = None
        
        def intercept_request(route, request):
            url = request.url
            
            if 'api-nopaperd.al.rs.gov.br/api/v1/documents/preview' in url:
                if modo_debug:
                    print(f"Requisicao a API detectada: {url}")
                    print(f"Metodo: {request.method}")
                    print(f"Headers: {request.headers}")
                
                route.continue_()
            else:
                route.continue_()
        
        def handle_response(response):
            nonlocal pdf_url
            
            url = response.url
            if 'api-nopaperd.al.rs.gov.br/api/v1/documents/preview' in url and response.status == 200:
                if modo_debug:
                    print(f"Resposta da API recebida: {url}")
                
                try:
                    response_text = page.evaluate("""
                        async (response) => {
                            try {
                                const data = await response.json();
                                console.log('Resposta JSON da API:', data);
                                
                                if (data.url) {
                                    window._pdfUrlFromApi = data.url;
                                    return { type: 'json', data: data };
                                } else if (data.documentUrl) {
                                    window._pdfUrlFromApi = data.documentUrl;
                                    return { type: 'json', data: data };
                                } else if (data.blobUrl) {
                                    window._pdfUrlFromApi = data.blobUrl;
                                    return { type: 'json', data: data };
                                } else if (data.pdfUrl) {
                                    window._pdfUrlFromApi = data.pdfUrl;
                                    return { type: 'json', data: data };
                                }
                                return { type: 'json', data: data };
                            } catch (e) {
                                console.log('Resposta nao e JSON, pode ser blob');
                                return { type: 'blob' };
                            }
                        }
                    """, response)
                    
                    if response_text and response_text.get('type') == 'json':
                        self.variaveis['api_response_json'] = response_text['data']
                
                except Exception as e:
                    if modo_debug:
                        print(f"Erro ao processar resposta: {e}")
        
        page.route("**/*", intercept_request)
        page.on("response", handle_response)
        page.click(passo['seletor'])
        
        timeout = passo.get('timeout', 15000)
        start_time = datetime.now()
        
        while not pdf_url and (datetime.now() - start_time).total_seconds() * 1000 < timeout:
            page.wait_for_timeout(500)
            result = page.evaluate("window._pdfUrlFromApi || null")
            if result:
                pdf_url = result
        
        page.unroute("**/*", intercept_request)
        page.remove_listener("response", handle_response)
        
        if pdf_url:
            print(f"URL do PDF capturada: {pdf_url}")
            self.variaveis['pdf_captured_url'] = pdf_url
            
            nova_aba = page.context.new_page()
            nova_aba.goto(pdf_url)
            nova_aba.wait_for_load_state('networkidle')
            nova_aba.bring_to_front()
            
            return nova_aba
        else:
            print(f"Nenhuma URL capturada da API")
            return None
    
    def _monitorar_requisicoes(self, page, passo, modo_debug=False):
        if modo_debug:
            print(f"Ativando monitor de requisicoes...")
        
        page.evaluate("""
            (function() {
                console.log('=== MONITOR DE REQUISICOES ATIVADO ===');
                
                const originalFetch = window.fetch;
                window.fetch = function(...args) {
                    const url = args[0];
                    const options = args[1] || {};
                    
                    console.log('FETCH:', {
                        url: url,
                        method: options.method || 'GET',
                        headers: options.headers,
                        body: options.body ? (typeof options.body === 'string' ? options.body : 'Binary/FormData') : null
                    });
                    
                    return originalFetch.apply(this, args).then(response => {
                        console.log('FETCH RESPONSE:', {
                            url: response.url,
                            status: response.status,
                            statusText: response.statusText,
                            headers: Object.fromEntries(response.headers.entries())
                        });
                        
                        const clonedResponse = response.clone();
                        
                        clonedResponse.json().then(data => {
                            console.log('FETCH RESPONSE DATA (JSON):', data);
                        }).catch(() => {
                            clonedResponse.text().then(text => {
                                if (text.length < 1000) {
                                    console.log('FETCH RESPONSE DATA (Text):', text.substring(0, 500));
                                } else {
                                    console.log('FETCH RESPONSE DATA (Text, first 500 chars):', text.substring(0, 500));
                                }
                            }).catch(e => {
                                console.log('FETCH RESPONSE DATA: Binary data, size:', text ? text.length : 0);
                            });
                        });
                        
                        return response;
                    }).catch(error => {
                        console.error('FETCH ERROR:', error);
                        throw error;
                    });
                };
                
                const originalXHR = window.XMLHttpRequest.prototype.open;
                window.XMLHttpRequest.prototype.open = function(method, url) {
                    console.log('XHR OPEN:', method, url);
                    this._requestUrl = url;
                    this._requestMethod = method;
                    return originalXHR.apply(this, arguments);
                };
                
                const originalSend = window.XMLHttpRequest.prototype.send;
                window.XMLHttpRequest.prototype.send = function(body) {
                    console.log('XHR SEND:', {
                        url: this._requestUrl,
                        method: this._requestMethod,
                        body: body ? (typeof body === 'string' ? body : 'Binary/FormData') : null
                    });
                    
                    this.addEventListener('load', function() {
                        console.log('XHR RESPONSE:', {
                            url: this._requestUrl,
                            status: this.status,
                            statusText: this.statusText,
                            responseType: this.responseType
                        });
                        
                        if (this.responseType === '' || this.responseType === 'text') {
                            try {
                                const data = JSON.parse(this.responseText);
                                console.log('XHR RESPONSE DATA (JSON):', data);
                            } catch {
                                console.log('XHR RESPONSE DATA (Text):', this.responseText.substring(0, 500));
                            }
                        }
                    });
                    
                    return originalSend.apply(this, arguments);
                };
                
                return 'Monitor de requisicoes ativado';
            })();
        """)
        
        if 'seletor' in passo:
            page.click(passo['seletor'])
        
        wait_time = passo.get('tempo', 10000)
        page.wait_for_timeout(wait_time)
        
        print(f"Monitoramento concluido. Verifique o console do navegador para ver as requisicoes.")
        return None
    
    def _gerar_pdf_direto(self, page, passo, modo_debug=False):
        if modo_debug:
            print(f"Extraindo dados do formulario/documento...")
        
        document_data = page.evaluate("""
            (function() {
                const data = {};
                
                const inputs = document.querySelectorAll('input[name], textarea[name], select[name]');
                inputs.forEach(input => {
                    const name = input.name;
                    const value = input.value;
                    if (name && value) {
                        const simpleName = name.replace(/data\\[camposDoFormulario\\]\\[/, '').replace(/\\]/g, '');
                        data[simpleName] = value;
                    }
                });
                
                const urlParams = new URLSearchParams(window.location.search);
                urlParams.forEach((value, key) => {
                    data[key] = value;
                });
                
                const idMatch = window.location.href.match(/(\\d+)/);
                if (idMatch) {
                    data.documentId = idMatch[1];
                }
                
                console.log('Dados extraidos:', data);
                return data;
            })();
        """)
        
        if modo_debug:
            print(f"Dados extraidos: {document_data}")
        
        api_response = page.evaluate("""
            async (documentData) => {
                try {
                    console.log('Fazendo requisicao direta a API NoPaper...');
                    
                    const headers = {
                        'Content-Type': 'application/json',
                        'Accept': 'application/json, application/pdf',
                    };
                    
                    const authToken = localStorage.getItem('auth_token') || 
                                     sessionStorage.getItem('auth_token') ||
                                     document.cookie.match(/auth_token=([^;]+)/)?.[1];
                    
                    if (authToken) {
                        headers['Authorization'] = `Bearer ${authToken}`;
                    }
                    
                    const response = await fetch('https://api-nopaperd.al.rs.gov.br/api/v1/documents/preview', {
                        method: 'POST',
                        headers: headers,
                        body: JSON.stringify(documentData)
                    });
                    
                    console.log('Resposta da API:', {
                        status: response.status,
                        statusText: response.statusText,
                        headers: Object.fromEntries(response.headers.entries())
                    });
                    
                    if (response.ok) {
                        const contentType = response.headers.get('content-type');
                        
                        if (contentType && contentType.includes('application/pdf')) {
                            const blob = await response.blob();
                            const blobUrl = URL.createObjectURL(blob);
                            console.log('PDF gerado via API:', blobUrl);
                            return { type: 'blob', url: blobUrl };
                        } else {
                            const data = await response.json();
                            console.log('Resposta JSON da API:', data);
                            return { type: 'json', data: data };
                        }
                    } else {
                        const errorText = await response.text();
                        console.error('Erro na API:', errorText);
                        return { type: 'error', error: errorText };
                    }
                } catch (error) {
                    console.error('Erro na requisicao:', error);
                    return { type: 'error', error: error.message };
                }
            }
        """, document_data)
        
        if api_response and api_response.get('type') == 'blob':
            blob_url = api_response['url']
            print(f"PDF gerado via API direta: {blob_url[:80]}...")
            
            nova_aba = page.context.new_page()
            nova_aba.goto(blob_url)
            nova_aba.wait_for_load_state('networkidle')
            nova_aba.bring_to_front()
            
            return nova_aba
        elif api_response and api_response.get('type') == 'json':
            print(f"API retornou JSON: {api_response['data']}")
            self.variaveis['api_direct_response'] = api_response['data']
            return None
        else:
            print(f"Falha ao gerar PDF via API: {api_response.get('error', 'Erro desconhecido')}")
            return None
    
    def _abrir_pdf_via_blob(self, page, passo, modo_debug=False):
        if 'pdf_blob_url' not in self.variaveis and 'pdf_api_blob_url' not in self.variaveis:
            raise ValueError("URL do blob nao foi capturada ainda. Execute 'capturar_pdf_da_api' primeiro.")
        
        blob_url = self.variaveis.get('pdf_api_blob_url') or self.variaveis.get('pdf_blob_url')
        
        if modo_debug:
            print(f"Abrindo PDF via blob URL: {blob_url[:80]}...")
        
        nova_aba = page.context.new_page()
        nova_aba.goto(blob_url)
        nova_aba.wait_for_load_state('networkidle')
        nova_aba.bring_to_front()
        nova_aba.wait_for_timeout(2000)
        
        return nova_aba
    
    # ===== MÉTODOS DE ESTRATÉGIAS DE PDF =====
    
    def _estrategia_chrome_pdf_viewer(self, page, pagina, modo_debug):
        resultado = page.evaluate(f"""
            (function() {{
                try {{
                    const viewer = document.querySelector('viewer-pdf-sidenav');
                    if (viewer && viewer.shadowRoot) {{
                        const thumbnailBar = viewer.shadowRoot.querySelector('viewer-thumbnail-bar');
                        if (thumbnailBar && thumbnailBar.shadowRoot) {{
                            const thumbnails = thumbnailBar.shadowRoot.querySelectorAll('viewer-thumbnail');
                            if (thumbnails.length >= {pagina}) {{
                                thumbnails[{pagina - 1}].click();
                                return {{ success: true, method: 'chrome_pdf_viewer' }};
                            }}
                        }}
                    }}
                    
                    const plugin = document.querySelector('embed[type="application/x-google-chrome-pdf"]');
                    if (plugin) {{
                        const viewerDiv = document.querySelector('#viewer');
                        if (viewerDiv) {{
                            const pages = viewerDiv.querySelectorAll('.page');
                            if (pages.length >= {pagina}) {{
                                pages[{pagina - 1}].scrollIntoView();
                                return {{ success: true, method: 'chrome_old_scroll' }};
                            }}
                        }}
                    }}
                    
                    return {{ success: false, error: 'Chrome viewer nao encontrado' }};
                }} catch (error) {{
                    return {{ success: false, error: error.message }};
                }}
            }})();
        """)
        
        if modo_debug and resultado.get('success'):
            print(f"Chrome PDF Viewer detectado")
        
        return resultado
    
    def _estrategia_firefox_pdf_viewer(self, page, pagina, modo_debug):
        resultado = page.evaluate(f"""
            (function() {{
                try {{
                    const viewer = document.querySelector('div[role="document"]');
                    if (viewer) {{
                        const thumbnails = viewer.querySelectorAll('[role="option"], .thumbnail');
                        if (thumbnails.length >= {pagina}) {{
                            thumbnails[{pagina - 1}].click();
                            return {{ success: true, method: 'firefox_pdf_viewer' }};
                        }}
                    }}
                    
                    return {{ success: false, error: 'Firefox viewer nao encontrado' }};
                }} catch (error) {{
                    return {{ success: false, error: error.message }};
                }}
            }})();
        """)
        
        if modo_debug and resultado.get('success'):
            print(f"Firefox PDF Viewer detectado")
        
        return resultado
    
    def _estrategia_generic_thumbnails(self, page, pagina, modo_debug):
        resultado = page.evaluate(f"""
            (function() {{
                try {{
                    const allThumbnails = document.querySelectorAll(
                        '[role="option"], .thumbnail, .page-thumbnail, .thumb, ' +
                        '.pageThumbnail, .pageThumb, [data-page-number]'
                    );
                    
                    if (allThumbnails.length >= {pagina}) {{
                        allThumbnails[{pagina - 1}].click();
                        return {{ success: true, method: 'generic_thumbnails', count: allThumbnails.length }};
                    }}
                    
                    return {{ success: false, error: 'Miniaturas genericas nao encontradas' }};
                }} catch (error) {{
                    return {{ success: false, error: error.message }};
                }}
            }})();
        """)
        
        if modo_debug and resultado.get('success'):
            print(f"Miniaturas genericas detectadas: {resultado.get('count')}")
        
        return resultado
    
    def _estrategia_by_class_names(self, page, pagina, modo_debug):
        resultado = page.evaluate(f"""
            (function() {{
                try {{
                    const classPatterns = [
                        'thumbnail', 'pageThumbnail', 'pdfThumbnail',
                        'thumb', 'page-thumb', 'pdf-thumb'
                    ];
                    
                    for (const pattern of classPatterns) {{
                        const selector = `[class*="${{pattern}}"]`;
                        const elements = document.querySelectorAll(selector);
                        if (elements.length >= {pagina}) {{
                            elements[{pagina - 1}].click();
                            return {{ success: true, method: 'class_pattern: ' + pattern, count: elements.length }};
                        }}
                    }}
                    
                    return {{ success: false, error: 'Classes especificas nao encontradas' }};
                }} catch (error) {{
                    return {{ success: false, error: error.message }};
                }}
            }})();
        """)
        
        if modo_debug and resultado.get('success'):
            print(f"Classes detectadas: {resultado.get('method')}")
        
        return resultado
    
    def _detectar_tipo_viewer_pdf(self, page, modo_debug=False):
        try:
            resultado = page.evaluate("""
                (function() {
                    const detectors = [
                        {
                            name: 'chrome_pdf_viewer',
                            check: () => document.querySelector('viewer-pdf-sidenav') !== null
                        },
                        {
                            name: 'firefox_pdf_viewer', 
                            check: () => document.querySelector('div[role="document"]') !== null
                        },
                        {
                            name: 'embed_pdf',
                            check: () => document.querySelector('embed[type*="pdf"]') !== null
                        },
                        {
                            name: 'iframe_pdf',
                            check: () => document.querySelector('iframe[src*=".pdf"]') !== null
                        },
                        {
                            name: 'object_pdf',
                            check: () => document.querySelector('object[data*=".pdf"]') !== null
                        }
                    ];
                    
                    for (const detector of detectors) {
                        if (detector.check()) {
                            return detector.name;
                        }
                    }
                    
                    return 'unknown';
                })();
            """)
            
            if resultado and resultado not in self.pdf_viewers_detected:
                self.pdf_viewers_detected.append(resultado)
                if modo_debug:
                    print(f"Viewer detectado: {resultado}")
            
            return resultado
            
        except Exception as e:
            if modo_debug:
                print(f"Erro ao detectar viewer: {e}")
            return 'detection_error'
    
    def _is_pdf_url(self, url):
        if not url:
            return False
        
        url_lower = url.lower()
        return ('.pdf' in url_lower or 
                'application/pdf' in url_lower or
                'blob:' in url_lower and 'pdf' in url_lower)
    
    def _substituir_variaveis_passo(self, passo):
        passo = copy.deepcopy(passo)
        
        campos = ['valor', 'seletor', 'url', 'nome', 'texto', 'esperado']
        
        for campo in campos:
            if campo in passo and isinstance(passo[campo], str):
                passo[campo] = self._substituir_texto(passo[campo])
        
        return passo
    
    def _substituir_texto(self, texto):
        def substituir(match):
            var_nome = match.group(1)
            if var_nome in self.variaveis:
                return str(self.variaveis[var_nome])
            else:
                print(f"Aviso: Variavel '{var_nome}' nao encontrada")
                return match.group(0)
        
        return re.sub(r'\{\{(\w+)\}\}', substituir, texto)
    
    def _executar_assert(self, page, passo):
        tipo = passo['tipo']
        
        if tipo == 'url_contem':
            assert passo['valor'] in page.url, f"URL nao contem '{passo['valor']}'"
        
        elif tipo == 'titulo_contem':
            assert passo['valor'] in page.title(), f"Titulo nao contem '{passo['valor']}'"
        
        elif tipo == 'texto_visivel':
            assert page.is_visible(f"text={passo['texto']}"), f"Texto '{passo['texto']}' nao esta visivel"
        
        elif tipo == 'elemento_visivel':
            assert page.is_visible(passo['seletor']), f"Elemento '{passo['seletor']}' nao esta visivel"
        
        elif tipo == 'elemento_existe':
            assert page.query_selector(passo['seletor']) is not None, f"Elemento '{passo['seletor']}' nao existe"
        
        elif tipo == 'valor_igual':
            valor = page.input_value(passo['seletor'])
            assert valor == passo['esperado'], f"Valor '{valor}' diferente de '{passo['esperado']}'"
        
        elif tipo == 'pagina_contem':
            assert passo['texto'] in page.content(), f"Pagina nao contem '{passo['texto']}'"
        
        else:
            raise ValueError(f"Tipo de assert desconhecido: {tipo}")
    
    def _tirar_screenshot(self, page, nome):
        self.screenshot_count += 1
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.screenshots_dir}/{self.screenshot_count:03d}_{timestamp}_{nome}.png"
        page.screenshot(path=filename, full_page=True)
        self._log(f"Screenshot: {filename}", "info")
    
    def _renomear_video(self, video_path, nome_teste):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        nome_teste = nome_teste.replace(' ', '_').lower()
        novo_nome = f"{self.videos_dir}/{timestamp}_{nome_teste}.webm"
        
        try:
            if os.path.exists(video_path):
                os.rename(video_path, novo_nome)
                return novo_nome
        except Exception:
            return video_path
        
        return video_path
    
    def _listar_screenshots(self):
        if not os.path.exists(self.screenshots_dir):
            return []
        
        screenshots = [
            os.path.join(self.screenshots_dir, f)
            for f in os.listdir(self.screenshots_dir)
            if f.endswith('.png')
        ]
        return sorted(screenshots)
    
    def _gerar_relatorio(self, resultado):
        print(f"\n{'='*60}")
        print("RELATORIO DO TESTE")
        print(f"{'='*60}")
        
        print(f"\nNome: {resultado['nome']}")
        
        if resultado['sucesso']:
            print(f"Status: PASSOU")
        else:
            print(f"Status: FALHOU")
        
        print(f"Passos: {resultado['passos_executados']}/{resultado['passos_total']}")
        print(f"Tempo: {resultado['tempo_execucao']:.2f}s")
        
        if resultado.get('pdf_viewers'):
            print(f"\nVisualizadores PDF detectados: {', '.join(resultado['pdf_viewers'])}")
        
        if resultado['erro']:
            print(f"\nErro:\n{resultado['erro']}")
        
        if resultado.get('variaveis'):
            variaveis_importantes = ['URL_BASE', 'NOME_AMBIENTE', 'numero_processo']
            variaveis_exibidas = {k: v for k, v in resultado['variaveis'].items() if k in variaveis_importantes}
            
            if variaveis_exibidas:
                print(f"\nVariaveis capturadas:")
                for var_nome, var_valor in variaveis_exibidas.items():
                    valor_str = str(var_valor)
                    if len(valor_str) > 50:
                        valor_str = valor_str[:47] + "..."
                    print(f"   {var_nome}: {valor_str}")
        
        if resultado['screenshots']:
            print(f"\nScreenshots ({len(resultado['screenshots'])}):")
            for screenshot in resultado['screenshots'][:5]:
                print(f"   - {screenshot}")
            if len(resultado['screenshots']) > 5:
                print(f"   ... e mais {len(resultado['screenshots']) - 5}")
        
        if resultado.get('video'):
            print(f"\nVideo gravado:\n   {resultado['video']}")
        
        print(f"\n{'='*60}\n")
    
    def _log(self, mensagem, tipo="info"):
        self.logs.append({
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "mensagem": mensagem,
            "tipo": tipo
        })
"""
Script para executar qualquer teste.
Use: python run.py <caminho_do_teste.json> [opções]
"""

import sys
import os

# Adiciona src ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from testador.testador_json import TestadorJSON


def main():
    # Verifica se passou o arquivo de teste
    if len(sys.argv) < 2:
        print("="*60)
        print("TESTADOR JSON - Executor Generico de Testes")
        print("="*60)
        print("\nUso: python run.py <arquivo_teste.json> [opcoes]")
        print("\nOpcoes:")
        print("  --headless        Executa sem mostrar navegador")
        print("  --no-video        Nao grava video")
        print("  --debug           Modo detalhado")
        print("  --browser=<n>     Navegador: chromium, firefox, webkit, brave")
        print("  --env=<ambiente>  Ambiente: dev, homolog, stage (padrao: homolog)")
        print("\nExemplos:")
        print("  python run.py tests/exemplos/abertura_PL.json")
        print("  python run.py tests/exemplos/abertura_PL.json --env=dev")
        print("  python run.py tests/exemplos/abertura_PL.json --env=stage --debug")
        print("  python run.py tests/exemplos/cargos.json --browser=brave --env=homolog")
        return
    
    # Pega o arquivo de teste
    arquivo_teste = sys.argv[1]
    
    # Verifica se arquivo existe
    if not os.path.exists(arquivo_teste):
        print(f"ERRO: Arquivo nao encontrado: {arquivo_teste}")
        return
    
    # Configuracoes padrao
    config = {
        'headless': '--headless' in sys.argv,
        'gravar_video': '--no-video' not in sys.argv,
        'modo_debug': '--debug' in sys.argv,
        'navegador': 'chromium',
        'ambiente': 'homolog'  # valor padrao
    }
    
    # Processa argumentos
    for arg in sys.argv:
        if arg.startswith('--browser='):
            config['navegador'] = arg.split('=', 1)[1]
        elif arg.startswith('--env='):
            config['ambiente'] = arg.split('=', 1)[1]
    
    # Mostra configuracao
    print("="*60)
    print(f"Teste: {arquivo_teste}")
    print(f"Ambiente: {config['ambiente']}")
    print(f"Navegador: {config['navegador']}")
    print(f"Gravar video: {'Sim' if config['gravar_video'] else 'Nao'}")
    print(f"Modo debug: {'Sim' if config['modo_debug'] else 'Nao'}")
    print(f"Headless: {'Sim' if config['headless'] else 'Nao'}")
    print("="*60)
    
    try:
        # Cria pastas de evidencia baseadas no nome do teste E ambiente
        nome_teste = os.path.splitext(os.path.basename(arquivo_teste))[0]
        pasta_screenshots = f"evidence/screenshots/{config['ambiente']}/{nome_teste}"
        pasta_videos = f"evidence/videos/{config['ambiente']}/{nome_teste}"
        
        # Cria testador
        testador = TestadorJSON(
            pasta_screenshots=pasta_screenshots,
            pasta_videos=pasta_videos
        )
        
        # Executa teste - AGORA COM PARAMETRO AMBIENTE
        resultado = testador.executar_teste(
            arquivo_json=arquivo_teste,
            headless=config['headless'],
            navegador=config['navegador'],
            gravar_video=config['gravar_video'],
            modo_debug=config['modo_debug'],
            ambiente=config['ambiente']  # <-- NOVO!
        )
        
        # Mostra resultado
        print("\n" + "="*60)
        print("RESULTADO FINAL")
        print("="*60)
        
        if resultado['sucesso']:
            print("TESTE PASSOU!")
            print(f"\nEstatisticas:")
            print(f"   Passos: {resultado['passos_executados']}/{resultado['passos_total']}")
            print(f"   Tempo: {resultado['tempo_execucao']:.2f}s")
            print(f"   Screenshots: {len(resultado['screenshots'])}")
            
            if resultado.get('video'):
                print(f"   Video: {resultado['video']}")
        else:
            print("TESTE FALHOU!")
            print(f"\nErro: {resultado['erro']}")
            
            if resultado['screenshots']:
                print(f"\nUltimo screenshot: {resultado['screenshots'][-1]}")
        
        print("\n" + "="*60)
        
    except Exception as e:
        print(f"\nERRO CRITICO: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
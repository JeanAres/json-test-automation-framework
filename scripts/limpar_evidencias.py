import shutil
import time
from pathlib import Path

def limpar_pastas():
    # Encontra a pasta raiz do projeto
    raiz_projeto = Path(__file__).resolve().parent.parent
    
    # Aponta para as pastas de evidencias
    pastas_alvo = [
        raiz_projeto / 'evidence' / 'screenshots',
        raiz_projeto / 'evidence' / 'videos'
    ]
    
    for caminho in pastas_alvo:
        if caminho.exists() and caminho.is_dir():
            try:
                # ignore_errors=True forca a exclusao ignorando bloqueios de leitura do Windows
                shutil.rmtree(caminho, ignore_errors=True)
                
                # Uma pausa de meio segundo para o sistema operacional processar a exclusao
                time.sleep(0.5) 
                
                caminho.mkdir(parents=True, exist_ok=True)
                print(f"Limpeza concluida com sucesso em: evidence/{caminho.name}")
            except Exception as e:
                print(f"Nao foi possivel limpar evidence/{caminho.name} totalmente.")
                print(f"O OneDrive ou o Playwright pode estar usando o arquivo. Detalhe: {e}")
        else:
            print(f"A pasta evidence/{caminho.name} ja esta limpa ou nao existe.")

if __name__ == '__main__':
    print("Iniciando limpeza de evidencias antigas...")
    limpar_pastas()
    print("Processo finalizado.")
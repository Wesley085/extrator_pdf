# test_client.py

import requests

# Crie um arquivo chamado 'sample.pdf' na mesma pasta para o teste
PDF_PATH = 'sample.pdf'
API_URL = 'http://127.0.0.1:5000/extract'
PAGES_TO_EXTRACT = '1' # Exemplo: extrair a página 1, 3 e 4

try:
    with open(PDF_PATH, 'rb') as f:
        files = {'file': (PDF_PATH, f, 'application/pdf')}
        data = {'pages': PAGES_TO_EXTRACT}
        
        print(f"Enviando requisição para {API_URL}...")
        response = requests.post(API_URL, files=files, data=data)

    print(f"Status da Resposta: {response.status_code}")

    if response.ok:
        # Salva o resultado para verificação
        with open('resultado.pdf', 'wb') as f:
            f.write(response.content)
        print("Sucesso! PDF extraído e salvo como 'resultado.pdf'.")
        print(f"Header 'Content-Type': {response.headers.get('Content-Type')}")
    else:
        # Imprime o erro retornado pela API
        print("Erro na requisição:")
        print(response.json())

except FileNotFoundError:
    print(f"Erro: O arquivo de teste '{PDF_PATH}' não foi encontrado.")
except requests.exceptions.ConnectionError:
    print(f"Erro: Não foi possível conectar à API em {API_URL}. A API está rodando?")
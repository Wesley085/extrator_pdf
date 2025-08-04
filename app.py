# app.py

import io
import os
from flask import Flask, request, Response, jsonify
from pypdf import PdfReader, PdfWriter
from pypdf.errors import PdfReadError
from flasgger import Swagger # Importa a biblioteca

app = Flask(__name__)

# --- CONFIGURAÇÃO DO SWAGGER ---
swagger_config = {
    "headers": [],
    "specs": [
        {
            "endpoint": 'apispec_1',
            "route": '/apispec_1.json',
            "rule_filter": lambda rule: True,
            "model_filter": lambda tag: True,
        }
    ],
    "static_url_path": "/flasgger_static",
    "swagger_ui": True,
    "specs_route": "/apidocs/" # Rota para acessar a UI do Swagger
}
swagger = Swagger(app, config=swagger_config)
# --- FIM DA CONFIGURAÇÃO DO SWAGGER ---


API_KEY = os.environ.get('PDF_EXTRACTOR_API_KEY', 'b30c78af-066e-4232-81a3-dbd9aea8da88')

@app.before_request
def check_api_key():
    # Ignora a verificação para a rota de documentação
    if request.path.startswith('/apidocs') or request.path.startswith('/flasgger_static') or request.path.startswith('/apispec_1.json'):
        return
    if not app.debug:
        if request.headers.get('X-API-KEY') != API_KEY:
            return jsonify({"error": "Acesso não autorizado. Chave de API inválida ou ausente."}), 401


# (A função parse_pages permanece a mesma)
def parse_pages(pages_str: str, max_pages: int) -> list[int]:
    # ... código da função parse_pages ...
    page_indices = set()
    parts = pages_str.replace(" ", "").split(',')
    
    for part in parts:
        if not part:
            continue
        if '-' in part:
            try:
                start, end = map(int, part.split('-'))
                if start > end:
                    raise ValueError("O início do intervalo não pode ser maior que o fim.")
                for i in range(start, end + 1):
                    if 1 <= i <= max_pages:
                        page_indices.add(i - 1)
                    else:
                        raise ValueError(f"A página {i} não existe no documento.")
            except (ValueError, TypeError):
                raise ValueError(f"Formato de intervalo inválido: '{part}'. Use 'inicio-fim'.")
        else:
            try:
                page = int(part)
                if 1 <= page <= max_pages:
                    page_indices.add(page - 1)
                else:
                    raise ValueError(f"A página {page} não existe no documento.")
            except (ValueError, TypeError):
                raise ValueError(f"Número de página inválido: '{part}'.")

    return sorted(list(page_indices))


@app.route('/extract', methods=['POST'])
def extract_pdf_pages():
    """
    Este é o docstring que o Flasgger usará para gerar a documentação.
    ---
    tags:
      - PDF Extractor
    summary: Extrai páginas específicas de um arquivo PDF.
    consumes:
      - multipart/form-data
    produces:
      - application/pdf
      - application/json
    parameters:
      - name: X-API-KEY
        in: header
        type: string
        required: true
        description: A chave de API para autorização.
      - name: file
        in: formData
        type: file
        required: true
        description: O arquivo PDF a ser processado.
      - name: pages
        in: formData
        type: string
        required: true
        description: A(s) página(s) a serem extraídas. Ex. '1', '1-3', '1,3,5'.
    responses:
      200:
        description: Um novo arquivo PDF contendo apenas as páginas solicitadas.
        schema:
          type: file
      400:
        description: Erro na requisição (ex. PDF inválido, páginas não encontradas, parâmetros faltando).
      401:
        description: Acesso não autorizado (Chave de API inválida ou ausente).
      500:
        description: Erro interno no servidor.
    """
    # (O código da função permanece o mesmo)
    # ...
    if 'file' not in request.files:
        return jsonify({"error": "Nenhum arquivo PDF foi enviado."}), 400
    if 'pages' not in request.form:
        return jsonify({"error": "O campo 'pages' com as páginas a serem extraídas é obrigatório."}), 400
    pdf_file = request.files['file']
    pages_str = request.form['pages']
    if not pdf_file.filename.lower().endswith('.pdf'):
        return jsonify({"error": "O arquivo enviado não é um PDF válido."}), 400
    try:
        pdf_stream = io.BytesIO(pdf_file.read())
        reader = PdfReader(pdf_stream)
        writer = PdfWriter()
        num_pages_total = len(reader.pages)
        try:
            target_pages = parse_pages(pages_str, num_pages_total)
        except ValueError as e:
            return jsonify({"error": str(e)}), 400
        if not target_pages:
            return jsonify({"error": "Nenhuma página válida foi selecionada."}), 400
        for page_index in target_pages:
            writer.add_page(reader.pages[page_index])
        output_buffer = io.BytesIO()
        writer.write(output_buffer)
        output_buffer.seek(0)
        return Response(
            output_buffer.getvalue(),
            mimetype='application/pdf',
            headers={
                'Content-Disposition': 'inline; filename="documento_extraido.pdf"'
            }
        )
    except PdfReadError:
        return jsonify({"error": "Arquivo PDF corrompido ou inválido."}), 400
    except Exception as e:
        print(f"Erro inesperado: {e}")
        return jsonify({"error": "Ocorreu um erro interno ao processar o arquivo."}), 500

if __name__ == '__main__':
    app.run(debug=True)
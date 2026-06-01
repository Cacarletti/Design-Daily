"""Servidor local simples para visualizar a pagina (apenas para testes)."""
import http.server, socketserver, functools, os

PORT = 8765
DIRETORIO = os.path.dirname(os.path.abspath(__file__))
Handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=DIRETORIO)
with socketserver.TCPServer(("", PORT), Handler) as httpd:
    print(f"Servindo {DIRETORIO} em http://localhost:{PORT}")
    httpd.serve_forever()

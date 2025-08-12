from http.server import SimpleHTTPRequestHandler, HTTPServer
import os

# Servir le dossier public/
WEB_DIR = os.path.join(os.path.dirname(__file__), 'public')
PORT = int(os.environ.get('PORT', 8000))

class Handler(SimpleHTTPRequestHandler):
    def translate_path(self, path):
        # Toujours servir depuis WEB_DIR
        path = super().translate_path(path)
        rel = os.path.relpath(path, os.getcwd())
        return os.path.join(WEB_DIR, os.path.normpath(rel).replace('..', ''))

if __name__ == '__main__':
    os.chdir(WEB_DIR)
    httpd = HTTPServer(('0.0.0.0', PORT), Handler)
    print(f"Server running at http://localhost:{PORT}/")
    httpd.serve_forever()
import json, sys
from http.server import BaseHTTPRequestHandler, HTTPServer
sys.path.insert(0, '/home/claude/work/spkg/mirisaju_model'); from predict import Model
M = Model('/home/claude/work/spkg/mirisaju_model/model'); LOG = open('e2e_log.jsonl', 'w')
class H(BaseHTTPRequestHandler):
    def _c(self):
        self.send_header('Access-Control-Allow-Origin', '*'); self.send_header('Access-Control-Allow-Headers', 'Content-Type'); self.send_header('Access-Control-Allow-Methods', 'POST,GET,OPTIONS')
    def do_OPTIONS(self): self.send_response(204); self._c(); self.end_headers()
    def do_GET(self): self.send_response(200); self._c(); self.end_headers(); self.wfile.write(b'{}')
    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
        try: out = M.predict(body); code = 200
        except Exception as e: out = {'error': repr(e)}; code = 500
        LOG.write(json.dumps({'req': body, 'res': out}, ensure_ascii=False, default=float) + '\n'); LOG.flush()
        b = json.dumps(out, ensure_ascii=False, default=float).encode()
        self.send_response(code); self.send_header('Content-Type', 'application/json'); self._c(); self.end_headers(); self.wfile.write(b)
    def log_message(self, *a): pass
HTTPServer.allow_reuse_address = True
HTTPServer(('127.0.0.1', 8765), H).serve_forever()

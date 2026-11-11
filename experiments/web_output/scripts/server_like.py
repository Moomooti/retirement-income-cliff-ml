import json, sys
from http.server import BaseHTTPRequestHandler, HTTPServer
sys.path.insert(0, '/home/claude/work/spkg/mirisaju_model'); from predict import Model
M = Model('/home/claude/work/spkg/mirisaju_model/model'); NEW = sys.argv[1] == 'new'; PORT = int(sys.argv[2])
NOTE = '노트'
def _num(v): return None if v is None or v != v else round(float(v), 3)
def to_response(r):
    base = {'eligible': bool(r['eligible']), 'ratio_now': _num(r.get('ratio_now'))}
    if not r['eligible']: return {**base, 'reason': r['reason'], 'model': {'note': NOTE}}
    out = {**base, 'band': r['band'], 'top_pct': round(r['top_pct'], 1), 'abstain': bool(r['abstain']),
           'reasons': [{'label': x['label'], 'effect': round(x['effect'], 3)} for x in r['reasons']], 'programs': [], 'model': {'version': r.get('model'), 'note': NOTE}}
    if NEW:
        out['mode'] = r.get('mode', 'above'); out['reasons'] = [{'feature': x['feature'], 'label': x['label'], 'effect': round(x['effect'], 3)} for x in r['reasons']]
    return out
class H(BaseHTTPRequestHandler):
    def do_POST(self):
        b = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
        o = json.dumps(to_response(M.predict(b)), ensure_ascii=False).encode()
        self.send_response(200); self.send_header('Content-Type', 'application/json'); self.end_headers(); self.wfile.write(o)
    def log_message(self, *a): pass
HTTPServer.allow_reuse_address = True; HTTPServer(('127.0.0.1', PORT), H).serve_forever()

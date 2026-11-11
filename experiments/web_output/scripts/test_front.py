import json, threading, http.server, socketserver, os, functools
from playwright.sync_api import sync_playwright
SITE = '/home/claude/front_e'; OUT = os.path.dirname(__file__)

class Mock(http.server.BaseHTTPRequestHandler):
    def _h(self):
        self.send_header('Access-Control-Allow-Origin', '*'); self.send_header('Access-Control-Allow-Headers', 'Content-Type'); self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
    def do_OPTIONS(self): self.send_response(204); self._h(); self.end_headers()
    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
        Mock.last = body
        r = {'band': 'high', 'top_pct': 12, 'abstain': False,
             'reasons': [{'label': '최근 4년 중 가장 낮았던 소득', 'effect': 0.8}, {'label': '최근 2년 내 실직', 'effect': 0.5}, {'label': '연금 가입', 'effect': -0.2}],
             'programs': ['중장년 재취업 지원 상담', '주택연금 예상액 조회'], 'model': {'note': '테스트 응답'}}
        b = json.dumps(r).encode(); self.send_response(200); self._h(); self.send_header('Content-Type', 'application/json'); self.end_headers(); self.wfile.write(b)
    def log_message(self, *a): pass

socketserver.TCPServer.allow_reuse_address = True
def serve(handler, port):
    s = socketserver.TCPServer(('127.0.0.1', port), handler); threading.Thread(target=s.serve_forever, daemon=True).start(); return s
serve(functools.partial(http.server.SimpleHTTPRequestHandler, directory=SITE), 8711)
serve(Mock, 8712)

with sync_playwright() as p:
    b = p.chromium.launch()
    errs = []
    def page(w, h, scheme='light'):
        ctx = b.new_context(viewport={'width': w, 'height': h}, color_scheme=scheme)
        pg = ctx.new_page(); pg.route('**/cdn.jsdelivr.net/**', lambda r: r.abort())
        pg.on('pageerror', lambda e: errs.append(str(e))); pg.on('console', lambda m: m.type == 'error' and 'jsdelivr' not in m.text and 'Failed to load' not in m.text and errs.append(m.text))
        return pg
    # 1 landing desktop + mobile + dark
    pg = page(1280, 900); pg.goto('http://127.0.0.1:8711/'); pg.screenshot(path=f'{OUT}/f1_landing.png', full_page=True)
    m = page(390, 844); m.goto('http://127.0.0.1:8711/'); m.screenshot(path=f'{OUT}/f2_mobile.png', full_page=True)
    print('mobile overflow', m.evaluate('document.documentElement.scrollWidth'), 'vs 390')
    d = page(1280, 900, 'dark'); d.goto('http://127.0.0.1:8711/'); d.screenshot(path=f'{OUT}/f3_dark.png')
    # 2 flow without API: parent, preset 2, submit
    pg.click('[data-start="parent"]'); print('title:', pg.text_content('#formTitle'))
    pg.click('.preset >> nth=1'); pg.screenshot(path=f'{OUT}/f4_form.png', full_page=True)
    pg.click('#submitBtn'); pg.wait_for_timeout(300); pg.screenshot(path=f'{OUT}/f5_result_noapi.png', full_page=True)
    print('noapi badge:', pg.text_content('#mlBody .badge'), '| short:', pg.text_content('#shortV'), '| after:', pg.text_content('#afterV'), '| ratio:', pg.text_content('#ratioV'))
    print('programs:', [x.strip()[:20] for x in pg.locator('#progList li').all_text_contents()])
    pg.uncheck('#solHouse'); print('after w/o house:', pg.text_content('#afterV'), pg.text_content('#addV'))
    # quick parse
    pg.click('[data-go="inputView"]'); pg.fill('#quickText', '어머니 63세 1인 가구, 월 180만원, 작년에 퇴직, 집 2.5억, 예금 3천, 대출 1천'); pg.click('#quickBtn')
    print('quick:', pg.text_content('#quickMsg'), {k: pg.input_value('#' + k) for k in ['age', 'hh', 'inc', 'real', 'fin', 'debt']},
          pg.get_attribute('.yn[data-k="lostJob"] [data-v="1"]', 'aria-pressed'), pg.get_attribute('.yn[data-k="female"] [data-v="1"]', 'aria-pressed'))
    # age out of range
    pg.fill('#age', '45'); pg.click('#submitBtn'); pg.wait_for_timeout(200); print('age45:', pg.text_content('#mlBody .badge'))
    # 3 with mock API
    a = page(1280, 900); a.goto('http://127.0.0.1:8711/?api=http://127.0.0.1:8712'); a.click('[data-start="me"]'); a.click('.preset >> nth=1'); a.click('#submitBtn')
    a.wait_for_selector('#mlBody .bars'); a.screenshot(path=f'{OUT}/f6_result_api.png', full_page=True)
    print('api badge:', a.text_content('#mlBody .badge'), '| sent:', Mock.last)
    am = page(390, 844); am.goto('http://127.0.0.1:8711/?api=http://127.0.0.1:8712'); am.click('[data-start="me"]'); am.click('#submitBtn'); am.wait_for_selector('#mlBody .bars')
    am.screenshot(path=f'{OUT}/f7_result_mobile.png', full_page=True); print('result mobile overflow', am.evaluate('document.documentElement.scrollWidth'))
    print('ERRORS:', errs)
    b.close()

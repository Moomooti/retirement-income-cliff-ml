from playwright.sync_api import sync_playwright
import sys
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page()
    pg.goto('file://' + sys.argv[2] if len(sys.argv) > 2 else 'file:///home/claude/work/report.html'); pg.wait_for_timeout(1500)
    pg.pdf(path=sys.argv[1], format='A4', print_background=True,
           display_header_footer=True, header_template='<span></span>',
           footer_template='<div style="font-size:7pt;color:#8a8984;width:100%;text-align:center;font-family:Noto Sans CJK KR">미리사주 · <span class="pageNumber"></span>/<span class="totalPages"></span></div>',
           margin=dict(top='14mm', bottom='16mm', left='15mm', right='15mm'))
    b.close()
print('pdf ok')

"""메인 화면 왼쪽 아래에 여우 영상(배경 제거한 움직이는 그림 fox.webp)을 띄운다. 화면 전환 연출 없음."""
import sys
src, out = sys.argv[1:3]
s = open(src, encoding='utf-8').read()
def rep(a, b):
    global s
    assert s.count(a) == 1, (a[:60], s.count(a)); s = s.replace(a, b)
rep('</style>\n</head>', '''
/* ===== 여우 친구 (메인 화면에서만) ===== */
#pet{position:fixed;left:max(8px,2vw);bottom:0;z-index:15;width:clamp(170px,22vw,300px);pointer-events:none;transition:opacity .5s}
#pet img{display:block;width:100%;height:auto;filter:drop-shadow(0 8px 10px rgba(120,92,40,.18))}
#pet.off{opacity:0}
@media (prefers-reduced-motion:reduce){#pet{display:none}}
</style>
</head>''')
rep('<canvas id="embers" aria-hidden="true"></canvas>',
    '<div id="pet" aria-hidden="true"><img src="fox.webp" alt="" width="467" height="320" decoding="async" onerror="this.parentNode.remove()"></div>\n<canvas id="embers" aria-hidden="true"></canvas>')
rep("function show(id){ views.forEach(v => $(v).classList.toggle('hidden', v !== id)); window.scrollTo({ top: 0, behavior: 'smooth' }); }",
    "function show(id){ views.forEach(v => $(v).classList.toggle('hidden', v !== id)); window.scrollTo({ top: 0, behavior: 'smooth' }); const pet = $('pet'); if (pet) pet.classList.toggle('off', id !== 'landing'); }")
open(out, 'w', encoding='utf-8').write(s); print('ok')

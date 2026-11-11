"""미리사주: 흑화(검정·핏빛·반말) → 온화한 아기씨(아이보리·금빛·존댓말). 구조·애니메이션 유지."""
import re, sys, base64
src, img, out = sys.argv[1:4]
s = open(src, encoding='utf-8').read()

def rep(a, b, n=1):
    global s
    c = s.count(a)
    assert c == n, (a[:70], c)
    s = s.replace(a, b)

# ---------- 1. 색 토큰 ----------
rep('''  --ink:#0b0708; --ink2:#120c0e; --card:#17100f; --card2:#1f1416; --line:#3a1f24; --line2:#5a2a31;
  --blood:#c8102e; --blood2:#ff2d4a; --ember:#ff5a6e; --silver:#cfc7c9; --text:#f4eceb; --text2:#c9b8b9; --text3:#8f7b7e;
  --gold:#e9c46a; --ok:#7bd3a5;''',
'''  --ink:#faf6ec; --ink2:#f4eddc; --card:#fffdf7; --card2:#fcf7ea; --line:#ebdfc4; --line2:#dcc896;
  --blood:#b8892b; --blood2:#d4a637; --ember:#a87420; --silver:#cfc7c9; --text:#3b3024; --text2:#5f5242; --text3:#8c7c64;
  --gold:#c9a24a; --ok:#5f9e80;''')
rep('<meta name="theme-color" content="#0b0708">', '<meta name="theme-color" content="#faf6ec">')

# ---------- 2. 하드코딩 색 ----------
s = s.replace('rgba(255,45,74,', 'rgba(212,166,55,').replace('rgba(200,16,46,', 'rgba(184,137,43,')
s = s.replace('rgba(120,10,30,', 'rgba(230,200,120,')
s = s.replace('rgba(11,7,8,', 'rgba(250,246,236,').replace('rgba(23,16,15,', 'rgba(255,253,247,').replace('rgba(15,10,11,', 'rgba(255,253,247,')
s = s.replace('rgba(233,196,106,', 'rgba(201,162,74,').replace('rgba(123,211,165,', 'rgba(95,158,128,')
s = re.sub(r'rgba\(0,0,0,(\.?\d*\.?\d+)\)', lambda m: f'rgba(120,92,40,{round(float(m.group(1))*0.28,3)})', s)
s = s.replace('#0f0a0b', '#fffdf8').replace('#1a0e10', '#fffdf7')
s = s.replace('stroke="#ff2d4a"', 'stroke="#c9a24a"').replace('stroke="#ff5a6e"', 'stroke="#d8b65e"').replace('stop-color="#ff2d4a"', 'stop-color="#f3d27a"')
# 제목 글자: 핏빛 그라데이션 → 금빛
rep('background:linear-gradient(180deg,#ffd9de 0%,#ff4560 38%,#c8102e 62%,#5c0716 100%)', 'background:linear-gradient(180deg,#e9c46a 0%,#c9962f 45%,#a87420 70%,#6f4c12 100%)')
rep('filter:drop-shadow(0 2px 0 #000)', 'filter:drop-shadow(0 1px 0 rgba(255,255,255,.9))')
rep('.titlebox .over{font-family:var(--title);font-weight:800;font-size:15px;letter-spacing:.35em;color:#f3d6da;', '.titlebox .over{font-family:var(--title);font-weight:800;font-size:15px;letter-spacing:.35em;color:#8a6420;')
rep('color:#ff8a98;letter-spacing:.2em', 'color:#8a6a2a;letter-spacing:.2em')
rep('background:linear-gradient(180deg,#e0153a,#9e0b23);color:#fff', 'background:linear-gradient(180deg,#dcb350,#b0842a);color:#fff')
rep('color:#ffd7dc}', 'color:#7a5a17}')
rep('.seg button[aria-pressed="true"]{border-color:var(--blood2);color:#fff;', '.seg button[aria-pressed="true"]{border-color:var(--blood2);color:var(--text);')
rep('.badge.high{color:#fff;', '.badge.high{color:#6b4a10;')
rep('.badge.mid{color:#ffe1a8;', '.badge.mid{color:#7d6224;')
rep('.badge.low{color:#c9f2dc;', '.badge.low{color:#3d6f57;')
rep('.fill.down{background:linear-gradient(90deg,#2f6f55,var(--ok))}', '.fill.down{background:linear-gradient(90deg,#a9d3bd,var(--ok))}')
rep('.dots i{display:block;aspect-ratio:1;border-radius:50%;background:rgba(255,255,255,.09)}', '.dots i{display:block;aspect-ratio:1;border-radius:50%;background:rgba(120,92,40,.12)}')
rep('.gcard .glinks a:hover,.gcard .glinks a:focus-visible{border-color:var(--blood2);color:#fff}', '.gcard .glinks a:hover,.gcard .glinks a:focus-visible{border-color:var(--blood2);color:var(--text)}')
rep('background:#fffdf7;color:#fff;font-weight:700;cursor:pointer;box-shadow', 'background:#fffdf7;color:var(--text);font-weight:700;cursor:pointer;box-shadow')
# 금빛 위 흰 글씨는 대비가 약하니 진하게
rep('.cb-msg.me{align-self:flex-end;background:var(--blood);color:#fff;', '.cb-msg.me{align-self:flex-end;background:#9a7020;color:#fff;')
rep('.cb-form button{border:0;border-radius:12px;padding:0 16px;background:var(--blood);color:#fff;', '.cb-form button{border:0;border-radius:12px;padding:0 16px;background:#9a7020;color:#fff;')
# 메인 버튼 글자 대비: 금빛 배경 + 흰 글씨 → 그림자 보강
rep('.btn.main:hover{filter:brightness(1.08)}', '.btn.main{text-shadow:0 1px 1px rgba(110,76,16,.45)}\n.btn.main:hover{filter:brightness(1.05)}')

# ---------- 3. 떠오르는 불티 → 금빛 빛가루 (밝은 배경에서 보이게 합성 방식 변경) ----------
rep("hue: Math.random() < .8 ? 352 : 18 }", "hue: Math.random() < .8 ? 43 : 50 }")
rep("ctx.clearRect(0, 0, W, H); ctx.globalCompositeOperation = 'lighter';", "ctx.clearRect(0, 0, W, H); ctx.globalCompositeOperation = 'source-over';")
rep("g.addColorStop(0, `hsla(${p.hue},100%,70%,${a})`); g.addColorStop(1, `hsla(${p.hue},100%,50%,0)`);",
    "g.addColorStop(0, `hsla(${p.hue},85%,58%,${a * .75})`); g.addColorStop(1, `hsla(${p.hue},90%,70%,0)`);")
rep("/* ===== 떠오르는 불티 (움직임 줄이기 설정이면 끔) ===== */", "/* ===== 떠오르는 금빛 빛가루 (움직임 줄이기 설정이면 끔) ===== */")

# ---------- 4. 캐릭터 그림 ----------
b64 = base64.b64encode(open(img, 'rb').read()).decode()
s, k = re.subn(r'<img src="data:image/[a-z]+;base64,[A-Za-z0-9+/=]+" width="864" height="1536" alt="[^"]*">',
               f'<img src="data:image/jpeg;base64,{b64}" width="864" height="1414" alt="흰 모자와 금빛 장식의 흰 한복을 입고 두 손을 모은 채 미소 짓는 아기씨 캐릭터">', s)
assert k == 1

# ---------- 5. 이름과 말투 ----------
rep('<title>미리사주 – 흑화 아기씨의 노후 사주</title>', '<title>미리사주 – 아기씨의 노후 사주</title>')
rep('<span class="kicker">흑화 아기씨의 노후 사주</span>', '<span class="kicker">아기씨가 살펴 드리는 노후 사주</span>')
rep('<p class="quote">"어서 오너라. 지금은 괜찮아 보여도, 2년 뒤의 노후 운은 내가 미리 짚어 주마."<small>— 흑화 아기씨</small></p>',
    '<p class="quote">"어서 오세요. 지금은 괜찮아 보여도, 2년 뒤의 노후 운을 제가 미리 살펴 드릴게요."<small>— 아기씨</small></p>')
rep('노후를 받치는 <b>네 기둥</b>을 차례로 알려 주면 된다. 겁낼 것 없다. 미리 보면 바꿀 수 있으니.',
    '노후를 받치는 <b>네 기둥</b>을 차례로 들려주세요. 걱정하지 않으셔도 돼요. 미리 보면 바꿀 수 있으니까요.')
rep('<div class="over">흑 화 아 기 씨</div>', '<div class="over">아 기 씨</div>')
rep('"태어난 해만 알려 주면, 국민연금이 언제 열리는지는 내가 셈하마."', '"태어난 해만 알려 주시면, 국민연금이 언제 열리는지는 제가 셈해 드릴게요."')
rep('"곳간에 어떤 연금이 들어 있는지만 말하거라. 금액은 묻지 않으마."', '"곳간에 어떤 연금이 들어 있는지만 알려 주세요. 금액은 묻지 않을게요."')
rep('"지금 얼마인지보다, 어떻게 흘러왔는지가 더 많은 걸 말해 준다."', '"지금 얼마인지보다, 어떻게 흘러왔는지가 더 많은 걸 알려 줘요."')
rep('"마지막이다. 일의 흐름과, 곳간 밖의 재산을 보자."', '"마지막이에요. 일의 흐름과 곳간 밖의 재산을 함께 볼게요."')
rep('네 기둥을 읽었다</h2>', '네 기둥을 읽었어요</h2>')
# 입력 오류 문구
for a, b in [('출생연도를 1940~2000 사이로 알려 주거라.', '출생연도를 1940~2000 사이로 알려 주세요.'),
             ('성별, 배우자, 학력을 골라 주거라.', '성별, 배우자, 학력을 골라 주세요.'),
             ('지금과 2년 전 가구원 수를 1~10명으로 알려 주거라.', '지금과 2년 전 가구원 수를 1~10명으로 알려 주세요.'),
             ('세 가지 연금을 모두 예·아니오로 골라 주거라.', '세 가지 연금을 모두 예·아니오로 골라 주세요.'),
             ('지금·1년 전·2년 전 월소득을 모두 적어 주거라.', '지금·1년 전·2년 전 월소득을 모두 적어 주세요.'),
             ('지금, 1년 전, 2년 전에 일했는지 골라 주거라.', '지금, 1년 전, 2년 전에 일했는지 골라 주세요.'),
             ('일의 형태를 골라 주거라.', '일의 형태를 골라 주세요.'),
             ('사는 집이 자가인지 골라 주거라.', '사는 집이 자가인지 골라 주세요.'),
             ('금융자산, 부동산, 부채를 적어 주거라. 없으면 0이다.', '금융자산, 부동산, 부채를 적어 주세요. 없으면 0이면 돼요.')]:
    rep(a, b)
rep('아기씨가 점괘를 읽는 중… (처음 한 번은', '아기씨가 풀이를 살피는 중이에요… (처음 한 번은')
rep('"이번 점괘는 위험과 평온이 함께 보이는구나. 확신하지 못할 때는 말을 아끼는 법이다."', '"이번 풀이는 걱정과 평온이 함께 보여요. 확신이 없을 때는 섣불리 말하지 않을게요."')
# 아기씨 한마디
rep(""""지금 곳간이 이미 얇구나. 혼자 버티지 말고, 주민센터 복지 상담부터 받아 보거라.\"""", """"지금 곳간이 조금 얇아 보여요. 혼자 버티지 마시고, 주민센터 복지 상담부터 받아 보세요.\"""")
rep(""""최근에 일을 내려놓았구나. 흐름이 꺾인 지금이 다음 일을 찾기 가장 좋은 때다. 고용센터의 중장년 재취업 지원을 살펴보거라.\"""",
    """"최근에 일을 내려놓으셨군요. 흐름이 바뀐 지금이 다음 일을 찾기 좋은 때예요. 고용센터의 중장년 재취업 지원을 함께 살펴봐요.\"""")
rep("""% 줄었구나. 꺾일 때가 준비하기 가장 좋은 때다.\"""", """% 줄었네요. 흐름이 바뀔 때가 준비하기 가장 좋은 때예요.\"""")
rep(""""식구가 줄었구나. 함께 벌던 손이 줄면 곳간도 달라진다. 연금과 생활비를 한 번 다시 셈해 보거라.\"""",
    """"식구가 줄었군요. 함께 벌던 손이 줄면 곳간도 달라져요. 연금과 생활비를 한 번 다시 셈해 보세요.\"""")
rep("""년, 그 사이를 받칠 다른 연금이 보이지 않는구나. 미리 다리를 놓아 두거라.\"""", """년, 그 사이를 받쳐 줄 다른 연금이 아직 보이지 않아요. 미리 다리를 놓아 두면 마음이 편해져요.\"""")
rep(""""빚이 연소득의 두 해 치를 넘는구나. 은퇴 전에 그 무게를 덜어 두면 노후가 한결 가볍다.\"""", """"빚이 연소득의 두 해 치를 넘어요. 은퇴 전에 그 무게를 조금씩 덜어 두면 노후가 한결 가벼워져요.\"""")
rep(""""네 기둥이 크게 흔들리지는 않는구나. 그래도 운은 해마다 바뀌니, 한 해에 한 번은 다시 짚어 보거라.\"""", """"네 기둥이 든든하게 서 있어요. 그래도 운은 해마다 바뀌니, 한 해에 한 번은 다시 살펴봐요.\"""")
# 챗봇
rep("add('bot', '어서 오너라. 노후 소득, 연금, 복지 제도에 대해 무엇이든 물어보거라.');", "add('bot', '어서 오세요. 노후 소득, 연금, 복지 제도에 대해 무엇이든 편하게 물어보세요.');")
rep("const wait = add('sys', '아기씨가 점괘를 읽는 중…');", "const wait = add('sys', '아기씨가 답을 살피는 중이에요…');")
rep('<meta name="description" content="출생연도와', '<meta name="description" content="아기씨가 다정하게 살펴 드리는 노후 사주. 출생연도와')

left = [w for w in ['거라', '흑화', '오너라', '하마', '으마', '#ff2d4a', '#c8102e', 'rgba(255,45,74'] if w in s]
print('남은 흔적:', left)
open(out, 'w', encoding='utf-8').write(s)

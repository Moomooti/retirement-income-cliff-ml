import sys, os, types, importlib
sys.path.insert(0, 'stub'); os.environ['ANTHROPIC_API_KEY'] = 'x'
FULL = dict(birth_year=1964, female=0, married=1, edu3=1, hh_size=2, hh_size_2y=2, pension_recv=0, retire_pension=0, private_pension=0,
            income_now=260, income_1y=300, income_2y=330, employed=1, employed_1y=1, employed_2y=1, job_type='regular', owner=1, fin_asset=3000, real_asset=30000)
B = lambda **k: types.SimpleNamespace(**k)
class Fake:
    """실제 문제 재현: 도구를 강제하지 않으면 모델이 도구를 건너뛰고 '다 모였어요'라고만 답한다."""
    def __init__(self, skip_reply_done=False): self.calls = []; self.messages = self; self.skip_reply_done = skip_reply_done
    def create(self, **kw):
        self.calls.append(kw); st = kw['system']
        if 'tools' in kw and 'tool_choice' not in kw:
            return B(content=[B(type='text', text='빚이 없으시다고요. 네 기둥이 다 모였어요. 아래 [풀이 보러 가기] 버튼을 눌러 주세요.')])
        if 'tool_choice' in kw:
            return B(content=[B(type='tool_use', input={'debt': 0})])
        done = '남은 칸 수: 0' in st
        txt = '네 기둥이 다 모였어요. 아래 [풀이 보러 가기] 버튼을 눌러 주세요.' if (done or self.skip_reply_done) else '빚은 얼마인가요?'
        return B(content=[B(type='text', text=txt)])
req = B(client=B(host='1.1.1.1'))
for name in ['orig_chat', 'chat_fixed']:
    m = importlib.import_module(name); f = Fake(); m.get_client = lambda f=f: f
    body = m.ChatIn(messages=[{'role': 'user', 'content': '빚은 없어요'}], profile=FULL)
    r = m.chat(body, req)
    print(f'{name:11s} ready={r["ready"]} missing={r["missing"]} 호출={len(f.calls)} reply={r["reply"][:40]}')
# 고친 코드: 모델이 빈칸이 남았는데도 '다 모였어요'라고 하면 → 남은 칸을 묻는 말로 바뀌는지
m = importlib.import_module('chat_fixed'); f = Fake(skip_reply_done=True); m.get_client = lambda: f
p = dict(FULL); p.pop('owner')
r = m.chat(m.ChatIn(messages=[{'role': 'user', 'content': '그냥 넘어갈게요'}], profile=p), req)
print('guard      ready=%s missing=%s reply=%s' % (r['ready'], r['missing'], r['reply']))

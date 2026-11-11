"""챗봇 테스트: 실제 Claude API는 부르지 않고 가짜 클라이언트로 확인한다."""
import logging, os, subprocess, sys
from types import SimpleNamespace
from fastapi.testclient import TestClient
import app.chat as chat
from app.main import app

client = TestClient(app)
SECRET = '비밀메모-48213'


class FakeClient:
    def __init__(self): self.calls = []
    @property
    def messages(self): return self
    def create(self, **kw):
        self.calls.append(kw)
        return SimpleNamespace(content=[SimpleNamespace(type='text', text='안녕하세요, 미리노후 안내 챗봇입니다.')])


def setup_function(_):
    chat._client = FakeClient(); chat._per_ip.clear(); chat._day.update(date='', n=0)


def test_chat_ok_and_key_stays_server_side():
    r = client.post('/chat', json={'messages': [{'role': 'user', 'content': '노후 준비 뭐부터 해요?'}]})
    assert r.status_code == 200 and r.json() == {'reply': '안녕하세요, 미리노후 안내 챗봇입니다.'}
    kw = chat._client.calls[0]
    assert kw['model'] == chat.MODEL and kw['system'] == chat.SYSTEM and kw['max_tokens'] == chat.MAX_TOKENS
    assert 'test-key-not-real' not in r.text


def test_chat_validation():
    bad = [{'messages': []}, {'messages': [{'role': 'system', 'content': 'x'}]},
           {'messages': [{'role': 'user', 'content': 'x' * 2001}]},
           {'messages': [{'role': 'assistant', 'content': 'hi'}]},
           {'messages': [{'role': 'user', 'content': 'a'}, {'role': 'assistant', 'content': 'b'}]}]
    for b in bad:
        assert client.post('/chat', json=b).status_code == 422, b


def test_chat_rate_limit():
    codes = [client.post('/chat', json={'messages': [{'role': 'user', 'content': 'hi'}]}).status_code
             for _ in range(chat.PER_MIN + 1)]
    assert codes[:-1] == [200] * chat.PER_MIN and codes[-1] == 429


def test_chat_no_content_in_logs(caplog):
    class Boom(FakeClient):
        def create(self, **kw): raise RuntimeError(SECRET)
    with caplog.at_level(logging.DEBUG):
        client.post('/chat', json={'messages': [{'role': 'user', 'content': SECRET}]})
        chat._client = Boom()
        r = client.post('/chat', json={'messages': [{'role': 'user', 'content': SECRET}]})
    assert r.status_code == 502 and SECRET not in caplog.text and SECRET not in r.text


def test_predict_off_by_default_and_chat_without_key():
    """기본 설정(ENABLE_PREDICT 없음, 키 없음)으로 띄우면 /predict는 503, /chat도 503."""
    code = ("import os\nfor k in ('ENABLE_PREDICT','ANTHROPIC_API_KEY'): os.environ.pop(k, None)\n"
            "from fastapi.testclient import TestClient\nfrom app.main import app, model\nc=TestClient(app)\n"
            "assert model is None\nassert c.get('/health').json()=={'status':'ok','predict':False}\n"
            "assert c.post('/predict', json={}).status_code in (422,503)\n"
            "assert c.post('/predict', json=dict(birth_year=1964,female=0,married=1,edu3=1,hh_size=2,hh_size_2y=2,pension_recv=0,retire_pension=0,private_pension=0,income_now=300,income_1y=300,income_2y=300,employed=1,employed_1y=1,employed_2y=1,job_type='regular',owner=1,fin_asset=0,real_asset=0,debt=0)).status_code==503\n"
            "assert c.post('/chat', json={'messages':[{'role':'user','content':'hi'}]}).status_code==503\n"
            "print('ok')")
    env = {k: v for k, v in os.environ.items() if k not in ('ENABLE_PREDICT', 'ANTHROPIC_API_KEY')}
    out = subprocess.run([sys.executable, '-c', code], cwd=os.path.join(os.path.dirname(__file__), '..'),
                         env=env, capture_output=True, text=True)
    assert out.stdout.strip() == 'ok', out.stderr

import sys
s = open(sys.argv[1], encoding='utf-8').read()
def rep(a, b):
    global s; assert s.count(a) == 1, a[:60]; s = s.replace(a, b)
old_start = s.index("    try:\n        try:                                                           # ① 값 뽑기")
old_end = s.index("    except Exception as e:                                             # 대화 내용이 섞이지 않게 예외 종류만 기록")
s = s[:old_start] + """    try:
        try:                                                           # ① 값 뽑기: 매 요청마다 fill_profile 도구를 '반드시' 쓰게 함
            r = client.messages.create(model=MODEL, max_tokens=MAX_TOKENS, system=SYSTEM + _state(profile),
                                       tools=[TOOL], tool_choice={'type': 'tool', 'name': 'fill_profile'},
                                       messages=msgs)                  # 말풍선보다 값 저장이 먼저 (도구를 건너뛰고 '다 모였어요'라고 답하는 일 방지)
            for t in [b for b in r.content if getattr(b, 'type', '') == 'tool_use']:  # 도구로 넣은 값마다
                profile.update(_clean(t.input))                        # 검사 통과한 값만 프로필에 합침
        except Exception as e:                                         # 값 뽑기가 실패해도 상담은 계속되게
            log.error('tool step failed: %s', type(e).__name__)        # 오류 종류만 기록
        r = client.messages.create(model=MODEL, max_tokens=MAX_TOKENS,  # ② 답하기: 갱신된 상태를 보고 말풍선을 만듦
                                   system=SYSTEM + _state(profile), messages=msgs)  # → 말풍선과 ready가 항상 같은 상태를 봄
        text = _text(r)                                                # 그 답을 씀
""" + s[old_end:]
rep("""    left = _needed(profile)                                            # 남은 빈칸
    if not text.strip():""", """    left = _needed(profile)                                            # 남은 빈칸
    if left and ('풀이 보러 가기' in text or '다 모였' in text):          # 아직 빈칸이 있는데 '다 모였다'고 말하면 (버튼이 안 나오는 어긋남)
        text = '거의 다 모였어요. ' + _ask(left)                          # 남은 칸을 여쭙는 말로 바꿈
    if not text.strip():""")
rep("""def _state(profile: dict) -> str:""", """ASK = {'birth_year': '태어나신 해', 'female': '성별', 'married': '배우자가 계신지', 'edu3': '학력',
       'hh_size': '지금 함께 사는 가구원 수', 'hh_size_2y': '2년 전 가구원 수', 'pension_recv': '국민연금 같은 공적연금을 받고 계신지',
       'retire_pension': '퇴직연금 가입 여부', 'private_pension': '개인연금 가입 여부', 'income_now': '지금 가구 한 달 실수령 소득',
       'income_1y': '1년 전 한 달 소득', 'income_2y': '2년 전 한 달 소득', 'employed': '지금 일하고 계신지', 'employed_1y': '1년 전에 일하셨는지',
       'employed_2y': '2년 전에 일하셨는지', 'job_type': '일의 형태(상용직·임시·일용직·자영업)', 'owner': '사는 집이 자가인지',
       'fin_asset': '예금·주식 같은 금융자산', 'real_asset': '가진 부동산 시세', 'debt': '남은 빚'}   # 남은 칸을 쉬운 말로 여쭐 때 씀


def _ask(left: list) -> str:                                           # 남은 칸이 있는 첫 묶음에서, 아직 빈 칸만 여쭙기
    g = next(([k for k in g if k in left] for g in GROUPS if any(k in left for k in g)), [])
    return (', '.join(ASK[k] for k in g) + '도 알려 주시겠어요?') if g else '이어서 말씀해 주세요.'


def _state(profile: dict) -> str:""")
open(sys.argv[2], 'w', encoding='utf-8').write(s); print('ok')

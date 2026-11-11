백엔드 chat.py 수정 (back_E/backend/app/chat.py) — 고칠 곳 3군데

■ 왜 한 번 더 보내야 버튼이 나왔나
지금 코드는 ①번 호출에서 Claude에게 fill_profile 도구를 "써도 되고 안 써도 되게" 준다.
마지막 답(예: "빚은 없어요")에서 Claude가 도구를 건너뛰고 글로만 "네 기둥이 다 모였어요"라고 답하면,
  - 말풍선: "다 모였어요, [풀이 보러 가기]를 눌러 주세요"
  - 서버 profile: debt가 아직 비어 있음 → ready = false → 버튼 안 나옴
다음 메시지("ㅇㅇ")에서야 도구가 대화 전체를 다시 읽어 debt=0을 채우고 ready = true가 된다.
→ 말풍선과 ready가 서로 다른 상태를 보고 있어서 생긴 어긋남.

■ 고치는 방법
① 값 뽑기 호출에서 도구를 "반드시" 쓰게 한다 (tool_choice). 값이 먼저 저장된다.
② 말풍선은 항상 저장이 끝난 상태를 보고 다시 만든다. 그래서 말풍선과 ready가 같은 상태를 본다.
③ 안전장치: 그래도 빈칸이 남았는데 "다 모였"이라고 말하면, 남은 칸을 여쭙는 말로 바꾼다.
비용: 매 메시지 Claude 호출 2번 (지금도 값이 있는 메시지는 2번이었음. 값 없는 질문만 1번 → 2번으로 늘어남).

========================================================================
[1] def _state(profile: dict) -> str:  바로 위에 아래를 추가
========================================================================
ASK = {'birth_year': '태어나신 해', 'female': '성별', 'married': '배우자가 계신지', 'edu3': '학력',
       'hh_size': '지금 함께 사는 가구원 수', 'hh_size_2y': '2년 전 가구원 수', 'pension_recv': '국민연금 같은 공적연금을 받고 계신지',
       'retire_pension': '퇴직연금 가입 여부', 'private_pension': '개인연금 가입 여부', 'income_now': '지금 가구 한 달 실수령 소득',
       'income_1y': '1년 전 한 달 소득', 'income_2y': '2년 전 한 달 소득', 'employed': '지금 일하고 계신지', 'employed_1y': '1년 전에 일하셨는지',
       'employed_2y': '2년 전에 일하셨는지', 'job_type': '일의 형태(상용직·임시·일용직·자영업)', 'owner': '사는 집이 자가인지',
       'fin_asset': '예금·주식 같은 금융자산', 'real_asset': '가진 부동산 시세', 'debt': '남은 빚'}   # 남은 칸을 쉬운 말로 여쭐 때 씀


def _ask(left: list) -> str:                                           # 남은 칸이 있는 첫 묶음에서, 아직 빈 칸만 여쭙기
    g = next(([k for k in g if k in left] for g in GROUPS if any(k in left for k in g)), [])
    return (', '.join(ASK[k] for k in g) + '도 알려 주시겠어요?') if g else '이어서 말씀해 주세요.'


========================================================================
[2] def chat(...) 안에서 아래 '원래' 부분을 통째로 지우고
========================================================================
    try:
        try:                                                           # ① 값 뽑기: 사용자가 말한 값이 있으면 도구로 받음
            r = client.messages.create(model=MODEL, max_tokens=MAX_TOKENS, system=SYSTEM + _state(profile),
                                       tools=[TOOL], messages=msgs)    # 도구를 줘서 호출
            used = [b for b in r.content if getattr(b, 'type', '') == 'tool_use']  # 도구 사용 블록 찾기
            for t in used:                                             # 도구로 넣은 값마다
                profile.update(_clean(t.input))                        # 검사 통과한 값만 프로필에 합침
            text = '' if used else _text(r)                            # 도구를 안 썼으면 이 답을 그대로 씀
        except Exception as e:                                         # 도구 호출이 실패해도 상담은 계속되게
            log.error('tool step failed: %s', type(e).__name__)        # 오류 종류만 기록
            text = ''                                                  # ②에서 다시 답을 만듦
        if not text.strip():                                           # ② 값을 저장했거나 ①이 실패했으면
            r = client.messages.create(model=MODEL, max_tokens=MAX_TOKENS,
                                       system=SYSTEM + _state(profile), messages=msgs)  # 도구 없이, 갱신된 상태로 한 번 더 호출
            text = _text(r)                                            # 그 답을 씀

------------------------------------------------------------------------
→ 이렇게 바꾼다
------------------------------------------------------------------------
    try:
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

========================================================================
[3] 같은 함수 아래쪽,  left = _needed(profile)  줄 바로 다음에 2줄 추가
========================================================================
    if left and ('풀이 보러 가기' in text or '다 모였' in text):          # 아직 빈칸이 있는데 '다 모였다'고 말하면 (버튼이 안 나오는 어긋남)
        text = '거의 다 모였어요. ' + _ask(left)                          # 남은 칸을 여쭙는 말로 바꿈

(SYSTEM 프롬프트, FIELDS, 프론트는 안 바꿔도 됨.)

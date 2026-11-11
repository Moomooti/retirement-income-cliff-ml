# 챗봇 연결 안내 (팀원용)

```
브라우저(GitHub Pages) ──POST /chat──▶ 이 서버(Render) ──▶ Claude API
                                       └ ANTHROPIC_API_KEY는 여기 환경변수에만
```

**API 키는 index.html이나 프론트 코드에 절대 넣지 않는다.** GitHub Pages는 누구나 소스를 볼 수 있다.

## 서버 API

`POST /chat`
```json
요청: {"messages": [{"role": "user", "content": "노후 준비 뭐부터 해요?"}]}
응답: {"reply": "..."}
```
- 서버는 대화를 저장하지 않는다. 프론트가 지금까지의 대화를 매번 통째로 보낸다 (최대 20개, 각 2,000자).
- 첫 메시지와 마지막 메시지는 `user`여야 한다.
- 오류: 422 입력 형식, 429 요청이 너무 많음, 502 Claude 호출 실패, 503 키 미설정

## 프론트에 붙일 코드 (index.html CONFIG 아래)

```html
<script>
const CHAT_BASE = 'https://YOUR-SERVICE.onrender.com';   // 배포한 Render 주소
const chatHistory = [];
async function sendChat(text) {
  chatHistory.push({ role: 'user', content: text });
  try {
    const res = await fetch(CHAT_BASE + '/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ messages: chatHistory.slice(-20) }),
    });
    if (res.status === 429) throw new Error('잠시 후 다시 시도해 주세요.');
    if (!res.ok) throw new Error('챗봇에 연결하지 못했어요.');
    const { reply } = await res.json();
    chatHistory.push({ role: 'assistant', content: reply });
    return reply;
  } catch (e) {
    chatHistory.pop();                  // 실패한 질문은 대화에서 뺀다 (첫/끝이 user 규칙 유지)
    return e.message;
  }
}
</script>
```
- 답변을 화면에 넣을 때는 `textContent`를 쓴다 (`innerHTML` 금지).
- 채팅창 아래에 안내 문구를 둔다: "입력한 내용은 답변 생성을 위해 Anthropic(Claude)으로 전송되며, 미리노후 서버에는 저장되지 않습니다. 주민등록번호·계좌번호는 적지 마세요."

## 설정값 (Render → 서비스 → Environment)
| 이름 | 종류 | 값 |
|---|---|---|
| ANTHROPIC_API_KEY | 환경변수 (값은 화면에 가려짐) | Claude Console에서 만든 키 |
| ALLOWED_ORIGINS | 환경변수 | `https://mirinohulab.github.io` |
| CLAUDE_MODEL | 환경변수 (선택) | 기본 `claude-haiku-5-5` |
| CHAT_PER_MIN / CHAT_PER_DAY | 환경변수 (선택) | 기본 10 / 300 |

`ENABLE_PREDICT`는 넣지 않는다. 진단 모델은 서비스 모델 검증과 패널 약관 확인 뒤에 켠다.
비공개 GitHub 저장소에서 배포하므로 모델 파일이 공개되지는 않는다. 무료 인스턴스는 15분 동안 요청이 없으면 잠들고, 깨어나는 데 1분 정도 걸린다.

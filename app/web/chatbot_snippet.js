/* ===== 상담 챗봇: 프론트 → CHAT_BASE/chat → Claude. API 키는 서버에만 있음 ===== */
// 서버 응답: { reply, profile, missing, ready }
//  - profile(지금까지 모인 값)은 여기서 들고 있다가 다음 요청에 그대로 보낸다 (대화가 잘려도 값은 안 잊음)
//  - ready가 true면 [풀이 보러 가기] 버튼 → 입력 폼을 profile로 채우고 결과 화면으로 이동
//  - profile·대화는 이 브라우저 메모리에만 있다 (새로고침하면 사라짐, 저장 안 함)
(function(){
  if (!CONFIG.CHAT_BASE) return;
  const BASE = CONFIG.CHAT_BASE.replace(/\/$/, '');
  const fab = $('cbFab'), panel = $('cbPanel'), log = $('cbLog'), form = $('cbForm'), input = $('cbInput'), send = $('cbSend');
  const REQ = ['birth_year', 'female', 'married', 'edu3', 'hh_size', 'hh_size_2y', 'pension_recv', 'retire_pension', 'private_pension',
    'income_now', 'income_1y', 'income_2y', 'employed', 'employed_1y', 'employed_2y', 'job_type', 'owner', 'fin_asset', 'real_asset', 'debt'];
  const history = []; let profile = {}, busy = false, warmed = false, goBox = null;
  fab.hidden = false;

  // 모인 칸 진행 막대 (머리 아래)
  const prog = document.createElement('div'); prog.className = 'cb-prog'; prog.hidden = true;
  prog.innerHTML = '<span>기둥 칸 <b id="cbDone">0</b>/<span id="cbAll">20</span></span><span class="bar"><i id="cbBar"></i></span>';
  panel.insertBefore(prog, log);
  function setProgress(missing){
    const need = REQ.filter(k => !(k === 'job_type' && profile.employed === 0));
    const left = Array.isArray(missing) ? missing.length : need.filter(k => !(k in profile)).length;
    const done = need.length - left;
    if (done <= 0) { prog.hidden = true; return; }
    prog.hidden = false; $('cbDone').textContent = done; $('cbAll').textContent = need.length; $('cbBar').style.width = (done / need.length * 100) + '%';
  }

  function add(cls, text){ const d = document.createElement('div'); d.className = 'cb-msg ' + cls; d.textContent = text; log.appendChild(d); log.scrollTop = log.scrollHeight; return d; }
  function open(v){ panel.hidden = !v; fab.setAttribute('aria-expanded', String(v)); if (v){ input.focus(); warm(); } }
  function warm(){ if (warmed) return; warmed = true; fetch(BASE + '/health').catch(()=>{}); }
  fab.onclick = () => open(panel.hidden);
  $('cbClose').onclick = () => { open(false); fab.focus(); };
  document.addEventListener('keydown', e => { if (e.key === 'Escape' && !panel.hidden) { open(false); fab.focus(); } });

  add('bot', '어서 오세요, 아기씨예요. 대화로 답해 주시면 노후 사주 칸을 대신 채워 드리고, 사이트 쓰는 법이나 연금·복지 제도도 쉽게 알려 드려요.');
  const sg = document.createElement('div'); sg.className = 'cb-sugg';
  ['대화로 노후 사주 볼래요', '이 사이트는 어떻게 써요?', '판단 보류는 무슨 뜻이에요?', '국민연금 더 받으려면 어떻게 해요?'].forEach(t => {
    const b = document.createElement('button'); b.type = 'button'; b.textContent = t; b.onclick = () => { sg.remove(); ask(t); }; sg.appendChild(b); });
  log.appendChild(sg);

  // ---- 모인 값으로 입력 폼 채우기 (칸 이름 = collect()의 키) ----
  const INPUT = { birth_year: 'birth', hh_size: 'hh', hh_size_2y: 'hh2', income_now: 'inc0', income_1y: 'inc1', income_2y: 'inc2',
    fin_asset: 'fin', real_asset: 'real', debt: 'debt' };
  const SEG = ['female', 'married', 'edu3', 'pension_recv', 'retire_pension', 'private_pension', 'employed', 'employed_1y', 'employed_2y', 'job_type', 'owner', 'health'];
  function fillForm(p){
    for (const [k, id] of Object.entries(INPUT)) {
      if (p[k] === undefined || p[k] === null) continue;
      const box = $(id); box.value = p[k]; box.dispatchEvent(new Event('input', { bubbles: true }));   // 안내 문구·빚 추가 질문도 함께 갱신
    }
    for (const k of SEG) {                                   // 선택 버튼은 눌러서 채움 (화면 표시와 값이 같이 바뀜)
      if (p[k] === undefined || p[k] === null) continue;
      if (k === 'job_type' && p.employed === 0) continue;
      const b = document.querySelector(`.seg[data-k="${k}"] button[data-v="${p[k]}"]`); if (b) b.click();
    }
  }
  function toResult(review){
    fillForm(profile); open(false);
    if (!review) {
      for (let n = 0; n < 4; n++) {                          // 입력 화면과 같은 검사. 빠진 칸이 있으면 그 기둥으로 보냄
        const e = validate(n);
        if (e) { show('inputView'); go(n); $('err').textContent = e + ' 상담에서 빠진 칸만 채워 주세요.'; return; }
      }
      render(collect()); show('resultView'); return;
    }
    show('inputView'); go(0);
  }
  function showGo(){
    if (goBox) goBox.remove();
    goBox = document.createElement('div'); goBox.className = 'cb-go';
    const p = document.createElement('p'); p.textContent = '당신의 기둥이 다 모였어요. 이 값으로 풀이를 볼까요?';
    const row = document.createElement('div'); row.className = 'row';
    const a = document.createElement('button'); a.type = 'button'; a.className = 'main'; a.textContent = '풀이 보러 가기 ✦'; a.onclick = () => toResult(false);
    const b = document.createElement('button'); b.type = 'button'; b.className = 'sub2'; b.textContent = '입력값 먼저 확인'; b.onclick = () => toResult(true);
    row.append(a, b); goBox.append(p, row); log.appendChild(goBox); log.scrollTop = log.scrollHeight;
  }

  async function ask(text){
    if (busy || !text) return;
    busy = true; input.disabled = send.disabled = true;
    add('me', text); history.push({ role: 'user', content: text });
    const wait = add('sys', '아기씨가 답을 살피는 중이에요…');
    const slow = setTimeout(() => { wait.textContent = '서버를 깨우는 중이에요. 처음 한 번은 1분 정도 걸릴 수 있어요…'; }, 6000);
    const ctl = new AbortController(); const tm = setTimeout(() => ctl.abort(), 90000);
    try {
      const res = await fetch(BASE + '/chat', { method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ messages: history.slice(-20), profile }), signal: ctl.signal });
      if (res.status === 429) throw new Error('질문이 너무 많아요. 1분쯤 뒤에 다시 물어봐 주세요.');
      if (res.status === 503) throw new Error('상담 서버가 아직 준비되지 않았어요. 첫 화면의 노후 사주 시작하기로 직접 입력해 주세요.');
      if (!res.ok) throw new Error('지금은 답을 가져오지 못했어요. 잠시 후 다시 시도해 주세요.');
      const data = await res.json();
      const reply = String(data.reply || '').trim() || '잘 알려 주셨어요. 이어서 말씀해 주세요.';
      if (data.profile && typeof data.profile === 'object') profile = data.profile;   // 서버가 검사한 값만 들고 있음
      history.push({ role: 'assistant', content: reply });
      wait.remove(); add('bot', reply);
      setProgress(data.missing);
      if (data.ready) showGo(); else if (goBox) { goBox.remove(); goBox = null; }
    } catch (e) {
      history.pop();
      wait.textContent = e.name === 'AbortError' ? '응답이 너무 늦어요. 잠시 후 다시 시도해 주세요.' : (e.message || '연결에 실패했어요.');
    } finally {
      clearTimeout(slow); clearTimeout(tm); busy = false; input.disabled = send.disabled = false; input.focus();
      while (history.length > 20) history.shift();
      while (history.length && history[0].role !== 'user') history.shift();
    }
  }
  form.onsubmit = e => { e.preventDefault(); const t = input.value.trim(); input.value = ''; ask(t); };
})();

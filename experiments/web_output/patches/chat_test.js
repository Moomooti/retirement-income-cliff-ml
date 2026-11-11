const { chromium } = require('playwright'); const fs = require('fs');
const C = JSON.parse(fs.readFileSync(__dirname + '/cases.json', 'utf8'));
const full = { birth_year: 1964, female: 0, married: 1, edu3: 1, hh_size: 2, hh_size_2y: 2, pension_recv: 0, retire_pension: 1, private_pension: 0,
  income_now: 260, income_1y: 300, income_2y: 330, employed: 1, employed_1y: 1, employed_2y: 1, job_type: 'regular', owner: 1, fin_asset: 3000, real_asset: 30000, debt: 2000, health: 3 };
(async () => {
  const b = await chromium.launch(); const pg = await b.newPage({ viewport: { width: 1100, height: 900 } }); const errs = []; const sent = [];
  pg.on('pageerror', e => errs.push(e.message));
  let turn = 0;
  await pg.route('**/health', r => r.fulfill({ status: 200, body: '{}' }));
  await pg.route('**/chat', async r => { const body = JSON.parse(r.request().postData()); sent.push(body); turn++;
    let out;
    if (turn === 1) out = { reply: '반가워요. 태어나신 해와 성별을 알려 주시겠어요?', profile: {}, missing: Object.keys(full).filter(k => k !== 'health'), ready: false };
    else if (turn === 2) { const p = { birth_year: 1964, female: 0, married: 1, edu3: 1, hh_size: 2, hh_size_2y: 2 }; out = { reply: '잘 알려 주셨어요. 연금은요?', profile: p, missing: Object.keys(full).filter(k => k !== 'health' && !(k in p)), ready: false }; }
    else out = { reply: '네 기둥이 다 모였어요. 아래 [풀이 보러 가기] 버튼을 눌러 주세요.', profile: full, missing: [], ready: true };
    r.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(out) }); });
  await pg.route('**/predict', async r => { const body = JSON.parse(r.request().postData()); sent.push({ predict: body }); r.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(C.mid.r) }); });
  await pg.goto('file://' + process.argv[2]); await pg.waitForTimeout(300);
  await pg.click('#cbFab'); await pg.waitForTimeout(200);
  await pg.screenshot({ path: __dirname + '/c0.png' });
  await pg.click('.cb-sugg button'); await pg.waitForTimeout(400);
  await pg.fill('#cbInput', '1964년생 남자, 배우자 있고 고졸, 둘이 살아요'); await pg.press('#cbInput', 'Enter'); await pg.waitForTimeout(400);
  await pg.fill('#cbInput', '퇴직연금만 있고 ... (나머지 다 말함)'); await pg.press('#cbInput', 'Enter'); await pg.waitForTimeout(400);
  await pg.screenshot({ path: __dirname + '/c1.png' });
  console.log('2nd request profile sent:', JSON.stringify(sent[1].profile), '| 3rd:', Object.keys(sent[2].profile).length, 'keys');
  await pg.click('.cb-go .main'); await pg.waitForTimeout(1500);
  const st = await pg.evaluate(() => ({ view: ['landing','inputView','resultView'].find(v => !document.getElementById(v).classList.contains('hidden')), err: document.getElementById('err').textContent,
    sel: JSON.stringify(sel), birth: document.getElementById('birth').value, panelHidden: document.getElementById('cbPanel').hidden }));
  console.log(st);
  const pr = sent.find(x => x.predict); console.log('predict payload matches:', pr && Object.keys(full).every(k => pr.predict[k] === full[k]), pr && JSON.stringify(pr.predict).slice(0, 400));
  await pg.screenshot({ path: __dirname + '/c2.png' });
  // 빠진 칸이 있는 profile로 ready → 입력 화면으로 가는지
  await pg.evaluate(() => { document.querySelectorAll('.seg button').forEach(b => b.setAttribute('aria-pressed','false')); Object.keys(sel).forEach(k => sel[k] = null); ['birth','hh','hh2','inc0','inc1','inc2','fin','real','debt'].forEach(i => document.getElementById(i).value=''); show('landing'); });
  console.log('errors', errs);
  await b.close();
})();

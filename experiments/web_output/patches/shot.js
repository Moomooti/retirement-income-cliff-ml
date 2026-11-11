const { chromium } = require('playwright'); const fs = require('fs');
const [file, tag] = [process.argv[2], process.argv[3] || 'a'];
const C = JSON.parse(fs.readFileSync(__dirname + '/cases.json', 'utf8'));
(async () => {
  const b = await chromium.launch(); const errs = [];
  for (const k of Object.keys(C)) {
    const pg = await b.newPage({ viewport: { width: 900, height: 1400 } });
    pg.on('pageerror', e => errs.push(k + ': ' + e.message));
    await pg.route('**/predict', r => r.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(C[k].r) }));
    await pg.route('**/health', r => r.fulfill({ status: 200, body: '{}' }));
    await pg.goto('file://' + file); await pg.waitForTimeout(300);
    await pg.evaluate(P => { const by=P.birth_year, age=THIS_YEAR-by; render(Object.assign({ health: null, debt_type: null, debt_stress: null, age, age_to_60: age-60, age_to_nps: age-npsStartAge(by), hh_change_2y: P.hh_size-P.hh_size_2y, lost_job_2y: P.employed===0&&P.employed_2y===1?1:0 }, P)); show('resultView'); }, C[k].P);
    await pg.waitForTimeout(1200);
    await pg.evaluate(() => document.querySelectorAll('details.more').forEach(d => d.open = true));
    const el = await pg.$('#resultView'); await el.screenshot({ path: `${__dirname}/${tag}_${k}.png` }); await pg.close();
  }
  await b.close(); console.log('errors', errs);
})();

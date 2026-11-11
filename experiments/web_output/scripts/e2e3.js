const { chromium } = require('playwright');
const page_ = process.argv[2] || 'index_pet.html';
const base={birth:'1964', female:'0', married:'1', edu3:'1', hh:'2', hh2:'2', pension_recv:'0', retire_pension:'0', private_pension:'0', inc:['280','300','330'], employed:'1', employed_1y:'1', employed_2y:'1', job_type:'regular', owner:'1', fin:'1000', real:'35000', debt:'18000', health:null};
const cases = [
 {...base,name:'기준선 아래', hh:'2', hh2:'2', inc:['180','230','260']},
 {...base,name:'국민연금 공백 50대', birth:'1968', inc:['420','430','440'], pension_recv:'0', retire_pension:'1'},
 {...base,name:'주담대 잘 갚음', extra:async pg=>{await pg.click('.seg[data-k="debt_type"] button[data-v="mortgage"]');await pg.click('.seg[data-k="debt_stress"] button[data-v="ok"]');}},
 {...base,name:'빚 답 안 함'},
 {...base,name:'신용대출 빠듯', extra:async pg=>{await pg.click('.seg[data-k="debt_type"] button[data-v="other"]');await pg.click('.seg[data-k="debt_stress"] button[data-v="tight"]');}},
 {...base,name:'연체 걱정', extra:async pg=>{await pg.click('.seg[data-k="debt_stress"] button[data-v="overdue"]');}},
 {name:'일하는 2인 가구', birth:'1966', female:'0', married:'1', edu3:'1', hh:'2', hh2:'2', pension_recv:'0', retire_pension:'1', private_pension:'0', inc:['350','360','380'], employed:'1', employed_1y:'1', employed_2y:'1', job_type:'regular', owner:'1', fin:'3000', real:'40000', debt:'15000', health:null},
 {name:'최근 실직 1인', birth:'1963', female:'1', married:'0', edu3:'0', hh:'1', hh2:'2', pension_recv:'0', retire_pension:'0', private_pension:'0', inc:['190','240','300'], employed:'0', employed_1y:'1', employed_2y:'1', job_type:null, owner:'0', fin:'800', real:'0', debt:'500', health:'4'},
 {name:'나이 대상 아님', birth:'1980', female:'0', married:'1', edu3:'2', hh:'3', hh2:'3', pension_recv:'0', retire_pension:'1', private_pension:'1', inc:['500','500','480'], employed:'1', employed_1y:'1', employed_2y:'1', job_type:'self', owner:'1', fin:'5000', real:'50000', debt:'20000', health:null},
];
(async()=>{const b=await chromium.launch();
 for (const c of cases){
  const pg=await b.newPage({viewport:{width:1280,height:900}}); const errs=[]; pg.on('pageerror',e=>errs.push(e.message));
  let sent=null;
  await pg.route('**/predict', async r=>{ sent=JSON.parse(r.request().postData()); const res=await fetch('http://127.0.0.1:8765/predict',{method:'POST',headers:{'Content-Type':'application/json'},body:r.request().postData()}); r.fulfill({status:res.status,contentType:'application/json',body:await res.text()}); });
  await pg.route('**/health', r=>r.fulfill({status:200,body:'{}'}));
  await pg.goto('file://'+process.cwd()+'/site_build/mirisaju/'+page_); await pg.waitForTimeout(500);
  await pg.click('#startBtn'); await pg.waitForTimeout(400);
  const seg=async(k,v)=>{ if(v===null) return; await pg.click(`.seg[data-k="${k}"] button[data-v="${v}"]`); };
  await pg.fill('#birth',c.birth); await seg('female',c.female); await seg('married',c.married); await seg('edu3',c.edu3); await pg.fill('#hh',c.hh); await pg.fill('#hh2',c.hh2);
  await pg.click('#nextBtn'); await pg.waitForTimeout(250);
  await seg('pension_recv',c.pension_recv); await seg('retire_pension',c.retire_pension); await seg('private_pension',c.private_pension);
  await pg.click('#nextBtn'); await pg.waitForTimeout(250);
  await pg.fill('#inc0',c.inc[0]); await pg.fill('#inc1',c.inc[1]); await pg.fill('#inc2',c.inc[2]);
  await pg.click('#nextBtn'); await pg.waitForTimeout(250);
  await seg('employed',c.employed); await seg('employed_1y',c.employed_1y); await seg('employed_2y',c.employed_2y); await seg('job_type',c.job_type);
  await seg('owner',c.owner); await pg.fill('#fin',c.fin); await pg.fill('#real',c.real); await pg.fill('#debt',c.debt); if (c.health) await seg('health',c.health);
  if (c.extra) await c.extra(pg);
  await pg.click('#nextBtn'); await pg.waitForTimeout(2500);
  const ml=await pg.evaluate(()=>document.getElementById('mlCard').innerText.slice(0,700)); const gd=await pg.evaluate(()=>[...document.querySelectorAll('#gList .gcard h4')].map(h=>h.textContent).join(' | ')); const dbt=await pg.evaluate(()=>document.getElementById('rDebtP').textContent);
  console.log('#####',c.name,'| err:',await pg.evaluate(()=>document.getElementById('err').textContent),'| pageerrors',errs);
  console.log('보낸 값:',JSON.stringify(sent)); console.log('화면:',ml.replace(/\n+/g,' / ').slice(0,1100)); console.log('다음 걸음:',gd); console.log('빚 카드:',dbt);
  await pg.screenshot({path:`e2e_${cases.indexOf(c)}.png`,fullPage:true}); await pg.close(); }
 await b.close();})();

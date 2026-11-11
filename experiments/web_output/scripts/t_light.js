const { chromium } = require('playwright');
(async()=>{const b=await chromium.launch();
for (const [vw,n] of [[{width:1280,height:860},'d'],[{width:390,height:844},'m']]){
 const pg=await b.newPage({viewport:vw}); const errs=[]; pg.on('pageerror',e=>errs.push(e.message));
 await pg.route('**/predict',r=>r.fulfill({status:200,contentType:'application/json',body:JSON.stringify({eligible:true,band:'high',top_pct:7.4,abstain:false,ratio_now:1.21,model:'mirisaju-koweps-S20',reasons:[{feature:'s_min3',label:'최근 3년 중 가장 낮았던 소득',effect:0.9},{feature:'s_lost',label:'최근 2년 내 일을 그만둠',effect:0.5},{feature:'s_lg_fin',label:'금융자산',effect:-0.2}]})}));
 await pg.route('**/health',r=>r.fulfill({status:200,body:'{}'}));
 await pg.goto('file://'+process.cwd()+'/site_build/mirisaju/index_light.html'); await pg.waitForTimeout(2200);
 await pg.screenshot({path:`light/${n}_landing.png`});
 await pg.click('#startBtn'); await pg.waitForTimeout(400); await pg.click('#nextBtn'); await pg.waitForTimeout(500);
 await pg.screenshot({path:`light/${n}_input.png`});
 await pg.evaluate(()=>{render({birth_year:1963,female:0,married:0,edu3:1,hh_size:1,hh_size_2y:2,pension_recv:0,retire_pension:0,private_pension:0,income_now:190,income_1y:240,income_2y:300,employed:0,employed_1y:1,employed_2y:1,job_type:'none',owner:1,fin_asset:800,real_asset:30000,debt:4000,health:null,age:63,age_to_60:3,age_to_nps:-1,hh_change_2y:-1,lost_job_2y:1}); show('resultView');});
 await pg.waitForTimeout(1600); await pg.screenshot({path:`light/${n}_result.png`,fullPage:true});
 await pg.click('#cbFab'); await pg.waitForTimeout(300); await pg.screenshot({path:`light/${n}_chat.png`});
 console.log(n,'errors',errs,'overflow',await pg.evaluate(()=>document.documentElement.scrollWidth-innerWidth)); await pg.close();}
await b.close();})();

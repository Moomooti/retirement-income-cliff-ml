const { chromium } = require('playwright');
const path='file://'+process.cwd()+'/site_build/mirisaju/index.html';
const cases={
 high:{P:{birth_year:1963,female:0,married:0,edu3:1,hh_size:1,hh_size_2y:2,pension_recv:0,retire_pension:0,private_pension:0,income_now:190,income_1y:240,income_2y:300,employed:0,employed_1y:1,employed_2y:1,job_type:'none',owner:1,fin_asset:800,real_asset:30000,debt:4000,health:null,age:63,age_to_60:3,age_to_nps:-1,hh_change_2y:-1,lost_job_2y:1},
  R:{eligible:true,band:'high',top_pct:7.4,abstain:false,ratio_now:1.21,model:'mirisaju-koweps-S20',reasons:[{feature:'s_min3',label:'최근 3년 중 가장 낮았던 소득',effect:0.9},{feature:'s_lost',label:'최근 2년 내 일을 그만둠',effect:0.5},{feature:'s_lg_fin',label:'금융자산',effect:-0.2}]}},
 low:{P:{birth_year:1968,female:1,married:1,edu3:2,hh_size:2,hh_size_2y:2,pension_recv:0,retire_pension:1,private_pension:1,income_now:520,income_1y:500,income_2y:510,employed:1,employed_1y:1,employed_2y:1,job_type:'regular',owner:1,fin_asset:9000,real_asset:60000,debt:2000,health:null,age:58,age_to_60:-2,age_to_nps:-7,hh_change_2y:0,lost_job_2y:0},
  R:{eligible:true,band:'low',top_pct:71,abstain:false,ratio_now:2.45,model:'mirisaju-koweps-S20',reasons:[{feature:'s_log_r',label:'지금 소득(빈곤선 대비)',effect:-0.8},{feature:'employed',label:'지금 일함',effect:-0.3},{feature:'s_d1',label:'1년 사이 소득 변화',effect:0.1}]}},
 abst:{P:null,R:{eligible:true,band:'mid',top_pct:35,abstain:true,ratio_now:1.6,model:'mirisaju-koweps-S21',reasons:[{feature:'s_d2',label:'2년 사이 소득 변화',effect:0.4},{feature:'s_owner',label:'자가',effect:-0.2},{feature:'age',label:'나이',effect:0.1}]}},
 inel:{P:null,R:{eligible:false,reason:'모델은 50~69세에서만 검증됐어요.',ratio_now:1.8}},
};
cases.abst.P=cases.high.P; cases.inel.P=cases.low.P;
(async()=>{
 const b=await chromium.launch();
 for (const [vw,name] of [[{width:1200,height:900},'d'],[{width:390,height:844},'m']]){
  for (const [k,c] of Object.entries(cases)){
   if(name==='m' && k!=='high') continue;
   const pg=await b.newPage({viewport:vw});
   const errs=[]; pg.on('pageerror',e=>errs.push(e.message));
   await pg.route('**/predict',r=>r.fulfill({status:200,contentType:'application/json',body:JSON.stringify(c.R)}));
   await pg.route('**/health',r=>r.fulfill({status:200,body:'{}'}));
   await pg.goto(path); await pg.waitForTimeout(300);
   await pg.evaluate(P=>{const i=document.getElementById('intro'); if(i) i.remove(); render(P); show('resultView');},c.P);
   await pg.waitForTimeout(1500);
   const ow=await pg.evaluate(()=>document.documentElement.scrollWidth-innerWidth);
   const txt=await pg.evaluate(()=>document.getElementById('mlCard').innerText+'\n=== GUIDE ===\n'+document.getElementById('guide').innerText);
   console.log('#####',name,k,'overflow',ow,'errors',errs); console.log(txt);
   await pg.screenshot({path:`shots/${name}_${k}.png`,fullPage:true});
   await pg.close();
  }}
 await b.close();
})();

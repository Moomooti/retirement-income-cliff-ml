const { chromium } = require('playwright');
(async()=>{const b=await chromium.launch();
for (const [vw,n] of [[{width:1280,height:800},'d'],[{width:390,height:844},'m']]){
 const pg=await b.newPage({viewport:vw}); const errs=[]; pg.on('pageerror',e=>errs.push(e.message));
 await pg.goto('file://'+process.cwd()+'/site_build/mirisaju/index_v2.html'); await pg.waitForTimeout(2500);
 await pg.screenshot({path:`fv/${n}_landing.png`});
 const loaded=await pg.evaluate(()=>{const i=document.querySelector('#pet img');return i&&i.naturalWidth});
 await pg.click('#startBtn'); await pg.waitForTimeout(700);
 const st=await pg.evaluate(()=>({pet:document.getElementById('pet').className,input:!document.getElementById('inputView').classList.contains('hidden'),wipe:!!document.getElementById('wipe')}));
 await pg.click('#logoBtn'); await pg.waitForTimeout(700);
 console.log(n,'img',loaded,st,'back',await pg.evaluate(()=>document.getElementById('pet').className),'errors',errs,'overflow',await pg.evaluate(()=>document.documentElement.scrollWidth-innerWidth)); await pg.close();}
await b.close();})();

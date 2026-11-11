const { chromium } = require('playwright');
(async()=>{const b=await chromium.launch();
for (const [vw,n] of [[{width:1280,height:800},'d'],[{width:390,height:844},'m']]){
 const pg=await b.newPage({viewport:vw}); const errs=[]; pg.on('pageerror',e=>errs.push(e.message));
 await pg.goto('file://'+process.cwd()+'/site_build/mirisaju/index_fox.html');
 const pos=[]; for(let i=0;i<8;i++){ await pg.waitForTimeout(1500); pos.push(await pg.evaluate(()=>{const e=document.getElementById('pet');return e.style.transform+' | '+e.querySelector('.pf').style.transform.slice(0,40)+' | '+(document.getElementById('petImg').src.length%1000)}));
   if(i===2||i===6) await pg.screenshot({path:`fox/${n}_land${i}.png`}); }
 console.log(n,pos.join('\n'));
 await pg.click('#startBtn'); await pg.waitForTimeout(350); await pg.screenshot({path:`fox/${n}_wipe1.png`});
 await pg.waitForTimeout(650); await pg.screenshot({path:`fox/${n}_wipe2.png`});
 await pg.waitForTimeout(1500); await pg.screenshot({path:`fox/${n}_after.png`});
 console.log(n,'input visible',await pg.evaluate(()=>!document.getElementById('inputView').classList.contains('hidden')),'pet off',await pg.evaluate(()=>document.getElementById('pet').className),'errors',errs,'overflow',await pg.evaluate(()=>document.documentElement.scrollWidth-innerWidth));
 await pg.click('#logoBtn'); await pg.waitForTimeout(800); console.log('back pet',await pg.evaluate(()=>document.getElementById('pet').className));
 await pg.close();}
await b.close();})();

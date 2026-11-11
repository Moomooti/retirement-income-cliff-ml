const { chromium } = require('playwright');
(async()=>{const b=await chromium.launch({args:['--autoplay-policy=no-user-gesture-required']});const pg=await b.newPage({viewport:{width:1200,height:800}});
const errs=[];pg.on('pageerror',e=>errs.push(e.message));pg.on('requestfailed',r=>{if(!/onrender/.test(r.url()))errs.push('fail '+r.url())});
await pg.goto('file://'+process.cwd()+'/site_build/mirisaju/index_nointro.html');await pg.waitForTimeout(2500);
console.log(await pg.evaluate(()=>({intro:!!document.getElementById('intro'),bgmPlaying:!document.getElementById('bgm').paused,landingVisible:!document.getElementById('landing').classList.contains('hidden'),bodyLock:document.body.className})));
console.log('errors',errs);await pg.screenshot({path:'shots/nointro.png'});await b.close();})();

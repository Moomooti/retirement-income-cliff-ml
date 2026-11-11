const { chromium } = require('playwright');
(async()=>{const b=await chromium.launch();const pg=await b.newPage({viewport:{width:390,height:844}});
for (const f of ['index_v2.html','index_pet.html']){
await pg.goto('file://'+process.cwd()+'/site_build/mirisaju/'+f); await pg.waitForTimeout(1500);
console.log(f, await pg.evaluate(()=>{const o=[];document.querySelectorAll('body *').forEach(e=>{const r=e.getBoundingClientRect();if(r.right>innerWidth+2&&getComputedStyle(e).position!=='fixed')o.push(e.tagName+'.'+e.className+' '+Math.round(r.right))});return [document.documentElement.scrollWidth-innerWidth,o.slice(0,6)]}));}
await b.close();})();

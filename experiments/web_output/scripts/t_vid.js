const { chromium } = require('playwright');
(async()=>{const b=await chromium.launch();const ctx=await b.newContext({viewport:{width:1280,height:720},recordVideo:{dir:'vid',size:{width:1280,height:720}}});
const pg=await ctx.newPage(); await pg.goto('file://'+process.cwd()+'/site_build/mirisaju/index_fox.html');
await pg.evaluate(()=>{Math.random=(()=>{let s=7;return()=>{s=(s*9301+49297)%233280;return s/233280;}})();});
await pg.waitForTimeout(16000); await pg.click('#startBtn'); await pg.waitForTimeout(3200); await ctx.close(); await b.close();})();

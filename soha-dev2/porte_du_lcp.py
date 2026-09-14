# -*- coding: utf-8 -*-
"""Le plus gros élément peint : ce que le visiteur attend avant de voir la page."""
import sys, statistics; sys.path.insert(0,"/home/user/centre-soha/soha-dev2")
import porte_du_contraste as P
from playwright.sync_api import sync_playwright
srv,port=P.servir(sys.argv[1],int(sys.argv[3]) if len(sys.argv)>3 else 9201)
MES="""()=>new Promise(r=>{
  let v=0,el='';
  new PerformanceObserver(l=>{for(const e of l.getEntries()){v=e.startTime;el=(e.element&&(e.element.tagName+'.'+String(e.element.className||'').split(' ')[0]))||e.url||'';}})
    .observe({type:'largest-contentful-paint',buffered:true});
  setTimeout(()=>r({lcp:Math.round(v),el:el.slice(0,60)}),2600);})"""
with sync_playwright() as p:
    n=p.chromium.launch(executable_path=P.CHROMIUM)
    for page in ("index.html",):
        vals=[]
        for i in range(4):
            ctx=n.new_context(viewport={"width":1440,"height":900})
            pg=ctx.new_page()
            cdp=ctx.new_cdp_session(pg)
            cdp.send("Network.emulateNetworkConditions", {"offline":False,
                "downloadThroughput":1_500_000//8, "uploadThroughput":750_000//8,
                "latency":150})   # 4G lent, le cas qui compte
            pg.goto("http://127.0.0.1:%d/%s"%(port,page), wait_until="load")
            r=pg.evaluate(MES); vals.append(r["lcp"]); dernier=r
            ctx.close()
        print("%-22s LCP médian %5d ms  (%s)  — %s" % (page, statistics.median(vals),
              ", ".join(str(v) for v in sorted(vals)), dernier["el"]))
    n.close()
srv.shutdown()

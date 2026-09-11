"""L'ossature de chaque page, mesurée dans le navigateur."""
import os, json, functools, http.server, socketserver, threading, time, sys
from playwright.sync_api import sync_playwright
S=os.getcwd(); D=os.path.join(S,"site14")
class M(http.server.SimpleHTTPRequestHandler):
    def log_message(self,*a): pass
srv=socketserver.TCPServer(("127.0.0.1",8931), functools.partial(M,directory=D)); srv.allow_reuse_address=True
threading.Thread(target=srv.serve_forever,daemon=True).start(); time.sleep(.4)

JS = r"""() => {
  const main = document.querySelector('main');
  const secs = Array.from(main.children).filter(e => e.getBoundingClientRect().height > 40);

  function famille(s){
    // une « famille de mise en page » : la forme de la grille interne
    const cs = getComputedStyle(s);
    const inner = s.querySelector(':scope > .e-con-inner') || s;
    const ics = getComputedStyle(inner);
    const kids = Array.from(inner.children).filter(e => e.getBoundingClientRect().height > 8);
    const imgs = s.querySelectorAll('img').length;
    const cols = (ics.gridTemplateColumns && ics.gridTemplateColumns !== 'none')
        ? ics.gridTemplateColumns.split(' ').length
        : (ics.display.indexOf('flex') >= 0 && ics.flexDirection === 'row' ? kids.length : 1);
    const fond = (cs.backgroundImage && cs.backgroundImage.indexOf('url(') === 0) ? 'photo'
               : (cs.backgroundColor && cs.backgroundColor !== 'rgba(0, 0, 0, 0)' ? 'teinte' : 'nu');
    return {cols, imgs: imgs > 0 ? (imgs === 1 ? 1 : 'n') : 0, fond,
            cle: cols + '|' + (imgs>0?(imgs===1?'1img':'nimg'):'0img') + '|' + fond};
  }

  const sections = secs.map((s,i) => {
    const r = s.getBoundingClientRect();
    const cs = getComputedStyle(s);
    const f = famille(s);
    const kick = Array.from(s.querySelectorAll('*')).filter(e => {
      if (e.children.length) return false;
      const t = (e.innerText||'').trim();
      if (!t || t.length > 42) return false;
      const c = getComputedStyle(e);
      return parseFloat(c.letterSpacing) > 1 && c.textTransform === 'uppercase';
    }).length;
    return {i, h: Math.round(r.height), padH: Math.round(parseFloat(cs.paddingTop)),
            padB: Math.round(parseFloat(cs.paddingBottom)), famille: f.cle,
            cols: f.cols, imgs: s.querySelectorAll('img').length, fond: f.fond, kickers: kick};
  });

  // typographie
  const tailles = {}, familles = {}, rayons = {};
  document.querySelectorAll('main *').forEach(e => {
    if (!e.children.length && (e.innerText||'').trim()) {
      const c = getComputedStyle(e);
      tailles[Math.round(parseFloat(c.fontSize))] = (tailles[Math.round(parseFloat(c.fontSize))]||0)+1;
      familles[c.fontFamily.split(',')[0].replace(/"/g,'')] = 1;
    }
    const br = getComputedStyle(e).borderRadius;
    if (br && br !== '0px') rayons[br] = (rayons[br]||0)+1;
  });

  // titres
  const titres = Array.from(main.querySelectorAll('h1,h2,h3,h4,h5,h6'))
      .map(h => ({n: +h.tagName[1], t: (h.innerText||'').trim().slice(0,40)}));
  let sauts = 0;
  for (let i=1;i<titres.length;i++) if (titres[i].n - titres[i-1].n > 1) sauts++;

  // mesure des paragraphes (en caractères)
  const mesures = [];
  main.querySelectorAll('p, .elementor-widget-text-editor div').forEach(e => {
    const t = (e.innerText||'').trim();
    if (t.length < 80) return;
    const c = getComputedStyle(e);
    const ch = e.getBoundingClientRect().width / (parseFloat(c.fontSize) * 0.5);
    mesures.push(Math.round(ch));
  });

  // images
  const images = Array.from(main.querySelectorAll('img')).map(im => ({
    r: im.naturalWidth && im.naturalHeight ? +(im.naturalWidth/im.naturalHeight).toFixed(2) : null,
    affiche: +(im.getBoundingClientRect().width / Math.max(im.getBoundingClientRect().height,1)).toFixed(2),
    w: im.getAttribute('width'), h: im.getAttribute('height'),
    alt: (im.getAttribute('alt')||'').length,
    objectFit: getComputedStyle(im).objectFit,
    large: Math.round(im.getBoundingClientRect().width)
  }));

  return {sections, tailles, familles: Object.keys(familles), rayons,
          h1: main.querySelectorAll('h1').length, sauts, titres: titres.length,
          mesures, images};
}"""

pages = sorted(f for f in os.listdir(D) if f.endswith(".html") and f != "lisez-moi.html")
tout = {}
with sync_playwright() as p:
    b=p.chromium.launch(executable_path="/opt/pw-browsers/chromium-1194/chrome-linux/chrome")
    pg=b.new_page(viewport={"width":1440,"height":900})
    for n in pages:
        pg.goto("http://127.0.0.1:8931/"+n, wait_until="networkidle"); pg.wait_for_timeout(200)
        tout[n]=pg.evaluate(JS)
    b.close()
srv.shutdown()
json.dump(tout, open(S+"/audit.json","w"), ensure_ascii=False)
print("mesuré :", len(tout), "pages →", S+"/audit.json")

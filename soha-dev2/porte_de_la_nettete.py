# -*- coding: utf-8 -*-
"""La netteté — mesurée sur le FICHIER, pas sur ce que le navigateur en dit.

Deux pièges traversés, notés pour ne pas y retomber :
 1. `naturalWidth` sans srcset = la taille du fichier. Avec srcset, c'est la
    taille de l'échelon choisi : un écran 1× choisit petit, et le contrôle
    criait au défaut.
 2. Pire : avec des descripteurs `w`, Chromium CORRIGE `naturalWidth` par la
    densité retenue. Un fichier de 2 400 px choisi pour une fente de 1 200 à
    densité 2 rapporte 1 200. Deux fois de suite, j'ai mesuré la mauvaise
    chose et failli annoncer des fautes qui n'existent pas.

Ici : on lit `currentSrc`, on ouvre le fichier correspondant sur le disque, et
on compare sa vraie largeur à la largeur affichée multipliée par la densité.
"""
import sys, glob, os; sys.path.insert(0,"/home/user/centre-soha/soha-dev2")
import porte_du_contraste as P
from PIL import Image
from playwright.sync_api import sync_playwright
site=sys.argv[1]; dpr=float(sys.argv[3]) if len(sys.argv)>3 else 2.0
srv,port=P.servir(site, int(sys.argv[2]))
pages=["journal.html"]+sorted(os.path.basename(f) for f in glob.glob(site+"/article-*.html"))
JS="""()=>[...document.querySelectorAll('img')].filter(i=>/journal/.test(i.currentSrc||i.src)).map(i=>({
  f:(i.currentSrc||i.src).split('/').pop(), aff:Math.round(i.getBoundingClientRect().width)}))"""
court=[]
with sync_playwright() as p:
    n=p.chromium.launch(executable_path=P.CHROMIUM)
    ctx=n.new_context(viewport={"width":1440,"height":900}, device_scale_factor=dpr)
    for nom in pages:
        pg=ctx.new_page()
        pg.goto("http://127.0.0.1:%d/%s"%(port,nom), wait_until="networkidle"); pg.wait_for_timeout(250)
        for x in pg.evaluate(JS):
            chemin=os.path.join(site,"medias",x["f"])
            if not os.path.exists(chemin): continue
            vraie=Image.open(chemin).size[0]
            besoin=round(x["aff"]*dpr)
            if vraie < besoin*0.95:
                court.append((nom, x["f"], x["aff"], vraie, besoin))
        pg.close()
    n.close()
srv.shutdown()
for nom,f,aff,vraie,besoin in court:
    print("  %-36s %-26s affichée %4d → fichier %4d (il faut %4d)" % (nom[:36],f[:26],aff,vraie,besoin))
print("%d photo(s) sous la densité %g× à 1440 px." % (len(court), dpr))

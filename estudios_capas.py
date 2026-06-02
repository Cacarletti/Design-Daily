"""
estudios_capas.py
-----------------
Baixa a imagem de capa (og:image) do site de cada estúdio do diretório e salva
em estudios_capas/. Gera estudios_capas.js (window.ESTUDIOS) que a página
estudios.html usa para montar os cards com capa.

Rode de novo para atualizar as capas ou mudar a lista.
"""

import json
import os
import re
import time
from urllib.parse import urljoin

import requests
import urllib3
urllib3.disable_warnings()

PASTA_CAPAS = "estudios_capas"
SAIDA_JS = "estudios_capas.js"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

# (nome, url, grupo)
ESTUDIOS = [
    ("Pentagram", "https://www.pentagram.com", "Internacionais"),
    ("Porto Rocha", "https://www.portorocha.com", "Internacionais"),
    ("COLLINS", "https://www.wearecollins.com", "Internacionais"),
    ("DIA", "https://dia.tv", "Internacionais"),
    ("Gretel", "https://gretelny.com", "Internacionais"),
    ("Franklyn", "https://franklyn.is", "Internacionais"),
    ("Bibliothèque", "https://www.bibliothequedesign.com", "Internacionais"),
    ("Base Design", "https://basedesign.com", "Internacionais"),
    ("Studio Dumbar / Dept", "https://www.studiodumbar.com", "Internacionais"),
    ("Build", "https://wearebuild.com", "Internacionais"),
    ("Hey Studio", "https://heystudio.es", "Internacionais"),
    ("Bond", "https://bond-agency.com", "Internacionais"),
    ("Manual", "https://manualcreative.com", "Internacionais"),
    ("Instrument", "https://www.instrument.com", "Internacionais"),
    ("High Tide", "https://hightide.nyc", "Internacionais"),
    ("Smith & Diction", "https://www.smithanddiction.com", "Internacionais"),
    ("Greco Design", "https://grecodesign.com.br", "Brasil"),
    ("Casa Rex", "https://www.casarex.com", "Brasil"),
    ("Oz Design", "https://ozdesign.com.br", "Brasil"),
    ("Chelles & Hayashi", "https://chelleshayashi.com.br", "Brasil"),
    ("Cauduro Martino", "https://www.cauduromartino.com.br", "Brasil"),
]


def nome_arquivo(nome):
    return re.sub(r"[^a-z0-9]+", "_", nome.lower()).strip("_") + ".jpg"


def og_image(url):
    r = requests.get(url, headers=HEADERS, timeout=25, verify=False, allow_redirects=True)
    h = r.text
    m = re.search(r'<meta[^>]+property=["\']og:image["\'][^>]*content=["\']([^"\']+)["\']', h, re.I)
    if not m:
        m = re.search(r'<meta[^>]+content=["\']([^"\']+)["\'][^>]*property=["\']og:image["\']', h, re.I)
    return urljoin(r.url, m.group(1)) if m else ""


def main():
    os.makedirs(PASTA_CAPAS, exist_ok=True)
    estudios = []
    for nome, url, grupo in ESTUDIOS:
        capa = ""
        try:
            img_url = og_image(url)
            if img_url:
                img = requests.get(img_url, headers=HEADERS, timeout=25, verify=False)
                ct = img.headers.get("content-type", "")
                if img.status_code == 200 and ct.startswith("image") and len(img.content) > 1500:
                    arq = nome_arquivo(nome)
                    with open(os.path.join(PASTA_CAPAS, arq), "wb") as f:
                        f.write(img.content)
                    capa = f"{PASTA_CAPAS}/{arq}"
            print(f"  {'OK' if capa else '--'} {nome}{'' if capa else ' (sem capa)'}")
        except Exception as e:
            print(f"  XX {nome}: {type(e).__name__}")
        estudios.append({"nome": nome, "url": url, "grupo": grupo, "capa": capa})
        time.sleep(0.8)

    with open(SAIDA_JS, "w", encoding="utf-8") as f:
        f.write("window.ESTUDIOS = ")
        json.dump(estudios, f, ensure_ascii=False)
        f.write(";")

    com = sum(1 for e in estudios if e["capa"])
    print(f"\n{len(estudios)} estúdios, {com} com capa. Gerado: {SAIDA_JS}")


if __name__ == "__main__":
    main()

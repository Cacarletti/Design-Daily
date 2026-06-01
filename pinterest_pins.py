"""
pinterest_pins.py
-----------------
Puxa os pins (imagem + link) de boards PÚBLICOS do Pinterest via RSS e gera
pinterest_pins.js (window.PINS) que a página referencias_pinterest.html usa
para mostrar um feed visual — você vê a imagem e só clica se gostar.

Funciona com qualquer board público (o seu ou de curadores que você curtir).
Edite a lista BOARDS abaixo e rode de novo quando quiser atualizar.
"""

import json
import re
import html

import requests
import feedparser

SAIDA_JS = "pinterest_pins.js"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
}

# (rótulo, URL do board público). O .rss é montado automaticamente.
BOARDS = [
    ("Meu board · graphic", "https://br.pinterest.com/cacarletti/graphic/"),
]


def rss_de(board_url):
    return board_url.rstrip("/") + ".rss"


def limpar(t):
    t = re.sub(r"<[^>]+>", " ", t or "")
    t = html.unescape(t)
    return re.sub(r"\s+", " ", t).strip()


def coletar(board_url):
    r = requests.get(rss_de(board_url), headers=HEADERS, timeout=25)
    p = feedparser.parse(r.content)
    pins = []
    for e in p.entries:
        m = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', e.get("summary", ""))
        if not m:
            continue
        img = re.sub(r"/\d+x/", "/736x/", m.group(1))  # resolução maior
        pins.append({
            "titulo": limpar(e.get("title", ""))[:80],
            "link": e.get("link", ""),
            "imagem": img,
        })
    return pins


def main():
    feeds = []
    for rotulo, url in BOARDS:
        try:
            pins = coletar(url)
            feeds.append({"board": rotulo, "url": url, "pins": pins})
            print(f"  OK {rotulo}: {len(pins)} pins")
        except Exception as e:
            print(f"  XX {rotulo}: {type(e).__name__}")

    with open(SAIDA_JS, "w", encoding="utf-8") as f:
        f.write("window.PINS = ")
        json.dump(feeds, f, ensure_ascii=False)
        f.write(";")

    total = sum(len(x["pins"]) for x in feeds)
    print(f"\n{len(feeds)} board(s), {total} pins. Gerado: {SAIDA_JS}")


if __name__ == "__main__":
    main()

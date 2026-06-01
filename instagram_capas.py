"""
instagram_capas.py
------------------
Baixa a foto de perfil (avatar) de cada perfil do Instagram da lista e salva
em instagram_capas/. Gera instagram_perfis.js (window.IGPERFIS) que a página
instagram.html lê para montar os cards.

As imagens ficam salvas LOCALMENTE (não expiram). Rode de novo quando quiser
atualizar as fotos ou mudar a lista de perfis.
"""

import json
import os
import re
import time

import requests

PASTA_CAPAS = "instagram_capas"
SAIDA_JS = "instagram_perfis.js"

# Lista de perfis monitorados (apenas o @, sem a URL).
PERFIS = [
    "morrre.dsgn", "counterprintbooks", "digital_archive", "thebrandidentity",
    "thegraphicaddict", "bountyhunters_", "typosters", "address.____",
    "designerbriefs", "hvnt.ter", "br.and.ing", "awwwards",
    "showcase.mockups", "designspiration", "graphicdesigncentral", "thedesigntip",
    "collletttivo", "slanted_publishers", "visualjournal.it", "sgustokdesign",
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
                  "AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 "
                  "Instagram 290.0.0.13.76",
    "x-ig-app-id": "936619743392459",
    "Accept": "*/*",
    "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
}


def nome_arquivo(handle):
    """Transforma o @ num nome de arquivo seguro."""
    return re.sub(r"[^a-z0-9]+", "_", handle.lower()).strip("_") + ".jpg"


def main():
    os.makedirs(PASTA_CAPAS, exist_ok=True)
    perfis = []
    for handle in PERFIS:
        url = f"https://i.instagram.com/api/v1/users/web_profile_info/?username={handle}"
        nome = handle
        capa = ""
        try:
            r = requests.get(url, headers=HEADERS, timeout=25)
            if r.status_code == 200 and "json" in r.headers.get("content-type", ""):
                user = r.json()["data"]["user"]
                nome = user.get("full_name") or handle
                pic = user.get("profile_pic_url_hd") or user.get("profile_pic_url")
                if pic:
                    img = requests.get(pic, headers=HEADERS, timeout=25)
                    if img.status_code == 200:
                        arq = nome_arquivo(handle)
                        with open(os.path.join(PASTA_CAPAS, arq), "wb") as f:
                            f.write(img.content)
                        capa = f"{PASTA_CAPAS}/{arq}"
                print(f"  OK @{handle}: {nome}{' (capa salva)' if capa else ' (sem foto)'}")
            else:
                print(f"  XX @{handle}: bloqueado (HTTP {r.status_code})")
        except Exception as e:
            print(f"  XX @{handle}: {type(e).__name__}")

        perfis.append({"nome": nome, "handle": handle,
                       "url": f"https://www.instagram.com/{handle}/", "capa": capa})
        time.sleep(1.5)  # respeita o Instagram, evita bloqueio

    with open(SAIDA_JS, "w", encoding="utf-8") as f:
        f.write("window.IGPERFIS = ")
        json.dump(perfis, f, ensure_ascii=False)
        f.write(";")

    com_capa = sum(1 for p in perfis if p["capa"])
    print(f"\n{len(perfis)} perfis, {com_capa} com foto. Gerado: {SAIDA_JS}")


if __name__ == "__main__":
    main()

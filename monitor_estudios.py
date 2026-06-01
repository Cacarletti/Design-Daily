"""
monitor_estudios.py
-------------------
Para estúdios SEM RSS: detecta projetos NOVOS comparando o site de hoje com
um "retrato" (snapshot) do dia anterior. Cada projeto novo vira um card simples
(capa + título + link) na categoria "Estúdios" do dia atual.

Como funciona:
  1. Visita a página de trabalhos do estúdio e lista as URLs de projeto.
  2. Compara com o que já estava salvo em estudios_snapshot.json.
  3. O que for novo: busca capa (og:image) e título (og:title) da página do projeto.
  4. Acrescenta esses cards ao arquivo do dia (dados/AAAA-MM-DD.json).
  5. Atualiza o snapshot.

No PRIMEIRO dia (sem snapshot) ele só fotografa o estado atual — nada é "novo"
ainda. As novidades começam a aparecer a partir do segundo dia.

Rode SEMPRE depois do coletar.py e ANTES do gerar_site.py.
"""

import json
import os
import re
from datetime import datetime, timezone, timedelta
from urllib.parse import urljoin, urlparse

import requests

CONFIG = "estudios.json"
SNAPSHOT = "estudios_snapshot.json"
PASTA_DADOS = "dados"
TIMEOUT = 20
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/124.0.0.0 Safari/537.36"
}


def buscar(url):
    return requests.get(url, headers=HEADERS, timeout=TIMEOUT, verify=False, allow_redirects=True)


def listar_projetos(estudio):
    """Devolve o conjunto de URLs de projeto encontradas no site do estúdio."""
    try:
        r = buscar(estudio["url"])
    except Exception as e:
        print(f"  XX {estudio['nome']}: {type(e).__name__}")
        return None
    base = r.url
    host = urlparse(base).netloc
    pat = re.compile(estudio["pattern"])
    urls = set()
    for href in re.findall(r'href=["\']([^"\']+)["\']', r.text):
        if href.startswith(("#", "mailto:", "tel:")):
            continue
        absoluto = urljoin(base, href)
        pr = urlparse(absoluto)
        if pr.netloc == host and pat.match(pr.path):
            # normaliza: sem barra final, sem query/hash
            urls.add(f"{pr.scheme}://{pr.netloc}{pr.path.rstrip('/')}")
    return urls


def meta_og(url):
    """Pega título e imagem de capa (og:title / og:image) da página do projeto."""
    try:
        h = buscar(url).text
    except Exception:
        return "", ""

    def og(prop):
        m = re.search(
            r'<meta[^>]+property=["\']og:' + prop + r'["\'][^>]*content=["\']([^"\']+)["\']',
            h, re.I)
        if not m:
            m = re.search(
                r'<meta[^>]+content=["\']([^"\']+)["\'][^>]*property=["\']og:' + prop + r'["\']',
                h, re.I)
        return m.group(1) if m else ""

    titulo = og("title")
    imagem = og("image")
    if imagem:
        imagem = urljoin(url, imagem)
    return titulo, imagem


def main():
    requests.packages.urllib3.disable_warnings()  # silencia aviso de SSL ignorado

    with open(CONFIG, encoding="utf-8") as f:
        estudios = json.load(f)["estudios"]

    snapshot = {}
    if os.path.exists(SNAPSHOT):
        with open(SNAPSHOT, encoding="utf-8") as f:
            snapshot = json.load(f)

    fuso_br = timezone(timedelta(hours=-3))
    agora = datetime.now(timezone.utc)
    dia = agora.astimezone(fuso_br).strftime("%Y-%m-%d")

    novos_cards = []
    for est in estudios:
        nome = est["nome"]
        atuais = listar_projetos(est)
        if atuais is None:
            continue  # erro de rede; mantém snapshot anterior

        conhecidos = set(snapshot.get(nome, []))
        if not conhecidos:
            # primeiro dia: só fotografa, nada é novidade
            snapshot[nome] = sorted(atuais)
            print(f"  -- {nome}: linha de base ({len(atuais)} projetos)")
            continue

        novos = atuais - conhecidos
        for url in sorted(novos):
            titulo, imagem = meta_og(url)
            novos_cards.append({
                "titulo": titulo or nome + " — novo projeto",
                "link": url,
                "data_iso": agora.isoformat(),
                "imagem": imagem,
                "descricao": "Novo projeto publicado no site do estúdio.",
                "fonte": nome,
                "categoria": "Estúdios",
                "idioma": est.get("idioma", "en"),
                "traduzido": False,
            })
        # snapshot acumula (união) para não re-alertar se um projeto sumir e voltar
        snapshot[nome] = sorted(conhecidos | atuais)
        print(f"  OK {nome}: {len(novos)} novo(s) de {len(atuais)} projetos")

    # salva snapshot atualizado
    with open(SNAPSHOT, "w", encoding="utf-8") as f:
        json.dump(snapshot, f, ensure_ascii=False, indent=2)

    if not novos_cards:
        print(f"\nNenhum projeto novo de estúdio hoje ({dia}).")
        return

    # mescla os cards novos no arquivo do dia
    os.makedirs(PASTA_DADOS, exist_ok=True)
    caminho = os.path.join(PASTA_DADOS, f"{dia}.json")
    if os.path.exists(caminho):
        with open(caminho, encoding="utf-8") as f:
            dados_dia = json.load(f)
    else:
        dados_dia = {"data": dia, "gerado_em": agora.astimezone(fuso_br).isoformat(),
                     "total": 0, "itens": []}

    por_link = {i["link"]: i for i in dados_dia["itens"]}
    for card in novos_cards:
        por_link[card["link"]] = card
    dados_dia["itens"] = list(por_link.values())
    dados_dia["itens"].sort(key=lambda x: x["data_iso"], reverse=True)
    dados_dia["total"] = len(dados_dia["itens"])

    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(dados_dia, f, ensure_ascii=False, indent=2)

    print(f"\n{len(novos_cards)} projeto(s) novo(s) de estúdio adicionado(s) a {caminho}")


if __name__ == "__main__":
    main()

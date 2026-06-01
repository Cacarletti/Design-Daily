"""
coletar.py
----------
Le o fontes.json, visita cada feed RSS e coleta os posts das ultimas N horas
(N = config.janela_coleta_horas). De cada post extrai:
    titulo, link, data, imagem de capa, descricao curta, fonte, categoria, idioma.

Aplica a regra_traducao: itens cujo idioma NAO seja 'en' nem 'pt' sao traduzidos
para portugues (se a biblioteca de traducao estiver disponivel).

Salva o resultado em dados/AAAA-MM-DD.json (um arquivo por dia de execucao).
Se rodar duas vezes no mesmo dia, mescla sem duplicar (chave = link).
"""

import json
import os
import re
import html
from datetime import datetime, timezone, timedelta

import requests
import feedparser

# Traducao e OPCIONAL. Se a lib nao estiver instalada, o script segue
# normalmente e apenas nao traduz (nenhum feed atual precisa disso).
try:
    from deep_translator import GoogleTranslator
    TEM_TRADUTOR = True
except Exception:
    TEM_TRADUTOR = False

ARQUIVO_FONTES = "fontes.json"
PASTA_DADOS = "dados"
TIMEOUT = 20
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/120.0 Safari/537.36"
}


# ----------------------------------------------------------------------------
# Funcoes auxiliares
# ----------------------------------------------------------------------------

def limpar_texto(texto, limite=240):
    """Remove tags HTML e corta a descricao num tamanho amigavel."""
    if not texto:
        return ""
    texto = re.sub(r"<[^>]+>", " ", texto)      # tira tags <...>
    texto = html.unescape(texto)                # converte &amp; -> &, etc
    texto = re.sub(r"\s+", " ", texto).strip()  # espacos repetidos
    if len(texto) > limite:
        texto = texto[:limite].rsplit(" ", 1)[0] + "…"
    return texto


def achar_imagem(entry):
    """Tenta descobrir a imagem de capa do post em varios lugares possiveis."""
    # 1) media:content / media:thumbnail (padrao mais comum)
    for campo in ("media_content", "media_thumbnail"):
        midias = entry.get(campo)
        if midias:
            for m in midias:
                if m.get("url"):
                    return m["url"]
    # 2) enclosures (anexos do tipo imagem)
    for enc in entry.get("enclosures", []):
        if str(enc.get("type", "")).startswith("image") and enc.get("href"):
            return enc["href"]
        if enc.get("href", "").lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
            return enc["href"]
    # 3) primeira <img> dentro do conteudo/resumo
    blocos = []
    if entry.get("content"):
        blocos.append(entry["content"][0].get("value", ""))
    blocos.append(entry.get("summary", ""))
    for bloco in blocos:
        m = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', bloco or "")
        if m:
            return m.group(1)
    return ""


def data_do_post(entry):
    """Devolve a data de publicacao como datetime com fuso (UTC) ou None."""
    for campo in ("published_parsed", "updated_parsed"):
        t = entry.get(campo)
        if t:
            # feedparser entrega uma struct_time em UTC
            return datetime(*t[:6], tzinfo=timezone.utc)
    return None


def traduzir(texto, idioma_origem):
    """Traduz para portugues se a regra mandar e o tradutor existir."""
    if not texto or idioma_origem in ("en", "pt"):
        return texto, False
    if not TEM_TRADUTOR:
        return texto, False
    try:
        traduzido = GoogleTranslator(source="auto", target="pt").translate(texto)
        return traduzido, True
    except Exception:
        return texto, False


# ----------------------------------------------------------------------------
# Coleta de um feed
# ----------------------------------------------------------------------------

def coletar_fonte(fonte, corte):
    """Baixa um feed e devolve os itens publicados depois de 'corte'."""
    itens = []
    try:
        resp = requests.get(fonte["rss"], headers=HEADERS, timeout=TIMEOUT)
        resp.raise_for_status()
        parsed = feedparser.parse(resp.content)
    except Exception as e:
        print(f"  XX {fonte['nome']}: {type(e).__name__}")
        return itens

    recentes = 0
    for entry in parsed.entries:
        data = data_do_post(entry)
        # Se nao houver data, NAO incluimos (nao da pra saber se e das ultimas 24h).
        if data is None or data < corte:
            continue

        idioma = fonte.get("idioma", "en")
        titulo = limpar_texto(entry.get("title", ""), limite=300)
        descricao = limpar_texto(entry.get("summary", ""))

        titulo, t1 = traduzir(titulo, idioma)
        descricao, t2 = traduzir(descricao, idioma)

        itens.append({
            "titulo": titulo or "(sem título)",
            "link": entry.get("link", ""),
            "data_iso": data.isoformat(),
            "imagem": achar_imagem(entry),
            "descricao": descricao,
            "fonte": fonte["nome"],
            "categoria": fonte["categoria"],
            "idioma": "pt" if (t1 or t2) else idioma,
            "traduzido": bool(t1 or t2),
        })
        recentes += 1

    print(f"  OK {fonte['nome']}: {recentes} post(s) nas ultimas 24h")
    return itens


# ----------------------------------------------------------------------------
# Programa principal
# ----------------------------------------------------------------------------

def main():
    with open(ARQUIVO_FONTES, encoding="utf-8") as f:
        config = json.load(f)

    janela = config["config"].get("janela_coleta_horas", 24)
    # Fuso de Brasilia (UTC-3) so para nomear o arquivo do dia corretamente.
    fuso_br = timezone(timedelta(hours=-3))
    agora = datetime.now(timezone.utc)
    corte = agora - timedelta(hours=janela)
    dia = agora.astimezone(fuso_br).strftime("%Y-%m-%d")

    print(f"Coletando posts desde {corte.isoformat()} (ultimas {janela}h)\n")

    todos = []
    for fonte in config["fontes"]:
        todos.extend(coletar_fonte(fonte, corte))

    # Remove duplicatas pelo link.
    vistos = {}
    for item in todos:
        chave = item["link"] or item["titulo"]
        vistos[chave] = item
    itens = list(vistos.values())
    # Mais recentes primeiro.
    itens.sort(key=lambda x: x["data_iso"], reverse=True)

    os.makedirs(PASTA_DADOS, exist_ok=True)
    caminho = os.path.join(PASTA_DADOS, f"{dia}.json")

    # Se ja existe arquivo do dia, mescla sem duplicar.
    if os.path.exists(caminho):
        with open(caminho, encoding="utf-8") as f:
            anterior = json.load(f)
        existentes = {i["link"]: i for i in anterior.get("itens", [])}
        for i in itens:
            existentes[i["link"]] = i
        itens = list(existentes.values())
        itens.sort(key=lambda x: x["data_iso"], reverse=True)

    saida = {
        "data": dia,
        "gerado_em": agora.astimezone(fuso_br).isoformat(),
        "total": len(itens),
        "itens": itens,
    }
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(saida, f, ensure_ascii=False, indent=2)

    print(f"\nTotal coletado: {len(itens)} posts")
    print(f"Salvo em: {caminho}")


if __name__ == "__main__":
    main()

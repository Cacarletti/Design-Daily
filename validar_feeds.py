"""
validar_feeds.py
----------------
Testa cada feed RSS listado em fontes.json e mostra um relatorio:
  OK  -> o feed respondeu e tem itens
  FALHOU -> o feed nao respondeu, deu erro ou veio vazio

No final, pergunta se voce quer remover os feeds quebrados do fontes.json.
Sempre faz um backup (fontes.backup.json) antes de mexer no arquivo.
"""

import json
import sys
import concurrent.futures

import requests
import feedparser

ARQUIVO = "fontes.json"
TIMEOUT = 15  # segundos de espera por feed
# Alguns sites bloqueiam requisicoes "sem navegador"; mandamos um User-Agent normal.
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/120.0 Safari/537.36"
}


def testar_feed(fonte):
    """Tenta baixar e ler um feed. Devolve (fonte, ok, detalhe)."""
    url = fonte["rss"]
    try:
        resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        if resp.status_code != 200:
            return fonte, False, f"HTTP {resp.status_code}"
        parsed = feedparser.parse(resp.content)
        n = len(parsed.entries)
        if n == 0:
            # Pode ser feed mal formado ou realmente vazio.
            if parsed.bozo:
                return fonte, False, "formato invalido / vazio"
            return fonte, False, "0 itens"
        return fonte, True, f"{n} itens"
    except requests.exceptions.Timeout:
        return fonte, False, "timeout"
    except requests.exceptions.RequestException as e:
        return fonte, False, f"erro de conexao: {type(e).__name__}"
    except Exception as e:
        return fonte, False, f"erro: {type(e).__name__}"


def main():
    with open(ARQUIVO, encoding="utf-8") as f:
        dados = json.load(f)

    fontes = dados["fontes"]
    print(f"Testando {len(fontes)} feeds (timeout {TIMEOUT}s cada)...\n")

    resultados = []
    # Testa varios feeds ao mesmo tempo (mais rapido).
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        for resultado in executor.map(testar_feed, fontes):
            resultados.append(resultado)

    # Mantem a ordem original do arquivo no relatorio.
    resultados.sort(key=lambda r: fontes.index(r[0]))

    ok, falhos = [], []
    for fonte, sucesso, detalhe in resultados:
        marca = "OK " if sucesso else "XX "
        nome = fonte["nome"].ljust(28)
        print(f"  {marca} {nome} {detalhe}")
        (ok if sucesso else falhos).append(fonte)

    print(f"\nResumo: {len(ok)} funcionam / {len(falhos)} falharam")

    if not falhos:
        print("Todos os feeds estao ativos. Nada a remover.")
        return

    print("\nFeeds que falharam:")
    for fonte in falhos:
        print(f"  - {fonte['nome']}")

    # Pergunta antes de alterar o arquivo.
    resposta = input("\nRemover os feeds quebrados do fontes.json? (s/n) ").strip().lower()
    if resposta != "s":
        print("Nada foi alterado.")
        return

    # Backup de seguranca.
    with open("fontes.backup.json", "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)

    nomes_falhos = {f["nome"] for f in falhos}
    dados["fontes"] = [f for f in fontes if f["nome"] not in nomes_falhos]
    with open(ARQUIVO, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)

    print(f"Pronto. Backup salvo em fontes.backup.json.")
    print(f"fontes.json agora tem {len(dados['fontes'])} feeds ativos.")


if __name__ == "__main__":
    main()

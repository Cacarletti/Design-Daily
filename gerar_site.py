"""
gerar_site.py
-------------
Le TODOS os arquivos de dias em dados/AAAA-MM-DD.json e junta num unico
arquivo dados.js que a pagina index.html consegue ler (sem precisar de servidor).

Tambem usa as categorias do fontes.json para manter a ordem de exibicao.
Roda sempre depois do coletar.py.
"""

import json
import os
import glob

PASTA_DADOS = "dados"
SAIDA_JS = "dados.js"
ARQUIVO_FONTES = "fontes.json"


def main():
    with open(ARQUIVO_FONTES, encoding="utf-8") as f:
        config = json.load(f)
    categorias = config["categorias"]

    historico = []
    # Pega todos os arquivos de dia (ex: dados/2026-06-01.json), ignora index.
    arquivos = sorted(glob.glob(os.path.join(PASTA_DADOS, "20*.json")))
    for caminho in arquivos:
        with open(caminho, encoding="utf-8") as f:
            dia = json.load(f)
        historico.append(dia)

    # Mais recente no topo.
    historico.sort(key=lambda d: d["data"], reverse=True)

    pacote = {
        "categorias": categorias,
        "dias": historico,
        "atualizado_em": historico[0]["gerado_em"] if historico else None,
    }

    # Escreve como JS: a pagina le window.HISTORICO direto, sem fetch/servidor.
    with open(SAIDA_JS, "w", encoding="utf-8") as f:
        f.write("window.HISTORICO = ")
        json.dump(pacote, f, ensure_ascii=False)
        f.write(";")

    total_posts = sum(d["total"] for d in historico)
    print(f"Site montado: {len(historico)} dia(s), {total_posts} posts no total.")
    print(f"Arquivo gerado: {SAIDA_JS}")


if __name__ == "__main__":
    main()

# Design Daily 🎨

Agregador diário de notícias de design com histórico por data.
Todo dia às **18h (horário de Brasília)** ele coleta os posts das últimas 24h
de vários feeds RSS, agrupa por categoria e publica numa página com histórico.

## Como funciona

| Arquivo | Papel |
|---|---|
| `fontes.json` | Configuração: feeds, categorias e regras |
| `validar_feeds.py` | Testa quais feeds estão ativos e limpa os quebrados |
| `coletar.py` | Coleta posts das últimas 24h → `dados/AAAA-MM-DD.json` |
| `monitor_estudios.py` | Estúdios SEM RSS: detecta projetos novos por snapshot-diff (`estudios.json` + `estudios_snapshot.json`) |
| `gerar_site.py` | Junta todos os dias num único `dados.js` |
| `index.html` | A página (dashboard responsivo com navegação por data) |
| `.github/workflows/diario.yml` | Automação diária no GitHub |

O histórico nunca é apagado: cada dia é um arquivo em `dados/`, e a página
lista todos, do mais recente ao mais antigo.

## Rodar localmente (no seu computador)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

python coletar.py        # coleta o dia de hoje
python gerar_site.py     # monta o dados.js
python serve.py          # abre em http://localhost:8765
```

## Publicar no GitHub Pages (passo a passo)

1. **Criar o repositório** no GitHub (ex: `design-daily`). Pode ser público.
2. **Enviar os arquivos** (na pasta do projeto):
   ```bash
   git init
   git add .
   git commit -m "Primeira versão do Design Daily"
   git branch -M main
   git remote add origin https://github.com/SEU-USUARIO/design-daily.git
   git push -u origin main
   ```
3. **Ligar o GitHub Pages:** no repositório → **Settings** → **Pages** →
   em *Source*, escolha **Deploy from a branch** → branch **main** / pasta **/ (root)** → **Save**.
   Em 1–2 minutos o site fica no ar em `https://SEU-USUARIO.github.io/design-daily/`.
4. **Permitir que a automação escreva:** Settings → **Actions** → **General** →
   em *Workflow permissions*, marque **Read and write permissions** → **Save**.
5. **Pronto.** A automação roda sozinha todo dia às 18h (Brasília).
   Para testar agora, vá em **Actions** → *Coleta diária de design* → **Run workflow**.

## Manutenção dos feeds

Rode `python validar_feeds.py` de tempos em tempos para checar quais feeds
continuam ativos. Ele faz backup (`fontes.backup.json`) antes de remover quebrados.

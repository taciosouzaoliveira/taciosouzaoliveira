#!/usr/bin/env python3
"""Gera os SVGs do perfil no tema Kurumin.

  python3 scripts/gerar_svgs.py botoes            # botões (uma vez)
  python3 scripts/gerar_svgs.py commits            # gráfico de commits por projeto (GitHub API)

O gráfico roda todo dia pela Action .github/workflows/commits.yml.
"""
import json, os, re, sys, urllib.request
from datetime import datetime, timezone
from html import escape

COR = {"bg": "#050a1a", "painel": "#0b1730", "linha": "#1f3560", "texto": "#e8f0ff",
       "fraco": "#93abcc", "azul": "#1eb8f0", "verde": "#2ee6a6"}
FONTE = "'Sora','Segoe UI',Helvetica,Arial,sans-serif"
MONO = "'JetBrains Mono','DejaVu Sans Mono',Consolas,monospace"
USUARIO = os.environ.get("GH_USER", "taciosouzaoliveira")

BOTOES = [
    ("site", "Kurumin Tecnologia", "kurumintecnologia.com.br", "azul"),
    ("escola", "Escola Kurumin", "LFCS · CKA com lab", "verde"),
    ("linkedin", "LinkedIn", "/in/taciosouzaoliveira", "azul"),
    ("livro", "Livro", "Kubernetes do Zero à CKA", "verde"),
    ("lab", "Laboratório", "engineer.tacio.cloud", "azul"),
    ("email", "E-mail", "contato@kurumintecnologia.com.br", "verde"),
]

def botao(nome, titulo, sub, cor):
    w = max(len(titulo) * 10.5, len(sub) * 8.2) + 56
    c = COR[cor]
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{w:.0f}" height="58" viewBox="0 0 {w:.0f} 58" role="img" aria-label="{escape(titulo)}">
  <rect x=".75" y=".75" width="{w-1.5:.1f}" height="56.5" rx="12" fill="{COR['painel']}" stroke="{c}" stroke-width="1.5"/>
  <circle cx="22" cy="29" r="5" fill="{c}"/>
  <text x="38" y="26" font-family="{FONTE}" font-size="16" font-weight="700" fill="{COR['texto']}">{escape(titulo)}</text>
  <text x="38" y="44" font-family="{MONO}" font-size="12" fill="{COR['fraco']}">{escape(sub)}</text>
</svg>
'''
    open(f"assets/btn-{nome}.svg", "w").write(svg)

def api(url):
    req = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json", "User-Agent": "perfil-kurumin"})
    tok = os.environ.get("GITHUB_TOKEN")
    if tok: req.add_header("Authorization", f"Bearer {tok}")
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r), r.headers.get("Link", "")

def contar_commits():
    repos, _ = api(f"https://api.github.com/users/{USUARIO}/repos?per_page=100&type=owner")
    out = {}
    for r in repos:
        if r["fork"] or r["archived"] or r["size"] == 0 or r["name"] == USUARIO:
            continue
        try:
            dados, link = api(f"https://api.github.com/repos/{USUARIO}/{r['name']}/commits?per_page=1")
        except Exception:
            continue
        m = re.search(r'page=(\d+)>; rel="last"', link)
        out[r["name"]] = int(m.group(1)) if m else len(dados)
    return out

def grafico(contagem, arquivo="assets/commits.svg", top=8):
    itens = sorted(contagem.items(), key=lambda x: -x[1])[:top]
    total = sum(contagem.values())
    W, linha, topo = 1200, 40, 104
    H = topo + linha * len(itens) + 54
    maior = max(v for _, v in itens) or 1
    barra_x, barra_w = 360, 700
    partes = [f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="Commits por projeto">
  <defs><linearGradient id="g" x1="0" x2="1"><stop offset="0" stop-color="{COR['azul']}"/><stop offset="1" stop-color="{COR['verde']}"/></linearGradient>
</defs>
  <rect x=".5" y=".5" width="{W-1}" height="{H-1}" rx="14" fill="{COR['bg']}" stroke="{COR['linha']}"/>
  <text x="32" y="50" font-family="{FONTE}" font-size="24" font-weight="800" fill="{COR['texto']}">Commits por projeto</text>
  <text x="32" y="76" font-family="{MONO}" font-size="13" fill="{COR['fraco']}">{total} commits em {len(contagem)} repositórios públicos · atualizado em {datetime.now(timezone.utc):%d/%m/%Y}</text>''']
    for i, (nome, v) in enumerate(itens):
        y = topo + i * linha
        w = max(6, barra_w * v / maior)
        partes.append(f'''  <text x="32" y="{y+22}" font-family="{MONO}" font-size="15" fill="{COR['texto']}">{escape(nome[:34])}</text>
  <rect x="{barra_x}" y="{y+6}" width="{barra_w}" height="22" rx="6" fill="{COR['painel']}"/>
  <rect x="{barra_x}" y="{y+6}" width="{w:.1f}" height="22" rx="6" fill="url(#g)"><animate attributeName="width" from="0" to="{w:.1f}" dur="1.2s" begin="{0.15+i*0.08:.2f}s" fill="freeze" calcMode="spline" keySplines=".2 .8 .2 1" keyTimes="0;1"/></rect>
  <text x="{barra_x+barra_w+16}" y="{y+23}" font-family="{MONO}" font-size="15" font-weight="700" fill="{COR['verde']}">{v}</text>''')
    partes.append("</svg>\n")
    open(arquivo, "w").write("\n".join(partes))

if __name__ == "__main__":
    os.makedirs("assets", exist_ok=True)
    cmd = sys.argv[1] if len(sys.argv) > 1 else "commits"
    if cmd == "botoes":
        for b in BOTOES: botao(*b)
    elif cmd == "commits":
        grafico(contar_commits())
    elif cmd == "commits-arquivo":           # contagem vinda de um JSON local (teste)
        c = json.load(open(sys.argv[2])); c.pop(USUARIO, None); grafico(c)

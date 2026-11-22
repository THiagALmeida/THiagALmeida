#!/usr/bin/env python3
"""Gera matrix-profile.svg: o README inteiro numa imagem só, com chuva Matrix de fundo.

Roda na GitHub Action (busca ícones e cards de stats atualizados) e pode rodar local.
Uso: python .github/scripts/build_profile.py [saida.svg]
"""
import base64
import json
import os
import random
import re
import sys
import time
import urllib.request

USER = "THiagALmeida"
OUT = sys.argv[1] if len(sys.argv) > 1 else "matrix-profile.svg"

W = 900
GREEN, DIM, DARK, BG, TEXT = "#00FF41", "#3FA34D", "#003B00", "#0D0208", "#C8FFD0"

DEV = "https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons"
ICONS = [
    ("JavaScript", f"{DEV}/javascript/javascript-original.svg"),
    ("TypeScript", f"{DEV}/typescript/typescript-original.svg"),
    ("React Native", f"{DEV}/reactnative/reactnative-original.svg"),
    ("Android", f"{DEV}/android/android-original.svg"),
    ("HTML5", f"{DEV}/html5/html5-original.svg"),
    ("CSS3", f"{DEV}/css3/css3-original.svg"),
    ("Tailwind CSS", f"{DEV}/tailwindcss/tailwindcss-original.svg"),
    ("Git", f"{DEV}/git/git-original.svg"),
    ("GitHub", "https://cdn.simpleicons.org/github/00FF41"),
    ("Antigravity", "https://unpkg.com/@lobehub/icons-static-svg@latest/icons/antigravity-color.svg"),
    ("Claude Code", "https://unpkg.com/@lobehub/icons-static-svg@latest/icons/claudecode-color.svg"),
    ("Wix", "https://cdn.simpleicons.org/wix/00FF41"),
]

CARD = "bg_color=0D0208&title_color=00FF41&icon_color=00FF41&text_color=8CFFA0&border_color=003B00&disable_animations=true"
STATS = f"https://github-stats-extended.vercel.app/api?username={USER}&show_icons=true&include_all_commits=true&count_private=true&{CARD}"
LANGS = f"https://github-stats-extended.vercel.app/api/top-langs/?username={USER}&layout=compact&langs_count=10&{CARD}"
STREAK = (f"https://streak-stats.demolab.com?user={USER}&background=0D0208&ring=00FF41&fire=00FF41"
          "&currStreakLabel=00FF41&sideLabels=8CFFA0&currStreakNum=FFFFFF&sideNums=FFFFFF&dates=3FA34D"
          "&border=003B00&stroke=003B00&disable_animations=true")

TYPING = ["React Native | Android | JavaScript", "Tailwind CSS | HTML | CSS"]

# Para testar sem internet: MATRIX_OFFLINE=mapa.json  ({"url": "caminho/local.svg"})
OFFLINE = json.load(open(os.environ["MATRIX_OFFLINE"])) if os.environ.get("MATRIX_OFFLINE") else None


def fetch(url, tries=3):
    if OFFLINE is not None:
        return open(OFFLINE[url], "rb").read()
    for n in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "matrix-profile-builder"})
            with urllib.request.urlopen(req, timeout=40) as r:
                data = r.read()
            if b"<svg" not in data[:2000]:
                raise ValueError("resposta não é SVG")
            return data
        except Exception as e:  # noqa: BLE001
            print(f"[tentativa {n + 1}] falhou {url}: {e}", file=sys.stderr)
            time.sleep(5 * (n + 1))
    raise SystemExit(f"Não consegui baixar {url} — mantendo o SVG anterior.")


def data_uri(svg_bytes):
    return "data:image/svg+xml;base64," + base64.b64encode(svg_bytes).decode()


def svg_size(svg_bytes):
    head = svg_bytes[:3000].decode("utf-8", "ignore")
    tag = re.search(r"<svg[^>]*>", head, re.S).group(0)
    w = re.search(r'\swidth="([\d.]+)', tag)
    h = re.search(r'\sheight="([\d.]+)', tag)
    if w and h:
        return float(w.group(1)), float(h.group(1))
    vb = re.search(r'viewBox="[\d.\-]+[ ,]+[\d.\-]+[ ,]+([\d.]+)[ ,]+([\d.]+)"', tag)
    return float(vb.group(1)), float(vb.group(2))


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


# ---------------------------------------------------------------- chuva
CHARS = list("アイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホマミムメモヤユヨラリルレロワン0123456789") \
    + list("01") * 8 + list("<>/{};=$#")


def rain(H, rnd):
    cols, fs = 60, 14
    step = W / cols
    out = []
    for i in range(cols):
        x = round(i * step + step / 2, 1)
        for strand in range(3):
            n = rnd.randint(8, 22)
            length = n * (fs + 2)
            speed = rnd.uniform(70, 170)
            dur = round((H + length + 40) / speed, 2)
            delay = round(-rnd.uniform(0, dur), 2)
            spans = []
            for j in range(n):
                op = round(0.1 + 0.9 * (j / (n - 1)) ** 1.6, 2)
                c = esc(rnd.choice(CHARS))
                fill = ' fill="#D7FFD9"' if j == n - 1 else ""
                spans.append(f'<tspan x="{x}" dy="{fs + 2}" opacity="{op}"{fill}>{c}</tspan>')
            out.append(f'<text class="rn" y="{-length}" style="animation-duration:{dur}s;'
                       f'animation-delay:{delay}s">{"".join(spans)}</text>')
    css = (f".rn{{font-family:'Fira Code','MS Gothic','Noto Sans Mono CJK JP',monospace;font-size:{fs}px;"
           f"fill:{GREEN};animation:fall linear infinite}}"
           f"@keyframes fall{{from{{transform:translateY(0)}}to{{transform:translateY({H + 400}px)}}}}")
    return css, "\n".join(out)


# ---------------------------------------------------------------- texto digitando
def typing(cy, rnd_unused=None):
    fs, cw = 22, 13.2
    type_t, hold, del_t, gap = 0.08, 1.8, 0.035, 0.3
    phases = []
    for line in TYPING:
        n = len(line)
        phases.append(n * type_t + hold + n * del_t + gap)
    T = round(sum(phases), 2)
    out, start = [], 0.0
    for idx, line in enumerate(TYPING):
        n = len(line)
        x0 = W / 2 - n * cw / 2
        times, widths = [0.0], [0]
        t = start
        times.append(t); widths.append(0)
        for k in range(1, n + 1):
            t += type_t; times.append(t); widths.append(k)
        t += hold
        for k in range(n - 1, -1, -1):
            t += del_t; times.append(t); widths.append(k)
        times.append(T); widths.append(0)
        kt, vals = [], []
        for tt, ww in zip(times, widths):
            v = round(tt / T, 4)
            if kt and v <= kt[-1]:
                continue
            kt.append(v); vals.append(ww)
        kt[-1] = 1
        wv = ";".join(str(round(v * cw, 1)) for v in vals)
        xv = ";".join(str(round(x0 + v * cw, 1)) for v in vals)
        vis_on, vis_off = round(start / T, 4), round((start + phases[idx] - gap) / T, 4)
        opv = "0;1;0" if vis_on > 0 else "1;0"
        opk = f"0;{vis_on};{vis_off}" if vis_on > 0 else f"0;{vis_off}"
        common = f'dur="{T}s" repeatCount="indefinite" calcMode="discrete"'
        out.append(
            f'<clipPath id="ty{idx}"><rect x="{x0}" y="{cy - 20}" width="0" height="30">'
            f'<animate attributeName="width" values="{wv}" keyTimes="{";".join(map(str, kt))}" {common}/></rect></clipPath>'
            f'<text x="{x0}" y="{cy}" class="ty" clip-path="url(#ty{idx})">{esc(line)}</text>'
            f'<rect class="tc" x="{x0}" y="{cy - 18}" width="11" height="22" opacity="0">'
            f'<animate attributeName="x" values="{xv}" keyTimes="{";".join(map(str, kt))}" {common}/>'
            f'<animate attributeName="opacity" values="{opv}" keyTimes="{opk}" {common}/></rect>')
        start += phases[idx]
    css = (f".ty{{font-family:'Fira Code',Consolas,monospace;font-size:{fs}px;font-weight:600;fill:{GREEN};"
           f"white-space:pre;filter:url(#glow)}}.tc{{fill:{GREEN}}}")
    return css, "\n".join(out)


# ---------------------------------------------------------------- badges
def badge(x, y, left, right, right_bg, icon=None):
    cw, h = 7.6, 26
    lw = len(left) * cw + 22 + (20 if icon else 0)
    rw = len(right) * cw + 22 if right else 0
    g = [f'<g transform="translate({x},{y})">',
         f'<rect width="{lw + rw}" height="{h}" fill="{BG}" stroke="{DARK}"/>']
    tx = 11
    if icon:
        g.append(f'<image href="{icon}" x="9" y="6" width="14" height="14"/>')
        tx = 30
    g.append(f'<text x="{tx}" y="17.5" class="bd" fill="{GREEN}">{esc(left)}</text>')
    if right:
        g.append(f'<rect x="{lw}" width="{rw}" height="{h}" fill="{right_bg}"/>')
        g.append(f'<text x="{lw + 11}" y="17.5" class="bd" fill="{BG}">{esc(right)}</text>')
    g.append("</g>")
    return lw + rw, "".join(g)


# ---------------------------------------------------------------- terminal
def terminal(ox, oy, begin0=1.0):
    rnd = random.Random(7)
    TW, TH, CW, X0 = 820, 330, 9.6, 28
    out, cid = [], [0]

    def typed(y, prompt, cmd, begin):
        cid[0] += 1
        i = cid[0]
        px = X0 + len(prompt) * CW + CW
        dur = round(len(cmd) * 0.09, 2)
        vals = ";".join(str(round(n * CW, 1)) for n in range(len(cmd) + 1))
        out.append(f'<clipPath id="tk{i}"><rect x="{px}" y="{y - 16}" width="0" height="22">'
                   f'<animate attributeName="width" begin="{begin}s" dur="{dur}s" fill="freeze" '
                   f'calcMode="discrete" values="{vals}"/></rect></clipPath>')
        out.append(f'<g opacity="0"><set attributeName="opacity" to="1" begin="{round(begin - 0.4, 2)}s" fill="freeze"/>'
                   f'<text x="{X0}" y="{y}" class="tp">{esc(prompt)}</text>'
                   f'<text x="{px}" y="{y}" class="tw" clip-path="url(#tk{i})">{esc(cmd)}</text></g>')
        return begin + dur

    def show(begin):
        return f'<set attributeName="opacity" to="1" begin="{round(begin, 2)}s" fill="freeze"/>'

    def line(y, parts, begin):
        s = "".join(f'<tspan class="{c}">{esc(t)}</tspan>' for c, t in parts)
        out.append(f'<text x="{X0}" y="{y}" opacity="0">{show(begin)}{s}</text>')

    def bar(y, filled, label, begin):
        out.append(f'<text x="{X0}" y="{y}" opacity="0" class="td">{show(begin)}&gt; [</text>')
        bx = X0 + 3 * CW + 2
        for n in range(10):
            x = bx + n * 16
            if n < filled:
                on = round(begin + 0.15 + n * 0.12, 2)
                pd = round(on + 0.4 + rnd.uniform(0, 1.5), 2)
                out.append(
                    f'<rect class="pon" x="{x}" y="{y - 13}" width="12" height="12" rx="1" fill="#06260C" opacity="0" '
                    f'style="animation-delay:{pd}s,{round(rnd.uniform(0, 6), 2)}s;'
                    f'animation-duration:{round(rnd.uniform(1.6, 2.8), 2)}s,{round(rnd.uniform(5, 11), 2)}s">'
                    f'{show(begin)}<set attributeName="fill" to="{GREEN}" begin="{on}s" fill="freeze"/></rect>')
            else:
                out.append(
                    f'<rect class="poff" x="{x}" y="{y - 13}" width="12" height="12" rx="1" fill="#06260C" '
                    f'stroke="#0B4D16" opacity="0" style="animation-delay:{round(begin + rnd.uniform(1, 8), 2)}s;'
                    f'animation-duration:{round(rnd.uniform(3, 7), 2)}s">{show(begin)}</rect>')
        ex = bx + 10 * 16 + 2
        done = begin + 0.15 + filled * 0.12 + 0.1
        out.append(f'<text x="{ex}" y="{y}" opacity="0" class="td">{show(begin)}]</text>')
        out.append(f'<text x="{ex + 2 * CW}" y="{y}" opacity="0" class="tw">{show(begin)}{esc(label)}</text>')
        out.append(f'<text x="{ex + 26 * CW}" y="{y}" opacity="0" class="tpct">{show(done)}{filled * 10}%</text>')

    t = typed(70, "thiago@matrix:~$", "whoami", begin0)
    line(98, [("td", "> "), ("tw", "Thiago José — estudante de ADS na UNIFACEMA")], t + 0.4)
    line(124, [("td", "> "), ("tw", "Dev de apps e sites | aprende rápido, constrói mais rápido ainda")], t + 0.7)
    t = typed(170, "thiago@matrix:~$", "cat foco.txt", t + 1.6)
    b = t + 0.4
    bar(200, 8, "React Native & Android", b)
    bar(228, 7, "Front-end com Tailwind", b + 1.4)
    bar(256, 5, "TypeScript", b + 2.6)
    fin = b + 3.8
    out.append(f'<g opacity="0">{show(fin)}<text x="{X0}" y="302" class="tp">thiago@matrix:~$</text>'
               f'<rect class="tcur" x="{X0 + 17 * CW}" y="288" width="10" height="17" fill="{GREEN}"/></g>')

    css = (
        ".tp,.tw,.td,.tpct,.tt{font-family:'Fira Code','Cascadia Code',Consolas,'Courier New',monospace;"
        "font-size:16px;white-space:pre}"
        f".tp{{fill:{GREEN};font-weight:700}}.tw{{fill:{TEXT}}}.td{{fill:{DIM}}}.tt{{fill:{DIM};font-size:13px}}"
        f".tpct{{fill:{GREEN};font-size:13px;filter:url(#glow2)}}"
        ".pon{filter:url(#glow2);animation-name:breathe,glitch;animation-iteration-count:infinite,infinite;"
        "animation-timing-function:ease-in-out,steps(1)}"
        "@keyframes breathe{0%,100%{opacity:1}50%{opacity:.55}}"
        "@keyframes glitch{0%,93%,100%{transform:none}94%{transform:translateY(-2px)}96%{transform:translateX(1px)}}"
        ".poff{animation-name:spark;animation-iteration-count:infinite;animation-timing-function:steps(1)}"
        f"@keyframes spark{{0%,86%,100%{{fill:#06260C}}88%{{fill:{GREEN}}}90%{{fill:#0A5A18}}92%{{fill:#00C832}}}}"
        ".tcur{animation:blink 1s steps(1) infinite}@keyframes blink{50%{opacity:0}}"
        f".tscan{{animation:tscan 6s linear infinite}}@keyframes tscan{{from{{transform:translateY(-40px)}}to{{transform:translateY({TH}px)}}}}"
    )
    body = f'''<g transform="translate({ox},{oy})">
<clipPath id="tclip"><rect x="1" y="1" width="{TW - 2}" height="{TH - 2}" rx="10"/></clipPath>
<rect x="1" y="1" width="{TW - 2}" height="{TH - 2}" rx="10" fill="{BG}" stroke="{DARK}" stroke-width="2"/>
<rect x="1" y="1" width="{TW - 2}" height="34" rx="10" fill="#071A0B"/><rect x="1" y="26" width="{TW - 2}" height="9" fill="#071A0B"/>
<circle cx="24" cy="18" r="6" fill="#0B4D16"/><circle cx="44" cy="18" r="6" fill="#0B4D16"/><circle cx="64" cy="18" r="6" fill="{GREEN}" opacity=".8"/>
<text x="{TW / 2}" y="23" text-anchor="middle" class="tt">thiago@matrix — bash</text>
{chr(10).join(out)}
<g clip-path="url(#tclip)"><rect class="tscan" x="1" y="0" width="{TW - 2}" height="40" fill="url(#scanG)"/>
<rect x="1" y="36" width="{TW - 2}" height="{TH - 38}" fill="url(#scanL)"/></g>
</g>'''
    return css, body, TH


# ---------------------------------------------------------------- montagem
def panel(x, y, w, h, op=0.78):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" fill="{BG}" opacity="{op}"/>'


def title(cy, text):
    w = len(text) * 10.8 + 40
    return panel(W / 2 - w / 2, cy - 22, w, 34) + \
        f'<text x="{W / 2}" y="{cy}" text-anchor="middle" class="st">{esc(text)}</text>'


def main():
    body, css = [], []
    y = 170  # topo livre só com chuva (antigo header)

    # texto digitando + badges
    body.append(panel(W / 2 - 300, y, 600, 96))
    c, b = typing(y + 36)
    css.append(c); body.append(b)
    gh_icon = data_uri(fetch(ICONS[8][1]))
    w1 = len("GITHUB") * 7.6 + 42
    w2 = len("STATUS") * 7.6 + 22 + len("ONLINE") * 7.6 + 22
    bx = W / 2 - (w1 + 10 + w2) / 2
    _, b1 = badge(bx, y + 56, "GITHUB", None, None, gh_icon)
    _, b2 = badge(bx + w1 + 10, y + 56, "STATUS", "ONLINE", GREEN)
    body += [b1, b2]
    y += 96 + 30

    # terminal
    c, b, th = terminal((W - 820) / 2, y)
    css.append(c); body.append(b)
    y += th + 50

    # stack
    body.append(title(y, "// stack carregada")); y += 30
    size, gap = 50, 14
    row_w = len(ICONS) * size + (len(ICONS) - 1) * gap
    body.append(panel(W / 2 - row_w / 2 - 18, y, row_w + 36, size + 28))
    x = W / 2 - row_w / 2
    for name, url in ICONS:
        body.append(f'<image href="{data_uri(fetch(url))}" x="{x}" y="{y + 14}" width="{size}" height="{size}">'
                    f'<title>{esc(name)}</title></image>')
        x += size + gap
    y += size + 28 + 55

    # cards
    body.append(title(y, "// leitura do sistema")); y += 30
    cards = [fetch(STATS), fetch(LANGS)]
    sizes = [svg_size(cd) for cd in cards]
    ch = 180
    ws = [s[0] * ch / s[1] for s in sizes]
    total = sum(ws) + 12
    k = min(1, (W - 40) / total)
    x = W / 2 - total * k / 2
    for cd, w in zip(cards, ws):
        body.append(f'<image href="{data_uri(cd)}" x="{round(x, 1)}" y="{y}" width="{round(w * k, 1)}" height="{round(ch * k, 1)}"/>')
        x += (w + 12) * k
    y += ch * k + 18
    streak = fetch(STREAK)
    sw, sh = svg_size(streak)
    sw2 = min(sw, W - 40) if sw > W - 40 else sw
    sh2 = sh * sw2 / sw
    body.append(f'<image href="{data_uri(streak)}" x="{round(W / 2 - sw2 / 2, 1)}" y="{y}" width="{sw2}" height="{round(sh2, 1)}"/>')
    y += sh2 + 140  # rodapé livre só com chuva

    H = round(y)
    rc, rb = rain(H, random.Random(42))
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" xml:space="preserve" viewBox="0 0 {W} {H}" width="{W}" height="{H}">
<title>THiagALmeida — perfil</title>
<style>
{rc}
.st{{font-family:'Fira Code',Consolas,monospace;font-size:18px;font-weight:700;fill:{GREEN};filter:url(#glow)}}
.bd{{font-family:Verdana,'DejaVu Sans',sans-serif;font-size:11px;font-weight:700;letter-spacing:1px}}
{"".join(css)}
</style>
<defs>
<filter id="glow" x="-20%" y="-60%" width="140%" height="220%"><feGaussianBlur stdDeviation="2.5" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
<filter id="glow2" x="-60%" y="-60%" width="220%" height="220%"><feGaussianBlur stdDeviation="2" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
<linearGradient id="scanG" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{GREEN}" stop-opacity="0"/><stop offset=".5" stop-color="{GREEN}" stop-opacity=".07"/><stop offset="1" stop-color="{GREEN}" stop-opacity="0"/></linearGradient>
<pattern id="scanL" width="4" height="4" patternUnits="userSpaceOnUse"><rect width="4" height="1" fill="#000" opacity=".35"/></pattern>
</defs>
<rect width="{W}" height="{H}" fill="{BG}"/>
<g opacity=".85">
{rb}
</g>
{chr(10).join(body)}
<rect x="1" y="1" width="{W - 2}" height="{H - 2}" fill="none" stroke="{DARK}" stroke-width="2"/>
</svg>'''
    open(OUT, "w", encoding="utf-8").write(svg)
    print(f"ok: {OUT} ({len(svg) // 1024} KB, {W}x{H})")


if __name__ == "__main__":
    main()

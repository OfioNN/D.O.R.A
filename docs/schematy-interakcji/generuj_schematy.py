# -*- coding: utf-8 -*-
"""Generator schematów blokowych interakcji z asystentem DORA.

Tworzy pliki SVG i PNG (PNG renderowany przez Microsoft Edge w trybie headless).
Uruchomienie:  python generuj_schematy.py
"""
import pathlib
import subprocess

OUT = pathlib.Path(__file__).resolve().parent
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
FONT = "Calibri, Carlito, 'Segoe UI', Arial, sans-serif"

FILL = {
    "term": "#F9B66E", "proc": "#CFE3F8", "io": "#FDE9A9", "dec": "#BDE5AE",
    "err": "#F7C9CE", "ref": "#EFEFEF", "note": "#FFFFFF",
}
STROKE = "#3a3a3a"
SKEW = 22  # przesunięcie boków równoległoboku


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


class Node:
    def __init__(self, kind, x, y, text, w=None, h=None, status=None, fs=None):
        self.kind, self.x, self.y, self.status = kind, x, y, status
        self.lines = text.split("\n")
        self.fs = fs or {"dec": 19, "ref": 17, "note": 17}.get(kind, 20)
        self.lh = round(self.fs * 1.22, 1)
        self.w = w or {"term": 230, "proc": 240, "io": 255, "err": 255, "dec": 240,
                       "ref": 200, "note": 290}[kind]
        if h:
            self.h = h
        elif kind == "dec":
            self.h = 180
        else:
            n = len(self.lines) + (1 if status else 0)
            self.h = n * self.lh + (40 if kind == "term" else 28)
            if kind in ("proc", "io", "err"):
                self.h = max(self.h, 78)

    # punkty zaczepienia
    @property
    def t(self): return (self.x, self.y - self.h / 2)
    @property
    def b(self): return (self.x, self.y + self.h / 2)
    @property
    def l(self):
        dx = SKEW / 2 if self.kind in ("io", "err") else 0
        return (self.x - self.w / 2 + dx, self.y)
    @property
    def r(self):
        dx = SKEW / 2 if self.kind in ("io", "err") else 0
        return (self.x + self.w / 2 - dx, self.y)

    def svg(self):
        x, y, w, h = self.x, self.y, self.w, self.h
        k = self.kind
        st = f'fill="{FILL[k]}" stroke="{STROKE}" stroke-width="2.2"'
        sh = 'filter="url(#sh)"'
        if k == "term":
            shape = f'<ellipse cx="{x}" cy="{y}" rx="{w/2}" ry="{h/2}" {st} {sh}/>'
        elif k == "dec":
            pts = f"{x},{y-h/2} {x+w/2},{y} {x},{y+h/2} {x-w/2},{y}"
            shape = f'<polygon points="{pts}" {st} {sh}/>'
        elif k in ("io", "err"):
            l, r, tp, bt = x - w / 2, x + w / 2, y - h / 2, y + h / 2
            pts = f"{l+SKEW},{tp} {r},{tp} {r-SKEW},{bt} {l},{bt}"
            shape = f'<polygon points="{pts}" {st} {sh}/>'
        elif k == "ref":
            shape = (f'<rect x="{x-w/2}" y="{y-h/2}" width="{w}" height="{h}" rx="14" '
                     f'fill="{FILL[k]}" stroke="#8a8a8a" stroke-width="2" stroke-dasharray="7 5"/>')
        elif k == "note":
            shape = (f'<rect x="{x-w/2}" y="{y-h/2}" width="{w}" height="{h}" rx="6" '
                     f'fill="#FFFFFF" stroke="#8a8a8a" stroke-width="1.6" stroke-dasharray="5 4"/>')
        else:
            shape = f'<rect x="{x-w/2}" y="{y-h/2}" width="{w}" height="{h}" rx="7" {st} {sh}/>'

        n = len(self.lines) + (1 if self.status else 0)
        y0 = y - (n - 1) * self.lh / 2 + self.fs * 0.34
        out = [shape]
        if k == "note":
            tx = x - w / 2 + 14
            out.append(f'<text x="{tx}" y="{y0}" font-family="{FONT}" font-size="{self.fs}" '
                       f'font-weight="700" fill="#444">')
            for i, ln in enumerate(self.lines):
                out.append(f'<tspan x="{tx}" y="{y0 + i*self.lh}">{esc(ln)}</tspan>')
            out.append("</text>")
            return "\n".join(out)
        col = "#555" if k == "ref" else "#1b1b1b"
        out.append(f'<text text-anchor="middle" font-family="{FONT}" font-size="{self.fs}" '
                   f'font-weight="700" fill="{col}">')
        for i, ln in enumerate(self.lines):
            out.append(f'<tspan x="{x}" y="{y0 + i*self.lh}">{esc(ln)}</tspan>')
        out.append("</text>")
        if self.status:
            sy = y0 + len(self.lines) * self.lh + 1
            out.append(f'<text x="{x}" y="{sy}" text-anchor="middle" font-family="{FONT}" '
                       f'font-size="{self.fs-2}" font-style="italic" font-weight="700" '
                       f'fill="#6A3FB0">▸ {esc(self.status)}</text>')
        return "\n".join(out)


class Diagram:
    def __init__(self, title, subtitle, W, H):
        self.title, self.subtitle, self.W, self.H = title, subtitle, W, H
        self.nodes, self.edges, self.labels, self.dots, self.texts = {}, [], [], [], []

    def node(self, nid, kind, x, y, text, **kw):
        self.nodes[nid] = Node(kind, x, y, text, **kw)

    def pt(self, p):
        if isinstance(p, str):
            nid, side = p.split(".")
            return getattr(self.nodes[nid], side)
        return p

    def e(self, src, dst, via=(), label=None, lp=None, arrow=True, dashed=False):
        a, b = self.pt(src), self.pt(dst)
        pts = [a, *via]
        last = pts[-1]
        if last[0] != b[0] and last[1] != b[1]:
            side = src.split(".")[1] if isinstance(src, str) and not via else None
            if side in ("l", "r") or (side is None and not via):
                pts.append((b[0], last[1]))
            else:
                pts.append((last[0], b[1]))
        pts.append(b)
        self.edges.append((pts, arrow, dashed))
        if label:
            if lp is None:
                (x1, y1), (x2, y2) = pts[0], pts[1]
                lp = ((x1 + x2) / 2, (y1 + y2) / 2)
            self.labels.append((label, lp))

    def dot(self, x, y):
        self.dots.append((x, y))

    def text(self, x, y, s, size=16, anchor="middle"):
        self.texts.append((x, y, s, size, anchor))

    def legend(self, y):
        items = [("term", "Start / koniec"), ("proc", "Proces"), ("io", "Wejście / wyjście"),
                 ("dec", "Decyzja"), ("err", "Komunikat błędu"), ("ref", "Przejście do innego wariantu"),
                 ("status", "Komunikat na pasku stanu (feedback)")]
        if not any(n.kind == "ref" for n in self.nodes.values()):
            items = [it for it in items if it[0] != "ref"]
        widths = []
        for k, t in items:
            widths.append((64 if k != "status" else 58) + 12 + len(t) * 8.6 + 34)
        x = (self.W - sum(widths)) / 2
        out = [f'<line x1="40" y1="{y-38}" x2="{self.W-40}" y2="{y-38}" stroke="#d0d0d0" stroke-width="1.5"/>']
        for (k, t), wdt in zip(items, widths):
            cx, sw, shh = x + 32, 64, 34
            if k == "term":
                out.append(f'<ellipse cx="{cx}" cy="{y}" rx="32" ry="17" fill="{FILL[k]}" stroke="{STROKE}" stroke-width="1.8"/>')
            elif k == "dec":
                out.append(f'<polygon points="{cx},{y-19} {cx+32},{y} {cx},{y+19} {cx-32},{y}" fill="{FILL[k]}" stroke="{STROKE}" stroke-width="1.8"/>')
            elif k in ("io", "err"):
                l, r = cx - 32, cx + 32
                out.append(f'<polygon points="{l+10},{y-17} {r},{y-17} {r-10},{y+17} {l},{y+17}" fill="{FILL[k]}" stroke="{STROKE}" stroke-width="1.8"/>')
            elif k == "ref":
                out.append(f'<rect x="{cx-32}" y="{y-17}" width="64" height="34" rx="9" fill="{FILL[k]}" stroke="#8a8a8a" stroke-width="1.6" stroke-dasharray="5 4"/>')
            elif k == "status":
                out.append(f'<text x="{x+4}" y="{y+6}" font-family="{FONT}" font-size="18" font-style="italic" font-weight="700" fill="#6A3FB0">▸ „…”</text>')
                sw = 58
            else:
                out.append(f'<rect x="{cx-32}" y="{y-17}" width="64" height="34" rx="5" fill="{FILL[k]}" stroke="{STROKE}" stroke-width="1.8"/>')
            out.append(f'<text x="{x+sw+12}" y="{y+6}" font-family="{FONT}" font-size="17" font-weight="700" fill="#333">{esc(t)}</text>')
            x += wdt
        # Tak / Nie
        return "\n".join(out)

    def pill(self, label, x, y):
        tak = label.lower().startswith("tak")
        fill, strk, col = ("#CDEFC4", "#6DBB5C", "#1d4d14") if tak else ("#F9D0D5", "#E07A86", "#6b1520")
        w = len(label) * 9.6 + 22
        return (f'<rect x="{x-w/2}" y="{y-14}" width="{w}" height="28" rx="14" fill="{fill}" '
                f'stroke="{strk}" stroke-width="1.8"/>'
                f'<text x="{x}" y="{y+6}" text-anchor="middle" font-family="{FONT}" font-size="18" '
                f'font-weight="700" fill="{col}">{esc(label)}</text>')

    def svg(self):
        o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.W}" height="{self.H}" '
             f'viewBox="0 0 {self.W} {self.H}">',
             '<defs>'
             '<marker id="ar" markerUnits="userSpaceOnUse" markerWidth="16" markerHeight="16" '
             'refX="15" refY="8" orient="auto"><path d="M0,1.5 L15,8 L0,14.5 z" fill="#222"/></marker>'
             '<marker id="arg" markerUnits="userSpaceOnUse" markerWidth="16" markerHeight="16" '
             'refX="15" refY="8" orient="auto"><path d="M0,1.5 L15,8 L0,14.5 z" fill="#8a8a8a"/></marker>'
             '<filter id="sh" x="-10%" y="-10%" width="125%" height="130%">'
             '<feDropShadow dx="2" dy="3" stdDeviation="1.6" flood-color="#000" flood-opacity="0.22"/>'
             '</filter></defs>',
             f'<rect width="{self.W}" height="{self.H}" fill="#ffffff"/>',
             f'<text x="{self.W/2}" y="58" text-anchor="middle" font-family="{FONT}" font-size="40" '
             f'font-weight="700" fill="#111">{esc(self.title)}</text>',
             f'<text x="{self.W/2}" y="92" text-anchor="middle" font-family="{FONT}" font-size="19" '
             f'font-weight="700" fill="#666">{esc(self.subtitle)}</text>']
        for pts, arrow, dashed in self.edges:
            d = " ".join(f"{x},{y}" for x, y in pts)
            col = "#8a8a8a" if dashed else "#222"
            extra = ' stroke-dasharray="8 6"' if dashed else ""
            mk = (' marker-end="url(#arg)"' if dashed else ' marker-end="url(#ar)"') if arrow else ""
            o.append(f'<polyline points="{d}" fill="none" stroke="{col}" stroke-width="2.6" '
                     f'stroke-linejoin="round"{extra}{mk}/>')
        for n in self.nodes.values():
            o.append(n.svg())
        for x, y in self.dots:
            o.append(f'<circle cx="{x}" cy="{y}" r="5.5" fill="#222"/>')
        for label, (x, y) in self.labels:
            o.append(self.pill(label, x, y))
        for x, y, s, size, anchor in self.texts:
            o.append(f'<text x="{x}" y="{y}" text-anchor="{anchor}" font-family="{FONT}" font-size="{size}" '
                     f'font-style="italic" font-weight="700" fill="#555">{esc(s)}</text>')
        o.append(self.legend(self.H - 42))
        o.append("</svg>")
        return "\n".join(o)

    def save(self, name):
        svg_path = OUT / f"{name}.svg"
        svg_path.write_text(self.svg(), encoding="utf-8")
        html_path = OUT / f".{name}.html"
        html_path.write_text(
            '<!doctype html><html><head><meta charset="utf-8"><style>html,body{margin:0;'
            'background:#fff;overflow:hidden}</style></head><body>' + self.svg() + "</body></html>",
            encoding="utf-8")
        png_path = OUT / f"{name}.png"
        subprocess.run([EDGE, "--headless=new", "--disable-gpu", "--hide-scrollbars",
                        f"--window-size={self.W},{self.H}", "--force-device-scale-factor=2",
                        f"--screenshot={png_path}", html_path.as_uri()],
                       check=True, capture_output=True)
        html_path.unlink()
        print("zapisano", svg_path.name, png_path.name)


# Siatka kolumn wspólna dla wszystkich schematów
C = {1: 145, 2: 445, 3: 745, 4: 1045, 5: 1345, 6: 1645}
W = 1840
SUB = "DORA – Developer’s Own Repository Assistant"


# ---------------------------------------------------------------- 0. schemat ogólny
def schemat_ogolny():
    d = Diagram("DORA – uproszczony schemat działania", SUB + " · schemat ogólny interakcji", W, 1180)
    A, B, Cr, D = 255, 525, 778, 1000
    d.node("start", "term", C[1], A, "Start\n(tryb\nbezczynności)")
    d.node("kam", "io", C[2], A, "Kamera przekazuje\nobraz (lokalnie,\nbez zapisu)")
    d.node("det", "proc", C[3], A, "Detekcja twarzy\nw przeglądarce\n(MediaPipe)")
    d.node("dface", "dec", C[4], A, "Czy wykryto\ntwarz przez\n≥ 1 s?")
    d.node("pow", "proc", C[5], A, "DORA sama wita\nsię i podpowiada\npytania", status="„Zapraszam do rozmowy”")
    d.node("err", "err", (C[4] + C[5]) / 2 + 20, 390, "„Nie zrozumiałam,\npowtórz proszę”")
    d.node("nas", "proc", C[6], B, "Mikrofon włącza\nsię sam: nasłuch\n+ wykrywanie mowy", status="„Słucham…”")
    d.node("pyt", "io", C[5], B, "Użytkownik zadaje\npytanie głosem\n(lub je wpisuje)")
    d.node("stt", "proc", C[4], B, "STT (Whisper)\nzamienia mowę\nna tekst", status="„Rozpoznaję mowę…”")
    d.node("dtr", "dec", C[3], B, "Czy\ntranskrypcja\njest\npoprawna?")
    d.node("rag", "proc", C[1], B, "RAG przeszukuje\nrepozytoria i indeks\ntechnologii", status="„Szukam w projektach…”")
    d.node("dfound", "dec", C[1], Cr, "Czy\nznaleziono\npasujące\nźródła?")
    d.node("llm", "proc", C[2], Cr, "LLM (Ollama)\ntworzy odpowiedź\nze źródłami", status="„Myślę…”")
    d.node("tts", "proc", C[3], Cr, "TTS (Piper)\nzamienia tekst\nna mowę")
    d.node("odp", "io", C[4], Cr, "DORA mówi\n(animacja ust),\nnapisy + źródła", status="„Mówię…”")
    d.node("dnext", "dec", C[5], Cr, "Czy\nużytkownik\nzadaje kolejne\npytanie?")
    d.node("nf", "err", C[1], D, "„Nie mam tego\nw swoich\nprojektach”")
    d.node("pozeg", "proc", C[5], D, "Pożegnanie\n„Do zobaczenia!”")
    d.node("end", "term", C[6], D, "Koniec / powrót\ndo trybu\nbezczynności")

    d.e("start.r", "kam.l"); d.e("kam.r", "det.l"); d.e("det.r", "dface.l")
    d.e("dface.r", "pow.l", label="Tak")
    d.e("dface.t", "kam.t", via=[(C[4], 125), (C[2], 125)], label="Nie", lp=((C[2] + C[4]) / 2, 125))
    d.e("pow.r", "nas.t", via=[(C[6], A)])
    d.e("dtr.t", "err.l", via=[(C[3], 390)], label="Nie", lp=(C[3] + 120, 390))
    d.e("err.r", (C[6], 390), arrow=False); d.dot(C[6], 390)
    d.e("nas.l", "pyt.r"); d.e("pyt.l", "stt.r"); d.e("stt.l", "dtr.r")
    d.e("dtr.l", "rag.r", label="Tak")
    d.e("rag.b", "dfound.t")
    d.e("dfound.r", "llm.l", label="Tak")
    d.e("dfound.b", "nf.t", label="Nie")
    d.e("nf.r", "tts.b", via=[(C[3], D)])
    d.e("llm.r", "tts.l"); d.e("tts.r", "odp.l"); d.e("odp.r", "dnext.l")
    d.e("dnext.r", "nas.b", via=[(C[6], Cr)], label="Tak")
    d.e("dnext.b", "pozeg.t", label="Nie")
    d.e("pozeg.r", "end.l")
    d.text(C[5] + 34, 921, "(cisza > 15 s lub odejście)", 15, "start")
    d.save("00-schemat-ogolny")


# ---------------------------------------------------------------- 1. przebieg prawidłowy
def wariant_1():
    d = Diagram("Wariant 1 – przebieg prawidłowy", SUB + " · interakcja zakończona sukcesem", W, 1180)
    A, B, Cr, D = 255, 525, 778, 1000
    d.node("start", "term", C[1], A, "Start\n(tryb\nbezczynności)")
    d.node("kam", "io", C[2], A, "Użytkownik staje\nprzed laptopem;\nkamera widzi twarz")
    d.node("det", "proc", C[3], A, "Detekcja twarzy\n(obraz tylko\nlokalnie)")
    d.node("dface", "dec", C[4], A, "Czy twarz jest\nwidoczna ≥ 1 s\ni dość duża?")
    d.node("pow", "proc", C[5], A, "Powitanie: „Cześć,\njestem DORA…”\n+ przykłady pytań", status="„Zapraszam do rozmowy”")
    d.node("ref1", "ref", (C[4] + C[5]) / 2 + 20, 390, "→ Wariant 3\n(błędne dane)", h=62)
    d.node("nas", "proc", C[6], B, "Automatyczny\nnasłuch\n(mikrofon + VAD)", status="„Słucham…”")
    d.node("pyt", "io", C[5], B, "„W którym projekcie\nużyłem Dockera?”")
    d.node("stt", "proc", C[4], B, "VAD wykrywa koniec\nwypowiedzi; STT\ntworzy tekst", status="„Rozpoznaję mowę…”")
    d.node("dtr", "dec", C[3], B, "Czy\ntranskrypcja\njest\npoprawna?")
    d.node("rag", "proc", C[1], B, "Indeks technologii\n+ wyszukanie\nfragmentów (RAG)", status="„Szukam w projektach…”")
    d.node("dfound", "dec", C[1], Cr, "Czy\nznaleziono\npasujące\nźródła?")
    d.node("llm", "proc", C[2], Cr, "LLM (Ollama)\nskłada odpowiedź\nz fragmentów", status="„Myślę…”")
    d.node("tts", "proc", C[3], Cr, "TTS (Piper)\nsyntezuje mowę;\nmikrofon wyciszony")
    d.node("odp", "io", C[4], Cr, "DORA mówi + ruch\nust; napisy i źródła\n(projekt, plik)", status="„Mówię…”")
    d.node("dnext", "dec", C[5], Cr, "Czy\nużytkownik\nzadaje kolejne\npytanie?")
    d.node("ref2", "ref", C[1], D, "→ Wariant 3\n(brak źródeł)", h=62)
    d.node("end", "term", C[3], D, "Koniec – sukces;\npowrót do\nbezczynności")
    d.node("clear", "proc", C[4], D, "Wyczyszczenie\nhistorii rozmowy,\nprzerwa 30 s")
    d.node("pozeg", "proc", C[5], D, "Pożegnanie:\n„Dzięki za\nrozmowę!”")
    d.node("note", "note", C[6], D, "W dowolnej chwili:\n• przycisk, Esc, odejście\n  lub „koniec” (gdy słucha)\n  → Wariant 2\n• awaria usługi → Wariant 4", w=270)

    d.e("start.r", "kam.l"); d.e("kam.r", "det.l"); d.e("det.r", "dface.l")
    d.e("dface.r", "pow.l", label="Tak")
    d.e("dface.t", "kam.t", via=[(C[4], 125), (C[2], 125)], label="Nie", lp=((C[2] + C[4]) / 2, 125))
    d.e("pow.r", "nas.t", via=[(C[6], A)])
    d.e("dtr.t", "ref1.l", via=[(C[3], 390)], label="Nie", lp=(C[3] + 120, 390), dashed=True)
    d.e("nas.l", "pyt.r"); d.e("pyt.l", "stt.r"); d.e("stt.l", "dtr.r")
    d.e("dtr.l", "rag.r", label="Tak")
    d.e("rag.b", "dfound.t")
    d.e("dfound.r", "llm.l", label="Tak")
    d.e("dfound.b", "ref2.t", label="Nie", dashed=True)
    d.e("llm.r", "tts.l"); d.e("tts.r", "odp.l"); d.e("odp.r", "dnext.l")
    d.e("dnext.r", "nas.b", via=[(C[6], Cr)], label="Tak")
    d.e("dnext.b", "pozeg.t", label="Nie")
    d.e("pozeg.l", "clear.r"); d.e("clear.l", "end.r")
    d.text(C[5] + 34, 915, "(cisza > 15 s lub odejście)", 15, "start")
    d.save("01-wariant-przebieg-prawidlowy")


# ---------------------------------------------------------------- 2. przerwanie świadome
def wariant_2():
    d = Diagram("Wariant 2 – przerwanie przez użytkownika (świadome)", SUB + " · użytkownik sam kończy rozmowę", W, 1200)
    A, B, Cr, D = 275, 550, 835, 1040
    d.node("start", "term", C[1], A, "Start:\ntrwa rozmowa\nz DORĄ")
    d.node("mon", "proc", C[2], A, "Monitorowanie:\nkamera, mikrofon,\nprzycisk „Zakończ”")
    d.node("dvoice", "dec", C[3], A, "Czy podczas\nsłuchania padło\n„koniec”?")
    d.node("dbtn", "dec", C[4], A, "Czy kliknięto\n„Zakończ”\nlub Esc?")
    d.node("dface", "dec", C[5], A, "Czy twarz\nzniknęła\nna > 5 s?")
    d.node("cont", "proc", C[6], A, "Rozmowa\ntoczy się dalej\n(wariant 1)")
    d.node("anul", "proc", C[4], B, "Przerwanie zadań:\nstop TTS, anulowanie\nzapytania do LLM", status="„Kończę rozmowę…”")
    d.node("dpres", "dec", C[3], B, "Czy\nużytkownik\nnadal jest\nprzed ekranem?", w=250)
    d.node("bye", "io", C[2], B, "Pożegnanie głosem:\n„Dzięki,\ndo zobaczenia!”")
    d.node("clear", "proc", C[1], B, "Wyczyszczenie\nhistorii\nrozmowy")
    d.node("cool", "proc", C[1], Cr, "Blokada\nponownego powitania\nna 30 s")
    d.node("drestart", "dec", C[2], Cr, "Czy kliknięto\n„Rozpocznij\nrozmowę”?")
    d.node("again", "ref", C[3] + 20, Cr, "→ Nowe powitanie\n(wariant 1)", h=62)
    d.node("end", "term", C[2], D, "Koniec: tryb\nbezczynności\n(gotowa na nowo)", w=250)

    d.e("start.r", "mon.l"); d.e("mon.r", "dvoice.l")
    d.e("dvoice.r", "dbtn.l", label="Nie"); d.e("dbtn.r", "dface.l", label="Nie")
    d.e("dface.r", "cont.l", label="Nie")
    d.e("cont.t", "mon.t", via=[(C[6], 140), (C[2], 140)])
    yb = 412
    d.e("dvoice.b", (C[4], yb), via=[(C[3], yb)], arrow=False, label="Tak", lp=(C[3], (A + 90 + yb) / 2))
    d.e("dface.b", (C[4], yb), via=[(C[5], yb)], arrow=False, label="Tak", lp=(C[5], (A + 90 + yb) / 2))
    d.e("dbtn.b", "anul.t", label="Tak", lp=(C[4], (A + 90 + yb) / 2))
    d.dot(C[4], yb)
    d.e("anul.l", "dpres.r")
    d.e("dpres.l", "bye.r", label="Tak")
    jx = (C[1] + 120 + C[2] - 255 / 2 + SKEW / 2) / 2
    d.e("bye.l", "clear.r")
    d.e("dpres.b", (jx, B), via=[(C[3], 700), (jx, 700)], arrow=False, label="Nie", lp=(C[3], 668))
    d.dot(jx, B)
    d.text((C[2] + C[3]) / 2 + 20, 726, "(tylko napis na ekranie: „Rozmowa zakończona”)", 15)
    d.e("clear.b", "cool.t"); d.e("cool.r", "drestart.l")
    d.e("drestart.r", "again.l", label="Tak")
    d.e("drestart.b", "end.t", label="Nie")
    d.text(C[2] + 34, 959, "(po 30 s detekcja twarzy znów aktywna)", 15, "start")
    d.save("02-wariant-przerwanie-swiadome")


# ---------------------------------------------------------------- 3. błędne dane / nieoczekiwane działanie
def wariant_3():
    d = Diagram("Wariant 3 – nieprawidłowe dane lub nieoczekiwane działanie",
                SUB + " · cisza, niezrozumiała mowa, pytanie spoza wiedzy", W, 1180)
    A, B, Cr, D = 255, 545, 790, 1000
    yj = 405
    d.node("start", "term", C[1], A, "Start: DORA\nczeka na\npytanie")
    d.node("nas", "proc", C[2], A, "Nasłuch:\nmikrofon + VAD", status="„Słucham…”")
    d.node("dsp", "dec", C[3], A, "Czy wykryto\nmowę\nw ciągu 15 s?")
    d.node("stt", "proc", C[4], A, "STT zamienia\nmowę na tekst", status="„Rozpoznaję mowę…”")
    d.node("dtr", "dec", C[5], A, "Czy\ntranskrypcja\njest\nzrozumiała?")
    d.node("rag", "proc", C[6], A, "Licznik prób = 0;\nRAG przeszukuje\nprojekty", status="„Szukam w projektach…”")
    d.node("end1", "term", C[3], B, "Pożegnanie,\npowrót do\nbezczynności")
    d.node("inc", "proc", C[4], B, "Licznik kolejnych\nnieudanych\nprób + 1")
    d.node("nf", "err", C[5], B, "„Nie znalazłam tego\nw projektach – zapytaj\nnp. o …”", w=270)
    d.node("dfound", "dec", C[6], B, "Czy\nznaleziono\nźródła\nw projektach?")
    d.node("dretry", "dec", C[4], Cr, "Czy było\nmniej niż 3\nkolejne nieudane\npróby?")
    d.node("back", "term", C[5], Cr, "Koniec: powrót\ndo nasłuchu\n(inne pytanie)")
    d.node("ans", "proc", C[6], Cr, "Odpowiedź ze\nźródłami (jak\nw wariancie 1)", status="„Mówię…”")
    d.node("msg", "err", C[4], D, "„Nie zrozumiałam –\npowtórz lub wpisz\npytanie”", w=265)
    d.node("end2", "term", C[6], D, "Koniec:\npytanie\nobsłużone")

    d.e("start.r", "nas.l"); d.e("nas.r", "dsp.l")
    d.e("dsp.r", "stt.l", label="Tak"); d.e("stt.r", "dtr.l")
    d.e("dtr.r", "rag.l", label="Tak")
    d.e("dsp.b", "end1.t", label="Nie")
    d.e("dtr.b", "inc.t", via=[(C[5], yj), (C[4], yj)], label="Nie", lp=(C[5], (A + 90 + yj) / 2))
    d.e("inc.b", "dretry.t")
    d.e("dretry.l", "end1.b", via=[(C[3], Cr)], label="Nie", lp=(C[3] + 70, Cr))
    d.e("dretry.b", "msg.t", label="Tak")
    d.e("msg.l", "nas.b", via=[(C[2], D)])
    d.e("rag.b", "dfound.t")
    d.e("dfound.l", "nf.r", label="Nie")
    d.e("nf.b", "back.t")
    d.e("dfound.b", "ans.t", label="Tak")
    d.e("ans.b", "end2.t")
    d.text(C[3] + 36, 404, "(cisza nie jest", 15, "start")
    d.text(C[3] + 36, 424, "nieudaną próbą)", 15, "start")
    d.text(C[1] - 70, 700, "Przykłady:", 16, "start")
    d.text(C[1] - 70, 724, "• cisza po powitaniu", 15, "start")
    d.text(C[1] - 70, 746, "• szum, mowa niewyraźna", 15, "start")
    d.text(C[1] - 70, 768, "• „Jaka jutro pogoda?”", 15, "start")
    d.text(C[1] - 70, 790, "• „Czy użyłem Rusta?”", 15, "start")
    d.text(C[1] - 56, 812, "(brak w projektach)", 15, "start")
    d.save("03-wariant-bledne-dane")


# ---------------------------------------------------------------- 4. błąd systemu
def wariant_4():
    d = Diagram("Wariant 4 – błąd systemu", SUB + " · przerwanie lub degradacja z przyczyn technicznych", W, 1200)
    R0, A, B, Cr, D = 172, 360, 600, 840, 1040
    d.node("start", "term", C[1], A, "Start:\nuruchomienie\nDORY")
    d.node("test", "proc", C[2], A, "Sprawdzenie usług:\nkamera, mikrofon,\nbackend, Ollama", status="„Uruchamiam…”")
    d.node("ddev", "dec", C[3], A, "Czy kamera\ni mikrofon\nsą dostępne?")
    d.node("msgdev", "err", C[3], R0, "Tryb zapasowy:\nprzycisk + pole\ntekstowe, komunikat", w=265)
    d.node("dback", "dec", C[5], A, "Czy backend\ni model\nodpowiadają?")
    d.node("reconn", "proc", C[6], A, "Ponowne\nłączenie co 5 s", status="„Łączę ponownie…”")
    d.node("drc", "dec", C[6], B, "Czy\npołączono\nw 3 próbach?")
    d.node("talk", "proc", C[5], B, "Rozmowa: pytanie\nwysłane do\nbackendu", status="„Szukam w projektach…”")
    d.node("dllm", "dec", C[4], B, "Czy\nodpowiedź\nnadeszła\nw 30 s?")
    d.node("dtts", "dec", C[3], B, "Czy synteza\nmowy (TTS)\ndziała?")
    d.node("say", "io", C[2], B, "Odpowiedź głosem\n+ napisy i źródła", status="„Mówię…”")
    d.node("endB", "term", C[1], B, "Koniec:\npowrót do\nnasłuchu")
    d.node("textonly", "err", C[3], Cr, "Odpowiedź tylko\njako tekst + „Brak\ndźwięku”")
    d.node("cancel", "proc", C[4], Cr, "Anulowanie\nzapytania, zapis\nbłędu w logu")
    d.node("sorry", "err", C[5], Cr, "„Przepraszam, mam\nproblem techniczny.\nSpróbuj ponownie”", w=270)
    d.node("fail", "err", C[6], Cr, "Ekran: „DORA jest\nchwilowo\nniedostępna”")
    d.node("endA", "term", C[6], D, "Koniec: tryb\nawaryjny (test\nco 30 s)")

    d.e("start.r", "test.l"); d.e("test.r", "ddev.l")
    d.e("ddev.r", "dback.l", label="Tak", lp=(C[3] + 160, A))
    d.e("ddev.t", "msgdev.b", label="Nie")
    d.e("msgdev.r", (C[4], A), via=[(C[4], R0)], arrow=False); d.dot(C[4], A)
    d.e("dback.r", "reconn.l", label="Nie")
    d.e("dback.b", "talk.t", label="Tak")
    d.e("reconn.b", "drc.t")
    d.e("drc.l", "talk.r", label="Tak")
    d.e("drc.b", "fail.t", label="Nie")
    d.e("fail.b", "endA.t")
    d.e("talk.l", "dllm.r")
    d.e("dllm.l", "dtts.r", label="Tak")
    d.e("dtts.l", "say.r", label="Tak")
    d.e("say.l", "endB.r")
    d.e("dllm.b", "cancel.t", label="Nie")
    d.e("cancel.r", "sorry.l")
    ybus = 985
    d.e("sorry.b", (C[1], Cr), via=[(C[5], ybus), (C[1], ybus)], arrow=False)
    d.dot(C[1], Cr)
    d.e("dtts.b", "textonly.t", label="Nie")
    d.e("textonly.l", "endB.b", via=[(C[1], Cr)])
    d.text((C[2] + C[3]) / 2, ybus - 10, "powrót do nasłuchu, bez ponawiania", 15)
    d.text((C[3] + C[5]) / 2, 1035, "Zerwanie połączenia w trakcie rozmowy → „Ponowne łączenie co 5 s”", 15)
    d.save("04-wariant-blad-systemu")


if __name__ == "__main__":
    schemat_ogolny()
    wariant_1()
    wariant_2()
    wariant_3()
    wariant_4()

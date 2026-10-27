"""Slide build library: page template + slide helpers. Content lives in deck_*.py.

Design rules enforced by construction (from the Databricks slide skill):
- dark slides always carry `dark-bg` so text switches to white; no inline colours
- every slide has an aria-label, a footer with the slide number, and optional speaker notes (press N)
- every content slide has an eyebrow; the headline carries the message
"""
import pathlib, re, html as _h

HERE = pathlib.Path(__file__).parent
CSS = "\n".join((HERE / f).read_text() for f in ("brand.css", "base.css", "a11y.css"))


def _logo(name: str) -> str:
    svg = (HERE / name).read_text()
    return re.sub(r"<!--.*?-->\s*", "", svg, flags=re.S).strip()

LOGO_DARK = _logo("databricks-logo-for-dark-bg.svg")    # for navy / ink backgrounds
LOGO_LIGHT = _logo("databricks-logo-for-light-bg.svg")  # for oat / white backgrounds

KINDS = {"dark": "slide slide-dark dark-bg", "ink": "slide slide-ink dark-bg",
         "light": "slide slide-light", "white": "slide slide-white"}


class Deck:
    def __init__(self, title: str, session: str, short: str):
        self.deck_title, self.session, self.short = title, session, short
        self.slides: list[str] = []

    # ---- core --------------------------------------------------------------------------
    def add(self, kind, label, inner, notes="", footer=True, extra_cls=""):
        n = len(self.slides) + 1
        foot = (f'<div class="slide-footer"><span>Context Engineering on Databricks · {self.session}</span><span>{n}</span></div>'
                if footer else "")
        note = f'<aside class="notes">{notes}</aside>' if notes else ""
        cls = f"{KINDS[kind]} {extra_cls}".strip()
        self.slides.append(
            f'<section class="{cls}" aria-label="Slide {n}: {_h.escape(label)}">'
            f'<div class="slide-content">{inner}</div>{foot}{note}</section>')

    # ---- slide types -------------------------------------------------------------------
    def title(self, heading, sub, meta, notes=""):
        self.add("dark", heading, f'<div class="logo-row">{LOGO_DARK}</div>'
                 f'<span class="eyebrow">{self.session}</span><h1>{heading}</h1><div class="accent-line wide"></div>'
                 f'<p class="lead">{sub}</p><p class="note-tag">{meta}</p>', notes, footer=False, extra_cls="title-slide texture-noise")

    def section(self, num, heading, sub, notes="", kind="ink"):
        self.add(kind, heading, f'<span class="eyebrow">Part {num}</span><h1>{heading}</h1>'
                 f'<div class="accent-line wide"></div><p class="lead">{sub}</p>', notes)

    def content(self, eyebrow, heading, body, lead="", notes="", kind="light"):
        lead_html = f'<p class="lead">{lead}</p>' if lead else ""
        self.add(kind, re.sub("<[^>]+>", "", heading),
                 f'<span class="eyebrow">{eyebrow}</span><h2>{heading}</h2><div class="accent-line"></div>{lead_html}{body}', notes)

    def stat(self, eyebrow, big_html, caption, notes="", kind="dark", heading=""):
        h = f"<h2>{heading}</h2>" if heading else ""
        self.add(kind, heading or caption, f'<span class="eyebrow">{eyebrow}</span>{h}<div class="stat-pair">{big_html}</div>'
                 f'<p class="caption">{caption}</p>', notes)

    def closing(self, heading, items, notes=""):
        lis = "".join(f"<li>{i}</li>" for i in items)
        self.add("dark", heading, f'<div class="logo-row">{LOGO_DARK}</div><span class="eyebrow">Next</span><h2>{heading}</h2>'
                 f'<div class="accent-line"></div><ul class="checklist">{lis}</ul>', notes, extra_cls="texture-noise")

    # ---- render ------------------------------------------------------------------------
    def render(self) -> str:
        return PAGE.replace("{{TITLE}}", _h.escape(self.deck_title)).replace("{{CSS}}", CSS).replace("{{SLIDES}}", "\n".join(self.slides))


# ---- inline component builders (return HTML) ----------------------------------------------
def cards(items, cols=3):
    out = []
    for it in items:
        kicker, title, text = (it + ("",))[:3] if len(it) == 2 else it
        k = f'<span class="kicker">{kicker}</span>' if kicker else ""
        out.append(f'<div class="card">{k}<h3>{title}</h3><p>{text}</p></div>')
    return f'<div class="card-grid cols-{cols}">{"".join(out)}</div>'

def rows(head, data, three=False):
    cls = "rows three" if three else "rows"
    h = "".join(f"<span>{c}</span>" for c in head)
    body = "".join('<div class="row">' + "".join(f"<span>{c}</span>" for c in r) + "</div>" for r in data)
    return f'<div class="{cls}"><div class="row head">{h}</div>{body}</div>'

def flow(steps):
    return '<div class="flow">' + "".join(f'<div class="step"><b>{i:02d}</b><span>{s}</span></div>' for i, s in enumerate(steps, 1)) + "</div>"

def code(text):
    return f'<pre class="code">{text}</pre>'

def hbars(items):  # (label, value 0..1 or 0..100, css, display)
    out = []
    for lbl, v, cls, disp in items:
        out.append(f'<div class="hbar {cls}"><span class="lbl">{lbl}</span><div class="track"><div class="fill" style="--w:{v}%"></div></div><span class="val">{disp}</span></div>')
    return f'<div class="hbars">{"".join(out)}</div>'

def two(left, right):
    return f'<div class="two-col"><div>{left}</div><div>{right}</div></div>'

def pair(a, a_label, a_cls, b, b_label, b_cls, sep="→"):
    """Two labelled big numbers: each figure states what it measures."""
    return (f'<div class="stat-col"><span class="big {a_cls}">{a}</span><span class="sub">{a_label}</span></div>'
            f'<span class="arrow">{sep}</span>'
            f'<div class="stat-col"><span class="big {b_cls}">{b}</span><span class="sub">{b_label}</span></div>')

def tags(items):
    return '<div class="lab-meta">' + "".join(f'<span class="tag {c}">{t}</span>' for t, c in items) + "</div>"

def lab_box(goal, steps, check):
    lis = "".join(f"<li>{s}</li>" for s in steps)
    return (f'<div class="two-col"><div><h3>Goal</h3><p>{goal}</p><h3 style="margin-top:1rem">Steps</h3><ol style="padding-left:1.3rem">{lis}</ol></div>'
            f'<div><h3>You are done when</h3><p>{check}</p></div></div>')


PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{{TITLE}}: Databricks</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,400;0,9..40,500;0,9..40,700;1,9..40,400&family=DM+Mono:wght@300;400;500&display=swap" rel="stylesheet">
<style>
{{CSS}}
</style>
</head>
<body>
<div class="progress-bar" role="progressbar" aria-valuenow="0" aria-valuemin="0" aria-valuemax="100"></div>
<nav class="nav-dots" aria-label="Slide navigation"></nav>
{{SLIDES}}
<div id="notes" role="region" aria-label="Speaker notes"><h5>Speaker notes (press N to hide)</h5><p></p></div>
<script>
class SlidePresentation {
  constructor() {
    this.slides = document.querySelectorAll('.slide'); this.progressBar = document.querySelector('.progress-bar');
    this.navDots = document.querySelector('.nav-dots'); this.notes = document.getElementById('notes'); this.currentSlide = 0; this.init();
  }
  init() { this.createNavDots(); this.setupObserver(); this.setupKeys(); this.setupTouch(); this.setupWheel(); this.updateProgress(); }
  createNavDots() { this.slides.forEach((_, i) => { const d = document.createElement('button'); d.className = 'nav-dot' + (i === 0 ? ' active' : ''); d.setAttribute('aria-label', 'Go to slide ' + (i + 1)); d.addEventListener('click', () => this.goTo(i)); this.navDots.appendChild(d); }); }
  setupObserver() { const o = new IntersectionObserver((es) => { es.forEach(e => { if (e.isIntersecting) { this.currentSlide = [...this.slides].indexOf(e.target); this.updateDots(); this.updateProgress(); this.updateNotes(); } }); }, { threshold: 0.5 }); this.slides.forEach(s => o.observe(s)); }
  setupKeys() { document.addEventListener('keydown', (e) => {
    if (['ArrowDown', 'ArrowRight', ' ', 'PageDown'].includes(e.key)) { e.preventDefault(); this.goTo(this.currentSlide + 1); }
    else if (['ArrowUp', 'ArrowLeft', 'PageUp'].includes(e.key)) { e.preventDefault(); this.goTo(this.currentSlide - 1); }
    else if (e.key === 'Home') { this.goTo(0); } else if (e.key === 'End') { this.goTo(this.slides.length - 1); }
    else if (e.key === 'n' || e.key === 'N') { this.notes.classList.toggle('on'); this.updateNotes(); } }); }
  setupTouch() { let y = 0; document.addEventListener('touchstart', e => { y = e.touches[0].clientY; }, { passive: true }); document.addEventListener('touchend', e => { const d = y - e.changedTouches[0].clientY; if (Math.abs(d) > 50) this.goTo(this.currentSlide + (d > 0 ? 1 : -1)); }, { passive: true }); }
  setupWheel() { let last = 0; document.addEventListener('wheel', e => { const t = Date.now(); if (t - last < 800) return; last = t; this.goTo(this.currentSlide + (e.deltaY > 0 ? 1 : -1)); }, { passive: true }); }
  goTo(i) { const t = Math.max(0, Math.min(i, this.slides.length - 1)); this.slides[t].scrollIntoView({ behavior: 'instant' }); }
  updateDots() { this.navDots.querySelectorAll('.nav-dot').forEach((d, i) => d.classList.toggle('active', i === this.currentSlide)); }
  updateProgress() { const p = ((this.currentSlide + 1) / this.slides.length) * 100; this.progressBar.style.width = p + '%'; this.progressBar.setAttribute('aria-valuenow', Math.round(p)); }
  updateNotes() { const n = this.slides[this.currentSlide].querySelector('aside.notes'); this.notes.querySelector('p').textContent = n ? n.textContent : '(no notes for this slide)'; }
}
new SlidePresentation();
</script>
</body>
</html>
"""

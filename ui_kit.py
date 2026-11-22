"""Premium look-and-feel for ElectionInsight: real light/dark themes, animated charts, 3D skyline."""
import json
import re
import numpy as np
import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components
from streamlit.delta_generator import DeltaGenerator as DG

MODE = {"dark": True}
PALETTE = {
    True: {"BJP": "#FF9933", "INC": "#FFFFFF", "AAP": "#00D0FF", "SAD": "#6C8CFF", "BSP": "#C77DFF", "OTH": "#8D99AE", "NONE": "#4B5563"},
    False: {"BJP": "#FFA94D", "INC": "#86C1F2", "AAP": "#4FD1C5", "SAD": "#8FA2FF", "BSP": "#CDA2E8", "OTH": "#B8C2D3", "NONE": "#CBD5E1"},
}
VARS = {
    True: "--bg:#0B0F1A;--card:rgba(255,255,255,.05);--line:rgba(255,255,255,.1);--text:#ECEEF4;--sub:#97A0B8;--gold:#D4AF6A;"
          "--hero:linear-gradient(135deg,rgba(212,175,106,.12),rgba(255,255,255,.03));--shadow:none;--side:#10162A;--tab:#ECEEF4;"
          "--orb1:rgba(212,175,106,.15);--orb2:rgba(80,120,210,.15)",
    False: "--bg:#F6F1E6;--card:rgba(255,255,255,.92);--line:rgba(27,35,64,.13);--text:#1B2340;--sub:#5D6784;--gold:#9C7420;"
           "--hero:linear-gradient(135deg,#FFFFFF,#F3E8CC);--shadow:0 12px 30px -16px rgba(27,35,64,.35);--side:#EDE4CD;--tab:#000000;"
           "--orb1:rgba(224,176,80,.30);--orb2:rgba(110,160,230,.26)",
}
CSS = """
@import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,600;9..144,700&family=Inter:wght@400;500;600&display=swap');
:root{%VARS%}
@property --v{syntax:'<integer>';initial-value:0;inherits:false}
html,body,.stApp{font-family:'Inter',sans-serif}
.stApp{background:var(--bg) !important;color:var(--text);transition:background .6s}
.stApp::before{content:"";position:fixed;inset:-20%;z-index:0;pointer-events:none;background:radial-gradient(40% 35% at 15% 20%,var(--orb1),transparent 70%),radial-gradient(35% 30% at 85% 75%,var(--orb2),transparent 70%);animation:drift 22s ease-in-out infinite alternate}
@keyframes drift{to{transform:translate3d(4%,3%,0) rotate(6deg) scale(1.08)}}
[data-testid="stMainBlockContainer"]{position:relative;z-index:1;padding-top:2.2rem}
[data-testid="stHeader"]{background:transparent}
[data-testid="stSidebar"]{background:var(--side) !important;border-right:1px solid var(--line)}
[data-testid="stSidebar"] label p{font-size:1.02rem;font-weight:500}
.brand{font-family:'Fraunces',Georgia,serif;font-size:1.9rem;font-weight:700;line-height:1.1;margin:6px 0 18px;color:var(--text)}
.brand span{display:block;font-family:'Inter',sans-serif;font-size:.72rem;font-weight:500;letter-spacing:.22em;text-transform:uppercase;color:var(--gold);margin-top:6px}
[data-testid="stMainBlockContainer"] .stMarkdown p{color:var(--text)}
.hero2{position:relative;overflow:hidden;padding:34px 40px;border-radius:22px;background:var(--hero);border:1px solid var(--line);box-shadow:var(--shadow);animation:rise .9s cubic-bezier(.2,.8,.2,1) both}
.hero2 h1{font-family:'Fraunces',Georgia,serif;font-size:2.9rem;font-weight:700;margin:0;padding:0;letter-spacing:-.01em;color:var(--text)}
.hero2 p{margin:8px 0 0;color:var(--sub);font-size:1.08rem}
.hero2::after{content:"";position:absolute;top:0;left:-60%;width:40%;height:100%;background:linear-gradient(100deg,transparent,rgba(255,255,255,.14),transparent);animation:sheen 6s ease-in-out infinite}
@keyframes sheen{to{left:130%}}
@keyframes rise{from{opacity:0;transform:translateY(24px)}}
.stripe2{height:4px;border-radius:4px;margin:16px 0 24px;background:linear-gradient(90deg,#FF9933,#fff,#138808,#FF9933);background-size:300% 100%;animation:flow 8s linear infinite}
@keyframes flow{to{background-position:300% 0}}
.k{height:156px;box-sizing:border-box;display:flex;flex-direction:column;justify-content:space-between;padding:18px 22px;border-radius:18px;background:var(--card);border:1px solid var(--line);border-top:4px solid var(--c);box-shadow:var(--shadow);transition:transform .35s cubic-bezier(.2,.8,.2,1),box-shadow .35s;animation:rise .8s cubic-bezier(.2,.8,.2,1) both;animation-delay:var(--d)}
.k:hover{transform:perspective(700px) rotateX(6deg) rotateY(-6deg) translateY(-8px) scale(1.02);box-shadow:0 26px 40px -22px var(--c)}
.k small{color:var(--sub);text-transform:uppercase;letter-spacing:.12em;font-size:.78rem;font-weight:600}
.k h2{font-family:'Fraunces',Georgia,serif;font-size:2.4rem;margin:0;padding:0;color:var(--text);line-height:1.1}
.k em{font-style:normal;color:var(--sub);font-size:.95rem}
.k em b.sn{font-size:1.35rem;font-weight:800;color:var(--text);letter-spacing:.01em}
.cnt{animation:count 1.8s cubic-bezier(.2,.8,.2,1) both;counter-reset:v var(--v)}
.cnt::before{content:counter(v)}
@keyframes count{from{--v:0}to{--v:var(--n)}}
.stTabs [data-baseweb="tab-list"]{gap:6px;border-bottom:1px solid var(--line)}
.stTabs [data-baseweb="tab"]{height:58px;padding:0 24px;border-radius:12px 12px 0 0;transition:all .3s ease}
.stTabs [data-baseweb="tab"] p{font-size:1.2rem !important;font-weight:600;letter-spacing:.01em;color:var(--tab) !important}
.stTabs [data-baseweb="tab"]:hover{background:rgba(212,175,106,.14);transform:translateY(-2px)}
.stTabs [aria-selected="true"] p{color:var(--gold) !important}
.stTabs [data-baseweb="tab-highlight"]{background:var(--gold) !important;height:3px}
iframe{border-radius:16px}
[data-testid="stSidebar"] .stButton button{justify-content:flex-start;background:var(--card);border:1px solid var(--line);border-radius:999px;padding:.4rem 1.1rem;transition:all .25s}
[data-testid="stSidebar"] .stButton button *{color:var(--text) !important;font-size:1.05rem;font-weight:600}
[data-testid="stSidebar"] .stButton button:hover{border-color:var(--gold);transform:translateY(-1px)}
"""
LIGHT_CSS = """
html,body,.stApp{-webkit-font-smoothing:antialiased;text-rendering:optimizeLegibility}
[data-testid="stHeader"] *{color:#1B2340 !important}
[data-testid="stHeader"] svg{fill:#1B2340 !important}
[data-testid="stSidebar"] :is(p,span,label,small,h1,h2,h3){color:#1B2340 !important}
[data-testid="stSidebar"] .brand span{color:#8A6418 !important}
[data-testid="stSidebar"] [role="radiogroup"] label p{font-weight:400 !important}
[data-testid="stSidebar"] label p{font-weight:600 !important}
label[data-baseweb="radio"]>div:first-child{border-color:#5D6784 !important}
[data-testid="stWidgetLabel"] :is(p,label,span),[data-testid="stSlider"] :is(p,div,span){color:#1B2340 !important}
[data-baseweb="select"]>div{background:#FFFFFF !important;border:1px solid rgba(27,35,64,.28) !important}
[data-baseweb="select"] :is(div,span,input){color:#1B2340 !important}
[data-baseweb="select"] svg{fill:#1B2340 !important}
[data-baseweb="popover"] :is(ul,[role="listbox"],[data-baseweb="menu"]){background:#FFFFFF !important}
[data-baseweb="popover"] li,[data-baseweb="popover"] li *{color:#1B2340 !important;background:transparent !important}
[data-baseweb="popover"] li:hover{background:#F3E8CC !important}
[data-testid="stDownloadButton"] button{background:#FFFFFF !important;border:1px solid rgba(27,35,64,.4) !important}
[data-testid="stDownloadButton"] button,[data-testid="stDownloadButton"] button *{color:#000000 !important;font-weight:600}
[data-testid="stDownloadButton"] button:hover{background:#F3E8CC !important;border-color:#8A6418 !important}
[data-testid="stAlert"] *{color:#1B2340 !important}
[data-testid="stDataFrame"]{filter:invert(1) hue-rotate(180deg)}
"""
TAG_CSS = """
[data-baseweb="select"] span[data-baseweb="tag"]{background:#5B3A1E !important;border-radius:8px}
[data-baseweb="select"] span[data-baseweb="tag"],[data-baseweb="select"] span[data-baseweb="tag"] *{color:#FFFFFF !important;font-weight:600}
[data-baseweb="select"] span[data-baseweb="tag"] svg{fill:#FFFFFF !important}
"""


def inject_theme(dark):
    MODE["dark"] = dark
    css = CSS.replace("%VARS%", VARS[dark]) + ("" if dark else LIGHT_CSS) + TAG_CSS
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


def ink(c):
    """Readable text colour (dark or white) for a given fill colour."""
    c = c.lstrip("#"); r, g, b = (int(c[i:i + 2], 16) for i in (0, 2, 4))
    return "#10162A" if .299 * r + .587 * g + .114 * b > 150 else "#FFFFFF"


def kpi(col, label, value, color, count=None, suffix="", i=0, sub=""):
    body = f'<span class="cnt" style="--n:{count}"></span>{suffix}' if count is not None else value
    col.markdown(f'<div class="k" style="--c:{color};--d:{i * .12}s"><small>{label}</small><h2>{body}</h2><em>{sub}</em></div>',
                 unsafe_allow_html=True)


def _theme_fig(fig, h=None):
    dark = MODE["dark"]
    fig.update_layout(template="plotly_dark" if dark else "plotly_white", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      font=dict(family="Inter, Segoe UI, sans-serif", color="#dbe4ff" if dark else "#1B2340", size=14),
                      title_font=dict(family="Georgia, serif", size=20, color="#ECEEF4" if dark else "#1B2340"))
    axl = "rgba(236,238,244,.55)" if dark else "#000000"
    ax = dict(showline=True, linecolor=axl, linewidth=1.6, zeroline=True, zerolinecolor=axl, zerolinewidth=1.6,
              ticks="outside", tickcolor=axl)
    if not dark:
        ax["gridcolor"] = "rgba(27,35,64,.12)"
    fig.update_xaxes(**ax)
    fig.update_yaxes(**ax)
    # legend sits in a row under the title so it can never be clipped on the right edge
    fig.update_layout(legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0,
                                  font=dict(size=14), title=dict(text=""), entrywidth=175, entrywidthmode="pixels",
                                  tracegroupgap=0, itemsizing="constant"))
    if h:
        fig.update_layout(height=h, margin=dict(l=10, r=20, t=88 if len(fig.data) > 1 else 56, b=10))
    return fig


def style(fig, h=420):
    return _theme_fig(fig, h)


# ------------------------------------------------------------ animation maths
def _back(x):
    c = 1.70158
    return 1 + (c + 1) * (x - 1) ** 3 + c * (x - 1) ** 2


def _io(x):
    return 4 * x ** 3 if x < .5 else 1 - (-2 * x + 2) ** 3 / 2


def _prog(n, steps=44, spread=.5, f=_back):
    """Per-item eased progress for each frame; item j starts later than item j-1 (stagger)."""
    n = max(n, 1)
    return [np.array([f(min(1, max(0, (s / steps - j / max(n - 1, 1) * spread) / (1 - spread)))) for j in range(n)])
            for s in range(1, steps + 1)]


def _nice(t):
    h = getattr(t, "hovertemplate", None)
    if isinstance(h, str) and "=" in h:
        t.hovertemplate = re.sub(r"(^|<br>)([^<=]+)=", lambda m: f"{m[1]}<b>{m[2].replace('_', ' ').strip()}</b>: ", h)


def _clean(arr):
    return [0.0 if v is None or v != v else float(v) for v in arr]


JS = """<script>(function(){var g=document.getElementById('g');if(!g)return;var F=%F%,done=false;
function ready(){return g._transitionData&&g._transitionData._frames&&g._transitionData._frames.length}
function play(){if(done)return;g.classList.add('go');if(F){if(!ready()){setTimeout(play,80);return}
Plotly.animate(g,null,{frame:{duration:24,redraw:true},transition:{duration:0},fromcurrent:false,mode:'immediate'})}done=true}
new IntersectionObserver(function(es){es.forEach(function(e){if(e.isIntersecting)play()})},{threshold:.3}).observe(g);})();</script>"""
WRAP_CSS = ("<style>html,body{margin:0;background:transparent}.plotly-graph-div{opacity:0}"
            ".plotly-graph-div.go{animation:in .9s cubic-bezier(.2,.8,.2,1) forwards}.sw.go{animation:swirl 1.2s cubic-bezier(.2,.8,.2,1) forwards}"
            "@keyframes in{from{opacity:0;transform:translateY(22px) scale(.97)}to{opacity:1;transform:none}}"
            "@keyframes swirl{from{opacity:0;transform:rotate(-40deg) scale(.55)}to{opacity:1;transform:none}}</style>")


def _html(fig):
    fig = _theme_fig(go.Figure(fig))
    ts, h, steps, cls, anim = list(fig.data), int(fig.layout.height or 420), 44, "", False
    for t in ts:
        _nice(t)
    kinds = {t.type for t in ts}
    if kinds == {"bar"} and all(t.y is not None and t.x is not None for t in ts):
        stack, tot = fig.layout.barmode in (None, "stack", "relative"), {}
        for t in ts:
            for x, y in zip(t.x, _clean(t.y)):
                k = (t.xaxis, x); tot[k] = tot.get(k, 0) + y if stack else max(tot.get(k, 0), y)
        ys = [np.array(_clean(t.y)) for t in ts]
        P = [_prog(len(y), steps) for y in ys]
        fig.update_yaxes(range=[0, (max(tot.values()) or 1) * 1.22])
        fig.frames = [go.Frame(data=[go.Bar(y=(ys[k] * P[k][s]).tolist()) for k in range(len(ts))], name=str(s)) for s in range(steps)]
        for t, y in zip(ts, ys):
            t.y = [0] * len(y)
        anim = True
    elif kinds == {"pie"} and len(ts) == 1:  # donut sweeps around from 12 o'clock until the circle closes
        t = ts[0]; labs, vals = list(t.labels), _clean(t.values); tot = sum(vals) or 1
        ln = t.marker.line
        t.update(labels=labs + [" "], values=vals + [tot * 1e3], sort=False, direction="clockwise", rotation=0, textinfo="text",
                 text=[f"<b>{l}</b><br>{int(v)}" for l, v in zip(labs, vals)] + [""],
                 hovertemplate="<b>%{label}</b><br>%{value} seats · %{percent}<extra></extra>",
                 marker=dict(colors=list(t.marker.colors) + ["rgba(0,0,0,0)"], line=dict(color=ln.color, width=ln.width)),
                 textfont=dict(size=15))
        fig.update_layout(showlegend=False)
        fr = [_io(s / steps) for s in range(1, steps + 1)]
        fig.frames = [go.Frame(data=[go.Pie(values=vals + [tot * (1 - f) / max(f, 1e-3) if s < steps - 1 else 0])], name=str(s))
                      for s, f in enumerate(fr)]
        anim = True
    elif kinds == {"heatmap"}:  # colours fill in and the numbers count up
        zs = [np.array(t.z, float) for t in ts]; zmax = max(z.max() for z in zs) or 1
        fig.update_coloraxes(cmin=0, cmax=zmax)
        for t in ts:
            t.zmin, t.zmax, t.texttemplate = 0, zmax, "%{z:.0f}"
        fig.frames = [go.Frame(data=[go.Heatmap(z=(z * _io(s / steps)).tolist()) for z in zs], name=str(s)) for s in range(steps)]
        for t, z in zip(ts, zs):
            t.z = np.zeros_like(z).tolist()
        anim = True
    elif kinds == {"scatter"} and all(t.mode and "markers" in t.mode and t.x is not None for t in ts):  # markers pop in one by one
        sz = []
        for t in ts:
            s0 = t.marker.size
            sz.append(np.array(s0, float) if hasattr(s0, "__len__") else np.full(len(t.x), float(s0 or 8)))
        P = [_prog(len(s_), steps, .6) for s_ in sz]
        fig.frames = [go.Frame(data=[go.Scatter(marker=dict(size=(sz[k] * P[k][s]).tolist())) for k in range(len(ts))], name=str(s)) for s in range(steps)]
        for t, s_ in zip(ts, sz):
            t.marker.size = [0] * len(s_)
        anim = True
    elif kinds == {"sunburst"}:
        cls = "sw"
    page = fig.to_html(include_plotlyjs="cdn", full_html=False, div_id="g", default_height=f"{h}px", default_width="100%",
                       config=dict(displayModeBar=False, responsive=True), auto_play=False)
    if cls:
        page = page.replace('class="plotly-graph-div"', f'class="plotly-graph-div {cls}"')
    return WRAP_CSS + page + JS.replace("%F%", "true" if anim else "false"), h


def _render(fig):
    html, h = _html(fig)
    components.html(html, height=h + 6)


def _render_in(dg, fig, **kw):
    with dg:
        _render(fig)


def patch_charts():
    """Every st.plotly_chart / column.plotly_chart now renders as an animated chart."""
    DG.plotly_chart = _render_in
    st.plotly_chart = lambda fig, **kw: _render(fig)


# ------------------------------------------------------------ 3D skyline
def _boxes(cells, w=.8):
    X, Y, H, D, I, J, K, T = [], [], [], [], [], [], [], []
    corners = [(0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0), (0, 0, 1), (1, 0, 1), (1, 1, 1), (0, 1, 1)]
    tris = [(0, 1, 2), (0, 2, 3), (4, 6, 5), (4, 7, 6), (0, 4, 5), (0, 5, 1), (1, 5, 6), (1, 6, 2), (2, 6, 7), (2, 7, 3), (3, 7, 4), (3, 4, 0)]
    for gx, gy, h, delay, label in cells:
        base = len(X)
        for dx, dy, dz in corners:
            X.append(gx + .1 + dx * w); Y.append(gy + .1 + dy * w); H.append(h * dz); D.append(delay); T.append(label)
        for a, b, c in tris:
            I.append(base + a); J.append(base + b); K.append(base + c)
    return X, Y, H, D, I, J, K, T


def landscape_html(d, color_of):
    dark = MODE["dark"]
    txt, sub, floor = ("#ECEEF4", "#97A0B8", "#1B2547") if dark else ("#1B2340", "#5D6784", "#E4DCC8")
    regs, cols, x0, lay = sorted(d.Region.unique()), 6, 0, {}
    for r in regs:
        lay[r] = (x0, int((d.Region == r).sum())); x0 += cols + 2
    xtot = x0 - 2
    zmax = max(.3 * xtot, 6.0)
    cells = {}
    for r in regs:
        g = d[d.Region == r].sort_values("AC_No").reset_index(drop=True)
        for k, row in g.iterrows():
            cf = float(np.nan_to_num(row.Conf)); gx = lay[r][0] + k % cols
            lab = (f"<b>{row.AC_Name}</b><br>{row.Pred} · {cf:.0f}% confidence<br>{r}"
                   + ("" if row.OK else f"<br>Actual winner: {row.Party_Clean}"))
            cells.setdefault(row.Pred, []).append((gx, k // cols, cf / 100 * zmax, gx / xtot, lab))
    fig = go.Figure()
    for r in regs:
        x, n = lay[r]; rows = int(np.ceil(n / cols))
        fig.add_trace(go.Mesh3d(x=[x - .3, x + cols + .3, x + cols + .3, x - .3], y=[-.3, -.3, rows + .3, rows + .3], z=[0] * 4,
                                i=[0, 0], j=[1, 2], k=[2, 3], color=floor, opacity=.95, hoverinfo="skip", lighting=dict(ambient=1)))
    fig.add_trace(go.Scatter3d(x=[lay[r][0] + cols / 2 for r in regs], y=[-1.6] * len(regs), z=[0] * len(regs), mode="text",
                               text=[f"<b>{r}</b><br>{lay[r][1]} seats" for r in regs], textfont=dict(size=15, color=txt), hoverinfo="skip"))
    fig.add_trace(go.Scatter3d(x=[-2] * 3, y=[0] * 3, z=[0, zmax / 2, zmax], mode="lines+text", text=["0%", "50%", "100%"],
                               textposition="middle left", textfont=dict(size=13, color=sub), line=dict(color=sub, width=5), hoverinfo="skip"))
    idx, H, D = [], [], []
    for p, cs in cells.items():
        X, Y, Hh, Dd, I, J, K, T = _boxes(cs)
        idx.append(len(fig.data)); H.append(np.round(Hh, 2).tolist()); D.append(np.round(Dd, 3).tolist())
        fig.add_trace(go.Mesh3d(x=X, y=Y, z=[0] * len(X), i=I, j=J, k=K, color=color_of(p), flatshading=True, hovertext=T, hoverinfo="text",
                                lighting=dict(ambient=.62, diffuse=.85, specular=.3, roughness=.55), lightposition=dict(x=120, y=-250, z=320)))
    ax = dict(visible=False)
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", height=660, margin=dict(l=0, r=0, t=0, b=0), showlegend=False,
                      font=dict(family="Inter, sans-serif", size=14),
                      scene=dict(xaxis=ax, yaxis=ax, zaxis=ax, bgcolor="rgba(0,0,0,0)", aspectmode="data",
                                 camera=dict(eye=dict(x=0, y=-1.8, z=.85), center=dict(x=0, y=0, z=-.1))))
    html = fig.to_html(include_plotlyjs="cdn", full_html=False, div_id="g", default_height="660px", default_width="100%",
                       config=dict(displayModeBar=False, responsive=True, scrollZoom=True))
    chips = "".join(f'<span><i style="background:{color_of(p)}"></i>{p} · {len(cs)}</span>' for p, cs in cells.items())
    ui = (f'<style>html,body{{margin:0;background:transparent;font-family:Inter,sans-serif}}.lg{{position:absolute;top:10px;left:14px;z-index:5;display:flex;gap:10px;flex-wrap:wrap}}'
          f'.lg span{{display:flex;align-items:center;gap:7px;padding:6px 12px;border-radius:20px;font-size:14px;font-weight:600;color:{txt};background:{floor};opacity:.95}}'
          f'.lg i{{width:12px;height:12px;border-radius:50%;display:inline-block}}.tip{{position:absolute;bottom:10px;left:14px;font-size:13px;color:{sub};z-index:5}}</style>'
          f'<div style="position:relative"><div class="lg">{chips}</div>{html}'
          f'<div class="tip">Each column is one constituency · height = model confidence · hover to pause the sway · drag to rotate · scroll to zoom</div></div>')
    js = """<script>(function(){var g=document.getElementById('g'),H=%H%,D=%D%,IDX=%I%,auto=true,raf=null,last=null,tt=0,ph=0,az0=0,r0=1.8,z0=.8,tch=null;
function ease(x){x=Math.max(0,Math.min(1,x));var c=1.70158;return 1+(c+1)*Math.pow(x-1,3)+c*Math.pow(x-1,2)}
function step(ts){var dt=last===null?0:Math.min(ts-last,50);last=ts;tt+=dt;var t=tt/2400;
if(t<1.3){Plotly.restyle(g,{z:H.map(function(h,k){return h.map(function(v,i){return v*ease((t-D[k][i]*.5)/.5)})})},IDX)}
if(auto){ph+=dt;var a=az0+.6*Math.sin(ph/2600);Plotly.relayout(g,{'scene.camera.eye':{x:r0*Math.sin(a),y:-r0*Math.cos(a),z:z0+.12*Math.sin(ph/3100)}})}
raf=requestAnimationFrame(step)}
function start(){if(!window.Plotly||!g.data){setTimeout(start,80);return}if(raf)return;last=null;raf=requestAnimationFrame(step)}
function stop(){if(raf)cancelAnimationFrame(raf);raf=null}
function pause(){auto=false}
function resume(){var L=g.layout&&g.layout.scene&&g.layout.scene.camera,c=(L&&L.eye)?L:(g._fullLayout&&g._fullLayout.scene&&g._fullLayout.scene.camera);
if(c&&c.eye){var e=c.eye;r0=Math.sqrt(e.x*e.x+e.y*e.y)||1.8;az0=Math.atan2(e.x,-e.y);z0=e.z;ph=0}auto=true}
g.addEventListener('mouseenter',pause);g.addEventListener('mouseleave',resume);
g.addEventListener('touchstart',function(){pause();if(tch)clearTimeout(tch)},{passive:true});
g.addEventListener('touchend',function(){tch=setTimeout(resume,1800)},{passive:true});
new IntersectionObserver(function(es){es.forEach(function(e){e.isIntersecting?start():stop()})},{threshold:.2}).observe(g);})();</script>"""
    return ui + js.replace("%H%", json.dumps(H)).replace("%D%", json.dumps(D)).replace("%I%", json.dumps(idx))

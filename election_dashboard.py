"""
ElectionInsight - Interactive Dashboard (Streamlit + Plotly)
Run:  pip install streamlit plotly pandas numpy openpyxl
      streamlit run election_dashboard.py

Reads the Excel written by your model script:
  <State>_MaxAccuracy_Bayesian_Comparison.xlsx  (sheet: Constituency_Predictions)
Put it in the same folder, or upload it from the sidebar.
If no file is found, demo data is shown so you can preview the look.
"""
import io, os
from pathlib import Path
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="ElectionInsight", page_icon="🗳️", layout="wide")
from ui_kit import inject_theme, kpi, style, landscape_html, patch_charts, components, PALETTE, ink
patch_charts()

PARTY = {"BJP": "#FF9933", "INC": "#FFFFFF", "AAP": "#00D0FF", "SAD": "#6C8CFF",
         "BSP": "#C77DFF", "OTH": "#8D99AE", "NONE": "#4B5563"}
MODES = {
    "80/20 Cross-Validation": ("Pred_80_20_CV", "Prob_80_20_%"),
    "Locked Past → Future Forecast": ("Pred_Future_Forecast", "Prob_Forecast_%"),
}
pc = lambda p: PARTY.get(p, "#8D99AE")

st.markdown("""
<style>
.stApp{background:radial-gradient(circle at 10% 0%,#1b2440 0%,#0b1020 55%,#070a14 100%);}
.hero{padding:22px 28px;border-radius:18px;background:linear-gradient(135deg,#1f2a4d,#121a33);
 border:1px solid #2c3a66;margin-bottom:6px}
.hero h1{margin:0;font-size:2.1rem;color:#fff}.hero p{margin:4px 0 0;color:#9fb0d9}
.stripe{height:5px;border-radius:4px;margin:10px 0 18px;
 background:linear-gradient(90deg,#FF9933 33%,#fff 33% 66%,#138808 66%)}
.kpi{padding:16px 18px;border-radius:16px;background:#141c36;border:1px solid #27345e;
 border-left:6px solid var(--c);}
.kpi small{color:#8fa0cc;text-transform:uppercase;letter-spacing:.06em}
.kpi h2{margin:2px 0 0;color:#fff;font-size:1.8rem}
</style>""", unsafe_allow_html=True)


# ---------------------------------------------------------------- data
@st.cache_data
def read_xlsx(src):
    x = pd.ExcelFile(io.BytesIO(src) if isinstance(src, bytes) else src)
    return x.parse("Constituency_Predictions")


@st.cache_data
def demo(state):
    rng = np.random.default_rng(7)
    n = 70 if state == "Uttarakhand" else 117
    parties = ["BJP", "INC", "BSP", "OTH"] if state == "Uttarakhand" else ["INC", "AAP", "SAD", "BJP", "OTH"]
    p = np.linspace(len(parties), 1, len(parties)); p /= p.sum()
    rows, prev = [], np.array(["NONE"] * n)
    for y in (2012, 2017, 2022):
        act = rng.choice(parties, n, p=p)
        ok1, ok2 = rng.random(n) < .78, rng.random(n) < .6
        cv = (np.where(ok1, act, rng.choice(parties, n)), ok1)
        fc = (np.where(ok2, act, rng.choice(parties, n)), ok2)
        for i in range(n):
            rows.append(dict(
                Election_Year=y, AC_No=i + 1, AC_Name=f"Constituency {i + 1}", Prev_Winner=prev[i],
                Actual_Winner=act[i], Party_Clean=act[i],
                Pred_80_20_CV=cv[0][i], **{"Prob_80_20_%": round(rng.uniform(55, 95) if cv[1][i] else rng.uniform(35, 65), 2)},
                Pred_Future_Forecast=fc[0][i] if y > 2012 else "N/A (Base Year)",
                **{"Prob_Forecast_%": round(rng.uniform(50, 90) if fc[1][i] else rng.uniform(33, 60), 2) if y > 2012 else np.nan}))
        prev = act
    return pd.DataFrame(rows)


def region(ac, state):
    if state == "Punjab":
        return "Majha" if ac <= 29 else "Doaba" if ac <= 52 else "Malwa"
    return ("Garhwal Hills" if ac <= 13 or 36 <= ac <= 41 else "Plains (HDW/DDN)" if ac <= 35
            else "Kumaon Hills" if ac <= 61 else "Terai (USN)")


def rgba(hex_, a=.45):
    h = hex_.lstrip("#"); return f"rgba({int(h[:2],16)},{int(h[2:4],16)},{int(h[4:],16)},{a})"



# ---------------------------------------------------------------- sidebar
st.session_state.setdefault("dark", True)
dark = st.session_state.dark
if st.sidebar.button("🌙  Night mode" if dark else "☀️  Day mode", key="mode_btn", width="stretch",
                     help="Click to switch between night and day mode"):
    st.session_state.dark = not dark
    st.rerun()
inject_theme(dark)
if not dark:  # day mode: tab labels black (hover / selected = gold). Uses ARIA roles, which every Streamlit version has.
    st.markdown("""<style>
html body [role="tab"],html body [role="tab"] *{
  color:#000000 !important;-webkit-text-fill-color:#000000 !important;opacity:1 !important;fill:#000000}
html body [role="tab"]:hover,html body [role="tab"]:hover *,
html body [role="tab"][aria-selected="true"],html body [role="tab"][aria-selected="true"] *{
  color:#9C7420 !important;-webkit-text-fill-color:#9C7420 !important}
html body [role="tablist"]{opacity:1 !important}
</style>""", unsafe_allow_html=True)
PARTY.update(PALETTE[dark])
st.sidebar.markdown('<div class="brand">ElectionInsight<span>Outcome Intelligence</span></div>', unsafe_allow_html=True)
state = st.sidebar.selectbox("State", ["Uttarakhand", "Punjab"])
path = Path(__file__).parent / f"{state}_MaxAccuracy_Bayesian_Comparison.xlsx"
if path.exists():
    pred, src = read_xlsx(str(path)), f"Model output · {path.name}"
else:
    pred, src = demo(state), "DEMO DATA (run your model script to generate real results)"
pred = pred.copy()
pred["Pred_Future_Forecast"] = pred["Pred_Future_Forecast"].replace("N/A (Base Year)", np.nan)

mode = st.sidebar.radio("Model view", list(MODES))
year = st.sidebar.select_slider("Election year", sorted(pred.Election_Year.unique()), value=2022)
pcol, probcol = MODES[mode]
st.sidebar.caption(f"Source: {src}")

d = pred[pred.Election_Year == year].dropna(subset=[pcol]).copy()
hero = f'<div class="hero2"><h1>{state} · {year}</h1><p>Explainable Bayesian outcome prediction &nbsp;·&nbsp; {mode}</p></div><div class="stripe2"></div>'
st.markdown(hero, unsafe_allow_html=True)
if d.empty:
    st.warning("The locked forecast does not exist for the 2012 base year. Pick 2017 or 2022."); st.stop()

d["Region"] = d.AC_No.apply(lambda a: region(a, state))
d["Pred"], d["Conf"] = d[pcol], d[probcol]
d["OK"] = d.Party_Clean == d.Pred
d["Category"] = pd.cut(d.Conf, [0, 50, 70, 101], labels=["Highly uncertain", "Competitive", "Safe"])
n = len(d); maj = n // 2 + 1
act_c, pred_c = d.Party_Clean.value_counts(), d.Pred.value_counts()
lead = pred_c.idxmax()

c = st.columns(4)
acc_, cf_ = d.OK.mean() * 100, d.Conf.mean()
kpi(c[0], "Constituencies", "", "#FF9933", count=n, i=0, sub="assembly seats analysed")
kpi(c[1], "Seat-level accuracy", "", "#138808", count=int(acc_), suffix=f".{int(acc_ * 10) % 10}%", i=1, sub="seats predicted correctly")
kpi(c[2], "Avg. confidence", "", "#C9A227", count=int(cf_), suffix=f".{int(cf_ * 10) % 10}%", i=2, sub="mean win probability")
kpi(c[3], "Predicted lead", lead, pc(lead), i=3, sub=f'<b class="sn">{pred_c[lead]} seats</b> · ' + ("majority" if pred_c[lead] >= maj else "hung house"))
st.write("")

tabs = st.tabs(["Overview", "Accuracy", "Constituency", "Vote Flow", "Regions", "Confidence", "3D Skyline", "Export"])

# ---------------------------------------------------------------- overview
with tabs[0]:
    a, b = st.columns([3, 2])
    parties = sorted(set(act_c.index) | set(pred_c.index))
    fig = go.Figure()
    for name, ser, pat in (("Actual", act_c, ""), ("Predicted", pred_c, "/")):
        fig.add_bar(x=parties, y=[ser.get(p, 0) for p in parties], name=name,
                    marker=dict(color=[pc(p) for p in parties], pattern_shape=pat,
                                line=dict(color="#94a3b8", width=1)),
                    text=[ser.get(p, 0) for p in parties], textposition="outside")
    fig.add_hline(y=maj, line_dash="dash", line_color="#FFD166", annotation_text=f"Majority ({maj})")
    fig.update_layout(title="Seats: Actual (solid) vs Predicted (hatched)", barmode="group")
    a.plotly_chart(style(fig), width="stretch")
    pie = go.Figure(go.Pie(labels=pred_c.index, values=pred_c.values, hole=.6,
                           marker=dict(colors=[pc(p) for p in pred_c.index], line=dict(color="#0b1020", width=3))))
    pie.update_layout(title="Predicted seat share", annotations=[dict(text=f"{n}<br>seats", showarrow=False, font_size=20)])
    b.plotly_chart(style(pie), width="stretch")

# ---------------------------------------------------------------- accuracy
with tabs[1]:
    rows = []
    for y, g in pred.groupby("Election_Year"):
        rows.append(("80/20 CV", y, (g.Party_Clean == g.Pred_80_20_CV).mean() * 100))
        f = g.dropna(subset=["Pred_Future_Forecast"])
        if len(f):
            rows.append(("Locked Forecast", y, (f.Party_Clean == f.Pred_Future_Forecast).mean() * 100))
    acc = pd.DataFrame(rows, columns=["Model", "Year", "Accuracy %"])
    a, b = st.columns(2)
    f1 = px.bar(acc, x="Year", y="Accuracy %", color="Model", barmode="group", text_auto=".1f",
                color_discrete_sequence=["#FF9933", "#138808"], title="Accuracy by election year")
    f1.update_xaxes(type="category")
    a.plotly_chart(style(f1), width="stretch")
    ct = pd.crosstab(d.Party_Clean, d.Pred)
    f2 = px.imshow(ct, text_auto=True, color_continuous_scale="YlOrRd", title="Confusion matrix (rows = actual)",
                   labels=dict(x="Predicted", y="Actual"))
    b.plotly_chart(style(f2), width="stretch")
    rec = d.groupby("Party_Clean").OK.mean().mul(100).reset_index()
    f3 = px.bar(rec, x="Party_Clean", y="OK", color="Party_Clean", color_discrete_map=PARTY, text_auto=".0f",
                title="Recall per party (% of its real wins predicted)", labels=dict(OK="%", Party_Clean="Party"))
    st.plotly_chart(style(f3, 320), width="stretch")

# ---------------------------------------------------------------- constituency
with tabs[2]:
    f1c, f2c, f3c = st.columns(3)
    sel_p = f1c.multiselect("Predicted party", sorted(d.Pred.unique()), default=sorted(d.Pred.unique()))
    sel_r = f2c.multiselect("Region", sorted(d.Region.unique()), default=sorted(d.Region.unique()))
    minc = f3c.slider("Min confidence %", 0, 100, 0)
    t = d[d.Pred.isin(sel_p) & d.Region.isin(sel_r) & (d.Conf >= minc)]
    show = t[["AC_No", "AC_Name", "Region", "Prev_Winner", "Party_Clean", "Pred", "Conf", "Category", "OK"]]
    show.columns = ["AC", "Name", "Region", "Previous", "Actual", "Predicted", "Confidence %", "Category", "Correct"]
    st.dataframe(show, width="stretch", hide_index=True, height=300,
                 column_config={"Confidence %": st.column_config.ProgressColumn(min_value=0, max_value=100, format="%.1f"),
                                "Correct": st.column_config.CheckboxColumn()})
    if len(t):
        pick = st.selectbox("Deep-dive a constituency", t.AC_No.astype(str) + " – " + t.AC_Name.astype(str))
        r = t[t.AC_No == int(pick.split(" – ")[0])].iloc[0]
        g1, g2 = st.columns([2, 3])
        gauge = go.Figure(go.Indicator(mode="gauge+number", value=r.Conf, number={"suffix": "%"},
                                       title={"text": f"Predicted: {r.Pred}"},
                                       gauge=dict(axis=dict(range=[0, 100]), bar=dict(color=pc(r.Pred)),
                                                  steps=[dict(range=[0, 50], color="#3a1f2b"), dict(range=[50, 70], color="#3a3320"),
                                                         dict(range=[70, 100], color="#1f3a2b")])))
        g1.plotly_chart(style(gauge, 300), width="stretch")
        hist = pred[pred.AC_No == r.AC_No].sort_values("Election_Year")[["Election_Year", "Actual_Winner", "Pred_80_20_CV", "Pred_Future_Forecast"]]
        g2.markdown(f"**{r.AC_Name}** · {r.Region} · {'✅ correct' if r.OK else '❌ missed'} · actual **{r.Party_Clean}**")
        g2.dataframe(hist, hide_index=True, width="stretch")

# ---------------------------------------------------------------- vote flow
with tabs[3]:
    cols = [("Prev_Winner", "Previous"), ("Party_Clean", "Actual"), ("Pred", "Predicted")]
    labels, idx = [], {}
    for col, tag in cols:
        for p in sorted(d[col].dropna().unique()):
            idx[(tag, p)] = len(labels); labels.append(f"{p} ({tag})")
    s, tg, v, lc = [], [], [], []
    for (c1, t1), (c2, t2) in zip(cols, cols[1:]):
        for (x, y), k in d.groupby([c1, c2]).size().items():
            s.append(idx[(t1, x)]); tg.append(idx[(t2, y)]); v.append(int(k)); lc.append(rgba(pc(x) if pc(x) != "#FFFFFF" else "#cbd5e1"))
    node_c = [pc(l.split(" (")[0]) for l in labels]
    sk = go.Figure(go.Sankey(node=dict(label=labels, color=node_c, pad=18, thickness=18),
                             link=dict(source=s, target=tg, value=v, color=lc)))
    sk.update_layout(title="How seats flow: previous winner → actual → predicted")
    st.plotly_chart(style(sk, 520), width="stretch")

# ---------------------------------------------------------------- regions
with tabs[4]:
    long = pd.concat([d.groupby(["Region", "Party_Clean"]).size().reset_index(name="Seats").assign(Series="Actual").rename(columns={"Party_Clean": "Party"}),
                      d.groupby(["Region", "Pred"]).size().reset_index(name="Seats").assign(Series="Predicted").rename(columns={"Pred": "Party"})])
    fr = px.bar(long, x="Region", y="Seats", color="Party", facet_col="Series", color_discrete_map=PARTY,
                title="Seats by region", text_auto=True)
    fr.for_each_annotation(lambda a_: a_.update(text=a_.text.split("=")[-1]))
    st.plotly_chart(style(fr, 420), width="stretch")
    reg = d.groupby("Region").size()
    rp = d.groupby(["Region", "Pred"]).size()
    ids, lab, par, val, col, tip = [], [], [], [], [], []
    for r, v in reg.items():
        ids.append(r); lab.append(r); par.append(""); val.append(int(v)); col.append("#D4AF6A" if dark else "#EBD9A4")
        tip.append(f"<b>{r}</b><br>{v} seats in this region")
    for (r, p_), v in rp.items():
        ids.append(f"{r}|{p_}"); lab.append(p_); par.append(r); val.append(int(v)); col.append(pc(p_))
        tip.append(f"<b>{p_}</b> in {r}<br>{v} of {reg[r]} seats ({v / reg[r]:.0%})")
    sb = go.Figure(go.Sunburst(ids=ids, labels=lab, parents=par, values=val, branchvalues="total", customdata=tip,
                               marker=dict(colors=col, line=dict(color="#0B0F1A" if dark else "#F6F1E6", width=2.5)),
                               texttemplate="<b>%{label}</b><br>%{value}", hovertemplate="%{customdata}<extra></extra>",
                               insidetextfont=dict(color=[ink(c_) for c_ in col], size=15), hoverlabel=dict(font_size=15)))
    sb.update_layout(title="Predicted winners by region")
    piv = d.pivot_table(index="Region", columns="Pred", values="AC_No", aggfunc="count", fill_value=0)
    hm = px.imshow(piv, text_auto=True, aspect="auto", color_continuous_scale=(["#10162A", "#7A5C25", "#D4AF6A"] if dark else ["#FBF3DC", "#EBCB7A", "#C08A1E"]),
                   title="Predicted seats: region by party")
    hm.update_traces(hovertemplate="<b>%{x}</b> in %{y}<br>%{z} seats<extra></extra>")
    hm.update_layout(coloraxis_showscale=False, xaxis_title=None, yaxis_title=None)
    c1, c2 = st.columns([3, 2])
    c1.plotly_chart(style(sb, 520), width="stretch")
    c2.plotly_chart(style(hm, 520), width="stretch")
    rb = px.scatter(d, x="AC_No", y="Region", color="Pred", symbol="OK", color_discrete_map=PARTY, hover_name="AC_Name",
                    symbol_map={True: "circle", False: "x"}, title="Seat ribbon: every constituency, in order",
                    labels={"AC_No": "Constituency number", "Pred": "Predicted party", "OK": "Prediction correct"})
    rb.update_traces(marker=dict(size=15, line=dict(color="#0B0F1A", width=1)))
    st.plotly_chart(style(rb, 380), width="stretch")
    demo_cols = [c_ for c_ in ["Urban_PR", "Female_PR", "Hindu_PR", "Muslim_PR", "Sikh_PR", "Christian_PR"] if c_ in d.columns]
    if demo_cols:
        xc = st.selectbox("Demographic explorer (x-axis)", demo_cols)
        st.plotly_chart(style(px.scatter(d, x=xc, y="Conf", color="Pred", color_discrete_map=PARTY, hover_name="AC_Name",
                                         symbol="OK", title=f"{xc} vs model confidence")), width="stretch")

# ---------------------------------------------------------------- confidence
with tabs[5]:
    a, b = st.columns(2)
    hs = px.histogram(d, x="Conf", color="OK", nbins=20, barmode="overlay", opacity=.8,
                      color_discrete_map={True: "#22c55e", False: "#ef4444"}, title="Confidence: correct vs wrong predictions",
                      labels=dict(Conf="Confidence %", OK="Correct"))
    a.plotly_chart(style(hs), width="stretch")
    cat = d.groupby(["Category", "Pred"], observed=True).size().reset_index(name="Seats")
    cb = px.bar(cat, x="Category", y="Seats", color="Pred", color_discrete_map=PARTY, title="Safe / Competitive / Highly uncertain seats",
                category_orders={"Category": ["Safe", "Competitive", "Highly uncertain"]})
    b.plotly_chart(style(cb), width="stretch")
    st.plotly_chart(style(px.box(d, x="Pred", y="Conf", color="Pred", color_discrete_map=PARTY, points="all",
                                 hover_name="AC_Name", title="Confidence spread per party"), 360), width="stretch")

# ---------------------------------------------------------------- export
with tabs[7]:
    out = d.drop(columns=["Category"]).assign(Category=d.Category.astype(str))
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as w:
        out.to_excel(w, sheet_name="Selected_Year", index=False)
        acc.to_excel(w, sheet_name="Accuracy", index=False)
        pd.DataFrame({"Actual": act_c, "Predicted": pred_c}).fillna(0).astype(int).to_excel(w, sheet_name="Seat_Tally")
    st.download_button("Download Excel report", buf.getvalue(), f"{state}_{year}_dashboard_report.xlsx",
                       "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    st.download_button("Download CSV", out.to_csv(index=False), f"{state}_{year}.csv", "text/csv")
    st.dataframe(out, hide_index=True, width="stretch")


# ---------------------------------------------------------------- 3D landscape
with tabs[6]:
    st.markdown("Every column is a constituency, grouped by region. The taller the column, the more confident the model.")
    components.html(landscape_html(d, pc), height=670)

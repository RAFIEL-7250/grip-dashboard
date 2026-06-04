"""GRIP Performance Dashboard — Apple style, dual-dashboard, GPC categorization | v2.2 晴澈"""

import streamlit as st
import plotly.graph_objects as go
import json, os, pandas as pd
from collections import defaultdict
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

st.set_page_config(page_title="GRIP Performance", page_icon="●", layout="wide", initial_sidebar_state="expanded")

# ========== CSS ==========
st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
*{font-family:'Inter',-apple-system,sans-serif}
.stApp{background:#f5f5f7}
[data-testid="stSidebar"]{background:rgba(255,255,255,0.72);backdrop-filter:blur(40px) saturate(180%);-webkit-backdrop-filter:blur(40px) saturate(180%);border-right:1px solid rgba(0,0,0,0.08)}
[data-testid="stSidebar"] .stMarkdown,[data-testid="stSidebar"] label,[data-testid="stSidebar"] .stCaption{color:#86868b!important}
[data-testid="stSidebar"] h1,[data-testid="stSidebar"] h3,[data-testid="stSidebar"] h2{color:#1d1d1f!important;font-weight:600!important;font-size:0.8rem!important}
.stTextInput input{background:rgba(255,255,255,0.56)!important;backdrop-filter:blur(12px)!important;border:1px solid rgba(0,0,0,0.1)!important;color:#1d1d1f!important;border-radius:10px!important;padding:10px 14px!important}
.stTextInput input:focus{border-color:#0071e3!important;box-shadow:0 0 0 4px rgba(0,113,227,0.1)!important;outline:none!important}
.stTextInput input::placeholder{color:#aeaeb2!important}
[data-testid="stMultiSelect"] [data-baseweb="tag"]{background:rgba(0,113,227,0.08)!important;color:#0071e3!important;border-radius:6px!important;max-width:120px!important;font-size:0.7rem!important}
.streamlit-expanderHeader{background:rgba(255,255,255,0.56)!important;backdrop-filter:blur(12px)!important;border:1px solid rgba(0,0,0,0.06)!important;border-radius:14px!important;color:#1d1d1f!important}
[data-testid="stDataFrame"]{border:1px solid rgba(0,0,0,0.06)!important;border-radius:14px!important;overflow:hidden!important}
[data-testid="stDataFrame"] th{background:rgba(245,245,247,0.8)!important;color:#86868b!important;font-weight:500!important;font-size:0.75rem!important;text-transform:uppercase;letter-spacing:0.04em}
[data-testid="stDataFrame"] td{color:#1d1d1f!important;font-size:0.85rem!important}
.stCaption{color:#aeaeb2!important} hr{border-color:rgba(0,0,0,0.06)!important}
[data-testid="stMetric"]{background:transparent!important;border:none!important;box-shadow:none!important;padding:8px 0!important}
.streamlit-expanderHeader,[data-testid="stMultiSelect"] [data-baseweb="tag"],.stTextInput input{transition:all 0.2s ease!important}
[data-testid="stSidebar"]::-webkit-scrollbar{width:4px}
[data-testid="stSidebar"]::-webkit-scrollbar-track{background:transparent}
[data-testid="stSidebar"]::-webkit-scrollbar-thumb{background:rgba(0,0,0,0.12);border-radius:4px}
.stDownloadButton button{background:rgba(0,113,227,0.08)!important;color:#0071e3!important;border:1px solid rgba(0,113,227,0.2)!important;border-radius:10px!important;font-weight:500!important;transition:all 0.2s ease!important}
.stDownloadButton button:hover{background:rgba(0,113,227,0.14)!important;border-color:#0071e3!important}
div[data-testid="stRadio"] > div[role="radiogroup"]{gap:4px;background:rgba(0,0,0,0.04);border-radius:10px;padding:3px}
div[data-testid="stRadio"] label[data-baseweb="radio"]{border-radius:8px!important;padding:6px 14px!important;margin:0!important;font-size:0.8rem!important;font-weight:500!important;color:#86868b!important;transition:all 0.2s ease!important;border:none!important}
div[data-testid="stRadio"] label[data-baseweb="radio"]:has(input:checked){background:#fff!important;color:#1d1d1f!important;box-shadow:0 1px 3px rgba(0,0,0,0.1)!important}
div[data-testid="stRadio"] input[type="radio"]{display:none!important}
.comp-block{border:1px solid rgba(0,0,0,0.06)!important;border-radius:16px!important;padding:24px 28px!important;margin-bottom:24px!important;background:rgba(255,255,255,0.56)!important;backdrop-filter:blur(16px)!important;-webkit-backdrop-filter:blur(16px)!important}
</style>""", unsafe_allow_html=True)

# ========== PALETTE ==========
ACCENT='#0071e3'; T1='#1d1d1f'; T2='#86868b'; T3='#aeaeb2'
DANGER='#e07b5a'; SUCCESS='#4d9b6e'
BUDGET_FILL='rgba(0,113,227,0.06)'; BUDGET_LINE='#0071e3'
FILL_T3='rgba(0,113,227,0.22)'; LINE_T3='#0071e3'
FILL_T5='rgba(0,113,227,0.78)'; LINE_T5='#005bb5'

def pbase(**kw):
    b={'plot_bgcolor':'rgba(0,0,0,0)','paper_bgcolor':'rgba(0,0,0,0)',
       'font':{'color':T2,'family':'Inter','size':12},
       'xaxis':{'gridcolor':'rgba(0,0,0,0.05)','linecolor':'rgba(0,0,0,0.08)','zerolinecolor':'rgba(0,0,0,0.06)','tickfont':{'color':T3,'size':11}},
       'yaxis':{'gridcolor':'rgba(0,0,0,0.05)','linecolor':'rgba(0,0,0,0.08)','zerolinecolor':'rgba(0,0,0,0.06)','tickfont':{'color':T3,'size':11}}}
    b.update(kw); return b

def section_title(icon, text):
    st.markdown(f"""<div style="margin-top:28px;margin-bottom:6px;display:flex;align-items:center;gap:10px">
        <span style="font-size:1.2rem">{icon}</span>
        <span style="font-size:0.85rem;font-weight:700;color:#1d1d1f;letter-spacing:0.06em;text-transform:uppercase">{text}</span>
    </div>""", unsafe_allow_html=True)

def fmt_val(v):
    if abs(v)>=1000: return f"€{v/1000:.1f}M"
    return f"€{v:,.0f}k"

# ========== HELPERS ==========
def alloc_budget(F, dim_key, total_budget):
    """Allocate total Budget to each dim by T3 share. Returns {dim: budget_val}."""
    t3_by_dim=defaultdict(float)
    for p in F: t3_by_dim[p[dim_key]]+=p['T3']
    total=sum(t3_by_dim.values())
    if total<=0: return {}
    return {d: total_budget*(v/total) for d,v in t3_by_dim.items()}

def compute_comparison(F, dim_key, value_a_key, value_b_key, total_budget=None):
    agg_a=defaultdict(float); agg_b=defaultdict(float); agg_t3=defaultdict(float)
    for p in F:
        d=p[dim_key]
        if value_a_key=='T3': agg_a[d]+=p['T3']
        elif value_a_key=='T5': agg_a[d]+=p['T5']
        if value_b_key=='T3': agg_b[d]+=p['T3']
        elif value_b_key=='T5': agg_b[d]+=p['T5']
        agg_t3[d]+=p['T3']
    total_t3=sum(agg_t3.values())
    all_dims=sorted(set(list(agg_a.keys())+list(agg_b.keys())))
    results=[]
    for d in all_dims:
        va=total_budget*(agg_t3.get(d,0)/total_t3) if value_a_key=='budget' and total_budget and total_t3>0 else agg_a.get(d,0)
        vb=agg_b.get(d,0)
        delta=vb-va; delta_pct=(delta/va*100)if va>0.01 else(999 if vb>0.01 else 0)
        results.append({'dim':d,'value_a':round(va,2),'value_b':round(vb,2),'delta':round(delta,2),'delta_pct':round(delta_pct,1)})
    results.sort(key=lambda x:x['delta'])
    return results

def grouped_hbar_chart(categories, metric_data, height=340, margin_r=100):
    """Horizontal grouped bar chart. metric_data: [(label, values, fill, line), ...].
    Categories sorted ascending so largest appears at TOP of Plotly h-bar."""
    fig=go.Figure()
    for label,vals,fill,line in metric_data:
        fig.add_trace(go.Bar(name=label,y=categories,x=vals,orientation='h',
            text=[fmt_val(v)for v in vals],textposition='outside',
            marker_color=fill,marker_line_color=line,marker_line_width=1.2,
            textfont={'color':T1,'size':12}))
    fig.update_layout(**pbase(),barmode='group',height=height,showlegend=True,
        legend=dict(orientation='h',yanchor='top',y=1.02,xanchor='left',x=0,font={'color':T1,'size':12}),
        margin=dict(t=10,b=10,l=10,r=margin_r))
    return fig

def render_comparison_block(block_label, value_a_key, value_b_key, F, D, fill_a, line_a, fill_b, line_b):
    st.markdown(f"<div style='display:flex;align-items:center;gap:8px;margin-bottom:12px'><span style='font-size:1rem'>📊</span><span style='font-size:0.82rem;font-weight:700;color:#1d1d1f;letter-spacing:0.04em;text-transform:uppercase'>{block_label}</span></div>",unsafe_allow_html=True)
    dim_key=st.radio(f"{block_label}_dim",["Zone","Division","GPC"],horizontal=True,
                     key=f"dim_{block_label}",label_visibility="collapsed")
    dim_map={'Zone':'zone','Division':'division','GPC':'wg'}
    results=compute_comparison(F,dim_map[dim_key],value_a_key,value_b_key,
                               total_budget=D['summary']['budget']if value_a_key=='budget'else None)
    if not results: st.caption("No data for current filters."); return
    total_a=sum(r['value_a']for r in results); total_b=sum(r['value_b']for r in results)
    delta=total_b-total_a; delta_pct=(delta/total_a*100)if total_a>0.01 else 0
    label_a_display='Budget'if value_a_key=='budget'else value_a_key
    label_b_display=value_b_key
    c1,c2,c3,c4=st.columns(4)
    with c1: st.markdown(f"<div style='font-size:0.65rem;color:#86868b;text-transform:uppercase;letter-spacing:0.06em'>{label_a_display}</div><div style='font-size:1.5rem;font-weight:700;color:#1d1d1f'>€{total_a:,.0f}k</div>",unsafe_allow_html=True)
    with c2: st.markdown(f"<div style='font-size:0.65rem;color:#86868b;text-transform:uppercase;letter-spacing:0.06em'>{label_b_display}</div><div style='font-size:1.5rem;font-weight:700;color:#1d1d1f'>€{total_b:,.0f}k</div>",unsafe_allow_html=True)
    with c3:
        c=SUCCESS if delta>=0 else DANGER
        st.markdown(f"<div style='font-size:0.65rem;color:#86868b;text-transform:uppercase;letter-spacing:0.06em'>Δ</div><div style='font-size:1.5rem;font-weight:700;color:{c}'>€{delta:+,.0f}k</div>",unsafe_allow_html=True)
    with c4:
        c=SUCCESS if delta>=0 else DANGER
        st.markdown(f"<div style='font-size:0.65rem;color:#86868b;text-transform:uppercase;letter-spacing:0.06em'>Δ %</div><div style='font-size:1.5rem;font-weight:700;color:{c}'>{delta_pct:+.1f}%</div>",unsafe_allow_html=True)
    cats=[r['dim'][:18]for r in results]
    fig=go.Figure(data=[
        go.Bar(name=label_a_display,x=cats,y=[r['value_a']for r in results],
               marker_color=fill_a,marker_line_color=line_a,marker_line_width=1.5,
               text=[fmt_val(r['value_a'])for r in results],textposition='outside',textfont={'color':T1,'size':12}),
        go.Bar(name=label_b_display,x=cats,y=[r['value_b']for r in results],
               marker_color=fill_b,marker_line_color=line_b,marker_line_width=1.5,
               text=[fmt_val(r['value_b'])for r in results],textposition='outside',textfont={'color':T1,'size':12}),
    ])
    fig.update_layout(**pbase(),barmode='group',height=420,
        legend=dict(orientation='h',yanchor='top',y=1.02,xanchor='left',x=0,font={'color':T1,'size':12}),
        bargap=0.25,bargroupgap=0.08,margin=dict(t=10,b=10,l=10,r=10))
    st.plotly_chart(fig,use_container_width=True)
    df=pd.DataFrame(results)
    df.columns=[dim_key,f'{label_a_display} (k€)',f'{label_b_display} (k€)','Delta (k€)','Delta (%)']
    csv=df.to_csv(index=False)
    st.download_button(f"⬇ Download {block_label}",csv,f"grip_{block_label.lower().replace(' ','_')}.csv","text/csv",key=f"dl_{block_label}")

# ========== DATA ==========
@st.cache_data
def load():
    with open(os.path.join(os.path.dirname(__file__),'data_cache.json')) as f:
        return json.load(f)
D=load()

# ========== SIDEBAR ==========
with st.sidebar:
    st.markdown("""<div style="display:flex;align-items:center;gap:10px;margin-bottom:6px">
    <span style="font-size:1.4rem">🏪</span>
    <span style="font-size:1.15rem;font-weight:700;color:#1d1d1f;letter-spacing:-0.02em">GRIP Performance</span></div>
    <span style="color:#86868b;font-size:0.78rem;margin-left:34px">Retail & Promotion · T3 → T5</span>""",unsafe_allow_html=True)
    st.markdown("")
    dashboard_mode=st.radio("Dashboard",["📊 Performance","📈 Comparison"],horizontal=True,label_visibility="collapsed",key="dash_mode")
    st.markdown("")

    # --- Filters ---
    st.markdown("<span style='color:#1d1d1f;font-weight:600;font-size:0.82rem'>🔍 Filters</span>",unsafe_allow_html=True)
    sel_z=st.multiselect("Zones",D['filters']['zones'],default=D['filters']['zones'],key="z")
    sel_d=st.multiselect("Divisions",D['filters']['divisions'],default=D['filters']['divisions'],key="d")
    sel_w=st.multiselect("GPCs",D['filters']['wgs'],default=D['filters']['wgs'],key="w")
    sel_p=st.multiselect("Perf. Types",D['filters']['perf_types'],default=D['filters']['perf_types'],key="p")

    # --- Metric toggles ---
    st.markdown("<span style='color:#1d1d1f;font-weight:600;font-size:0.82rem'>📐 Metrics to Display</span>",unsafe_allow_html=True)
    mc1,mc2,mc3=st.columns(3)
    with mc1: show_budget=st.checkbox("Budget",value=True,key="m_b")
    with mc2: show_t3=st.checkbox("T3",value=True,key="m_t3")
    with mc3: show_t5=st.checkbox("T5",value=True,key="m_t5")
    if not(show_budget or show_t3 or show_t5):
        show_t5=True  # force at least one

    st.divider()
    st.markdown("<span style='color:#1d1d1f;font-weight:600;font-size:0.82rem'>🤖 AI Assistant</span>",unsafe_allow_html=True)
    ai_q=st.text_input("Ask about the data",placeholder="e.g. How is Europe performing? Which GPCs are growing?",key="ai_q",label_visibility="collapsed")
    st.divider()
    st.caption("3,223 rows · 901 variants")

# ========== FILTER ==========
def fp(pl):
    return [p for p in pl if p['zone']in sel_z and p['division']in sel_d and p['wg']in sel_w and p['perf_type']in sel_p]
F=fp(D['projects'])
FT3=sum(p['T3']for p in F); FT5=sum(p['T5']for p in F); FD=FT5-FT3
DB=FT5-D['summary']['budget']; L=sum(p['latest']for p in F)

# Pre-compute budget allocations
budget_by_zone=alloc_budget(F,'zone',D['summary']['budget'])
budget_by_div=alloc_budget(F,'division',D['summary']['budget'])
budget_by_wg=alloc_budget(F,'wg',D['summary']['budget'])

# ========== AI ==========
import requests

DEEPSEEK_API_KEY = os.environ.get('DEEPSEEK_API_KEY') or st.secrets.get('DEEPSEEK_API_KEY', None)
if not DEEPSEEK_API_KEY:
    st.sidebar.warning("⚠️ DEEPSEEK_API_KEY not set — AI assistant disabled")

if ai_q and F and DEEPSEEK_API_KEY:
    q=ai_q.lower()
    zd=defaultdict(lambda:{'T3':0,'T5':0})
    for p in F:zd[p['zone']]['T3']+=p['T3'];zd[p['zone']]['T5']+=p['T5']
    wd=defaultdict(lambda:{'T3':0,'T5':0})
    for p in F:wd[p['wg']]['T3']+=p['T3'];wd[p['wg']]['T5']+=p['T5']
    dd=defaultdict(lambda:{'T3':0,'T5':0})
    for p in F:dd[p['division']]['T3']+=p['T3'];dd[p['division']]['T5']+=p['T5']
    t10=[p for p in F if p['delta']<-0.01];t10.sort(key=lambda x:x['delta'])
    top_inc=sorted([p for p in F if p['delta']>0.01],key=lambda x:x['delta'],reverse=True)[:10]

    R=""; G=None
    matched=[]
    for z in D['filters']['zones']:
        if z.lower()in q:matched.append(('zone',z))
    for d in D['filters']['divisions']:
        if d.lower()in q:matched.append(('division',d))
    for w in D['filters']['wgs']:
        if w.lower()in q:matched.append(('wg',w))

    if matched:
        for typ,name in matched[:1]:
            sub=F;label=name
            if typ=='zone':sub=[p for p in sub if p['zone']==name]
            elif typ=='division':sub=[p for p in sub if p['division']==name]
            elif typ=='wg':sub=[p for p in sub if p['wg']==name]
            s3=sum(p['T3']for p in sub);s5=sum(p['T5']for p in sub);sd=s5-s3
            cd=defaultdict(lambda:{'T3':0,'T5':0})
            for p in sub:cd[p['country']]['T3']+=p['T3'];cd[p['country']]['T5']+=p['T5']
            cl=[(c,v['T5']-v['T3'],v['T3'],v['T5'])for c,v in cd.items()if abs(v['T3'])>0.1 or abs(v['T5'])>0.1]
            cl.sort(key=lambda x:x[1])
            pd_=[(p['project'],p['delta'],p['T3'],p['T5'],p['buyer'])for p in sub if p['delta']<-1]
            pd_.sort(key=lambda x:x[1])
            pi_=[(p['project'],p['delta'],p['T3'],p['T5'],p['buyer'])for p in sub if p['delta']>0.01]
            pi_.sort(key=lambda x:x[1],reverse=True)
            pct=sd/s3*100 if s3>0.01 else 0

            # Build data block
            data_block=f"""**{label}**
T3: **{s3:,.0f}k€** → T5: **{s5:,.0f}k€** (Δ: **{sd:+,.0f}k€**, {pct:+.1f}%)\n"""

            if cl:
                data_block+="**By Country**\n"
                for c,d,t3,t5 in cl[:8]:
                    data_block+=f"• {c}: T3={t3:,.0f} → T5={t5:,.0f} (Δ {d:+,.0f}k)\n"
            if pd_:
                data_block+="\n**Top Declines**\n"
                for pr,d,t3,t5,b in pd_[:5]:
                    data_block+=f"• {pr[:55]} [{b}]: {d:+,.0f}k\n"
            if pi_:
                data_block+="\n**Top Increases**\n"
                for pr,d,t3,t5,b in pi_[:5]:
                    data_block+=f"• {pr[:55]} [{b}]: {d:+,.0f}k\n"

            R=data_block

            if cl and len(cl)>1:
                G=go.Figure()
                cn=[c[0][:18]for c in cl[:8]];ds=[c[1]for c in cl[:8]];cs=[DANGER if d<0 else SUCCESS for d in ds]
                G.add_trace(go.Bar(x=ds,y=cn,orientation='h',marker_color=cs,marker_line_width=0,
                    text=[f"  {d:+,.0f}  "for d in ds],textposition='outside',textfont={'color':T1,'size':12}))
                G.update_layout(**pbase(),height=max(220,len(cl)*38),margin=dict(t=10,b=10,l=10,r=70))

        try:
            zone_sum="\n".join([f"- {z}: T3={zd[z]['T3']:,.0f}→T5={zd[z]['T5']:,.0f} (Δ={zd[z]['T5']-zd[z]['T3']:+,.0f}k)"for z in D['filters']['zones']])
            wg_sum="\n".join([f"- {w}: T3={wd[w]['T3']:,.0f}→T5={wd[w]['T5']:,.0f} (Δ={wd[w]['T5']-wd[w]['T3']:+,.0f}k)"for w in D['filters']['wgs']])
            div_sum="\n".join([f"- {d}: T3={dd[d]['T3']:,.0f}→T5={dd[d]['T5']:,.0f} (Δ={dd[d]['T5']-dd[d]['T3']:+,.0f}k)"for d in D['filters']['divisions']])
            inc_items="\n".join([f"- {p['project'][:50]}: Δ={p['delta']:+,.0f}k (+{p['delta_pct']}%)"for p in top_inc[:5]])
            dec_items="\n".join([f"- {p['project'][:50]}: Δ={p['delta']:+,.0f}k ({p['delta_pct']}%)"for p in t10[:8]])
            ctx=f"""You are a GRIP Performance data analyst. Answer the user's question concisely in well-formatted Markdown.

**FORMAT REQUIREMENTS:**
1. Start with a **1-sentence overview** of the overall picture (include key numbers).
2. Then use **bullet points** for detailed findings — one bullet per insight.
3. **ALWAYS include BOTH positive and negative findings** — never only show declines. Highlight what's working well AND what needs attention.
4. Keep each bullet short (1 line). Use bold for key numbers.
5. No greetings, no sign-offs.

**DATA:**
{name} detail: T3={s3:,.0f}k → T5={s5:,.0f}k (Δ={sd:+,.0f}k, {pct:+.1f}%)
All zones:
{zone_sum}
All GPCs:
{wg_sum}
Divisions:
{div_sum}
Growing projects:
{inc_items}
Declining projects:
{dec_items}

User question: {ai_q}"""
            resp=requests.post(
                "https://api.deepseek.com/v1/chat/completions",
                headers={"Authorization":f"Bearer {DEEPSEEK_API_KEY}","Content-Type":"application/json"},
                json={"model":"deepseek-chat","messages":[{"role":"user","content":ctx}],"max_tokens":300,"temperature":0.3},
                timeout=10
            )
            if resp.status_code==200:
                insight=resp.json()['choices'][0]['message']['content']
                R+="\n\n---\n💡 **AI Insight**\n\n"+insight
        except:
            pass
    else:
        zone_sum="\n".join([f"- {z}: T3={zd[z]['T3']:,.0f}k → T5={zd[z]['T5']:,.0f}k (Δ={zd[z]['T5']-zd[z]['T3']:+,.0f}k)"for z in D['filters']['zones']])
        wg_sum="\n".join([f"- {w}: T3={wd[w]['T3']:,.0f}k → T5={wd[w]['T5']:,.0f}k (Δ={wd[w]['T5']-wd[w]['T3']:+,.0f}k)"for w in D['filters']['wgs']])
        div_sum="\n".join([f"- {d}: T3={dd[d]['T3']:,.0f}k → T5={dd[d]['T5']:,.0f}k (Δ={dd[d]['T5']-dd[d]['T3']:+,.0f}k)"for d in D['filters']['divisions']])
        inc_items="\n".join([f"- {p['project'][:55]}: Δ={p['delta']:+,.0f}k (+{p['delta_pct']}%)"for p in top_inc[:8]])
        dec_items="\n".join([f"- {p['project'][:55]}: Δ={p['delta']:+,.0f}k ({p['delta_pct']}%)"for p in t10[:8]])

        ctx=f"""You are a GRIP Performance data analyst. Answer the user's question concisely in well-formatted Markdown.

**FORMAT REQUIREMENTS:**
1. Start with a **1-sentence overview** of the overall picture (key metrics).
2. Then use **bullet points** for findings — one insight per bullet.
3. **MUST include BOTH positive and negative findings.** Highlight growth areas AND concerns.
4. Keep bullets short and scannable. Use **bold** for key numbers.
5. No greetings, no sign-offs.

**DATA:**
Overview: Budget {D['summary']['budget']:,}k€ | T3 {FT3:,.0f}k€ | T5 {FT5:,.0f}k€ | T5-T3 Δ {FD:+,.0f}k€ | T5-Budget Δ {DB:+,.0f}k€
Zones:
{zone_sum}
GPCs:
{wg_sum}
Divisions:
{div_sum}
Growing projects:
{inc_items}
Declining projects:
{dec_items}

Question: {ai_q}"""
        try:
            resp=requests.post(
                "https://api.deepseek.com/v1/chat/completions",
                headers={"Authorization":f"Bearer {DEEPSEEK_API_KEY}","Content-Type":"application/json"},
                json={"model":"deepseek-chat","messages":[{"role":"user","content":ctx}],"max_tokens":400,"temperature":0.3},
                timeout=15
            )
            if resp.status_code==200:
                R=resp.json()['choices'][0]['message']['content']
            else:
                R=f"⚠️ AI unavailable (status {resp.status_code})"
        except Exception as e:
            R=f"⚠️ Query failed: {str(e)[:80]}"

    if R:
        with st.sidebar:
            with st.expander(f"📊 {ai_q[:35]}...",expanded=True):
                st.markdown(R)
                if G:st.plotly_chart(G, use_container_width=True)

# ========== HEADER ==========
subtitle_text="Performance Overview" if dashboard_mode=="📊 Performance" else "Difference Analysis · Budget ↔ T3/T5"
cT,cD=st.columns([3,1])
with cT:
    st.markdown(f"<div style='display:flex;align-items:center;gap:12px'><span style='font-size:1.6rem'>🏪</span><div><div style='font-size:1.8rem;font-weight:700;color:#1d1d1f;letter-spacing:-0.04em;line-height:1.1'>Retail & Promotion</div><div style='font-size:0.92rem;color:#86868b;font-weight:400;margin-top:2px'>{subtitle_text}</div></div></div>",unsafe_allow_html=True)
with cD:
    st.markdown(f"<div style='text-align:right;padding-top:8px'><div style='font-size:0.7rem;color:#aeaeb2;text-transform:uppercase;letter-spacing:0.06em'>Data as of</div><div style='font-size:0.9rem;color:#1d1d1f;font-weight:500'>{datetime.now().strftime('%B %Y')}</div></div>",unsafe_allow_html=True)

if not F:
    st.warning("⚠️ No projects match the current filters. Try adjusting your selection in the sidebar.")
    st.stop()

# ===================================================================
# DASHBOARD 1 — Performance
# ===================================================================
if dashboard_mode=="📊 Performance":
    # Determine primary sort metric for Top projects
    primary_metric='T5'if show_t5 else('T3'if show_t3 else'budget')

    # ========== KPI ==========
    st.markdown("<br>",unsafe_allow_html=True)
    kpi_items=[]
    if show_budget: kpi_items.append(('Budget (B26)',f"€{D['summary']['budget']:,}k"))
    if show_t3: kpi_items.append(('T3',f"€{FT3:,.0f}k"))
    if show_t5: kpi_items.append(('T5',f"€{FT5:,.0f}k"))
    kpi_items.append(('Latest Forecast',f"€{L:,.0f}k"))
    kpi_items.append(('Projects',str(len(F))))
    cols=st.columns(len(kpi_items))
    for i,(label,val) in enumerate(kpi_items):
        with cols[i]:
            st.markdown(f"<div style='font-size:0.7rem;color:#86868b;text-transform:uppercase;letter-spacing:0.06em;margin-bottom:2px'>{label}</div><div style='font-size:2rem;font-weight:700;color:#1d1d1f'>{val}</div>",unsafe_allow_html=True)
    st.markdown("<br>",unsafe_allow_html=True)

    # ========== ROW 1: Performance by Zone ==========
    section_title("📈", "PERFORMANCE BY ZONE")
    zd=defaultdict(lambda:{'T3':0,'T5':0})
    for p in F:zd[p['zone']]['T3']+=p['T3'];zd[p['zone']]['T5']+=p['T5']
    zo=[z for z in D['filters']['zones']if z in zd]
    # Sort ascending so largest bar appears at top (vertical bar: ascending = smallest first on x-axis)
    # For vertical grouped bar, x-axis goes left→right, so we sort by T5 ascending for cleaner look
    zo_sorted=sorted(zo,key=lambda z:zd[z].get('T5',0))

    bar_data=[]
    if show_budget: bar_data.append(('Budget',[budget_by_zone.get(z,0)for z in zo_sorted],BUDGET_FILL,BUDGET_LINE))
    if show_t3: bar_data.append(('T3',[zd[z]['T3']for z in zo_sorted],FILL_T3,LINE_T3))
    if show_t5: bar_data.append(('T5',[zd[z]['T5']for z in zo_sorted],FILL_T5,LINE_T5))

    if bar_data:
        fig=go.Figure()
        for label,vals,fill,line in bar_data:
            fig.add_trace(go.Bar(name=label,x=zo_sorted,y=vals,
                marker_color=fill,marker_line_color=line,marker_line_width=1.5,
                text=[fmt_val(v)for v in vals],textposition='outside',textfont={'color':T1,'size':12}))
        fig.update_layout(**pbase(),barmode='group',height=480,
            legend=dict(orientation='h',yanchor='top',y=1.04,xanchor='left',x=0,font={'color':T1,'size':12}),
            bargap=0.25,bargroupgap=0.08,margin=dict(t=10,b=10,l=10,r=10))
        st.plotly_chart(fig,use_container_width=True)

    # ========== ROW 2: Performance by GPC + Division ==========
    r2ta,r2tb=st.columns(2)
    with r2ta: section_title("🏗️", "PERFORMANCE BY GPC")
    with r2tb: section_title("🏢", "PERFORMANCE BY DIVISION")
    r2a,r2b=st.columns(2)

    with r2a:
        wd=defaultdict(lambda:{'T3':0,'T5':0})
        for p in F:wd[p['wg']]['T3']+=p['T3'];wd[p['wg']]['T5']+=p['T5']
        ws=sorted(wd.keys(),key=lambda w:wd[w].get('T5',0))  # ascending → largest at TOP
        wg_bar_data=[]
        if show_budget: wg_bar_data.append(('Budget',[budget_by_wg.get(w,0)for w in ws],BUDGET_FILL,BUDGET_LINE))
        if show_t3: wg_bar_data.append(('T3',[wd[w]['T3']for w in ws],FILL_T3,LINE_T3))
        if show_t5: wg_bar_data.append(('T5',[wd[w]['T5']for w in ws],FILL_T5,LINE_T5))
        if wg_bar_data:
            cats=[w[:22]for w in ws]
            st.plotly_chart(grouped_hbar_chart(cats,wg_bar_data,height=320,margin_r=100),use_container_width=True)

    with r2b:
        dd=defaultdict(lambda:{'T3':0,'T5':0})
        for p in F:dd[p['division']]['T3']+=p['T3'];dd[p['division']]['T5']+=p['T5']
        ds=sorted(dd.keys(),key=lambda d:dd[d].get('T5',0))  # ascending → largest at TOP
        div_bar_data=[]
        if show_budget: div_bar_data.append(('Budget',[budget_by_div.get(d,0)for d in ds],BUDGET_FILL,BUDGET_LINE))
        if show_t3: div_bar_data.append(('T3',[dd[d]['T3']for d in ds],FILL_T3,LINE_T3))
        if show_t5: div_bar_data.append(('T5',[dd[d]['T5']for d in ds],FILL_T5,LINE_T5))
        if div_bar_data:
            cats=[d[:22]for d in ds]
            st.plotly_chart(grouped_hbar_chart(cats,div_bar_data,height=320,margin_r=100),use_container_width=True)

    # ========== ROW 3: Top 10 Master Projects ==========
    section_title("🏆", "TOP 10 MASTER PROJECTS")
    mp_agg=defaultdict(lambda:{'T3':0,'T5':0,'buyer':''})
    for p in F:
        mp=p['master_project']if p['master_project']else p['project']
        mp_agg[mp]['T3']+=p['T3'];mp_agg[mp]['T5']+=p['T5']
        if not mp_agg[mp]['buyer']: mp_agg[mp]['buyer']=p['buyer']

    # Sort by chosen primary metric, ascending (largest at top in hbar)
    if primary_metric=='budget':
        # For budget sorting, we use T3 share as proxy for budget allocation
        top_mps=sorted(mp_agg.items(),key=lambda x:x[1]['T3'])[-10:]
    else:
        top_mps=sorted(mp_agg.items(),key=lambda x:x[1][primary_metric])[-10:]

    mp_names=[f"{n[:45]}"for n,_ in top_mps]

    mp_bar_data=[]
    metric_key_map={'Budget':None,'T3':'T3','T5':'T5'}
    if show_budget:
        # Budget by master project: proportional to T3
        total_mp_t3=sum(v['T3']for _,v in top_mps)
        mp_budget=[D['summary']['budget']*(v['T3']/total_mp_t3)if total_mp_t3>0 else 0 for _,v in top_mps]
        mp_bar_data.append(('Budget',mp_budget,BUDGET_FILL,BUDGET_LINE))
    if show_t3: mp_bar_data.append(('T3',[v['T3']for _,v in top_mps],FILL_T3,LINE_T3))
    if show_t5: mp_bar_data.append(('T5',[v['T5']for _,v in top_mps],FILL_T5,LINE_T5))

    if mp_bar_data:
        buyer_labels=[v['buyer']for _,v in top_mps]
        fig=go.Figure()
        for label,vals,fill,line in mp_bar_data:
            fig.add_trace(go.Bar(name=label,y=mp_names,x=vals,orientation='h',
                text=[f"  {fmt_val(v)} · {b}  "for v,b in zip(vals,buyer_labels)],
                textposition='outside',marker_color=fill,marker_line_color=line,marker_line_width=1,
                opacity=0.9,textfont={'color':T1,'size':11}))
        fig.update_layout(**pbase(),height=400,showlegend=True,
            legend=dict(orientation='h',yanchor='top',y=1.02,xanchor='left',x=0,font={'color':T1,'size':12}),
            margin=dict(t=10,b=10,l=10,r=220))
        st.plotly_chart(fig,use_container_width=True)

    # ========== TABLE ==========
    section_title("📊", "ALL PROJECTS")
    pdf=pd.DataFrame([{
        'Master Project':(p['master_project']if p['master_project']else p['project'])[:50],
        'Project':p['project'][:50],'Zone':p['zone'],
        'Division':p['division'],'GPC':p['wg'],'Type':p['perf_type'][:30],
        'Buyer':p['buyer'],'Status':p['status'],
        'T3 (k€)':round(p['T3'],1),'T5 (k€)':round(p['T5'],1),
    }for p in F])
    pdf=pdf.sort_values('T5 (k€)',ascending=False)
    all_cols=list(pdf.columns)
    visible_cols=st.multiselect("Columns to display",all_cols,default=all_cols,key="vis_cols")
    csv=pdf.to_csv(index=False)
    st.download_button("⬇ Download CSV",csv,"grip_performance_data.csv","text/csv",key="dl_perf")
    st.dataframe(pdf[visible_cols]if visible_cols else pdf,use_container_width=True,hide_index=True,height=350)

# ===================================================================
# DASHBOARD 2 — Comparison
# ===================================================================
else:
    # ========== KPI WITH DELTAS ==========
    st.markdown("<br>",unsafe_allow_html=True)
    c1,c2,c3,c4=st.columns(4)
    with c1:
        c=SUCCESS if FD>=0 else DANGER
        st.markdown(f"<div style='font-size:0.7rem;color:#86868b;text-transform:uppercase;letter-spacing:0.06em;margin-bottom:2px'>T3 → T5 Δ</div><div style='font-size:2rem;font-weight:700;color:{c}'>€{FD:+,.0f}k</div><div style='font-size:0.85rem;font-weight:600;color:{c};margin-top:2px'>{FD/FT3*100:+.1f}% vs T3</div>",unsafe_allow_html=True)
    with c2:
        c=SUCCESS if DB>=0 else DANGER
        st.markdown(f"<div style='font-size:0.7rem;color:#86868b;text-transform:uppercase;letter-spacing:0.06em;margin-bottom:2px'>T5 vs Budget Δ</div><div style='font-size:2rem;font-weight:700;color:{c}'>€{DB:+,.0f}k</div><div style='font-size:0.85rem;font-weight:600;color:{c};margin-top:2px'>{DB/D['summary']['budget']*100:+.1f}%</div>",unsafe_allow_html=True)
    with c3:
        st.markdown(f"<div style='font-size:0.7rem;color:#86868b;text-transform:uppercase;letter-spacing:0.06em;margin-bottom:2px'>T3 Total</div><div style='font-size:2rem;font-weight:700;color:#1d1d1f'>€{FT3:,.0f}k</div>",unsafe_allow_html=True)
    with c4:
        st.markdown(f"<div style='font-size:0.7rem;color:#86868b;text-transform:uppercase;letter-spacing:0.06em;margin-bottom:2px'>T5 Total</div><div style='font-size:2rem;font-weight:700;color:#1d1d1f'>€{FT5:,.0f}k</div>",unsafe_allow_html=True)
    st.markdown("<br>",unsafe_allow_html=True)

    # ========== WATERFALL ==========
    section_title("🌊", "WATERFALL  T3 → T5")
    wf=D['waterfall']
    fig=go.Figure(go.Waterfall(name="T3→T5",orientation="v",
        measure=["absolute","relative","relative","relative","total"],
        x=["T3",f"Removed<br>({wf['removed']['count']})",f"Added<br>({wf['added']['count']})",f"Reduced<br>({wf['reduced']['count']})","T5"],
        y=[wf['t3_total'],-wf['removed']['value'],wf['added']['value'],-abs(wf['reduced']['value']),wf['t3_total']+wf['net_change']],
        text=[f"€{wf['t3_total']:,.0f}k",f"-€{wf['removed']['value']:,.0f}k",f"+€{wf['added']['value']:,.0f}k",f"-€{abs(wf['reduced']['value']):,.0f}k",f"€{wf['t3_total']+wf['net_change']:,.0f}k"],
        decreasing={"marker":{"color":DANGER,"line":{"width":0}}},
        increasing={"marker":{"color":SUCCESS,"line":{"width":0}}},
        totals={"marker":{"color":ACCENT,"line":{"color":ACCENT,"width":1}}},
        textfont={"color":T1,"size":13}))
    fig.update_layout(**pbase(),height=460,showlegend=False,margin=dict(t=10,b=10,l=10,r=10))
    st.plotly_chart(fig,use_container_width=True)

    # ========== MODULE SELECTOR ==========
    st.markdown("<br>",unsafe_allow_html=True)
    st.markdown("<div style='font-size:0.78rem;color:#86868b;text-transform:uppercase;letter-spacing:0.06em;margin-bottom:8px'>📋 Comparison Modules</div>",unsafe_allow_html=True)
    cb1,cb2,cb3=st.columns(3)
    with cb1: show_bvt3=st.checkbox("💰 Budget vs T3",value=True,key="cb_bvt3")
    with cb2: show_bvt5=st.checkbox("📊 Budget vs T5",value=True,key="cb_bvt5")
    with cb3: show_t3vt5=st.checkbox("📈 T3 vs T5",value=True,key="cb_t3vt5")

    if show_bvt3:
        with st.container():
            st.markdown("<div class='comp-block'>",unsafe_allow_html=True)
            render_comparison_block("Budget vs T3","budget","T3",F,D,BUDGET_FILL,BUDGET_LINE,FILL_T3,LINE_T3)
            st.markdown("</div>",unsafe_allow_html=True)
    if show_bvt5:
        with st.container():
            st.markdown("<div class='comp-block'>",unsafe_allow_html=True)
            render_comparison_block("Budget vs T5","budget","T5",F,D,BUDGET_FILL,BUDGET_LINE,FILL_T5,LINE_T5)
            st.markdown("</div>",unsafe_allow_html=True)
    if show_t3vt5:
        with st.container():
            st.markdown("<div class='comp-block'>",unsafe_allow_html=True)
            render_comparison_block("T3 vs T5","T3","T5",F,D,FILL_T3,LINE_T3,FILL_T5,LINE_T5)
            st.markdown("</div>",unsafe_allow_html=True)

    # ========== HEATMAP ==========
    section_title("🗺️", "ZONE × GPC  DELTA HEATMAP")
    hd=defaultdict(lambda:defaultdict(float))
    for p in F:hd[p['zone']][p['wg']]+=p['delta']
    wl=D['filters']['wgs'];zl=D['filters']['zones']
    hmz=[[round(hd[z].get(w,0),1)for z in zl]for w in wl]
    hmt=[[f"{v:+,.0f}"for v in r]for r in hmz]
    fig=go.Figure(data=go.Heatmap(z=hmz,x=zl,y=wl,text=hmt,texttemplate="%{text}",
        colorscale=[[0,'#e8a090'],[0.25,'#f0c8b8'],[0.5,'#e8e8e8'],[0.75,'#b8d8c0'],[1,'#70b880']],
        zmid=0,textfont={"size":13,"color":T1},xgap=3,ygap=3,showscale=False))
    fig.update_layout(**pbase(),height=310,xaxis_side='top',margin=dict(t=10,b=10,l=10,r=10))
    st.plotly_chart(fig,use_container_width=True)

    # ========== TOP DECLINES + TOP INCREASES ==========
    r4ta,r4tb=st.columns(2)
    with r4ta: section_title("📉", "TOP PROJECT DECLINES")
    with r4tb: section_title("📈", "TOP PROJECT INCREASES")
    r4a,r4b=st.columns(2)

    with r4a:
        td=[p for p in F if p['delta']<-0.01];td.sort(key=lambda x:x['delta']);td=td[:8]
        td_rev=list(reversed(td))  # plotly hbar: first at bottom, so reverse for largest decline at top
        fig=go.Figure()
        for p in td_rev:
            fig.add_trace(go.Bar(y=[f"{p['zone'][:3]} / {p['project'][:45]}"],x=[p['delta']],orientation='h',
                text=f"  {p['delta']:+,.0f}k · {p['buyer']}  ",textposition='outside',
                marker_color=DANGER,marker_line_width=0,opacity=0.85,textfont={'color':T1,'size':11}))
        fig.update_layout(**pbase(),height=340,showlegend=False,margin=dict(t=10,b=10,l=10,r=200))
        st.plotly_chart(fig,use_container_width=True)

    with r4b:
        ti=[p for p in F if p['delta']>0.01];ti.sort(key=lambda x:x['delta']);ti=ti[-8:]  # ascending, last 8 = largest
        # ti is ascending, so in hbar: smallest at bottom, largest at top ✅
        fig=go.Figure()
        for p in ti:
            fig.add_trace(go.Bar(y=[f"{p['zone'][:3]} / {p['project'][:45]}"],x=[p['delta']],orientation='h',
                text=f"  {p['delta']:+,.0f}k · {p['buyer']}  ",textposition='outside',
                marker_color=SUCCESS,marker_line_width=0,opacity=0.85,textfont={'color':T1,'size':11}))
        fig.update_layout(**pbase(),height=340,showlegend=False,margin=dict(t=10,b=10,l=10,r=200))
        st.plotly_chart(fig,use_container_width=True)

# ========== FOOTER ==========
st.divider()
st.caption("Frosted glass · Apple-inspired · GRIP Performance v2.3 — 晴澈")

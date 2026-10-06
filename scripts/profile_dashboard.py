#!/usr/bin/env python3
import datetime, html, json, os, re, subprocess, sys
import requests
from bs4 import BeautifulSoup

USER = os.environ.get("GH_PROFILE_USER", "JuliaRomeira")
NAME = os.environ.get("PROFILE_NAME", "Júlia Danieli Romera Lage")
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_DIR = os.path.join(ROOT, "data")
os.makedirs(DATA_DIR, exist_ok=True)

BG="#0d1117"; BG2="#111722"; TILE="#161b22"; FRAME="#30363d"
MUTED="#7d8590"; TEXT="#e6edf3"; GREEN="#39d353"; BAR="#26a641"; CYAN="#22d3ee"
PALETTE=["#161b22","#0e4429","#006d32","#26a641","#39d353"]

def fetch_days():
    url=f"https://github.com/users/{USER}/contributions"
    r=requests.get(url,headers={"User-Agent":"profile-readme-bot/1.0"},timeout=30)
    r.raise_for_status()
    soup=BeautifulSoup(r.text,"html.parser")
    days=[]
    for td in soup.select("td.ContributionCalendar-day"):
        date=td.get("data-date")
        if not date: continue
        tid=td.get("id")
        tip=soup.find("tool-tip",attrs={"for":tid}) if tid else None
        t=tip.get_text(strip=True) if tip else ""
        m=re.match(r"(\d+)",t)
        count=0 if re.search("no contributions",t,re.I) else (int(m.group(1)) if m else 0)
        days.append({"date":date,"count":count,"level":int(td.get("data-level") or 0)})
    days.sort(key=lambda d:d["date"])
    if not days: raise RuntimeError("Nenhum dado de contribuicao encontrado.")
    return days

def streaks(days):
    idx=len(days)-1
    if days[idx]["count"]==0: idx-=1
    cur=0
    while idx>=0 and days[idx]["count"]>0:
        cur+=1; idx-=1
    longest=run=0
    for d in days:
        if d["count"]>0:
            run+=1; longest=max(longest,run)
        else: run=0
    return cur,longest

def build_data(days):
    total=sum(d["count"] for d in days)
    active=sum(1 for d in days if d["count"]>0)
    best=max(days,key=lambda d:d["count"])
    cur,longest=streaks(days)
    monthly={}
    for d in days:
        monthly[d["date"][:7]]=monthly.get(d["date"][:7],0)+d["count"]
    return {
      "username":USER,"generated_at":datetime.datetime.utcnow().isoformat()+"Z",
      "total":total,"active_days":active,"current_streak":cur,"longest_streak":longest,
      "best_day":best,"monthly":[{"month":k,"total":v} for k,v in sorted(monthly.items())],
      "days":days
    }

def esc(s): return html.escape(str(s))

def heatmap(data):
    days=data["days"]
    first=datetime.date.fromisoformat(days[0]["date"])
    pad=(first.weekday()+1)%7
    cells=[None]*pad+days
    cols=(len(cells)+6)//7
    cell,gap,step=12,3,15
    left,top=42,54
    W=left+cols*step+20; H=190
    out=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="ui-monospace,SFMono-Regular,Menlo,Consolas,monospace">',
         '<style>@keyframes pop{0%{opacity:0;transform:translateY(-5px)}100%{opacity:1;transform:translateY(0)}}.c{opacity:0;animation:pop .35s ease-out both}@media(prefers-reduced-motion:reduce){.c{opacity:1!important;animation:none!important}}</style>',
         f'<rect width="{W}" height="{H}" rx="12" fill="{BG}"/><rect x=".5" y=".5" width="{W-1}" height="{H-1}" rx="12" fill="none" stroke="{FRAME}"/>']
    for i,c in enumerate(["#ff5f56","#ffbd2e","#27c93f"]):
        out.append(f'<circle cx="{18+i*16}" cy="16" r="5" fill="{c}"/>')
    out.append(f'<text x="{W/2}" y="20" text-anchor="middle" fill="{MUTED}" font-size="12">{USER.lower()}@github: ~/contributions --graph</text>')
    months=set()
    for i,d in enumerate(cells):
        if not d: continue
        col=i//7; row=i%7
        x=left+col*step; y=top+row*step
        lvl=max(0,min(4,int(d.get("level",0))))
        delay=(col*.018+row*.035)
        out.append(f'<rect class="c" style="animation-delay:{delay:.3f}s" x="{x}" y="{y}" width="{cell}" height="{cell}" rx="2" fill="{PALETTE[lvl]}"><title>{esc(d["date"])}: {d["count"]}</title></rect>')
        dt=datetime.date.fromisoformat(d["date"])
        key=(dt.year,dt.month)
        if dt.day<=7 and key not in months:
            months.add(key); out.append(f'<text x="{x}" y="46" fill="{MUTED}" font-size="9">{dt.strftime("%b")}</text>')
    for r,n in [(1,"Mon"),(3,"Wed"),(5,"Fri")]:
        out.append(f'<text x="12" y="{top+r*step+10}" fill="{MUTED}" font-size="9">{n}</text>')
    out.append(f'<text x="{left}" y="178" fill="{GREEN}" font-size="12" font-weight="700">{data["total"]:,}</text>')
    out.append(f'<text x="{left+52}" y="178" fill="{MUTED}" font-size="11">contribuições no último ano</text></svg>')
    return "".join(out)

def stats_svg(data):
    W,H=840,880; pad=20; gap=16; tw=(W-pad*2-gap)/2; th=150
    tiles=[
      ("sequência atual",data["current_streak"]," dias"),
      ("maior sequência",data["longest_streak"]," dias"),
      ("contribuições",data["total"],""),
      ("dias ativos",data["active_days"],""),
      ("melhor dia",data["best_day"]["count"],""),
      ("média / dia ativo",round(data["total"]/data["active_days"],1) if data["active_days"] else 0,"")
    ]
    out=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="ui-monospace,SFMono-Regular,Menlo,Consolas,monospace">',
         '<style>@keyframes in{from{opacity:0;transform:translateY(12px)}to{opacity:1;transform:translateY(0)}}.t{opacity:0;animation:in .45s ease-out both}@media(prefers-reduced-motion:reduce){.t{opacity:1!important;animation:none!important}}</style>',
         f'<rect width="{W}" height="{H}" rx="12" fill="{BG}"/><rect x=".5" y=".5" width="{W-1}" height="{H-1}" rx="12" fill="none" stroke="{FRAME}"/>']
    for i,c in enumerate(["#ff5f56","#ffbd2e","#27c93f"]): out.append(f'<circle cx="{20+i*16}" cy="16" r="5" fill="{c}"/>')
    out.append(f'<text x="{W/2}" y="20" text-anchor="middle" fill="{MUTED}" font-size="12">{USER.lower()}@github: ~$ ./stats.sh</text>')
    for i,(label,val,suf) in enumerate(tiles):
        col,row=i%2,i//2; x=pad+col*(tw+gap); y=54+row*(th+gap)
        out.append(f'<g class="t" style="animation-delay:{i*.12:.2f}s"><rect x="{x}" y="{y}" width="{tw}" height="{th}" rx="10" fill="{TILE}" stroke="{FRAME}"/><text x="{x+24}" y="{y+40}" fill="{MUTED}" font-size="21">$ {esc(label)}</text><text x="{x+24}" y="{y+102}" fill="{GREEN if i==0 else TEXT}" font-size="50" font-weight="700">{esc(val)}<tspan fill="{MUTED}" font-size="22">{esc(suf)}</tspan></text></g>')
    monthly=data["monthly"][-12:]
    y0=570; chart_h=245
    out.append(f'<rect x="{pad}" y="{y0}" width="{W-pad*2}" height="{chart_h}" rx="10" fill="{TILE}" stroke="{FRAME}"/><text x="{pad+24}" y="{y0+40}" fill="{MUTED}" font-size="21">$ contribuições / mês</text>')
    peak=max([m["total"] for m in monthly] or [1]); slot=(W-pad*2-48)/max(1,len(monthly))
    base=y0+195
    for i,m in enumerate(monthly):
        bh=max(3,120*m["total"]/peak); x=pad+24+i*slot+slot*.2; bw=slot*.58
        out.append(f'<rect x="{x:.1f}" y="{base-bh:.1f}" width="{bw:.1f}" height="{bh:.1f}" rx="3" fill="{GREEN if m["total"]==peak else BAR}"/><text x="{x+bw/2:.1f}" y="{base+25}" text-anchor="middle" fill="{MUTED}" font-size="16">{m["month"][5:]}</text>')
    out.append('</svg>'); return "".join(out)

def build_ascii_svg():
    photo_path = os.path.join(ROOT, "source-photo.png")
    prepped_path = os.path.join(ROOT, "source-prepped.png")
    ascii_path = os.path.join(ROOT, "julia-ascii.svg")
    avatar_url = f"https://github.com/{USER}.png?size=800"
    if not os.path.exists(photo_path):
        response = requests.get(avatar_url, headers={"User-Agent":"profile-readme-bot/1.0"}, timeout=30)
        response.raise_for_status()
        with open(photo_path, "wb") as photo:
            photo.write(response.content)
    scripts_dir = os.path.dirname(__file__)
    subprocess.run([sys.executable, os.path.join(scripts_dir, "prep_photo.py"), photo_path, prepped_path], check=True)
    subprocess.run([sys.executable, os.path.join(scripts_dir, "make_ascii_svg.py"), prepped_path, ascii_path], check=True)

if __name__=="__main__":
    days=fetch_days(); data=build_data(days)
    with open(os.path.join(DATA_DIR,"contributions.json"),"w",encoding="utf-8") as f: json.dump(data,f,ensure_ascii=False,indent=2)
    with open(os.path.join(ROOT,"contrib-heatmap.svg"),"w",encoding="utf-8") as f: f.write(heatmap(data))
    with open(os.path.join(ROOT,"stats.svg"),"w",encoding="utf-8") as f: f.write(stats_svg(data))
    build_ascii_svg()
    print("Dashboard atualizado para",USER)

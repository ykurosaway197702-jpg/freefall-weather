#!/usr/bin/env python3
"""Build a standalone offline HTML dashboard with a snapshot of GFS JSON.
No public hosting, authentication tokens, external scripts, or local web server.
"""
import base64
import json
from pathlib import Path

root=Path(__file__).resolve().parents[1]
source=(root/"index.html").read_text(encoding="utf-8")
data=json.loads((root/"data/gfs_winds.json").read_text(encoding="utf-8"))
if data.get("status")!="ok" or not data.get("forecasts"):
    raise SystemExit("Refusing to build offline dashboard without valid GFS data")
encoded=base64.b64encode(json.dumps(data,ensure_ascii=False,separators=(",",":")).encode()).decode()
injection="""
(function(){
 try {
  const binary=atob("__DATA__");
  const bytes=Uint8Array.from(binary, c=>c.charCodeAt(0));
  const embedded=JSON.parse(new TextDecoder("utf-8").decode(bytes));
  acceptGfs(embedded,"Private GitHub Actions オフライン版");
  const status=el("autoStatus");
  if(status)status.textContent="内蔵GFSデータを読込済み（オフライン）";
 }catch(error){
  const status=el("autoStatus");
  if(status)status.textContent="内蔵データの読込失敗："+error.message;
 }
})();
""".replace("__DATA__",encoded)
marker="</script></body></html>"
if source.count(marker)!=1:raise SystemExit("Unexpected index.html layout")
html=source.replace(marker,injection+marker)
# Disable online API buttons in offline bundle; JMA links remain available for manual checking.
html=html.replace('<button id="fetch">','<button id="fetch" disabled title="オフライン版では利用不可">')
html=html.replace('<button id="windFetch">','<button id="windFetch" disabled title="オフライン版では利用不可">')
html=html.replace('<button id="autoGfs">','<button id="autoGfs" disabled title="内蔵GFSデータを利用">')
html=html.replace('<button id="jmaFetch">','<button id="jmaFetch" disabled title="オフライン版では公式予報の自動更新不可">')
html=html.replace("<header><h1>freefall-weather</h1>","<header><h1>freefall-weather（Private・オフライン版）</h1>")
html=html.replace("<main>","<main><section><strong>オフラインスナップショット</strong>：GFSはファイル作成時点の予報です。自動更新されません。新しいデータはGitHub Actionsから最新版を再ダウンロードしてください。気象庁の公式予報・現地観測は別途確認が必要です。</section>",1)
# Keep the private offline interface focused on the embedded snapshot.
# Remove unsupported live API controls and empty duplicate tables entirely.
import re
html=re.sub(r'<button id="fetch"[^>]*>予報を取得</button>', '', html)
html=re.sub(r'<section><h2>地上付近の予報</h2>.*?</section>', '', html, flags=re.S)
html=re.sub(r'<label>予報モデル：.*?<h3>NOAA GFS（GitHub Actions取得結果）</h3>',
            '<h3>NOAA GFS（GitHub Actions取得結果）</h3>', html, flags=re.S)
html=re.sub(r'<p><button id="autoGfs"[^>]*>最新GFSを読み込む</button>.*?</p>', 
            '<p id="autoStatus" role="status">内蔵データ確認中</p>', html, flags=re.S)
html=re.sub(r'<p>GitHub Actionsが生成した <code>data/gfs_winds.json</code>.*?<p id="noaaStatus"',
            '<details><summary>別のGFS JSONファイルを手動で読み込む</summary><label>GFS JSONファイル：<input type="file" id="noaaFile" accept=".json,application/json"></label><p id="noaaStatus"',html,flags=re.S)
html=html.replace('<p id="noaaMeta" class="muted">データ初期時刻・取得時刻：不明</p>',
                  '<p id="noaaMeta" class="muted">データ初期時刻・取得時刻：不明</p></details>')
html=re.sub(r'<p><button id="jmaFetch"[^>]*>気象庁の予報を取得</button>.*?</p>',
            '<p>オフライン版では自動取得できません。以下の気象庁公式画面で最新情報を確認してください。</p>',html,flags=re.S)
html=re.sub(r'<p id="jmaMeta".*?<p id="jmaOverview"></p>', '', html,flags=re.S)
# Preserve legacy DOM nodes hidden so that existing JavaScript event handlers remain valid.
legacy_ids=["fetch","windFetch","autoGfs","jmaFetch","jmaStatus","jmaMeta","jmaRows","jmaOverview",
            "meta","forecast","status","windStatus","windRows","windMeta","windModel"]
hidden='<div hidden aria-hidden="true">'
for name in legacy_ids:
    if 'id="'+name+'"' not in html:
        tag="tbody" if name in ("jmaRows","forecast","windRows") else "select" if name=="windModel" else "button" if name in ("fetch","windFetch","autoGfs","jmaFetch") else "span"
        hidden+=f'<{tag} id="{name}"></{tag}>'
hidden+='</div>'
html=html.replace('</main><script>',hidden+'</main><script>')
# Ensure the displayed table accurately identifies its JST time zone.
html=html.replace('<th>予報有効時刻（UTC）</th>','<th>予報有効時刻（JST）</th>')
# Provide official verification destinations, but do not imply they are fetched offline.
official='''<section><h2>危険気象・航空気象：公式情報の確認先</h2>
<p>このオフライン版では雲底、視程、雷、乱流、ウインドシア、火山灰、METAR/TAFを取得していません。すべて<strong>不明（未取得）</strong>です。下記は確認先へのリンクであり、情報の自動照合ではありません。</p>
<ul>
<li><a href="https://www.jma.go.jp/bosai/warning/" target="_blank" rel="noopener noreferrer">気象庁：気象警報・注意報</a></li>
<li><a href="https://www.jma.go.jp/bosai/nowc/" target="_blank" rel="noopener noreferrer">気象庁：雨雲の動き・雷活動</a></li>
<li><a href="https://www.jma.go.jp/bosai/volcano/" target="_blank" rel="noopener noreferrer">気象庁：火山情報（霧島山）</a></li>
<li><a href="https://www.jma.go.jp/bosai/" target="_blank" rel="noopener noreferrer">気象庁：防災情報（最新の公式情報）</a></li>
</ul>
<p class="warn">航空気象、雲底・視程、乱流・ウインドシア、火山灰の有無は現地および航空気象情報で別途確認。未取得は「危険なし」を意味しません。</p></section>'''
html=html.replace('<section><h2>航空気象・危険気象</h2>',official+'<section><h2>航空気象・危険気象</h2>')
# Add wind-from compass labels to the existing displayed direction column, while retaining numeric degrees.
html=html.replace('p.wind_direction_deg_from,p.wind_speed_ms]);',
                  'p.wind_direction_deg_from+"°（"+["北","北東","東","南東","南","南西","西","北西"][Math.round(p.wind_direction_deg_from/45)%8]+"から）",p.wind_speed_ms]);')

out=root/"dist";out.mkdir(exist_ok=True)
(out/"freefall-weather-offline.html").write_text(html,encoding="utf-8")
print("Created standalone private offline HTML; embedded GFS cycles:",len(data["forecasts"]))

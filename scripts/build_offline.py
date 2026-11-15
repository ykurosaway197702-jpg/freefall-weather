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
out=root/"dist";out.mkdir(exist_ok=True)
(out/"freefall-weather-offline.html").write_text(html,encoding="utf-8")
print("Created standalone private offline HTML; embedded GFS cycles:",len(data["forecasts"]))

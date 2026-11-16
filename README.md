# freefall-weather
自由降下訓練向け気象分析アプリ

## 開発時の確認

```bash
python -m unittest discover -s tests -v
python -m py_compile scripts/*.py
```

`index.html` はGitHub Pages向けの画面です。Pagesワークフローは公開に必要な
`index.html` と `data/gfs_winds.json` だけを `_site` に配置して配信します。

> このアプリは訓練実施可否を判定するものではありません。現地観測、公式な
> 気象情報、部隊の正式な基準を確認してください。

## 参照地点

- 霧島演習場周辺（暫定）
- 南種子町周辺（暫定）
- 習志野演習場周辺（暫定）: 35.7114533, 140.0696580

習志野の代表点はOpenStreetMap contributorsの公開地物中心を2026年11月16日に
参照した暫定値です。正式な降下地点、地表標高、部隊資料による確認は未実施です。


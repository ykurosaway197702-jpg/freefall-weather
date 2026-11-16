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
- 習志野演習場周辺（暫定）: MGRS 54SVE1646751869
  （WGS84換算: 35.70722400, 140.07658381）

習志野の代表点は利用者指定のMGRS座標をWGS84緯度経度へ換算した暫定値です。
座標系・原点・正式な降下地点・地表標高は、正式資料と照合してください。


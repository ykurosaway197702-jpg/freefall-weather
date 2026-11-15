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


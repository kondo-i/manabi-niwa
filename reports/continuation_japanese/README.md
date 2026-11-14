# 中2国語「用言の活用」追加ドラフト（2026-11-14）

Claudeへの送信操作を改善する間も制作を進め、中2国語「用言の活用（形と文脈）」25問を追加した。通常メニューと定期テスト対策の両方で解答・採点・解説確認までできる。main・配信サイトには反映しない。

比較元は `839d39db1326d7c810600b62dc704c868ebd9a58`（前回ドラフト）。問題IDは `CR-JPN2-001〜025`、単元IDは `repair-japanese-g2-conjugation`。前回までの8,773問は全フィールド一致で保持。今回は25問追加、既存修正0、削除0。

## 成果物

`artifacts/japanese-conjugation-20261114/manabi_25.html` が今回の生徒用。`teacher_answers.csv` は全問正答・解説、`unit_counts.csv` と `unit_quality.csv` は問題数と表面の異文数。`manabi_classroom.zip` はデータ・レポートを含む一式。

実測は **8,798 ID、正規化問題文8,784種類、通常345単元、定期テスト274小単元、テスト参照7,018 ID**。教員CSVは8,798行、HTML埋込JSONは794ファイル。追加25問はID・正規化文とも25で、旧8,773問との正規化文一致は0。全通常・テスト小単元で、同一回に同文を重ねない25問開始を確認した。表面の異文数を学習内容数とみなさない。

今回の25問は用言の定義、六活用形、語幹と活用語尾、動詞の五種類、同音・語尾による誤分類、形容詞・形容動詞、三種の音便を扱う。ふりがなは付けていない。作者と別の担当が全設問・全選択肢・正答・解説を読み直した。作者の校正で品詞分類の階層、語幹・語尾の不足、引用表記を改善した。独立監査・根拠資料は `author_review.md` と `independent_review.md`。

指導要領国語編 第2学年知識及び技能(1)オ、光村令和7年度計画中2 PDF p20「文法2 用言の活用」を根拠にした。対応表は、以前不足とした「用言の活用」の行を今回の実単元・25問に対応づけ直し、全15組合せ・274登録小単元を維持した。全範囲の完全収録、全既存問題の内容正確性は未証明。作文推敲、自由記述での活用表完成、助詞・助動詞の全範囲、採択版本文・学校範囲との全対応も未完了。

## 再現と検査

前回の固定入力は `733c50ca5d46aea2b5367a90f8f06e62d23b746e:data/v10/questions.json`。SHA-256は `f84a54070d254a16a35416a58ef8a5111df12e739e0d3972fa8988ad8436749a`。Python3・Node・ffmpeg、ブラウザ検査用にPlaywright/Chromiumを使用。

出力先は新規パスを指定する。比較元は別worktreeで前回の手順を実行して再現する。以下の `/tmp/manabi-final` は前回8,773問版のビルド出力、`/tmp/manabi-final-exam` は前回の6,463問の定期テスト前段ビルドである。

```sh
git show 733c50ca5d46aea2b5367a90f8f06e62d23b746e:data/v10/questions.json > /tmp/manabi-vocab-v10.json
git worktree add --detach /tmp/manabi-previous-source 839d39db1326d7c810600b62dc704c868ebd9a58
python3 /tmp/manabi-previous-source/scripts/build_exam_units.py /tmp/manabi-final-exam --vocabulary /tmp/manabi-vocab-v10.json
python3 /tmp/manabi-previous-source/scripts/build_all25.py /tmp/manabi-final --exam-base /tmp/manabi-final-exam --vocabulary /tmp/manabi-vocab-v10.json
python3 scripts/build_all25.py /tmp/manabi-japanese-20261114 --exam-base /tmp/manabi-final-exam --vocabulary /tmp/manabi-vocab-v10.json
node scripts/verify_all25.cjs /tmp/manabi-japanese-20261114 /tmp/manabi-final
python3 scripts/analyze_classroom.py /tmp/manabi-japanese-20261114 /tmp/manabi-final --expect-conjugation
python3 scripts/build_coverage_report.py /tmp/manabi-japanese-20261114
node scripts/verify_classroom_browser.cjs /tmp/manabi-japanese-20261114
python3 scripts/package_classroom.py /tmp/manabi-japanese-20261114 artifacts/japanese-conjugation-20261114 --report-dir reports/continuation_japanese
```

`verify_all25` は全旧問題保持・全問題の登録正答による採点整合・25問開始等、`analyze_classroom` は今回の追加25問限定・CSV全列・埋込JSON一致を検査する。登録正答を採点器に与える検査と、本文の内容監査を区別する。結果はこのディレクトリのJSON/CSVに保存。ブラウザ結果は `browser/`。375px/1280pxで計16シナリオが成功し、新国語は通常25/25と単独テスト25/25、小単元結果、範囲へ戻る選択保持まで確認した。JavaScriptエラー・横溢れ・外部要求・不要なポップアップは0。図の拡大、誤答の翌日復習も回帰確認した。file URLは管理ブラウザの制限で遮断されるため、同じ単体HTMLをlocalhost HTTPで検査した。画面幅375px/1280pxの検査とiPhone実機確認は区別し、実機は未実施。

## スマホ試用

教材ZIPをPCで展開し、そのフォルダで `python3 -m http.server 8000 --bind 0.0.0.0` を実行する。同じWi-FiのSafariから `http://PCのローカルIPv4:8000/manabi_25.html` を開く。試用後はCtrl+Cで終了する。配信サイトの更新は不要。詳細と前回までの不足範囲はリポジトリの `reports/coverage_repair/README.md`、`NEXT_TASKS.md` を参照。

Claude送信用の3本のPDFは `artifacts/claude-audit-20261114/`。これは前回の80問が対象であり、今回の国語25問へのClaude監査実績ではない。無料の利用制限が出たら回復を待つ。別サービスの返答待ちを理由に、本制作の作問・検査は止めない。ただしこの会話が停止している間に自動継続する仕組みは設定していない。

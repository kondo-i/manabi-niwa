# 配信更新・図表50問追加（2026-11-14）

ユーザーの「Claudeは使わずサイト更新・問題追加」の指示により、既存Sitesを更新する。配信先は `https://kondo-study-lab.vast-stone-7426.chatgpt.site`、project_idは `appgprj_6adf49333e2081918804182bd0af840b`。取得時のサイトは公開・所有者権限、第24版、ソース `b54cc88b362ee144a2ba013d920ed8bf41b4083a`。公開範囲は変更しない。GitHub教材リポジトリのmainを変更せず、Sites専用ソースへ検査済み出力を同期する。

## 今回生徒ができること

最新の25問版を実際の配信URLに反映し、通常と定期テストの両画面で学年・教科・範囲を選んで解答、採点、解説確認までできるようにする。前回までの中1素因数分解、中2英語の義務/禁止/不必要、中2国語の用言、中3理科資料読解も反映対象。

追加は中3理科「水圧・浮力の実験」25問（CR-SCI3B-001〜025）と中2数学「箱ひげ図の読み取りと比較」25問（CR-MATH2B-001〜025）。水中の力の図1枚と、箱ひげ図4枚を追加。数学は23問に図を付けた。数値違いだけでなく、測定条件、比較、資料から判断できないこと、反例を含む。

最終実測は **8,848 ID、通常347単元、定期テスト276小単元、定期テスト参照7,068 ID**。正規化問題文8,834種類。教員CSV8,848行、HTML埋込JSON796ファイル。比較元は直前の `29c946952f2abb4e47576ca04af441270420bdb1`、8,798問。追加50、削除0、既存1問の設問・解説修正、他8,797問は全フィールド一致。全15学年×教科・全276小単元の対応表を再出力した。

取得時の実配信は91通常単元・900通常問題で、全900 IDが最新にも存在する。9問には以前のドラフトからの内容改訂があり、今回全9問を独立に再読した。うち助動詞 `japanese-g2-auxiliary-context-balance-001:q4` は、尊敬のつもりの「先生が予定を話される」が受け身にも読めるため、尊敬として読む条件を明示し、解説も連動させた。他8問に確定不備なし。`production_legacy_review.md` と `production_question_delta.json` に記録する。

## 検証範囲

- 追加50問は作者と別担当が全設問・全選択肢・正答・解説と図を確認。計算・四分位位置・反例・SVG座標を別手順で照合。記録は各author/independentメモ。
- 全通常347単元と全テスト276小単元で、同文を重ねない25問開始を検査。全登録正答の採点器との整合、学年教科・ID・音声75ファイル・図の同梱を確認。
- 新2単元は通常25問を最後まで採点して25/25、既存同学年教科の単元と混ぜた25問も最後まで採点して25/25、小単元別12/13配分と結果表示をNode VMで確認。中3理科の既存通常25問/混合25問も回帰確認。
- これらは実装をVMで動かす自動検査であり、ブラウザのクリック操作やiPhone実機確認とは異なる。今回 `SITES_MANAGED_LINUX_CONTAINER=1` だが `cua_repl.js` が提供されておらず、Sitesスキルに従い配信用ブラウザQAをスキップし、代替ブラウザ・プレビューサーバーは起動しない。以前の16シナリオの結果を今回の新内容のブラウザ検証へ読み替えない。
- 箱ひげ図は独立担当が初稿を描画しラベル重なりを修正した後、最終SVGをさらに14px以上の文字へ拡大した。最終字体調整後のブラウザ表示は未確認。図の現ソース・座標・ラベルは静的に照合。旧確認画像は途中段階の証拠であり最終版のスクリーンショットではない。
- CSVの全列とHTML埋込JSONを出題データに全件照合。ZIPは実展開して全ファイルのハッシュ・入口・問題パック参照を確認する。

機械検査を全問題の内容監査や教科書全範囲の充足としない。全校の本文・巻末索引対応、全既存問題の内容再監査、生徒試用、iPhone実機は未完了。既存paired_itemsの推測できる選択肢、他の未収録範囲は前回NEXT_TASKSに残っている。今回の追加50問には同種の手がかりがないよう確認した。

## 再現

国語入力SHAは `733c50ca5d46aea2b5367a90f8f06e62d23b746e`、`data/v10/questions.json`、SHA-256 `f84a54070d254a16a35416a58ef8a5111df12e739e0d3972fa8988ad8436749a`。比較元は別worktreeで前回READMEの手順から再現する。下記の旧出力は前回の8,798問版、新出力先は空の新規パスを指定する。

```sh
python3 scripts/build_all25.py /tmp/manabi-publish-20261114 --exam-base /tmp/manabi-final-exam --vocabulary /tmp/manabi-vocab-v10.json
node scripts/verify_all25.cjs /tmp/manabi-publish-20261114 /tmp/manabi-japanese-20261114 --allow-clarification
python3 scripts/analyze_classroom.py /tmp/manabi-publish-20261114 /tmp/manabi-japanese-20261114 --expect-publication
python3 scripts/build_coverage_report.py /tmp/manabi-publish-20261114
python3 scripts/package_classroom.py /tmp/manabi-publish-20261114 artifacts/publication-20261114 --report-dir reports/publication_20261114
```

## 配信への反映

既存Sitesのソースを正規の書込資格情報で取得し、同じproject_id/公開範囲を保持する。Sitesスキルのsource helperは実行環境内に存在せず、skillsからのスクリプト取得も失敗したため、認証を標準入力・プロセス内メモリのみに渡すGit操作で代替した。資格情報はファイル・コマンド引数・ログに残さない。

`prepare_site_release.py` は検査結果がpassedであることを確認してからdistを同期し、全参照先を検査する。JS/CSSのキャッシュ識別子を更新し、古いJSが残る問題を防ぐ。ブラウザ保存のキー `kondo-study-lab-v1` は配信前後で同一、消去処理は追加しない。別ブラウザの学習記録は同期されない。

Sites専用ソースのコミット/プッシュ後に、そのコミットと同じdistおよび `.openai/hosting.json` をtarに梱包し、native save/deployを実行する。配信完了ID・版・ソースSHAは別のdeployment記録に保存する。公開後にHTTPでrelease.json・catalog・新問題パックを取得してローカルとの一致を確認する。成功したnative結果とHTTP検査を、実ブラウザ操作の確認とは区別する。

## 別ブラウザからこの会話を見る方法

別のSafari/Chromeで `https://chatgpt.com/` を開き、この会話を使っている同じChatGPTアカウントでログインし、履歴から「まなびの庭」の会話を開く。同じワークスペースも選ぶ。会話の全文を学習サイトへ載せたり、公開共有リンクを作ったりはしない。こちらからユーザー端末のログイン操作や履歴の表示を代行する機能はない。これは公開設定の変更ではなく、同一アカウントの履歴同期を利用する手順。

# まなびの庭 範囲照合・優先不足修正版（2026-11-13）

生徒用は `artifacts/coverage-repair/manabi_25.html`、教材一式は同ディレクトリの `manabi_classroom.zip`。main・配信サイトは変更していない。全範囲完成版ではなく、固定版を再現して不足を調べ、優先3小単元を授業で試せる状態にしたドラフト。

## 生徒が今回できること

通常「科目・単元」でも「定期テスト対策」でも、中1数学「素数と素因数分解」、中2英語「義務・禁止・不必要の使い分け」、中3理科「中3理科の実験・資料読解」を各25問解ける。理科には学習用の記録表とグラフが入り、図は同じ画面で拡大して閉じられる。正答・解説、複数小単元の25問テスト、小単元別結果を引き継いだ。誤答時の結果画面に、翌日の練習を促す説明と復習ボタンを追加した。

復習待ちはこのブラウザのlocalStorageに保持する。翌日専用の予約通知や自動間隔調整ではなく、次の日も「もう一度」から誤答を解き直せる方式。名前・メール・アカウントは入力しない。ブラウザや開くURLが変わると記録は共有されない。

## 固定版の再現と実測

- 起点: `e537d753465c00ab5cf43bf060661094dd608055`（`draft/all25-20261113`）。比較用前版: `4247b6bcee52e2d1211b2ff386c534024a3488ad`。
- 国語入力: `733c50ca5d46aea2b5367a90f8f06e62d23b746e:data/v10/questions.json`。SHA-256 `f84a54070d254a16a35416a58ef8a5111df12e739e0d3972fa8988ad8436749a`。
- 固定版をビルドし、8,698 ID・通常341単元・テスト270小単元を再計測。`summary.json`・`unit_counts.csv`・`verification.json` はリポジトリ保存済みの3ファイルとバイト一致。元の生徒用HTML・教員CSVの保存ファイルは当該コミットにないため、元成果物とのバイト同一性は証明できない。今回再生成した固定版の全出力ハッシュを `baseline_sha256.json` に保存。
- 最終: **8,773 ID、正規化問題文8,759種類、通常344単元、テスト273小単元、テスト参照6,993 ID**。同じ問題を二画面で共有するので通常とテストの件数を足さない。
- 追加75、既存変更5、削除0、固定版と同内容8,693。従来前版の6,463問は内容を保持。国語第10稿の1,040問は本文・選択肢・正答・解説が一致。文字の一致は内容監査合格とは異なる。
- 全体では正規化後の同文が14 ID分あるが、各登録単元の25問と同一セッションの重複除外を別に検査。数値マスク6,384種類は表面の指標で、学習内容数ではない。`unit_quality.csv` にID数・異文数・数値マスク種類・問題形式を分けた。
- 教員用CSV **8,773行**の全列をデータと照合。単体HTML埋込JSON **793ファイル**を出題データと照合。音声75ファイル同梱。

## 直した不備と内容確認の範囲

英語 `exam-section-093-all25:q01〜q05` は `of all the students` に和訳「3人の中で」が付いていたため「全生徒の中で」に修正。正答語 `the tallest` は不変。選択肢の循環配置は問題文ハッシュに連動するため配列・正答indexが変わる場合がある。

追加75問は作問者と別担当が全設問・全選択肢・解説を読み、計算は別手順でも確認した（各独立監査メモ）。理科は平均と瞬間の区別、仕事における等速・エネルギー蓄積条件、金星の補助データ、観察から分かる範囲など8件を修正。数学は定義選択肢を同じ長さ・構造にし、語尾や長さだけで正答を推測しやすい形を改善。これはClaudeの監査ではない。既存8,698問の全内容監査は未実施。

国語 `JVQ-114-03-C` は第9稿の誤答「伝達」が第10稿で「訂正」へ変わり、解説も修正済み。社会 `SOC-HIS-011` は現バンクに存在せず、別ドラフト修正が現版に反映済みとは言えない。強み出題のq1〜q12数値順は実コードで確認。詳細は各教科メモ。

図の別タブ拡大は埋込data URLをブラウザが遮断する例があったため、同じページのdialogに変更し、拡大・閉じる・元の問題への復帰を確認した。

## 範囲表と残件

`coverage_matrix.csv` は320行、全15学年×教科、全273登録小単元を根拠資料・実出題数・本文確認範囲・不足・次ファイルに対応づけた初回照合表。詳細は `language_coverage.csv`、`social_math_coverage.csv`、`science_coverage.csv` と教科別監査メモ。表の候補を網羅的な指導要領の全内容リストとみなさない。言語は本文抜粋と生成コード、数学・社会は原則各4問（偏り単元は全件）、理科は既存各3問と全件の型集計による確認であり、登録済み問題の全件正誤監査ではない。

`NEXT_TASKS.md` に次の小単元名・追加目標・ファイルを記載。特に国語の活用・作品本文読解、数学の箱ひげ図・確率・平方根、社会の消費者契約・世界史・資料読解、理科の水圧浮力・熱変化・太陽黒点などが残る。既存 `paired_items()` の組み合わせ問題には対象語の一致だけで選べるものがあり、全選択肢を並行な構造にして内容を再監査する必要がある。

国語光村の巻末漢字一覧・採択版の掲載語・新出学年、各社索引、学校の範囲表・本文との対応は未提供につき未確定。数学・英語の出版社計画は参考で、採択を仮定していない。iPhone実機・生徒試用・第19版670問との意味重複全件照合・外部Claude監査も未実施。

## 検査

`verification.json`: 全15画面、通常344単元・テスト273小単元の25問開始、問題文重複なし、全8,773問の採点器との整合、学年教科・ID、従来6,463問保持、音声・図同梱。中3理科の通常25問と混合25問は最終採点・結果まで自動確認。採点器検査は登録答えを通す検査なので、内容の正しさの独立証明ではない。

`browser/browser-verification.json`: Chromium 375px/1280px各6、計12シナリオ。追加3単元は各25問を両幅で完走。通常記録タイマー5/25問、混合25問（8/8/9配分）、解説、結果から復習、11月14日への時計変更と再読込による翌日再訪、誤答解消までDOM操作。図の表示・拡大・閉じるも成功。JSエラー・横溢れ・外部要求・不要popupは0。これは画面幅検査で、iPhone実機確認ではない。管理Chromiumのfile URLは実際に試してポリシー拒否を記録し、同一HTMLのlocalhost HTTPで検証した。

## 再現手順

Gitオブジェクト一式、Python 3.12、Node 24、ffmpeg 7.1（flite・libmp3lame）が必要。ブラウザ検査はPlaywrightとChromiumを使用。以下の出力先は新規空パスにする。`PYTHONDONTWRITEBYTECODE=1` を指定してもよい。

```sh
git show 733c50ca5d46aea2b5367a90f8f06e62d23b746e:data/v10/questions.json > /tmp/manabi-vocab-v10.json
git worktree add --detach /tmp/manabi-fixed e537d753465c00ab5cf43bf060661094dd608055
python3 /tmp/manabi-fixed/scripts/build_exam_units.py /tmp/manabi-exam-before --vocabulary /tmp/manabi-vocab-v10.json
python3 /tmp/manabi-fixed/scripts/build_all25.py /tmp/manabi-all25 --exam-base /tmp/manabi-exam-before --vocabulary /tmp/manabi-vocab-v10.json
node /tmp/manabi-fixed/scripts/verify_all25.cjs /tmp/manabi-all25 /tmp/manabi-exam-before
python3 scripts/build_exam_units.py /tmp/manabi-final-exam --vocabulary /tmp/manabi-vocab-v10.json
python3 scripts/build_all25.py /tmp/manabi-final --exam-base /tmp/manabi-final-exam --vocabulary /tmp/manabi-vocab-v10.json
node scripts/verify_all25.cjs /tmp/manabi-final /tmp/manabi-exam-before
python3 scripts/analyze_classroom.py /tmp/manabi-final /tmp/manabi-all25 --expect-repair
python3 scripts/build_coverage_report.py /tmp/manabi-final
node scripts/verify_classroom_browser.cjs /tmp/manabi-final
```

実行に必要なネットワークやブラウザ起動権限は環境による。本セッションではGitHub取得とChromium起動のみ環境の標準承認機構を通して実行した。

## スマホで試す方法（公開サイトは更新しない）

ZIPをPCで展開し、展開したフォルダで次を実行する。

```sh
python3 -m http.server 8000 --bind 0.0.0.0
```

同じWi-FiのiPhoneのSafariで `http://PCのローカルIPv4アドレス:8000/manabi_25.html` を開く。PCのファイアウォールで家庭内ネットワークからの接続を許可する必要がある場合がある。テスト後はPCでCtrl+Cを押して終了する。常時公開や配信URLの変更は不要。GitHubのHTML表示画面はアプリ実行画面ではない。iPhoneのファイルプレビューからの直接実行可否は確認していない。

授業試用前に、担当範囲の教員用正答・解説を確認する。公開判断は既存の内容偏り・推測できる選択肢・範囲未充足の解消と実機試用を踏まえる。

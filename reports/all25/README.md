# まなびの庭 全単元25問版

中学1〜3年の国語・数学・英語・理科・社会が対象。各学年と教科の組み合わせで、通常学習と定期テスト対策を選べる。通常学習341単元と定期テスト対策270小単元は同じ問題を一部共有する。通常単元・定期テスト小単元とも、問題文をNFKC正規化して空白を除いたうえで25種類以上ある。問題バンクは8,698 ID、前版6,463 IDの内容を引き継ぎ、2,235問を追加した。定期テストから参照する問題は6,918 ID。追加問題には、異なる数値の計算演習、異なる形式での同一知識の確認、場面や資料を使う問題を含む。

## 定期テスト対策の小単元数

| 教科 | 中1 | 中2 | 中3 |
| --- | ---: | ---: | ---: |
| 国語 | 25 | 39 | 11 |
| 数学 | 18 | 13 | 15 |
| 英語 | 20 | 13 | 13 |
| 理科 | 23 | 18 | 20 |
| 社会 | 16 | 17 | 9 |

中3理科は通常23単元、定期テスト20小単元。力の合成・分解、記録タイマー、仕事率、電気分解、進化、金星などを追加した。社会は世界6州と日本7地方の各演習を追加した。国語の語彙力49小単元では、意味・場面に加えて一部に意味から語を選ぶ逆引きを入れた。

範囲の参照先は[中学校学習指導要領解説](https://www.mext.go.jp/a_menu/shotou/new-cs/1387016.htm)と[大日本図書の中学校理科指導計画資料](https://www.dainippon-tosho.co.jp/science/curriculum.html)。小単元は共通の学習内容をもとにしたアプリ内の区分。学校別のページ対応、国語と英語の採択教科書固有の本文、全問の内容監査、生徒による試用は未確認。

## 再現と検証

比較元は `4247b6bcee52e2d1211b2ff386c534024a3488ad`。国語入力の出典は [前版の手順](../exam_units/README.md) に記載。Python 3、Node.js、fliteとlibmp3lameに対応したffmpegを使用する。既存のない出力先を指定する。

```sh
git fetch origin draft/japanese-vocab-v10-20261109
git show 733c50ca5d46aea2b5367a90f8f06e62d23b746e:data/v10/questions.json > /tmp/manabi-vocab-v10.json
python3 scripts/build_exam_units.py /tmp/manabi-exam-before --vocabulary /tmp/manabi-vocab-v10.json
python3 scripts/build_all25.py /tmp/manabi-all25 --exam-base /tmp/manabi-exam-before --vocabulary /tmp/manabi-vocab-v10.json
node scripts/verify_all25.cjs /tmp/manabi-all25 /tmp/manabi-exam-before
```

結果のHTMLは `manabi_25.html`。スマートフォンとパソコンの画面幅に合わせたレイアウトを引き継いでいる。CSVには全単元の問題数と全問題の正答・解説が入る。機械検査は全15組み合わせの画面、通常341単元・定期テスト270小単元での25問開始、セッション内の出題文の重複、学年・教科の整合、全問題の採点、音声ファイルの同梱、既存問題の内容一致を対象とした。中3理科の通常演習と混合テストは25問目を解いて結果を確認するところまで自動検査した。ブラウザでは中3理科の通常メニューから記録タイマーの出題と採点を確認した。

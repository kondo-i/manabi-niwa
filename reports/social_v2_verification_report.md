# 社会第2稿 制作・機械検証報告

2026-11-03。親コミット `6d8a1868c32b8efe4c3a038be56434a2538ea288`。`draft/social-v2-20261103`。国語第7稿とは別のドラフトで、国語第6稿の既存ファイルを改変しない。main・配信アプリへ未反映。

- 30問（地理10・歴史10・公民10）を維持。新規ID 0、設問内容の差し替え1（HIS-010）、依頼の内容修正7問。正答位置変更25問、総差分27問・72フィールド。HIS-006〜008は対応する出典も更新した。
- 位置1・2・3は各10問。旧各分野の周期1,2,3を解消。全体・各分野で周期長1〜5の反復なし。選択肢内の「だけ／必ず／すべて」は0件。
- JSON/CSVの全フィールド、ID、3択の重複、正答位置と正答文、説明と誤答対応、出典ID、Markdown、変更表全前後値を別スクリプトで再照合。
- 縮尺：GEO-007は2×25,000cm=500m、008は3×50,000cm=1.5km、009は100,000cm÷25,000=4cm。010は同じ紙の幅なら実際に収まる距離が半分になる。面積比は1/4。
- Claude判定CSVは未提供。文面に示された7問を反映し、正答位置は制作側で再配置した。Claudeの推奨順を再現したものではない。

## 出典本文の確認

|対象|参照した本文と照合した内容|
|---|---|
|GEO-001〜006|[国立天文台・緯度と経度](https://eco2.mtk.nao.ac.jp/koyomi/wiki/C3CFB5E52FB7D0C5D9A4C8B0DEC5D9.html)の基本節：赤道・本初子午線、南北・東西。|
|GEO-007〜010|[国土地理院・距離と縮尺](https://www.gsi.go.jp/KIDS/KIDS04.html)の地図の縮尺節。数値・範囲比較は制作側が別計算。|
|HIS-001・002・005|[国立公文書館・年表](https://www.archives.go.jp/ayumi/table.html)の1871・1872・1873年。|
|HIS-003・004|[地租改正条例](https://www.archives.go.jp/ayumi/kobetsu/m06_1873_03.html)の解説本文：地価基準と物納から金納。|
|HIS-006・009|[大日本帝国憲法の発布](https://www.archives.go.jp/ayumi/kobetsu/m22_1889_01.html)と[廃藩置県](https://www.archives.go.jp/ayumi/kobetsu/m04_1871_04.html)の解説本文：1889年と政府による任命。|
|HIS-007・008|[衆議院・日本国憲法](https://www.shugiin.go.jp/Internet/itdb_annai.nsf/html/statics/shiryo/dl-constitution.htm)の冒頭：1946年11月3日公布、1947年5月3日施行。旧年表リンクだけでは施行日を直接裏づけないため変更。|
|HIS-010|[国立国会図書館・大日本帝国憲法本文](https://www.ndl.go.jp/constitution/etc/j02.html)第1・4条、5・37・38条と、[日本国憲法](https://www.shugiin.go.jp/Internet/itdb_annai.nsf/html/statics/shiryo/dl-constitution.htm)の前文・第1条。帝国議会の関与と統治権の所在を区別。|
|CIV-001〜010|同じ日本国憲法本文の前文・第1・14・20・21・22・25・26・30・41・42・65・76条を参照。|

再現：`python scripts/build_social_v2.py` → `python scripts/verify_social_v2.py`。第1稿の検証も実行し成功。第2稿の結果とハッシュは `social_v2_verification_results.json`。Windowsで第1稿を再現する場合は `python -X utf8 scripts/verify_social_v1.py`。

## 次に確認すべき点

対象は緯度経度・縮尺、明治の改革、憲法の基礎。社会全体の網羅性は主張しない。定義を覚える問の次に、地図や短い史料を根拠に選ぶ問を置く。暗記の問題を単純に増やすより、生活に結びつく短い資料で同じ知識を使い直せる流れを優先する。
GEO-009と配信中の `social-g1-geography-data-balance-001:q10` は同じ縮尺・数値を逆方向に問う。重複候補の具体例で、全30問と既存社会問題の意味重複を照合し終えたものではない。次回は同一技能・同じ条件・逆向きの転用を区別する。
学年配当・ふりがな・漢字配当の新規判定、全配信問題との意味重複、ユーザー試験は未実施。掲載した一次資料との照合は制作側の作業であり、Claudeの第6回監査で行われた扱いにはしない。
`reports/app_review/` は現行試用アプリの別枠レビュー。ここにある185問は社会第2稿30問や国語第7稿1,040問の配信データではない。

ハッシュはGitに保存されるLF改行に正規化して計算し、Windowsの改行変換に依存しません。

# 次に実装する範囲

固定版の本文抜粋・公開計画から見つけた優先候補。下記の25は、新設する場合の最低追加目標であり、学習内容の完全収録に必要な確定数ではない。既存の一部対応問題を流用する場合も、異文数と学習内容を別々に確認する。

|学年・教科|小単元・不足内容|最低追加目標|次に触るファイル|
|---|---|---:|---|
|中1国語|詩の表現と情景・根拠をもつ読解|25|data/coverage_repair/japanese_poetry.json（新規）|
|中2国語|用言の活用（形と文脈）|25|data/coverage_repair/japanese_conjugation.json（新規）|
|中3国語|古典本文・歌の表現を根拠に読む|25|data/coverage_repair/japanese_classics.json（新規）|
|全学年国語|光村巻末漢字・500語の掲載と新出学年|資料待ち、問数未算定|data/v10/questions.json（別固定SHAから取得）、各学年語彙メタデータ|
|中1英語|文脈による読解・応答・短い記述|25|data/coverage_repair/english_reading_g1.json（新規）|
|中2英語|接続詞や不定詞を含む読解・発信|25|data/coverage_repair/english_reading_g2.json（新規）|
|中3英語|過去分詞による名詞修飾|25|scripts/exam_units/new_items.py、data/coverage_repair/english_participles.json（新規）|
|中1数学|円柱・円錐の表面積、展開図|25|scripts/exam_units/new_items.py、data/coverage_repair/math_solid_figures.json（新規）|
|中2数学|箱ひげ図を表示して分布を比較する|25|scripts/unit20/math.py、data/coverage_repair/math_boxplots.json（新規）|
|中2数学|樹形図・二段階試行の確率|25|scripts/unit20/math.py、data/coverage_repair/math_probability.json（新規）|
|中3数学|平方根の±・近似・有理化|25|scripts/unit20/math.py、data/coverage_repair/math_roots.json（新規）|
|中3数学|標本抽出の偏り・調査方法の妥当性|25|scripts/unit20/math.py、data/coverage_repair/math_sampling.json（新規）|
|中1社会|雨温図・生活文化・世界文明の比較|25|data/coverage_repair/social_geography_sources.json（新規）|
|中2社会|ルネサンス・宗教改革・市民革命・産業革命|25|data/coverage_repair/social_world_history.json（新規）|
|中3社会|消費者と契約・権利・取引の資料|25|data/coverage_repair/social_consumers.json（新規）|
|中1理科|プレート・断層・褶曲の資料|25|data/coverage_repair/science_earth.json（新規）|
|中2理科|化学変化と熱・発熱と吸熱|25|data/coverage_repair/science_heat.json（新規）|
|中2理科|炭酸水素Naの熱分解実験|25|data/coverage_repair/science_decomposition.json（新規）|
|中3理科|水圧・浮力の実験|25|data/coverage_repair/science_buoyancy.json（新規）|
|中3理科|太陽表面・黒点の観察資料|25|data/coverage_repair/science_sun.json（新規）|
|理社の既存教材|対象語の一致だけで選べる組み合わせ問題|全該当数を次回算定、25問単位で再監査|scripts/all25/items.py のpaired_items、data/all25/regions.txt|

各学年・教科の詳細候補、既存ID、実数、参照箇所はcoverage_matrix.csvに記録。ここにない領域が充足したという意味ではない。

次回の順序は、(1)既存paired_itemsの推測手がかりを除く→内容監査、(2)箱ひげ図・浮力等の図表不足、(3)国語活用・消費者契約等の未収録、(4)採択資料との照合と全件内容監査。追加データを作ったら scripts/build_all25.py のadd_reviewed_materialに登録し、analyze_classroom.pyの受入条件は比較元と実際の変更IDに合わせて更新する。全学年の教科書索引、学校の範囲表があれば対応を絞れる。

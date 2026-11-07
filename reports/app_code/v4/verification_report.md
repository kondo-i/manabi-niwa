# 同日チャレンジ再出題の修正：アプリコード第4案

2026-11-07。比較元GitHubコミット fea74f767cd2467a2eda897a4ddc6cd4e7f371f3。
新ブランチ draft/app-strengths-v4-20261107。サイトに配信せず、既存のv3監査用ZIPの実コードへ3ファイルの修正を適用して検証。

## 設計

Strengths.choose(bank,subject,records,grade=0,previousId='') は、科目・学年で候補を選び、候補2問以上なら直前IDを除外する。その後、未挑戦、古いlastDate、少ないattempts、古いlastAt、IDの順に並べる。候補0ならnull、候補1なら同じ問題の再提示を許す（回避可能な別候補がないため）。既存の4引数呼び出しも互換。

直前IDは state.lastStretchIds[subject] に出題開始時点で保存する。再読込や途中で別科目へ移動しても科目ごとに記憶する。正答・誤答・解説を直接見る経路でlastAtを保存。通常の解答記録にも追加する。lastAtはUNIXミリ秒の数値で、現在時刻と既存記録の最大値+1の大きい方。時計が同じ値でも逆行しても単調増加する。古い記録にlastAtがなくても利用できる。

対象コードは app_drafts/strengths-v4/{strengths.js,strength-ui.js,app.js}。実際のdistへの統一差分はcode_changes.patch、元/修正後のハッシュはpatch_manifest.json。サイトの元ソースSHAを、このGitHubブランチのSHAと混同しない。

## 実施結果

- node --test app_drafts/strengths-v4/choose.test.cjs：4テストPASS。20回の同日・凍結時計、一巡前の重複0、隣接重複0、履歴の公平性、0/1候補、旧記録、学年指定、選出順位、純粋性、時刻の単調性。
- python3 scripts/prepare_strengths_v4.py <空の出力先>：v3 ZIPから実ランタイムを再現。既存ZIP131ファイルのうち3ファイルだけをコード修正し、マニフェストを再計算。
- node scripts/simulate_learning_v4.cjs <出力先> <検査結果出力先>：実ハンドラと模擬DOM/保存で、通常改稿9問＋難問27問、ヒント利用、自力/補助付き正答の区別、国語からの継続、社会の同日20回連続を実行。初回7問は全て別ID、隣接同一0、再読込後も前問を回避、lastAt保存を確認。known_issue_same_question_after_cycle=false。
- シミュレーターの既定の出力先は一時フォルダ。実行するだけでは追跡中ファイルを書き換えない。確定結果を上記learning_simulation_results.jsonへ別途収録。

この枝の教材はv3の187問のまま。社会v4の188問は別ブランチで管理し、結合検証の対象・結果は社会v4側の報告へ記載する。既存149件のテストを今回すべて再実行したとは報告しない。

## 未実施

実ブラウザ・実機・生徒による試験、配信済みサイトの変更、学習意欲の実測。模擬DOMはレイアウト・視覚的な使いやすさを証明しない。

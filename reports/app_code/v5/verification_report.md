# 第9回監査対応：自然な数値順

2026-11-09。比較元 577cddeb89fa01a2e90a1be6787ad5c14675b582。
対象 draft/app-strengths-v5-20261109。

実コードの変更はchoose()の最後の比較だけ。String(a.id).localeCompare(String(b.id),undefined,{numeric:true})へ変更。未挑戦・lastDate・attempts・lastAt・直前除外は維持する。
app_drafts/strengths-v5/には再現用の3コードとテストを収録。strength-ui.js/app.jsは第4案と同じ。

node --test app_drafts/strengths-v5/choose.test.cjs：既存4＋新1＝5テスト成功。q1〜q12の逆順入力から最初の一巡がq1,q2,...q12になること、20回同日連続の隣接同一0を確認。
python3 scripts/prepare_strengths_v5.py <一時出力先> と node scripts/simulate_learning_v5.cjs <一時出力先> <結果出力先> でも、実ハンドラの通常9問・難問27問、社会20回・再読込を検査。known_issue_same_question_after_cycle=false。

基点のサイトソースb54cc88b362ee144a2ba013d920ed8bf41b4083aと、GitHubの親コミットは別。配信へ反映していない。実機・生徒試験は未実施。既定の検査出力はプロジェクト外の一時フォルダ。

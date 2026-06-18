#!/usr/bin/env sh
set -eu

PYTHONPATH=src python3 -m pytest
PYTHONPATH=src python3 -m voi_bw_commander.cli apply "저그로 해. 드론 5개 더 찍고 2햇 뮤탈. 침략적으로 가되 정면 싸움은 피하고 일꾼만 흔들어." >/tmp/voi_bw_apply.json
PYTHONPATH=src python3 -m voi_bw_commander.cli verify-demo "저그 드론 5개 더 2햇 뮤탈 견제 일꾼만" >/tmp/voi_bw_verify.json
PYTHONPATH=src python3 -m voi_bw_commander.cli readiness --root . >/tmp/voi_bw_readiness.json
PYTHONPATH=src python3 -m voi_bw_commander.cli eval-corpus fixtures/parser_corpus.json >/tmp/voi_bw_parser_eval.json
PYTHONPATH=src python3 -m voi_bw_commander.cli hook-plan --backend McRave >/tmp/voi_bw_hook_plan.json
PYTHONPATH=src python3 -m voi_bw_commander.cli transcript --text "테란 벌처 3기 생산하고 마인업" --queue /tmp/voi_bw_commands.jsonl >/tmp/voi_bw_transcript.json
PYTHONPATH=src python3 -m voi_bw_commander.cli write-ui --output /tmp/voi_bw_commander.html --queue /tmp/voi_bw_commands.jsonl >/tmp/voi_bw_ui.json
printf '{"metric":"intent_adherence_score","value":0.75}\n' >/tmp/voi_bw_replay_metrics.jsonl
PYTHONPATH=src python3 -m voi_bw_commander.cli replay-ingest /tmp/voi_bw_replay_metrics.jsonl --output /tmp/voi_bw_replay_telemetry.jsonl >/tmp/voi_bw_replay_ingest.json
PYTHONPATH=src python3 -m voi_bw_commander.cli stardata-features /tmp/voi_bw_replay_metrics.jsonl >/tmp/voi_bw_stardata.json
python3 scripts/apply_purplewave_integration.py third_party/PurpleWave --dry-run >/tmp/voi_bw_purplewave_patch_plan.txt

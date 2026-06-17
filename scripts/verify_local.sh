#!/usr/bin/env sh
set -eu

PYTHONPATH=src python3 -m pytest
PYTHONPATH=src python3 -m voi_bw_commander.cli apply "저그로 해. 드론 5개 더 찍고 2햇 뮤탈. 침략적으로 가되 정면 싸움은 피하고 일꾼만 흔들어." >/tmp/voi_bw_apply.json
PYTHONPATH=src python3 -m voi_bw_commander.cli verify-demo "저그 드론 5개 더 2햇 뮤탈 견제 일꾼만" >/tmp/voi_bw_verify.json

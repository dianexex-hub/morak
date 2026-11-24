#!/bin/bash
# 모락 NEXT 작업 환경 준비 (Claude 작업 환경용). 한 번만 돌리면 됨.
# - bpy 5.3(다이앤 Blender와 같은 버전) + scikit-image : 모형 스크립트(avatar.py, rotenburo.py)
# - three r128 로컬 사본 : 시험 촬영 때 cdnjs 대신 끼움
# - 게임 서버 : http://localhost:8123
set -e
[ -x /home/claude/bvenv/bin/python ] || { python3 -m venv /home/claude/bvenv; /home/claude/bvenv/bin/pip install -q bpy==5.3.0 scikit-image; }
[ -f /tmp/three/package/build/three.min.js ] || { mkdir -p /tmp/three && cd /tmp/three && npm pack -q three@0.128.0 >/dev/null && tar xzf three-0.128.0.tgz; }
curl -s -o /dev/null localhost:8123 || (cd "$(dirname "$0")/../.." && nohup python3 -m http.server 8123 >/dev/null 2>&1 &)
sleep 1; echo "준비 끝: bpy=$(/home/claude/bvenv/bin/python -c 'import bpy;print(bpy.app.version_string)' 2>/dev/null), 서버 localhost:8123"

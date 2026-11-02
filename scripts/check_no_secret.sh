#!/bin/sh
# 키 노출 grep: 작업 트리와 전체 커밋 이력에서 키 형태·키체인 값을 찾는다. 0건이어야 통과.
cd "$(dirname "$0")/.." || exit 2
KEY=$(security find-generic-password -a youcam -s youcam-api-key -w 2>/dev/null)
n=0
if [ -n "$KEY" ]; then
  c1=$(git grep -c -F "$KEY" $(git rev-list --all) 2>/dev/null | wc -l | tr -d ' ')
  c2=$(grep -rIlF "$KEY" . --exclude-dir=.git 2>/dev/null | wc -l | tr -d ' ')
  n=$((c1 + c2))
fi
p=$(git grep -n -E 'YOUCAM_API_KEY=[A-Za-z0-9_-]{16,}|Bearer [A-Za-z0-9_-]{20,}' $(git rev-list --all) 2>/dev/null | wc -l | tr -d ' ')
echo "key-hits=$n pattern-hits=$p"
[ "$n" = 0 ] && [ "$p" = 0 ]

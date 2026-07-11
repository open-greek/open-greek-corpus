#!/bin/bash
# Incremental work-lemma matrix rebuild with the GPU lemmatization phase on
# CORSAIRONE (Ubuntu partition, RTX 2080 Ti). Run from the Mac, from the repo
# root or anywhere:
#
#   scripts/rebuild_matrix_remote.sh            # full incremental rebuild
#   SHARDS=6 scripts/rebuild_matrix_remote.sh   # more parallel GPU workers
#
# Thanks to the caches under data/cache/ this only tokenizes new/changed
# corpus files and only lemmatizes never-seen forms, so most reruns ship a
# small forms list. If nothing is missing, the remote phase is skipped
# entirely. The remote runs the CURRENT local lemmatize_forms.py (scp'd each
# run, so remote code can never be stale); Dilemma's per-form beam search is
# Python-bound, so SHARDS parallel workers share the GPU (default 4).
#
# One-time host setup (already done 2026-07-03): ~/dilemma-env venv with
# torch cu130; ~/repos/dilemma cloned + pip install -e; dilemma data at
# ~/.cache/dilemma with encoder.onnx removed (forces the torch CUDA backend).
set -euo pipefail

REPO="$(cd "$(dirname "$0")/.." && pwd)"
HOST="${CORSAIRONE:-cisco@corsairone.local}"
PY="~/dilemma-env/bin/python"
RDIR="matrix_rebuild"
SHARDS="${SHARDS:-4}"

cd "$REPO"

echo "== phase 1: incremental tokenization + missing-forms list =="
python3 scripts/build_work_lemma_counts.py --emit-missing data/missing_forms.tsv

n_missing=$(wc -l < data/missing_forms.tsv | tr -d ' ')
if [ "$n_missing" -eq 0 ]; then
  echo "== no unseen forms: finishing locally, no GPU phase =="
  python3 scripts/build_work_lemma_counts.py
  exit 0
fi

echo "== phase 2: lemmatize $n_missing forms on $HOST ($SHARDS workers) =="
ssh "$HOST" "mkdir -p ~/$RDIR && rm -f ~/$RDIR/shard_* ~/$RDIR/map_shard_*"
scp -q data/missing_forms.tsv scripts/lemmatize_forms.py "$HOST:~/$RDIR/"
ssh "$HOST" "cd ~/$RDIR && split -n l/$SHARDS -d missing_forms.tsv shard_ && \
  for s in shard_*; do \
    setsid bash -c \"nohup $PY ~/$RDIR/lemmatize_forms.py ~/$RDIR/\$s ~/$RDIR/map_\$s.tsv --device cuda --chunk 10000 > ~/$RDIR/\$s.log 2>&1\" < /dev/null & \
  done; sleep 2; pgrep -fc 'lemmatize_forms.py' || true"

echo "== waiting for workers (polling every 60s) =="
while ssh "$HOST" "pgrep -f 'lemmatize_forms.py' > /dev/null"; do
  done_n=$(ssh "$HOST" "cat ~/$RDIR/map_shard_*.tsv 2>/dev/null | wc -l" | tr -d ' ')
  echo "  mapped $done_n/$n_missing ..."
  sleep 60
done
ssh "$HOST" "grep -l Traceback ~/$RDIR/shard_*.log 2>/dev/null" && {
  echo "ERROR: a worker crashed; see ~/$RDIR/*.log on $HOST" >&2; exit 1; } || true

ssh "$HOST" "cat ~/$RDIR/map_shard_*.tsv" > data/lemma_map.tsv
echo "== pulled $(wc -l < data/lemma_map.tsv | tr -d ' ') mappings =="

echo "== phase 3: merge map + roll up the matrix locally =="
python3 scripts/build_work_lemma_counts.py --lemma-map data/lemma_map.tsv
echo "== rebuild complete =="

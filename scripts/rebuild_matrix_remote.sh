#!/bin/bash
# Incremental work-lemma matrix rebuild with the GPU lemmatization phase on
# fragbox (RTX 4090). Run from the Mac, from the repo
# root or anywhere:
#
#   scripts/rebuild_matrix_remote.sh            # full incremental rebuild
#   SHARDS=6 scripts/rebuild_matrix_remote.sh   # more parallel GPU workers
#
# Thanks to the caches under data/cache/ this only tokenizes new/changed
# corpus files and only lemmatizes never-seen forms, so most reruns ship a
# small forms list. If nothing is missing, the remote phase is skipped
# entirely. The source checkout must be committed and clean; this script pushes
# its branch, pulls it remotely and verifies the exact commit before any GPU
# step. Only the generated forms list is copied. Dilemma's beam search is
# Python-bound, so SHARDS parallel workers share the GPU (default 4).
#
# The SSH host defaults to fragbox; MATRIX_HOST can select another configured
# Linux host. MATRIX_REMOTE_REPO defaults to repos/open-greek-corpus under the
# remote home directory. MATRIX_PYTHON defaults to repos/dilemma/.venv/bin/python.
# The Dilemma environment must already have working CUDA. This wrapper does not
# install packages or modify the model environment.
set -euo pipefail

REPO="$(cd "$(dirname "$0")/.." && pwd)"
HOST="${MATRIX_HOST:-fragbox}"
REMOTE_REPO="${MATRIX_REMOTE_REPO:-repos/open-greek-corpus}"
PY="${MATRIX_PYTHON:-repos/dilemma/.venv/bin/python}"
RDIR="matrix_rebuild"
SHARDS="${SHARDS:-4}"
case "$SHARDS" in
  ''|*[!0-9]*) echo "SHARDS must be a positive integer." >&2; exit 1 ;;
esac
[ "$SHARDS" -gt 0 ] || { echo "SHARDS must be positive." >&2; exit 1; }

cd "$REPO"

remote_bash() {
  local arguments
  printf -v arguments '%q ' "$@"
  ssh "$HOST" "bash -s -- $arguments"
}

echo "== phase 1: incremental tokenization + missing-forms list =="
python3 scripts/build_work_lemma_counts.py --emit-missing data/missing_forms.tsv

n_missing=$(wc -l < data/missing_forms.tsv | tr -d ' ')
if [ "$n_missing" -eq 0 ]; then
  echo "== no unseen forms: finishing locally, no GPU phase =="
  python3 scripts/build_work_lemma_counts.py
  exit 0
fi

if [ -n "$(git status --porcelain)" ]; then
  echo "Commit and push local changes before running the remote pipeline." >&2
  exit 1
fi
branch=$(git symbolic-ref --quiet --short HEAD) || {
  echo "Check out a branch before running the remote pipeline." >&2
  exit 1
}
commit=$(git rev-parse HEAD)
origin=$(git remote get-url origin)
git push origin "$branch"

echo "== update remote source checkout to $commit =="
remote_bash "$REMOTE_REPO" "$branch" "$commit" "$origin" "$PY" <<'REMOTE'
set -euo pipefail
repo=$1
branch=$2
expected=$3
origin=$4
python=$5
[[ "$repo" = /* ]] || repo="$HOME/$repo"
[[ "$python" = /* ]] || python="$HOME/$python"
if ! git -C "$repo" rev-parse --is-inside-work-tree > /dev/null 2>&1; then
  mkdir -p "$(dirname "$repo")"
  git clone --branch "$branch" "$origin" "$repo"
fi
cd "$repo"
if [ -n "$(git status --porcelain)" ]; then
  echo "Remote checkout has local changes; preserve them before updating." >&2
  exit 1
fi
git fetch origin "$branch"
if git show-ref --verify --quiet "refs/heads/$branch"; then
  git switch "$branch"
else
  git switch --create "$branch" --track "origin/$branch"
fi
git pull --ff-only origin "$branch"
test "$(git rev-parse HEAD)" = "$expected" || {
  echo "Remote source commit differs from the pushed local commit." >&2
  exit 1
}
test -x "$python" || {
  echo "Set MATRIX_PYTHON to the prepared Dilemma environment's Python." >&2
  exit 1
}
REMOTE

echo "== phase 2: lemmatize $n_missing forms on $HOST ($SHARDS workers) =="
ssh "$HOST" "mkdir -p ~/$RDIR && rm -f ~/$RDIR/shard_* ~/$RDIR/map_shard_*"
scp -q data/missing_forms.tsv "$HOST:~/$RDIR/"
remote_bash "$REMOTE_REPO" "$PY" "$RDIR" "$SHARDS" <<'REMOTE'
set -euo pipefail
repo=$1
python=$2
directory="$HOME/$3"
shards=$4
[[ "$repo" = /* ]] || repo="$HOME/$repo"
[[ "$python" = /* ]] || python="$HOME/$python"
cd "$directory"
split -n "l/$shards" -d missing_forms.tsv shard_
for shard in shard_*; do
  setsid nohup "$python" -u "$repo/scripts/lemmatize_forms.py" \
    "$directory/$shard" "$directory/map_$shard.tsv" --device cuda --chunk 10000 \
    < /dev/null > "$directory/$shard.log" 2>&1 &
done
REMOTE

echo "== waiting for workers (polling every 60s) =="
while ssh "$HOST" "pgrep -f '[l]emmatize_forms.py.*$RDIR/shard_' > /dev/null"; do
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

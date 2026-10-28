#!/bin/bash
# Lane ME pod entry: devpod runs `bash run.sh <minutes>` with cwd = the payload and $OUT exported; everything under $OUT is
# pulled and sha256'd before the release. Order: manifest -> pinned torch -> CIFAR-10 fetch (md5 pinned) -> checks ->
# CIFAR and LM lr selection (validation) -> the pre-registered CIFAR and LM lists (sweep.py --phase pod, then minspec)
# until done or the deadline. Results are DEV.
set -u
MIN=${1:-100}
HERE=$(cd "$(dirname "$0")" && pwd)
OUT=${OUT:-$HERE/out}
mkdir -p "$OUT"
T0=$(date +%s)
DEADLINE=$(( T0 + (MIN - 4) * 60 ))
log() { echo "$(date -u +%H:%M:%SZ) $*" | tee -a "$OUT/RUN-STEPS.txt"; }
log "start; run minutes $MIN"
( cd "$HERE" && sha256sum -c MANIFEST.sha256 > "$OUT/manifest-check.txt" 2>&1 ) || { log "PAYLOAD MANIFEST MISMATCH"; exit 3; }
nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv > "$OUT/gpu.txt" 2>&1
nproc > "$OUT/nproc.txt" 2>&1
PY=${ME_PY:-$(command -v python3 || command -v python)}
if [ "${ME_DRY:-0}" != "1" ]; then
  $PY -m pip install --no-cache-dir torch==2.7.1 numpy==2.2.6 --index-url https://download.pytorch.org/whl/cu126 > "$OUT/pip.log" 2>&1 \
    || $PY -m pip install --no-cache-dir torch==2.7.1 numpy --index-url https://download.pytorch.org/whl/cu126 >> "$OUT/pip.log" 2>&1 \
    || { log "PIP FAILED"; exit 4; }
  $PY -m pip freeze > "$OUT/pip-freeze.txt" 2>&1
  log "torch $($PY -c 'import torch;print(torch.__version__, torch.cuda.get_device_name(0))' 2>&1)"
  mkdir -p "$HERE/data"
  curl -sS -L --retry 3 -A "altone-x1kme/1" -o "$HERE/data/cifar-10-python.tar.gz" https://www.cs.toronto.edu/~kriz/cifar-10-python.tar.gz \
    || log "CIFAR FETCH FAILED"
  MD5=$(md5sum "$HERE/data/cifar-10-python.tar.gz" 2>/dev/null | cut -c1-32)
  echo "$MD5  cifar-10-python.tar.gz" > "$OUT/cifar-md5.txt"
  if [ "$MD5" = "c58f30108f718f92721af3b95e74349a" ]; then
    ( cd "$HERE/data" && tar xzf cifar-10-python.tar.gz ) && log "cifar ok (md5 pinned)"
  else
    log "CIFAR MD5 MISMATCH ($MD5): CIFAR skipped"
  fi
fi
export ME_RECORDS="$OUT/records"
mkdir -p "$ME_RECORDS" && cp "$HERE"/records/*.json "$ME_RECORDS/"
export ME_CIFAR="$HERE/data/cifar-10-batches-py" ME_ENWIK8_SLICES="$HERE/slices" PYTHONDONTWRITEBYTECODE=1
$PY -B "$HERE/sim/test_memsim.py" --out "$OUT/TESTS-pod.json" > "$OUT/tests.txt" 2>&1 || { log "CHECKS FAILED ON THE POD"; tail -3 "$OUT/tests.txt"; exit 5; }
log "checks: $(tail -1 "$OUT/tests.txt")"
W=${ME_WORKERS:-3}
LOGS="$OUT/logs"
SW="$PY -B $HERE/sim/sweep.py --workers $W --logdir $LOGS --deadline-epoch $DEADLINE"
PHASE=${ME_PHASE:-podall}
for T in lm cifar; do
  if [ "$PHASE" != podall ]; then break; fi
  if [ "$T" = cifar ] && [ ! -d "$ME_CIFAR" ]; then continue; fi
  $SW --phase lrsel --task $T > "$OUT/sweep-lrsel-$T.txt" 2>&1 && $PY -B "$HERE/sim/choose.py" lr $T >> "$OUT/sweep-lrsel-$T.txt" 2>&1
  log "lrsel $T rc $?: $(tail -1 "$OUT/sweep-lrsel-$T.txt" | cut -c1-120)"
done
TS=lm; [ -d "$ME_CIFAR" ] && TS=lm,cifar
TS=${ME_TASKS:-$TS}
if [ "$PHASE" = scalelr ]; then
  for J in ${ME_SCALE_JOBS:-}; do
    $PY -B "$HERE/sim/scale_lr.py" --task ${J%%:*} --width ${J##*:} --workers $W >> "$OUT/sweep-scalelr.txt" 2>&1
    log "scalelr $J rc $?: $(tail -1 "$OUT/sweep-scalelr.txt" | cut -c1-120)"
  done
  log "done"
  exit 0
fi
$SW --phase $PHASE --task $TS > "$OUT/sweep-$PHASE.txt" 2>&1
log "$PHASE $TS rc $?: $(tail -1 "$OUT/sweep-$PHASE.txt" | cut -c1-200)"
log "done"
exit 0

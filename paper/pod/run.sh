#!/bin/bash
# Lane ME-PAPER pod entry: devpod runs `bash run.sh <minutes>` with cwd = the payload and $OUT exported; everything under $OUT
# is pulled and sha256'd before the release. Order:
#   1. manifest;
#   2. pinned torch;
#   3. CIFAR-10 fetch (md5 pinned) when a phase needs it;
#   4. both check suites (a failure stops the sitting);
#   5. the phases of $ME_PHASES in order, each as "phase[:tasks]", until done or the deadline.
# Results are DEV until the paper's tables are generated from them.
set -u
MIN=${1:-100}
HERE=$(cd "$(dirname "$0")" && pwd)
OUT=${OUT:-$HERE/out}
mkdir -p "$OUT"
T0=$(date +%s)
DEADLINE=$(( T0 + (MIN - 4) * 60 ))
log() { echo "$(date -u +%H:%M:%SZ) $*" | tee -a "$OUT/RUN-STEPS.txt"; }
log "start; run minutes $MIN; phases ${ME_PHASES:-none}"
( cd "$HERE" && sha256sum -c MANIFEST.sha256 > "$OUT/manifest-check.txt" 2>&1 ) || { log "PAYLOAD MANIFEST MISMATCH"; exit 3; }
nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv > "$OUT/gpu.txt" 2>&1
nproc > "$OUT/nproc.txt" 2>&1
cat /sys/fs/cgroup/cpu.max > "$OUT/cpu-max.txt" 2>&1
PY=${ME_PY:-$(command -v python3 || command -v python)}
if [ "${ME_DRY:-0}" != "1" ]; then
  $PY -m pip install --no-cache-dir torch==2.7.1 numpy==2.2.6 --index-url https://download.pytorch.org/whl/cu126 > "$OUT/pip.log" 2>&1 \
    || $PY -m pip install --no-cache-dir torch==2.7.1 numpy --index-url https://download.pytorch.org/whl/cu126 >> "$OUT/pip.log" 2>&1 \
    || { log "PIP FAILED"; exit 4; }
  $PY -m pip freeze > "$OUT/pip-freeze.txt" 2>&1
  log "torch $($PY -c 'import torch;print(torch.__version__, torch.cuda.get_device_name(0))' 2>&1)"
  if [ "${ME_NO_CIFAR:-0}" != "1" ]; then
    mkdir -p "$HERE/data"
    curl -sS -L --retry 3 -A "altone-x1kmp/1" -o "$HERE/data/cifar-10-python.tar.gz" https://www.cs.toronto.edu/~kriz/cifar-10-python.tar.gz \
      || log "CIFAR FETCH FAILED"
    MD5=$(md5sum "$HERE/data/cifar-10-python.tar.gz" 2>/dev/null | cut -c1-32)
    echo "$MD5  cifar-10-python.tar.gz" > "$OUT/cifar-md5.txt"
    if [ "$MD5" = "c58f30108f718f92721af3b95e74349a" ]; then
      ( cd "$HERE/data" && tar xzf cifar-10-python.tar.gz ) && log "cifar ok (md5 pinned)"
    else
      log "CIFAR MD5 MISMATCH ($MD5)"; exit 6
    fi
  fi
fi
export ME_RECORDS="$OUT/records" ME_LANE_ME="$HERE/lane_me"
mkdir -p "$ME_RECORDS" && cp "$HERE"/records/*.json "$ME_RECORDS/"
[ -f "$HERE/records/runs.tar" ] && tar xf "$HERE/records/runs.tar" -C "$ME_RECORDS"
export ME_CIFAR="${ME_CIFAR:-$HERE/data/cifar-10-batches-py}" ME_ENWIK8_SLICES="$HERE/slices" ME_MNIST="$HERE/data/mnist" PYTHONDONTWRITEBYTECODE=1
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
$PY -B "$HERE/sim/test_paper.py" --out "$OUT/TESTS-PAPER-pod.json" > "$OUT/tests-paper.txt" 2>&1 || { log "PAPER CHECKS FAILED ON THE POD"; tail -3 "$OUT/tests-paper.txt"; exit 5; }
$PY -B "$HERE/sim/test_memsim.py" --out "$OUT/TESTS-laneME-pod.json" > "$OUT/tests-laneme.txt" 2>&1 || { log "LANE ME CHECKS FAILED ON THE POD"; exit 5; }
log "checks: $(tail -1 "$OUT/tests-paper.txt") $(tail -1 "$OUT/tests-laneme.txt")"
W=${ME_WORKERS:-6}
SW="$PY -B $HERE/sim/sweep_paper.py --workers $W --logdir $OUT/logs --deadline-epoch $DEADLINE ${ME_EXTRA:-}"
for PH in ${ME_PHASES:-}; do
  P=${PH%%:*}; T=""
  [ "$P" != "$PH" ] && T="--task ${PH#*:}"
  log "phase $PH begins"
  $SW --phase $P $T > "$OUT/sweep-$P-$(date +%s).txt" 2>&1
  log "phase $PH rc $?"
  [ $(date +%s) -ge $DEADLINE ] && { log "deadline reached"; break; }
done
log "done"
exit 0

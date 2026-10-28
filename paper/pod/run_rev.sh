#!/bin/bash
# Lane ME-REVISE pod entry (derived from pod/run.sh): devpod runs `bash run.sh <minutes>` with cwd = the payload and $OUT
# exported; everything under $OUT is pulled and sha256'd before the release. Order:
#   1. manifest; 2. pinned torch; 3. ME_AIHWKIT=1: aihwkit from PyPI in its own venv, in the background, then its preset
#   curves (revision/aihwkit_curves.py -> $OUT/AIHWKIT-CURVES.json); 4. CIFAR-10 (md5 pinned) unless ME_NO_CIFAR=1;
#   5. the revision checks (test_rev.py; a failure stops the sitting); 6. the phases of $ME_PHASES (sweep_rev.py).
set -u
MIN=${1:-100}
HERE=$(cd "$(dirname "$0")" && pwd)
OUT=${OUT:-$HERE/out}
mkdir -p "$OUT"
T0=$(date +%s)
DEADLINE=$(( T0 + (MIN - 4) * 60 ))
log() { echo "$(date -u +%H:%M:%SZ) $*" | tee -a "$OUT/RUN-STEPS.txt"; }
log "start; run minutes $MIN; phases ${ME_PHASES:-none}; aihwkit ${ME_AIHWKIT:-0}"
( cd "$HERE" && sha256sum -c MANIFEST.sha256 > "$OUT/manifest-check.txt" 2>&1 ) || { log "PAYLOAD MANIFEST MISMATCH"; exit 3; }
nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv > "$OUT/gpu.txt" 2>&1
nproc > "$OUT/nproc.txt" 2>&1
cat /sys/fs/cgroup/cpu.max > "$OUT/cpu-max.txt" 2>&1
PY=${ME_PY:-$(command -v python3 || command -v python)}
$PY --version > "$OUT/python-version.txt" 2>&1
if [ "${ME_AIHWKIT:-0}" = "1" ]; then
  (
    if $PY -m venv /root/aihw > "$OUT/aihw-pip.log" 2>&1; then
      APY=/root/aihw/bin/python; APATH=""
      # aihwkit 1.1.0 (2026-02-03, the newest with cp310 wheels) does not state the torch it was built against: torch 2.14.1
      # broke its tensor binding (r2) and 2.9.1 lacks a symbol it needs (r3). Install it without dependencies, then try torch
      # CPU wheels in order until its compiled module imports; the version found is recorded in aihw-freeze.txt.
      $APY -m pip install --no-cache-dir --no-deps aihwkit==1.1.0 >> "$OUT/aihw-pip.log" 2>&1
      $APY -m pip install --no-cache-dir matplotlib scipy numpy requests protobuf tqdm scikit-learn >> "$OUT/aihw-pip.log" 2>&1
      for TV in 2.10.0 2.11.0 2.12.0 2.13.0 2.10.1 2.11.1 2.8.0; do
        $APY -m pip install --no-cache-dir "torch==$TV" --index-url https://download.pytorch.org/whl/cpu >> "$OUT/aihw-pip.log" 2>&1 || continue
        if $APY -c "import aihwkit.simulator.rpu_base" >> "$OUT/aihw-pip.log" 2>&1; then echo "aihwkit imports with torch $TV" >> "$OUT/aihw-pip.log"; break; fi
      done
      $APY -c "import aihwkit.utils.visualization" >> "$OUT/aihw-pip.log" 2>&1 \
        || $APY -m pip install --no-cache-dir --no-deps torchvision --index-url https://download.pytorch.org/whl/cpu >> "$OUT/aihw-pip.log" 2>&1
    else  # no venv module in the image: a separate target directory
      APY=$PY; APATH=/root/aihwlib
      $PY -m pip install --no-cache-dir --target /root/aihwlib aihwkit matplotlib >> "$OUT/aihw-pip.log" 2>&1
    fi
    PYTHONPATH=$APATH $APY -m pip freeze --path "${APATH:-/root/aihw/lib}" > "$OUT/aihw-freeze.txt" 2>&1
    PYTHONPATH=$APATH OMP_NUM_THREADS=2 CUDA_VISIBLE_DEVICES= $APY -B "$HERE/revision/aihwkit_curves.py" "$OUT/AIHWKIT-CURVES.json" > "$OUT/aihw-run.txt" 2>&1
    echo "aihwkit rc $?" >> "$OUT/aihw-run.txt"
  ) &
  AIHW_PID=$!
fi
if [ "${ME_DRY:-0}" != "1" ]; then
  $PY -m pip install --no-cache-dir torch==2.7.1 numpy==2.2.6 --index-url https://download.pytorch.org/whl/cu126 > "$OUT/pip.log" 2>&1 \
    || $PY -m pip install --no-cache-dir torch==2.7.1 numpy --index-url https://download.pytorch.org/whl/cu126 >> "$OUT/pip.log" 2>&1 \
    || { log "PIP FAILED"; exit 4; }
  $PY -m pip freeze > "$OUT/pip-freeze.txt" 2>&1
  log "torch $($PY -c 'import torch;print(torch.__version__, torch.cuda.get_device_name(0))' 2>&1)"
  if [ "${ME_NO_CIFAR:-0}" != "1" ]; then
    mkdir -p "$HERE/data"
    curl -sS -L --retry 3 -A "altone-x1kmr/1" -o "$HERE/data/cifar-10-python.tar.gz" https://www.cs.toronto.edu/~kriz/cifar-10-python.tar.gz \
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
mkdir -p "$ME_RECORDS/revision" && cp "$HERE"/records/*.json "$ME_RECORDS/" && cp "$HERE"/records/revision/*.json "$ME_RECORDS/revision/"
[ -f "$HERE/records/runs.tar" ] && tar xf "$HERE/records/runs.tar" -C "$ME_RECORDS"
export ME_CIFAR="${ME_CIFAR:-$HERE/data/cifar-10-batches-py}" ME_ENWIK8_SLICES="$HERE/slices" ME_MNIST="$HERE/data/mnist" PYTHONDONTWRITEBYTECODE=1
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
if [ "${ME_SKIP_TESTS:-0}" != "1" ]; then
  $PY -B "$HERE/sim/test_rev.py" --out "$OUT/TESTS-REV-pod.json" > "$OUT/tests-rev.txt" 2>&1 || { log "REVISION CHECKS FAILED ON THE POD"; tail -3 "$OUT/tests-rev.txt"; exit 5; }
  log "checks: $(tail -1 "$OUT/tests-rev.txt")"
fi
W=${ME_WORKERS:-8}
SW="$PY -B $HERE/sim/sweep_rev.py --workers $W --logdir $OUT/logs --deadline-epoch $DEADLINE ${ME_EXTRA:-}"
for PH in ${ME_PHASES:-}; do
  P=${PH%%:*}; T=""
  [ "$P" != "$PH" ] && T="--task ${PH#*:}"
  log "phase $PH begins"
  $SW --phase $P $T > "$OUT/sweep-$P-$(date +%s).txt" 2>&1
  log "phase $PH rc $?"
  [ $(date +%s) -ge $DEADLINE ] && { log "deadline reached"; break; }
done
if [ -n "${AIHW_PID:-}" ]; then
  wait $AIHW_PID
  log "aihwkit: $(tail -1 "$OUT/aihw-run.txt" 2>/dev/null)"
fi
log "done"
exit 0

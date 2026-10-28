#!/usr/bin/env python3
"""Fetch the three public datasets of the memistor paper and check them against the digests the paper pins.

The deposit does not contain MNIST, CIFAR-10 or enwik8. This script downloads them (standard library only) into
<this folder>/data/ and verifies every file:

    data/mnist/{train-images-idx3-ubyte.gz, train-labels-idx1-ubyte.gz, t10k-images-idx3-ubyte.gz, t10k-labels-idx1-ubyte.gz}
    data/cifar-10-batches-py/{data_batch_1, ..., test_batch}     (from cifar-10-python.tar.gz)
    data/enwik8                                                  (100,000,000 bytes, from enwik8.zip)

The simulators find them there by default (paper/sim/tasks.py and sim/tasks.py default to <deposit>/data/...;
the environment variables ME_MNIST, ME_CIFAR and ME_ENWIK8 still override).

Where each digest comes from:
  * MNIST: the four SHA-256 values in paper/sim/tasks.py (DATA["mnist_sha"]); the paper's loader refuses any other bytes.
  * enwik8: the SHA-256 in paper/sim/tasks.py (DATA["enwik8_sha"]) and the SHA-256 of the two slices the paper cuts from it
    (SLICE_SHA: 8 MB from byte 40,000,000 for training; 0.5 MB from byte 60,000,000 for validation).
  * CIFAR-10: the paper pins the MD5 of cifar-10-python.tar.gz (pod/run.sh: c58f30108f718f92721af3b95e74349a). The SHA-256
    of that tar and of the batch files below were computed by the deposit builder from the copy whose MD5 matches the
    pinned one; they are extra checks, not values taken from the paper.

Usage:
    python fetch_data.py                     fetch whatever is missing or wrong, then verify everything
    python fetch_data.py --verify-only       download nothing; verify the files under data/ (exit 1 on any failure)
    python fetch_data.py --only mnist        one of: mnist cifar10 enwik8 (repeatable)
    python fetch_data.py --verify-only --mnist-dir D --cifar-dir D --enwik8-file F    verify copies kept elsewhere
    python fetch_data.py --selftest          show that the verify step FAILS on a corrupted copy of each kind of file
"""
import argparse
import hashlib
import io
import os
import shutil
import sys
import tarfile
import tempfile
import urllib.request
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
UA = "memistor-deposit-fetch/1.0 (+python-urllib)"

MNIST_SHA = {
    "train-images-idx3-ubyte.gz": "440fcabf73cc546fa21475e81ea370265605f56be210a4024d2ca8f203523609",
    "train-labels-idx1-ubyte.gz": "3552534a0a558bbed6aed32b30c495cca23d567ec52cac8be1a0730e8010255c",
    "t10k-images-idx3-ubyte.gz": "8d422c7b0a1c1c79245a5bcf07fe86e33eeafee792b84584aec276f5a2dbc4e6",
    "t10k-labels-idx1-ubyte.gz": "f7ae60f92e00ec6debd23a6088c31dbd2371eca3ffa0defaefb259924204aec6",
}
MNIST_MIRRORS = [
    "https://ossci-datasets.s3.amazonaws.com/mnist/",
    "https://storage.googleapis.com/cvdf-datasets/mnist/",
    "https://yann.lecun.com/exdb/mnist/",
]
CIFAR_URL = "https://www.cs.toronto.edu/~kriz/cifar-10-python.tar.gz"
CIFAR_TAR_MD5 = "c58f30108f718f92721af3b95e74349a"  # pinned by the paper (pod/run.sh)
CIFAR_TAR_SHA256 = "6d958be074577803d12ecdefd02955f39262c83c16fe9348329d7fe0b5c001ce"  # computed by the builder
CIFAR_BATCH_SHA = {  # computed by the builder from the extracted copy of the md5-matching tar (the files the loader reads)
    "data_batch_1": "54636561a3ce25bd3e19253c6b0d8538147b0ae398331ac4a2d86c6d987368cd",
    "data_batch_2": "766b2cef9fbc745cf056b3152224f7cf77163b330ea9a15f9392beb8b89bc5a8",
    "test_batch": "f53d8d457504f7cff4ea9e021afcf0e0ad8e24a91f3fc42091b8adef61157831",
}
ENWIK8_URLS = ["http://mattmahoney.net/dc/enwik8.zip", "https://mattmahoney.net/dc/enwik8.zip"]
ENWIK8_SHA = "2b49720ec4d78c3c9fabaee6e4179a5e997302b3a70029f30f2d582218c024a8"
ENWIK8_BYTES = 100_000_000
ENWIK8_SLICES = {  # name -> (offset, length, sha256), as in paper/sim/tasks.py (DATA lm_train / lm_val, SLICE_SHA)
    "train": (40_000_000, 8_000_000, "eab3bbbebfe6297b6502200a80f3837bc2806fb7e90d6945dac1ba0163b1d2eb"),
    "val": (60_000_000, 500_000, "a40733af023fca66f601216d01ffb4f4225c9c625d18a3b432357cac0303884d"),
}


def hexdigest(path, algo="sha256"):
    h = hashlib.new(algo)
    with open(path, "rb") as f:
        for blk in iter(lambda: f.read(1 << 20), b""):
            h.update(blk)
    return h.hexdigest()


def slice_sha(path, off, n):
    with open(path, "rb") as f:
        f.seek(off)
        b = f.read(n)
    return len(b), hashlib.sha256(b).hexdigest()


# ---- verify (each returns a list of problems; empty = verified) ----
def verify_mnist(d):
    bad = []
    for fn, want in MNIST_SHA.items():
        p = os.path.join(d, fn)
        if not os.path.isfile(p):
            bad.append(f"mnist: missing {p}")
        elif hexdigest(p) != want:
            bad.append(f"mnist: SHA-256 mismatch {p}")
    return bad


def verify_cifar(d):
    bad = []
    for fn, want in CIFAR_BATCH_SHA.items():
        p = os.path.join(d, fn)
        if not os.path.isfile(p):
            bad.append(f"cifar10: missing {p}")
        elif hexdigest(p) != want:
            bad.append(f"cifar10: SHA-256 mismatch {p}")
    return bad


def verify_enwik8(path):
    if not os.path.isfile(path):
        return [f"enwik8: missing {path}"]
    bad = []
    if os.path.getsize(path) != ENWIK8_BYTES:
        bad.append(f"enwik8: size {os.path.getsize(path)} != {ENWIK8_BYTES}")
    if hexdigest(path) != ENWIK8_SHA:
        bad.append(f"enwik8: SHA-256 mismatch {path}")
    for name, (off, n, want) in ENWIK8_SLICES.items():
        got_n, got = slice_sha(path, off, n)
        if got_n != n or got != want:
            bad.append(f"enwik8: slice '{name}' ({off}+{n}) digest mismatch")
    return bad


# ---- fetch ----
def http_get(url, dest):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=120) as r, open(dest, "wb") as f:
        shutil.copyfileobj(r, f, 1 << 20)


def fetch_mnist(d):
    os.makedirs(d, exist_ok=True)
    for fn, want in MNIST_SHA.items():
        p = os.path.join(d, fn)
        if os.path.isfile(p) and hexdigest(p) == want:
            continue
        ok = False
        for base in MNIST_MIRRORS:
            tmp = p + ".part"
            try:
                print(f"  GET {base}{fn}")
                http_get(base + fn, tmp)
            except Exception as e:  # try the next mirror
                print(f"    failed: {e}")
                continue
            if hexdigest(tmp) == want:
                os.replace(tmp, p)
                ok = True
                break
            print("    digest mismatch, trying the next mirror")
            os.remove(tmp)
        if not ok:
            raise SystemExit(f"mnist: no mirror gave {fn} with the pinned SHA-256")


def safe_extract(tf, dest):
    root = os.path.realpath(dest)
    for m in tf.getmembers():
        t = os.path.realpath(os.path.join(dest, m.name))
        if not (t == root or t.startswith(root + os.sep)) or not (m.isfile() or m.isdir()):
            raise SystemExit(f"cifar10: refusing archive member {m.name!r}")
    tf.extractall(dest)


def fetch_cifar(d, top):
    if not verify_cifar(d):
        return
    os.makedirs(top, exist_ok=True)
    tar = os.path.join(top, "cifar-10-python.tar.gz")
    if not (os.path.isfile(tar) and hexdigest(tar, "md5") == CIFAR_TAR_MD5):
        print(f"  GET {CIFAR_URL}")
        http_get(CIFAR_URL, tar + ".part")
        if hexdigest(tar + ".part", "md5") != CIFAR_TAR_MD5:
            os.remove(tar + ".part")
            raise SystemExit("cifar10: the download does not match the md5 the paper pins")
        os.replace(tar + ".part", tar)
    if hexdigest(tar) != CIFAR_TAR_SHA256:
        raise SystemExit("cifar10: tar SHA-256 differs from the builder's record (md5 matched)")
    with tarfile.open(tar, "r:gz") as tf:
        safe_extract(tf, top)


def fetch_enwik8(path):
    if not verify_enwik8(path):
        return
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    zp = path + ".zip.part"
    last = None
    for u in ENWIK8_URLS:
        try:
            print(f"  GET {u}")
            http_get(u, zp)
            last = None
            break
        except Exception as e:
            last = e
            print(f"    failed: {e}")
    if last is not None:
        raise SystemExit(f"enwik8: download failed: {last}")
    with zipfile.ZipFile(zp) as z:
        names = z.namelist()
        if names != ["enwik8"]:
            raise SystemExit(f"enwik8: unexpected zip members {names}")
        with z.open("enwik8") as src, open(path + ".part", "wb") as dst:
            shutil.copyfileobj(src, dst, 1 << 20)
    os.remove(zp)
    os.replace(path + ".part", path)


# ---- selftest: the verify step must FAIL on each corrupted kind of file ----
def selftest():
    sys.stdout.write("selftest: corrupt a copy of each kind of file and require the verify step to fail\n")
    tmp = tempfile.mkdtemp(prefix="fetchselftest-")
    fails = []
    try:
        # a verify of a missing dataset must fail
        for name, bad in (("mnist (missing)", verify_mnist(os.path.join(tmp, "none"))),
                          ("cifar10 (missing)", verify_cifar(os.path.join(tmp, "none"))),
                          ("enwik8 (missing)", verify_enwik8(os.path.join(tmp, "none")))):
            print(f"  {name}: {'refused' if bad else 'NOT REFUSED'}")
            if not bad:
                fails.append(name)
        # wrong bytes under the right names must fail
        for d, names, fn in ((os.path.join(tmp, "m"), MNIST_SHA, verify_mnist),
                             (os.path.join(tmp, "c"), CIFAR_BATCH_SHA, verify_cifar)):
            os.makedirs(d)
            for n in names:
                with open(os.path.join(d, n), "wb") as f:
                    f.write(b"not the real bytes")
            bad = fn(d)
            print(f"  wrong bytes under {len(names)} names: {len(bad)} problems reported")
            if len(bad) != len(names):
                fails.append(d)
        e = os.path.join(tmp, "enwik8")
        with open(e, "wb") as f:
            f.write(b"x" * ENWIK8_BYTES)
        bad = verify_enwik8(e)
        print(f"  enwik8 of the right size and wrong bytes: {len(bad)} problems reported")
        if len(bad) < 2:
            fails.append("enwik8")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print("SELFTEST_OK" if not fails else "SELFTEST_FAILED " + ",".join(fails))
    return 0 if not fails else 1


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data", default=os.path.join(HERE, "data"), help="folder for the three datasets (default: ./data next to this script)")
    ap.add_argument("--only", action="append", choices=["mnist", "cifar10", "enwik8"])
    ap.add_argument("--verify-only", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--mnist-dir")
    ap.add_argument("--cifar-dir")
    ap.add_argument("--enwik8-file")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    which = a.only or ["mnist", "cifar10", "enwik8"]
    mnist = a.mnist_dir or os.path.join(a.data, "mnist")
    cifar = a.cifar_dir or os.path.join(a.data, "cifar-10-batches-py")
    enwik = a.enwik8_file or os.path.join(a.data, "enwik8")
    if not a.verify_only:
        if "mnist" in which:
            print("MNIST")
            fetch_mnist(mnist)
        if "cifar10" in which:
            print("CIFAR-10")
            fetch_cifar(cifar, os.path.dirname(os.path.abspath(cifar)))
        if "enwik8" in which:
            print("enwik8")
            fetch_enwik8(enwik)
    problems = []
    if "mnist" in which:
        problems += verify_mnist(mnist)
    if "cifar10" in which:
        problems += verify_cifar(cifar)
    if "enwik8" in which:
        problems += verify_enwik8(enwik)
    for p in problems:
        print("FAIL", p)
    print("DATA_OK " + " ".join(which) if not problems else f"DATA_FAILED ({len(problems)} problems)")
    return 0 if not problems else 1


if __name__ == "__main__":
    sys.exit(main())

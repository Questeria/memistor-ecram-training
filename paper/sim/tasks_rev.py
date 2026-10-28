"""REVISION copy of paper/sim/tasks.py (lane ME-REVISE 2026-10-26): imports memsim_rev; Lin takes a Streams
(memsim_rev) so the logical init comes from its own stream in every arm, the digital (Adam) arm included.

Tasks for lane ME: MNIST (MLP), a CIFAR-10 subset (small CNN), a byte-level LM on an enwik8 slice
(human-written Wikipedia text of 2006). Data are local files pinned by sha256 (DATA below); nothing is
downloaded by this code."""
import gzip
import hashlib
import math
import os
import pickle

import numpy as np
import torch
import torch.nn.functional as F

from memsim_rev import AnalogLinear

DATA = {
    "mnist_dir": os.environ.get("ME_MNIST", os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "data", "mnist")),
    "mnist_sha": {
        "train-images-idx3-ubyte.gz": "440fcabf73cc546fa21475e81ea370265605f56be210a4024d2ca8f203523609",
        "train-labels-idx1-ubyte.gz": "3552534a0a558bbed6aed32b30c495cca23d567ec52cac8be1a0730e8010255c",
        "t10k-images-idx3-ubyte.gz": "8d422c7b0a1c1c79245a5bcf07fe86e33eeafee792b84584aec276f5a2dbc4e6",
        "t10k-labels-idx1-ubyte.gz": "f7ae60f92e00ec6debd23a6088c31dbd2371eca3ffa0defaefb259924204aec6",
    },
    "cifar_dir": os.environ.get("ME_CIFAR", os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "data", "cifar-10-batches-py")),
    "enwik8": os.environ.get("ME_ENWIK8", os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "data", "enwik8")),
    "enwik8_sha": "2b49720ec4d78c3c9fabaee6e4179a5e997302b3a70029f30f2d582218c024a8",
    # the LM slice: 8 MB train from byte 40,000,000; 0.5 MB validation from byte 60,000,000
    "lm_train": (40_000_000, 8_000_000),
    "lm_val": (60_000_000, 500_000),
}


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for blk in iter(lambda: f.read(1 << 20), b""):
            h.update(blk)
    return h.hexdigest()


def _idx(path):
    with gzip.open(path, "rb") as f:
        b = f.read()
    nd = b[3]
    dims = [int.from_bytes(b[4 + 4 * i: 8 + 4 * i], "big") for i in range(nd)]
    return np.frombuffer(b, dtype=np.uint8, offset=4 + 4 * nd).reshape(dims)


def load_mnist(device, check=True):
    d = DATA["mnist_dir"]
    if check:
        for fn, want in DATA["mnist_sha"].items():
            got = sha256(os.path.join(d, fn))
            if got != want:
                raise SystemExit(f"MNIST digest mismatch {fn}: {got}")
    xtr = _idx(os.path.join(d, "train-images-idx3-ubyte.gz")).reshape(-1, 784).astype(np.float32) / 255.0
    ytr = _idx(os.path.join(d, "train-labels-idx1-ubyte.gz")).astype(np.int64)
    xte = _idx(os.path.join(d, "t10k-images-idx3-ubyte.gz")).reshape(-1, 784).astype(np.float32) / 255.0
    yte = _idx(os.path.join(d, "t10k-labels-idx1-ubyte.gz")).astype(np.int64)
    t = lambda a: torch.from_numpy(np.ascontiguousarray(a)).to(device)
    # train 0..54999, validation 55000..59999 (lr selection only), test = the 10k test set
    return dict(xtr=t(xtr[:55000]), ytr=t(ytr[:55000]), xva=t(xtr[55000:]), yva=t(ytr[55000:]),
                xte=t(xte), yte=t(yte))


def load_cifar_subset(device, n_train=10000):
    d = DATA["cifar_dir"]
    def rd(fn):
        with open(os.path.join(d, fn), "rb") as f:
            o = pickle.load(f, encoding="bytes")
        return o[b"data"].reshape(-1, 3, 32, 32).astype(np.float32) / 255.0, np.array(o[b"labels"], np.int64)
    xs, ys = zip(*[rd(f"data_batch_{i}") for i in (1, 2)])
    x, y = np.concatenate(xs), np.concatenate(ys)
    xte, yte = rd("test_batch")
    mean = x[:n_train].mean(axis=(0, 2, 3), keepdims=True)
    std = x[:n_train].std(axis=(0, 2, 3), keepdims=True)
    nrm = lambda a: (a - mean) / std
    t = lambda a: torch.from_numpy(np.ascontiguousarray(a)).to(device)
    # train = first n_train images of data_batch_1..2; validation = next 2,000; test = the 10k test set
    return dict(xtr=t(nrm(x[:n_train])), ytr=t(y[:n_train]), xva=t(nrm(x[n_train:n_train + 2000])),
                yva=t(y[n_train:n_train + 2000]), xte=t(nrm(xte)), yte=t(yte))


SLICE_SHA = {  # sha256 of the two slices cut from the pinned enwik8 at the DATA offsets; the pod carries only these
    "train": "eab3bbbebfe6297b6502200a80f3837bc2806fb7e90d6945dac1ba0163b1d2eb",
    "val": "a40733af023fca66f601216d01ffb4f4225c9c625d18a3b432357cac0303884d",
}


def load_enwik8_slice(device, check=True):
    sd = os.environ.get("ME_ENWIK8_SLICES")
    if sd:  # the pod: pre-cut slices, each pinned
        t = lambda b: torch.from_numpy(np.frombuffer(b, dtype=np.uint8).astype(np.int64)).to(device)
        out = {}
        for k, fn in (("tr", "train"), ("va", "val")):
            b = open(os.path.join(sd, fn + ".bin"), "rb").read()
            if hashlib.sha256(b).hexdigest() != SLICE_SHA[fn]:
                raise SystemExit(f"enwik8 slice digest mismatch: {fn}")
            out[k] = t(b)
        return out
    p = DATA["enwik8"]
    if check and sha256(p) != DATA["enwik8_sha"]:
        raise SystemExit("enwik8 digest mismatch")
    with open(p, "rb") as f:
        o, n = DATA["lm_train"]; f.seek(o); tr = f.read(n)
        o, n = DATA["lm_val"]; f.seek(o); va = f.read(n)
    t = lambda b: torch.from_numpy(np.frombuffer(b, dtype=np.uint8).astype(np.int64)).to(device)
    return dict(tr=t(tr), va=t(va))


# ---------------------------------------------------------------- models
class Lin:
    """Factory: analog (AnalogLinear over a DeviceSpec) or digital torch.nn.Linear (Adam context arm)."""

    def __init__(self, kind, spec=None, ucfg=None, gen=None, device=None, alpha=None, streams=None):
        self.kind, self.spec, self.ucfg, self.gen, self.device = kind, spec, ucfg, gen, device
        self.streams = streams  # REVISION: None = legacy (gen shared)
        self.alpha = alpha  # fixed weight scale of every layer (the Gokmen-Haensch validation); None: from the init

    def __call__(self, i, o, bias=True, init_gain=1.0):
        if self.kind == "analog":
            return AnalogLinear(i, o, self.spec, self.ucfg, self.gen, self.device, bias=bias, init_gain=init_gain,
                                alpha=self.alpha, streams=self.streams)
        m = torch.nn.Linear(i, o, bias=bias).to(self.device)
        with torch.no_grad():
            b = init_gain * math.sqrt(3.0 / i)
            if self.streams is not None and self.streams.mode == "split":  # the analog arms' formula and stream
                self.streams.next_layer()
                w0 = (torch.rand((o, i), generator=self.streams.init, device=self.device) * 2 - 1) * b
                self.streams.init_log.append(w0)
                m.weight.copy_(w0)
            else:
                m.weight.uniform_(-b, b, generator=self.gen)
            if bias:
                m.bias.zero_()
        return m


class MLP(torch.nn.Module):
    def __init__(self, lin):
        super().__init__()
        self.l1, self.l2, self.l3 = lin(784, 256), lin(256, 128), lin(128, 10)

    def forward(self, x):
        return self.l3(torch.tanh(self.l2(torch.tanh(self.l1(x)))))


class FCN_GH(torch.nn.Module):
    """The fully connected network of Gokmen and Vlasov 2016 and Gokmen and Haensch 2020: 784-256-128-10, sigmoid."""

    def __init__(self, lin):
        super().__init__()
        self.l1, self.l2, self.l3 = lin(784, 256), lin(256, 128), lin(128, 10)

    def forward(self, x):
        return self.l3(torch.sigmoid(self.l2(torch.sigmoid(self.l1(x)))))


class Conv(torch.nn.Module):
    """3x3 conv, padding 1, as a matmul over unfolded patches (the crossbar view)."""

    def __init__(self, lin, cin, cout):
        super().__init__()
        self.cin, self.cout = cin, cout
        self.mm = lin(cin * 9, cout, init_gain=math.sqrt(2.0))

    def forward(self, x):
        B, C, H, W = x.shape
        p = F.unfold(x, 3, padding=1).transpose(1, 2)  # (B, HW, C*9)
        y = self.mm(p)  # (B, HW, cout)
        return y.transpose(1, 2).reshape(B, self.cout, H, W)


class CNN(torch.nn.Module):
    def __init__(self, lin, c=32):  # c = 32 is the pre-registered network; other c only for the DEV scale check
        super().__init__()
        self.c1, self.c2, self.c3 = Conv(lin, 3, c), Conv(lin, c, 2 * c), Conv(lin, 2 * c, 2 * c)
        self.f1, self.f2 = lin(2 * c * 16, 4 * c, init_gain=math.sqrt(2.0)), lin(4 * c, 10)

    def forward(self, x):
        x = F.max_pool2d(F.relu(self.c1(x)), 2)
        x = F.max_pool2d(F.relu(self.c2(x)), 2)
        x = F.max_pool2d(F.relu(self.c3(x)), 2)
        return self.f2(F.relu(self.f1(x.flatten(1))))


class Block(torch.nn.Module):
    def __init__(self, lin, d, nh):
        super().__init__()
        self.nh = nh
        self.n1, self.n2 = torch.nn.LayerNorm(d), torch.nn.LayerNorm(d)
        self.qkv, self.proj = lin(d, 3 * d, bias=False), lin(d, d, bias=False)
        self.fc1, self.fc2 = lin(d, 4 * d), lin(4 * d, d)

    def forward(self, x):
        B, T, D = x.shape
        q, k, v = self.qkv(self.n1(x)).split(D, dim=-1)
        sh = lambda t: t.reshape(B, T, self.nh, D // self.nh).transpose(1, 2)
        a = F.scaled_dot_product_attention(sh(q), sh(k), sh(v), is_causal=True)
        x = x + self.proj(a.transpose(1, 2).reshape(B, T, D))
        return x + self.fc2(F.gelu(self.fc1(self.n2(x))))


class TinyLM(torch.nn.Module):
    def __init__(self, lin, d=128, nl=2, nh=4, ctx=128, vocab=256):
        super().__init__()
        self.vocab = vocab
        self.emb = lin(vocab, d, bias=False, init_gain=1.0)
        self.pos = torch.nn.Parameter(torch.zeros(ctx, d))
        self.blocks = torch.nn.ModuleList([Block(lin, d, nh) for _ in range(nl)])
        self.nf = torch.nn.LayerNorm(d)
        self.head = lin(d, vocab, bias=False)

    def forward(self, idx):
        oh = F.one_hot(idx, self.vocab).float()
        x = self.emb(oh) + self.pos[: idx.shape[1]]
        for b in self.blocks:
            x = b(x)
        return self.head(self.nf(x))

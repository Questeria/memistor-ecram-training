"""ME-REVISE-2 (review 2, finding 1): explicit pulse streams beside the aggregate Poisson surrogate of memsim_rev.py.

The surrogate (memsim_rev.pulse_counts + Tile._step) draws, per batch and per cell, independent Poisson up and down counts
and applies all of them in one exact ODE step (uniform interleaving), with the write noise evaluated at the pre-batch state.
The physical stochastic-pulse scheme (Gokmen and Vlasov 2016) instead fires, per sample and per slot, each row line with
probability |p_x,i| and each column line with probability |p_d,j|; a cell receives a pulse when both fire, its sign set by
sign(x_i d_j); samples follow one another in time. Two explicit streams are provided:

- `slot`: the literal stream. Per sample, per slot: Bernoulli line firings, one pulse per coincident cell through the
  per-pulse device step s_up(u) = k_up (1 - g_up u), s_dn(u) = k_dn (1 + g_dn u), write noise per pulse (std c2c s(u) at the
  current state), clipping after every pulse. Exact for the model; costs M * BL tile steps per batch (probes only).
- `seq`: per sample, the same Bernoulli line firings give each cell's coincidence count n (= sum over slots of the product
  of its two line firings; shared lines keep the cross-cell correlation). Within one sample every pulse of a cell has the same
  sign, so the noise-free train has the exact closed form u_n = a^n u_0 + k (1 - a^n) / q (q = k g, a = 1 - q) and the order
  inside the sample does not matter; the write noise of the n pulses is added once per sample at the pre-sample state
  (std c2c sqrt(n) s(u)). Samples are applied one after another. Used for training (`run_rev2.py --pulse seq`).

The line probabilities are those of memsim_rev.pulse_counts (same update management, same clipping at 1), so the three
methods share the requested and the policy-expected update and differ only in how pulses are drawn and applied.
"""
import math

import torch


def line_probs(x, d, lr, k_nom, BL):
    """The signed, clipped line probabilities of memsim_rev.pulse_counts (x: (M, in), d: (M, out))."""
    eta = lr / k_nom
    mx = x.abs().max().clamp_min(1e-12)
    md = d.abs().max().clamp_min(1e-12)
    c = math.sqrt(eta / BL)
    cx = c * torch.sqrt(md / mx)
    cd = c * torch.sqrt(mx / md)
    return (cx * x).clamp(-1.0, 1.0), (cd * d).clamp(-1.0, 1.0), eta


def dev_params(tile):
    """Per-device step parameters of a memsim_rev.Tile as full tensors (out, in)."""
    full = lambda v: v if torch.is_tensor(v) and v.dim() == 2 else torch.full_like(tile.u, float(v))
    lo = full(tile.lo) if tile.aihw else torch.full_like(tile.u, -1.0)
    hi = full(tile.hi) if tile.aihw else torch.full_like(tile.u, 1.0)
    return dict(k_up=full(tile.k_up), k_dn=full(tile.k_dn), gu=full(tile.gu), gd=full(tile.gd), lo=lo, hi=hi,
                c2c=float(tile.spec.c2c))


def _ac(n, sg, P, xi=None):
    """Per-sample affine maps u -> a u + c of each cell's same-sign train (n pulses, sign sg), (S, out, in).
    Noise-free: a = (1 - q)^n, c = +-k (1 - a) / q (q = k g; c = +-k n when q = 0). With write noise xi (standard normal per
    cell and sample) the train's noise c2c sqrt(n) s(u_pre) xi, s(u) = k (1 -+ g u), is affine in u_pre as well, so it is
    folded into a and c (the surrogate's clamp of s(u) at 0, reached only beyond the saturation fixed point, is not)."""
    up = (sg > 0) & (n > 0)
    dn = (sg < 0) & (n > 0)
    k = torch.where(up, P["k_up"], P["k_dn"])
    g = torch.where(up, P["gu"], P["gd"])
    q = (k * g).clamp(0.0, 0.999)
    an = torch.exp(n * torch.log1p(-q))
    inc = torch.where(q > 1e-12, (1.0 - an) / q.clamp_min(1e-12), n)
    sign = up.to(n.dtype) - dn.to(n.dtype)
    a = torch.where(up | dn, an, torch.ones_like(an))
    c = sign * k * inc
    if xi is not None and P["c2c"] > 0:
        sq = P["c2c"] * n.sqrt() * k * xi
        a = a - sign * sq * g  # up: sq (1 - g u); down: sq (1 + g u)
        c = c + (up | dn).to(n.dtype) * sq
    return a, c, up, dn


def counts(px_b, pd_b, BL, gen):
    """Coincidence counts of one or more samples: px_b (S, in), pd_b (S, out) -> (S, out, in), via Bernoulli line firings."""
    S, nin = px_b.shape
    nout = pd_b.shape[1]
    fx = (torch.rand((S, BL, nin), generator=gen, device=px_b.device) < px_b.abs()[:, None, :]).float()
    fd = (torch.rand((S, BL, nout), generator=gen, device=px_b.device) < pd_b.abs()[:, None, :]).float()
    return torch.bmm(fd.transpose(1, 2), fx), fx, fd


def seq_apply(u, P, px, pd, BL, gen, ngen=None, chunk=32, return_counts=False, fire=None, keep_fire=None):
    """Apply a batch sample by sample (the `seq` stream). u (out, in) is not modified; returns the new state
    (and the total up and down counts). fire: replay these line firings (one (fx, fd) per chunk); keep_fire: a list that
    receives this draw's firings. Each sample's train is one affine map per cell (_ac), applied in sample order with the
    device bounds after every sample."""
    ngen = gen if ngen is None else ngen
    u = u.clone()
    nup_t = torch.zeros_like(u)
    ndn_t = torch.zeros_like(u)
    M = px.shape[0]
    for ci, s0 in enumerate(range(0, M, chunk)):
        if fire is None:
            n_all, fx, fd = counts(px[s0:s0 + chunk], pd[s0:s0 + chunk], BL, gen)
        else:
            fx, fd = fire[ci]
            n_all = torch.bmm(fd.transpose(1, 2), fx)
        if keep_fire is not None:
            keep_fire.append((fx, fd))
        sg = -(pd[s0:s0 + chunk][:, :, None] * px[s0:s0 + chunk][:, None, :])  # descent: up when x d < 0
        xi = torch.randn(n_all.shape, generator=ngen, device=u.device) if P["c2c"] > 0 else None
        a, c, up, dn = _ac(n_all, sg, P, xi)
        for b in range(n_all.shape[0]):
            u = torch.max(torch.min(a[b] * u + c[b], P["hi"]), P["lo"])
        if return_counts:
            nup_t += (n_all * up).sum(0)
            ndn_t += (n_all * dn).sum(0)
    return (u, nup_t, ndn_t) if return_counts else u


def slot_apply(u, P, px, pd, BL, gen, ngen=None, chunk=32, fire=None):
    """The literal stream: per sample, per slot, one pulse per coincident cell, noise and clipping per pulse.
    fire: optional list of (fx, fd) per chunk to reuse the same line firings as a `seq` draw (paired comparison)."""
    ngen = gen if ngen is None else ngen
    u = u.clone()
    M = px.shape[0]
    ci = 0
    for s0 in range(0, M, chunk):
        if fire is None:
            _, fx, fd = counts(px[s0:s0 + chunk], pd[s0:s0 + chunk], BL, gen)
        else:
            fx, fd = fire[ci]
        ci += 1
        for b in range(fx.shape[0]):
            sg = -(pd[s0 + b][:, None] * px[s0 + b][None, :])
            up_cell, dn_cell = sg > 0, sg < 0
            for t in range(BL):
                m = fd[b, t][:, None] * fx[b, t][None, :]
                if not bool(m.any()):
                    continue
                su = P["k_up"] * (1 - P["gu"] * u).clamp_min(0)
                sd = P["k_dn"] * (1 + P["gd"] * u).clamp_min(0)
                if P["c2c"] > 0:
                    z = torch.randn(u.shape, generator=ngen, device=u.device)
                    su = su * (1 + P["c2c"] * z)
                    sd = sd * (1 + P["c2c"] * z)
                du = torch.where(up_cell, su, torch.where(dn_cell, -sd, torch.zeros_like(u))) * m
                u = torch.max(torch.min(u + du, P["hi"]), P["lo"])
    return u

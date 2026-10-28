"""Derive paper/sim/memsim.py from lane ME's sim/memsim.py by named anchor substitutions (each anchor must match once).

    python -B derive_memsim.py ../../sim/memsim.py memsim.py
"""
import sys

src, dst = sys.argv[1], sys.argv[2]
t = open(src, 'rb').read().decode('utf-8')
SUBS = [
    ("doc",
     '"""Lane ME (X1000 phase 2): device-aware training with three-terminal electrochemical weights.\n',
     '"""Paper lane ME-PAPER: derived from lane ME\'s memsim.py by paper/sim/derive_memsim.py (anchors named there).\n'
     'Adds: per-device spread of the saturation (gamma_d2d), a fixed weight scale (alpha), Tiki-Taka v1 (Gokmen and\n'
     'Haensch 2020), chopped TTv2 and AGAD (Rasch et al. 2024). The SGD and TTv2 paths are unchanged (checked bit for bit).\n\n'
     'Lane ME (X1000 phase 2): device-aware training with three-terminal electrochemical weights.\n'),
    ("spec_field",
     "    ideal_float: bool = False      # bypass the device: w += exact digital update (control arm)\n",
     "    ideal_float: bool = False      # bypass the device: w += exact digital update (control arm)\n"
     "    gamma_d2d: float = 0.0         # device-to-device spread (relative std) of gamma_up and gamma_dn, drawn independently\n"),
    ("tile_gamma",
     "        gu, gd = spec.gamma_up, spec.gamma_dn\n        den = self.k_up * gu + self.k_dn * gd\n        if gu == 0 and gd == 0:\n",
     "        gu, gd = spec.gamma_up, spec.gamma_dn\n"
     "        if spec.gamma_d2d > 0:  # per-device saturation slopes (the RPU-baseline model of Gokmen and Haensch 2020)\n"
     "            gu = (gu * (1.0 + spec.gamma_d2d * r())).clamp_min(0.0)\n"
     "            gd = (gd * (1.0 + spec.gamma_d2d * r())).clamp_min(0.0)\n"
     "        self.gu, self.gd = gu, gd\n"
     "        den = self.k_up * gu + self.k_dn * gd\n"
     "        if spec.gamma_up == 0 and spec.gamma_dn == 0:\n"),
    ("pulses_B",
     "        B = self.k_up * s.gamma_up * n_up + self.k_dn * s.gamma_dn * n_dn\n",
     "        B = self.k_up * self.gu * n_up + self.k_dn * self.gd * n_dn\n"),
    ("pulses_noise",
     "            su = self.k_up * (1 - s.gamma_up * u0).clamp_min(0)\n            sd = self.k_dn * (1 + s.gamma_dn * u0).clamp_min(0)\n",
     "            su = self.k_up * (1 - self.gu * u0).clamp_min(0)\n            sd = self.k_dn * (1 + self.gd * u0).clamp_min(0)\n"),
    ("ucfg_algo",
     "    algo: str = \"sgd\"              # sgd | ttv2\n",
     "    algo: str = \"sgd\"              # sgd | ttv1 | ttv2 | cttv2 | agad\n"),
    ("ucfg_more",
     "    tt_reset: bool = True          # reset the read A columns to their symmetry point after a read\n",
     "    tt_reset: bool = True          # reset the read A columns to their symmetry point after a read\n"
     "    tt_cols: int = 0               # columns of A read per batch (0: ceil(in / tt_period)); TTv1 with ns = 1: the batch size\n"
     "    tt_rho: float = 0.1            # chopper flip probability per read (cttv2, agad)\n"
     "    agad_beta: float = 0.5         # AGAD leaky average of the A reads (1: the last read only)\n"),
    ("lin_sig",
     "    def __init__(self, in_f, out_f, spec, ucfg: UpdateCfg, gen, device, bias=True, init_gain=1.0,\n                 range_frac=0.4):\n",
     "    def __init__(self, in_f, out_f, spec, ucfg: UpdateCfg, gen, device, bias=True, init_gain=1.0,\n                 range_frac=0.4, alpha=None):\n"),
    ("lin_alpha",
     "        alpha = bound / range_frac  # init occupies +-range_frac of the device range\n",
     "        alpha = bound / range_frac if alpha is None else float(alpha)  # init at +-range_frac of the range unless fixed\n"),
    ("lin_tiles",
     "        if ucfg.algo == \"ttv2\":\n            self.A = Tile((out_f, in_f), spec, alpha, gen, device)\n"
     "            self.A.program(torch.zeros_like(w0))\n            self.H = torch.zeros((out_f, in_f), device=device)\n"
     "            self.col_ptr = 0\n",
     "        self.chop = None\n"
     "        if ucfg.algo in (\"ttv1\", \"ttv2\", \"cttv2\", \"agad\"):\n"
     "            self.A = Tile((out_f, in_f), spec, alpha, gen, device)\n"
     "            self.A.program(torch.zeros_like(w0))\n            self.H = torch.zeros((out_f, in_f), device=device)\n"
     "            self.col_ptr = 0\n"
     "        if ucfg.algo in (\"cttv2\", \"agad\"):\n"
     "            self.chop = torch.ones(in_f, device=device)  # chopper signs c_j on the inputs (Rasch et al. 2024)\n"
     "        if ucfg.algo == \"agad\":\n"
     "            self.P = torch.zeros((out_f, in_f), device=device)     # leaky average of the A reads\n"
     "            self.Pref = torch.zeros((out_f, in_f), device=device)  # the reference, set from P at a chopper flip\n"),
    ("upd_chop",
     "        tgt = self.A if self.A is not None else self.C\n        lr_t = u.lr * (u.tt_lr_ratio if self.A is not None else 1.0)\n"
     "        if tgt.spec.ideal_float:\n",
     "        tgt = self.A if self.A is not None else self.C\n        lr_t = u.lr * (u.tt_lr_ratio if self.A is not None else 1.0)\n"
     "        if self.chop is not None:\n"
     "            x = x * self.chop  # modulate the inputs: the A update sees c * x\n"
     "        if tgt.spec.ideal_float:\n"),
    ("tr_head",
     "        u = self.ucfg\n        ncols = max(1, math.ceil(self.in_f / u.tt_period))\n"
     "        idx = torch.arange(self.col_ptr, self.col_ptr + ncols, device=self.H.device) % self.in_f\n"
     "        self.col_ptr = int((self.col_ptr + ncols) % self.in_f)\n"
     "        wA = self.A.weight()[:, idx]\n"
     "        self.H[:, idx] += u.tt_lambda * wA / (self.C.alpha * self.C.k_nom)\n",
     "        u = self.ucfg\n"
     "        ncols = max(1, math.ceil(self.in_f / u.tt_period)) if u.tt_cols <= 0 else min(self.in_f, u.tt_cols)\n"
     "        idx = torch.arange(self.col_ptr, self.col_ptr + ncols, device=self.H.device) % self.in_f\n"
     "        self.col_ptr = int((self.col_ptr + ncols) % self.in_f)\n"
     "        if u.algo == \"ttv1\":\n"
     "            return self._transfer_v1(idx)\n"
     "        wA = self.A.weight()[:, idx]\n"
     "        z = wA\n"
     "        if u.algo == \"agad\":  # dynamic reference: z = c (w_A - p_ref); p <- (1 - beta) p + beta w_A\n"
     "            z = wA - self.Pref[:, idx]\n"
     "            self.P[:, idx] = (1.0 - u.agad_beta) * self.P[:, idx] + u.agad_beta * wA\n"
     "        if self.chop is not None:\n"
     "            z = z * self.chop[idx]  # demodulate with the column's chopper sign\n"
     "        self.H[:, idx] += u.tt_lambda * z / (self.C.alpha * self.C.k_nom)\n"),
    ("tr_tail",
     "                self.n_pulses += float(n.abs().sum())\n            self.H[:, idx] = h - n\n",
     "                self.n_pulses += float(n.abs().sum())\n            self.H[:, idx] = h - n\n"
     "        if self.chop is not None:  # flip each read column's chopper with probability rho\n"
     "            flip = torch.rand(idx.shape, generator=self.gen, device=idx.device) < u.tt_rho\n"
     "            if bool(flip.any()):\n"
     "                fi = idx[flip]\n"
     "                self.chop[fi] = -self.chop[fi]\n"
     "                if u.algo == \"agad\":\n"
     "                    self.Pref[:, fi] = self.P[:, fi]\n"
     "\n"
     "    @torch.no_grad()\n"
     "    def _transfer_v1(self, idx):\n"
     "        \"\"\"Tiki-Taka v1 (Gokmen and Haensch 2020): read columns j of A and add tt_lambda * A[:, j] to C[:, j] by a pulsed\n"
     "        outer product with the one-hot input e_j (no digital buffer; A is not reset); forward weight C + tt_gamma A.\"\"\"\n"
     "        u = self.ucfg\n"
     "        v = self.A.weight()[:, idx]  # (out, ncols)\n"
     "        X = torch.zeros((idx.numel(), self.in_f), device=v.device)\n"
     "        X[torch.arange(idx.numel(), device=v.device), idx] = 1.0\n"
     "        if self.C.spec.ideal_float:\n"
     "            self.C.apply_exact(u.tt_lambda * (v @ X))\n"
     "        else:  # pulse_counts descends (dw = -lr d^T x), so d = -v^T gives dw = +lr v e_j^T\n"
     "            n_up, n_dn = pulse_counts(X, -v.t(), u.tt_lambda / self.C.alpha, self.C.k_nom, u.BL, self.gen)\n"
     "            self.C.apply_pulses(n_up, n_dn)\n"
     "            self.n_pulses += float(n_up.sum() + n_dn.sum())\n"),
]
POST = [  # applied after SUBS: bookkeeping without a device sync per layer and step (numerics unchanged)
    ("stats_px",
     "        stats[\"px\"] = stats.get(\"px\", 0.0) + float(px.abs().mean(1).sum())\n"
     "        stats[\"pd\"] = stats.get(\"pd\", 0.0) + float(pd.abs().mean(1).sum())\n",
     "        stats[\"px\"] = stats.get(\"px\", 0.0) + px.abs().mean(1).sum()\n"
     "        stats[\"pd\"] = stats.get(\"pd\", 0.0) + pd.abs().mean(1).sum()\n"),
    ("npulses_upd",
     "            tgt.apply_pulses(n_up, n_dn)\n            self.n_pulses += float(n_up.sum() + n_dn.sum())\n",
     "            tgt.apply_pulses(n_up, n_dn)\n            self.n_pulses = self.n_pulses + (n_up.sum() + n_dn.sum())\n"),
    ("npulses_tr",
     "                self.n_pulses += float(n.abs().sum())\n",
     "                self.n_pulses = self.n_pulses + n.abs().sum()\n"),
    ("npulses_v1",
     "            self.C.apply_pulses(n_up, n_dn)\n            self.n_pulses += float(n_up.sum() + n_dn.sum())\n",
     "            self.C.apply_pulses(n_up, n_dn)\n            self.n_pulses = self.n_pulses + (n_up.sum() + n_dn.sum())\n"),
    ("flip_nosync",
     "            if bool(flip.any()):\n                fi = idx[flip]\n                self.chop[fi] = -self.chop[fi]\n"
     "                if u.algo == \"agad\":\n                    self.Pref[:, fi] = self.P[:, fi]\n",
     "            c = self.chop[idx]\n            self.chop[idx] = torch.where(flip, -c, c)\n"
     "            if u.algo == \"agad\":\n"
     "                self.Pref[:, idx] = torch.where(flip[None, :], self.P[:, idx], self.Pref[:, idx])\n"),
]
for name, a, b in SUBS:
    c = t.count(a)
    if c != 1:
        raise SystemExit(f"anchor {name}: {c} matches")
    t = t.replace(a, b)
for name, a, b in POST:
    c = t.count(a)
    if c != 1:
        raise SystemExit(f"post anchor {name}: {c} matches")
    t = t.replace(a, b)
open(dst, 'wb').write(t.encode('utf-8'))
print("derived", dst, len(SUBS), "anchors")

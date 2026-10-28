"""Derive paper/sim/tasks.py and run.py from lane ME's copies by named anchors (each must match once).

    python -B edit_tasks_run.py ../../sim
"""
import sys


def sub(path_in, path_out, subs):
    t = open(path_in, 'rb').read().decode('utf-8')
    for name, a, b in subs:
        c = t.count(a)
        if c != 1:
            raise SystemExit(f"{path_out} anchor {name}: {c} matches")
        t = t.replace(a, b)
    open(path_out, 'wb').write(t.encode('utf-8'))
    print("derived", path_out, len(subs))


TASKS = [
    ("lin_alpha",
     "    def __init__(self, kind, spec=None, ucfg=None, gen=None, device=None):\n"
     "        self.kind, self.spec, self.ucfg, self.gen, self.device = kind, spec, ucfg, gen, device\n",
     "    def __init__(self, kind, spec=None, ucfg=None, gen=None, device=None, alpha=None):\n"
     "        self.kind, self.spec, self.ucfg, self.gen, self.device = kind, spec, ucfg, gen, device\n"
     "        self.alpha = alpha  # fixed weight scale of every layer (the Gokmen-Haensch validation); None: from the init\n"),
    ("lin_call",
     "            return AnalogLinear(i, o, self.spec, self.ucfg, self.gen, self.device, bias=bias, init_gain=init_gain)\n",
     "            return AnalogLinear(i, o, self.spec, self.ucfg, self.gen, self.device, bias=bias, init_gain=init_gain,\n"
     "                                alpha=self.alpha)\n"),
    ("fcn_gh",
     "class Conv(torch.nn.Module):\n",
     "class FCN_GH(torch.nn.Module):\n"
     "    \"\"\"The fully connected network of Gokmen and Vlasov 2016 and Gokmen and Haensch 2020: 784-256-128-10, sigmoid.\"\"\"\n"
     "\n"
     "    def __init__(self, lin):\n"
     "        super().__init__()\n"
     "        self.l1, self.l2, self.l3 = lin(784, 256), lin(256, 128), lin(128, 10)\n"
     "\n"
     "    def forward(self, x):\n"
     "        return self.l3(torch.sigmoid(self.l2(torch.sigmoid(self.l1(x)))))\n"
     "\n"
     "\n"
     "class Conv(torch.nn.Module):\n"),
]
RUN = [
    ("budget",
     "    \"lm\": dict(steps=3000, batch=32, ctx=128),\n}\n",
     "    \"lm\": dict(steps=3000, batch=32, ctx=128),\n"
     "    \"mnist_gh\": dict(epochs=50, batch=16),  # Gokmen and Haensch 2020: 50 epochs (their batch is 1: PLAN-PAPER.md)\n}\n"),
    ("build",
     "    if task == \"mnist\":\n        return tasks.MLP(lin)\n",
     "    if task == \"mnist\":\n        return tasks.MLP(lin)\n    if task == \"mnist_gh\":\n        return tasks.FCN_GH(lin)\n"),
    ("choices",
     "    ap.add_argument(\"--task\", required=True, choices=[\"mnist\", \"cifar\", \"lm\"])\n",
     "    ap.add_argument(\"--task\", required=True, choices=[\"mnist\", \"cifar\", \"lm\", \"mnist_gh\"])\n"),
    ("algos",
     "    ap.add_argument(\"--algo\", default=\"sgd\", choices=[\"sgd\", \"ttv2\"])\n",
     "    ap.add_argument(\"--algo\", default=\"sgd\", choices=[\"sgd\", \"ttv1\", \"ttv2\", \"cttv2\", \"agad\"])\n"
     "    ap.add_argument(\"--alpha\", type=float, default=None, help=\"fixed weight scale of every analog layer\")\n"
     "    ap.add_argument(\"--epochs\", type=int, default=None, help=\"override the task's epochs (recorded)\")\n"
     "    ap.add_argument(\"--batch\", type=int, default=None, help=\"override the task's batch (recorded)\")\n"),
    ("lin",
     "    lin = tasks.Lin(\"digital\" if a.arm == \"fp_adam\" else \"analog\", spec, ucfg, gen, dev)\n",
     "    lin = tasks.Lin(\"digital\" if a.arm == \"fp_adam\" else \"analog\", spec, ucfg, gen, dev, alpha=a.alpha)\n"),
    ("bud",
     "    b = BUDGET[a.task]\n",
     "    b = dict(BUDGET[a.task])\n    if a.epochs:\n        b[\"epochs\"] = a.epochs\n    if a.batch:\n        b[\"batch\"] = a.batch\n"),
    ("load",
     "    if a.task in (\"mnist\", \"cifar\"):\n"
     "        D = tasks.load_mnist(dev) if a.task == \"mnist\" else tasks.load_cifar_subset(dev)\n",
     "    if a.task in (\"mnist\", \"cifar\", \"mnist_gh\"):\n"
     "        D = tasks.load_mnist(dev) if a.task != \"cifar\" else tasks.load_cifar_subset(dev)\n"
     "        if a.task == \"mnist_gh\":  # the validation trains on all 60,000 images, as the paper did\n"
     "            D = dict(D, xtr=torch.cat([D[\"xtr\"], D[\"xva\"]]), ytr=torch.cat([D[\"ytr\"], D[\"yva\"]]))\n"),
    ("lm_val",
     "        tr = D[\"tr\"]\n",
     "        tr = D[\"tr\"]\n"
     "        if a.split == \"val\":  # PLAN-PAPER.md section 0: selection runs hold out the slice's last 0.5 MB\n"
     "            tr = tr[:-500_000]\n"),
    ("nosync_loss",
     "        return float(loss) / (1 if opt is not None else len(yb))\n",
     "        return loss.detach() / (1 if opt is not None else len(yb))  # no device sync per step\n"),
    ("hist_cls",
     "            hist.append(dict(epoch=ep + 1, train_loss=ls / max(nb, 1)))\n",
     "            hist.append(dict(epoch=ep + 1, train_loss=float(ls) / max(nb, 1)))\n"),
    ("hist_lm",
     "                hist.append(dict(step=s + 1, train_loss_nats=ls / 500)); ls = 0.0\n",
     "                hist.append(dict(step=s + 1, train_loss_nats=float(ls) / 500)); ls = 0.0\n"),
    ("layers",
     "        layers.append(dict(shape=[m.out_f, m.in_f], pulses=m.n_pulses, rows=rows[id(m)],\n"
     "                           pulses_per_weight_per_row=m.n_pulses / max(1, nw * rows[id(m)]),\n"
     "                           mean_px=m.stats.get(\"px\", 0.0) / max(1, rows[id(m)]),\n"
     "                           mean_pd=m.stats.get(\"pd\", 0.0) / max(1, rows[id(m)])))\n",
     "        npul = float(m.n_pulses)\n"
     "        layers.append(dict(shape=[m.out_f, m.in_f], pulses=npul, rows=rows[id(m)],\n"
     "                           pulses_per_weight_per_row=npul / max(1, nw * rows[id(m)]),\n"
     "                           mean_px=float(m.stats.get(\"px\", 0.0)) / max(1, rows[id(m)]),\n"
     "                           mean_pd=float(m.stats.get(\"pd\", 0.0)) / max(1, rows[id(m)])))\n"),
    ("rec",
     "               ucfg=ucfg.__dict__, lr=a.lr, seed=a.seed, scale=a.scale, tag=a.tag, width=a.width, metric=metric, hist=hist,\n",
     "               ucfg=ucfg.__dict__, lr=a.lr, seed=a.seed, scale=a.scale, tag=a.tag, width=a.width, metric=metric, hist=hist,\n"
     "               budget=b, alpha=a.alpha, schema_paper=\"altone.x1000.me-paper.run.v1\",\n"),
]
sub(sys.argv[1] + '/tasks.py', 'tasks.py', TASKS)
sub(sys.argv[1] + '/run.py', 'run.py', RUN)

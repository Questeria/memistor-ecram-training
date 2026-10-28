# Lane ME: deviations from PLAN.md (each written before the affected runs)

## D1 (2026-10-24 about 21:35 ET): the reference of a constant-step asymmetric device

Found in the first MNIST grid records (grid B, asym > 0 with gamma = 0): the code put the symmetry point of a constant-step
device with any asymmetry at a BOUND (sign(k_up - k_dn)), and the reference conductance with it, so the read weight could only
move one way (positive weights were clipped at programming). Even asym 0.01 lost about 3 pp under SGD and TTv2 collapsed to
chance. That is a modelling bug, not a device property: a constant-step device has no symmetry point, and a real array would
reference it mid-range. Fix: the reference of a gamma = 0 device is u = 0 (memsim.py), with a new check
(c_constant_step_reference) that catches the old behaviour as a planted fault (records/TESTS.json). Every grid-B record made
before the fix is moved to records/superseded/ and grid B is re-run. Grids A, C-F and the catalog are not affected (A has
asym 0, where the old code already gave u* = 0; every other spec has gamma > 0).

## D2 (2026-10-24 about 21:35 ET): the TTv2 selection grid gains a learning-rate-matched arm

The pre-registered TTv2 grid (lambda {0.3, 1, 3} x period {16, 64}, A's lr = the SGD lr) chose lambda 0.3 / period 64 on MNIST
validation with the mid device. In TTv2 the weight C moves by lambda x (A's accumulated update), so every arm of that grid with
lambda < 1 is SGD at a reduced learning rate; the first test records (grid A) show TTv2 flat in the state count but about 1 pp
below SGD on ideal devices, the signature of a slowed learner in a fixed 10-epoch budget. So the selection grid gains four arms
in which A's lr is raised to keep lambda x lr_A = lr: lambda {0.1, 0.3} x period {16, 64} with tt_lr_ratio = 1 / lambda.
The choice is still made on MNIST VALIDATION with the same mid device, best of all ten arms (choose.py); the test results above
were not used to choose among arms. If the choice changes, every TTv2 test record is moved to records/superseded/ and re-run.

## D3 (2026-10-25 about 00:50 ET): the second seeds, and an FP sensitivity seed

Sitting 1 (pod op67xk1z4xy4mp, A4000, 23:51-00:40 ET) gave single-seed CIFAR / LM catalog gaps within a quarter of their
threshold for ecram_li_tang2018 and protonic_onen2022 under TTv2 on both tasks. PLAN.md's rule adds a second seed there:
sweep.py --phase seed2 derives that list mechanically from records/RESULTS.json (4 runs). The 2-seed FP CIFAR baseline has an
sd of 1.6 pp, comparable to the 2 pp threshold, so ONE more FP seed per task (FPSENS__s2) is run as a SENSITIVITY check: the
verdict keeps the pre-registered 2-seed FP baseline, and RESULTS.json reports the gaps against the 3-seed FP mean beside it.
These 6 runs are sitting 2 (one sitting on 10-25 ET; sitting 1 started 23:49 ET on 10-24).

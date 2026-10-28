# Lane ME bench test: a pencil-lead memistor built today (PROPOSAL ONLY: nothing is bought, built or run by the lane)

Written 2026-10-24 about 21:15 ET. The owner decides whether to build it. The lane's simulated "pencil lead built today" is an
ESTIMATE (PLAN.md); this bench replaces the estimate by measurements, and `bench/analyze_bench.py` turns the log into the
simulator's device spec so the measured device can be placed on the same map.

## What success means

At least **32 near-linear, symmetric levels** on one lead: over at least 32 consecutive equal-charge pulses in each direction,
(i) the mean up step and the mean down step agree within 10 %, (ii) the step varies by less than +-30 % across that range
(gamma <= 0.3 in the simulator's terms), (iii) the pulse-to-pulse scatter is under half a step (c2c <= 0.5). Then a 4-input
ADALINE trained by LMS on the four leads cuts its mean squared error at least 10x.

## Parts (estimated 2026 prices, USD; prices are estimates, not quotes)

| # | part | est. cost |
|---|---|---|
| 1 | 2.0 mm HB graphite leads (clutch-pencil refills), pack of 12 | 3 |
| 2 | copper(II) sulphate pentahydrate, 1 lb ("root killer", >= 98 %) | 8 |
| 3 | 22 AWG insulated solid hook-up wire, 2 m, plus 40 cm of bare solid copper wire (counter electrodes) | 3 |
| 4 | Arduino Nano (clone) with USB cable | 6 |
| 5 | INA219 current/voltage breakout (I2C) | 3 |
| 6 | CD4052 (or 74HC4052) dual 4-channel analog multiplexer | 1 |
| 7 | resistors: 1 kOhm, 270 Ohm, and a 1.00 Ohm 1 % reference (from an assortment) | 2 |
| 8 | mini breadboard and jumper wires | 3 |
| 9 | clear nail polish (insulates the bottom contacts) | 2 |
| 10 | distilled water, 1 gallon | 1.5 |
| 11 | nitrile gloves and splash goggles | 6 |
| 12 | four small glass jars or glasses (household; never used for food again) | 0 |
| | **totals** | printed by `python -B bench/analyze_bench.py --parts` (from bench/PARTS.json): all new, and without the items most homes have (gloves, goggles, jars, water, nail polish) |

Software: the Arduino IDE (free) to load `bench/memistor_bench.ino`. Installing it is the owner's choice; the lane installs nothing.

## Safety (copper sulphate)

- Copper sulphate is harmful if swallowed, causes serious eye irritation and skin irritation, and is very toxic to aquatic
  life. Wear splash goggles and nitrile gloves whenever the solution is open. Work on a tray, away from food, children and pets.
- No acid in this protocol (Widrow added sulphuric acid and brighteners; both are left out on purpose: the plain sulphate bath
  is safer and still plates copper; expect some hysteresis without brighteners, which the bench measures).
- Never let aluminium touch the solution (it reacts). Low voltage only (USB, 5 V); keep the computer and the Arduino off the
  tray and out of splash range. If bubbles form on an electrode, the current is too high: stop and lower it.
- Waste: never down the drain. Keep used solution and rinse water in a labelled, closed jar and take it to household hazardous
  waste collection. Rinse skin with plenty of water; for eye contact rinse 15 minutes and seek medical advice.

## Build

1. Solution: 12.5 g of the pentahydrate in 100 mL distilled water (0.5 M). Fill each jar with about 25 mL.
2. Each memistor: one 2.0 mm lead, about 50 mm long. Wrap 2 cm of stripped hook-up wire tightly round the bottom 5 mm of the
   lead (sense and current contact B) and another at the top (contact A, stays above the liquid). Paint the bottom wrap and 2 mm
   either side with three coats of nail polish, drying between coats, so no bare metal there touches the solution. A second
   thin wire at each wrap gives the 4-wire sense pair. Fill so that 20 mm of exposed graphite between the wraps is wetted
   (the length the lane's estimate assumes).
3. Counter electrode: 10 cm of bare copper wire coiled along the jar wall, not touching the lead.
4. Wiring (see the sketch's header): the four leads' current contacts in series (A of lead 1 to B of lead 2, ...), the chain's
   free end to pin 6 through the 1 kOhm (A0 on the pin side, A1 on the chain side), the chain's other end and pins 7/8 through
   the 270 Ohm for the read current; each jar's counter electrode to pins 2-5; each lead's two sense wires to the CD4052 (X and Y
   channels, address pins 9 and 10) and its common outputs to the INA219's VIN+ and VIN-; INA219 on I2C (A4/A5).
5. Calibrate the read: put the 1.00 Ohm reference in place of lead 1 (dry), send `R 0` ten times, and set the read-current
   constant in `readOhm()` so it reads 1000 mOhm.

## Protocol (about 2 evenings plus an overnight drift run)

All commands from the Arduino IDE's serial monitor (115200 baud); save the monitor output as `bench-log-<date>.csv`.

1. **Baseline and read noise (10 min):** `S` every 30 s. The read noise sigma_R is the scatter of each lead's readings.
2. **Plating range:** plate lead 0 in 1,000 uC pulses (`P 0 1000`, about 0.2 s each at ~4.5 mA) until its resistance falls below
   0.7 Ohm or 400 pulses; record the count. The lane's Faraday estimate of the full 5 -> 0.5 Ohm range is
   records/ENERGY.json pencil_geometry.plating_charge_full_range_c (a 20 mm wetted length of 0.5 mm lead; a 2.0 mm lead has
   four times the surface and a lower bare resistance, so expect more charge and a smaller ratio).
3. **Steps:** from mid-range, 64 pulses down (`D 0 Q`) then 64 up (`P 0 Q`) with Q = (charge of step 2) / 100, then repeat
   twice. This gives the step per pulse versus conductance, up versus down, and the scatter.
4. **Drift:** set mid-range, then `S` every minute for 2 h with the jar covered (cling film), and overnight if possible.
   A second run with 30 s of gentle stirring before shows whether dissolved oxygen drives the drift.
5. **Energy per update:** the log's energy_uJ column is the integral of cell voltage x current per pulse.
6. **Endurance:** 20 full plate/deplate cycles of lead 1; compare the first and last cycle.
7. **ADALINE:** the four leads are the weights (w_k = G_k - G_mid). For the 16 patterns x in {-1, +1}^4 and the target
   y = 0.5 x1 - 0.3 x2 + 0.2 x3 - 0.1 x4 (in units of the range), compute y_hat = sum w_k x_k from reads, and apply the LMS update
   dw_k = 2 mu e x_k as round(|dw_k| / step) pulses of the step charge (sign by direction); mu = 0.05; 50 epochs. Log the MSE per
   epoch. (The weighted sum is computed from the reads; a true analog sum is a later step.)

## What the lane does with the log

`python -B bench/analyze_bench.py bench-log.csv` (desk, standard library only) fits: levels = range / mean step, asymmetry,
gamma (the step's slope across the range), c2c (scatter / step), drift tau, energy per step, and prints a DeviceSpec. The lane
then runs that spec through the same MNIST / CIFAR / LM map (sim/run.py) and reports where the real pencil lead sits.

## What the bench cannot show

A pencil-lead memistor is macroscopic: its energy per step is set by the copper moved (the lane's estimate per level and the
GPU's weight-gradient MAC are both in records/ENERGY.json: pencil_energy_per_level_j, gpu.update_pj_peak_floor). It can confirm or refute the three-terminal
LINEARITY and SYMMETRY that the doctrine of the memistor promises; it cannot make training cheaper. The cheap direction, if
any, is the nanoscale heirs (ECRAM, protonic resistors), which this lane maps in simulation.

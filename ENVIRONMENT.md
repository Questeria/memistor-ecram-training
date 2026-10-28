# Environment

Every number in this file is derived by `make_deposit.py` from the deposit's own run records and from the pod logs (which are not in the deposit); none is typed.

## What the training runs used

- torch build recorded in the run records: `2.7.1+cu126` (2691 records).
- NumPy printed by the pods' `pip` installs: 2.2.6 (in 87 pod log lines). The pods pin `numpy==2.2.6` (`paper/pod/run.sh`).
- Python on the pods (the image's `python3`): 3.10.12 (in 7 pod log lines).
- CUDA: the PyTorch wheel `torch-2.7.1+cu126` ships the CUDA 12.6 runtime (cuDNN 9.5.1.17 (in 11 pod log lines)). The pod driver 595.91.07 (in 54 pod log lines) reports CUDA 13.2 (in 54 pod log lines).
- matplotlib printed by the pods' figure/build installs: 3.9.2 (in 96 pod log lines), 3.10.9 (in 6 pod log lines) (the build recipe pins 3.9.2).

## GPU models (run records by the `device` field)

- `NVIDIA RTX A4000`: 2421 records
- `Quadro P2000`: 252 records
- `Quadro P2200`: 18 records

The RTX A4000 runs were made on rented pods; the Quadro P2000 and P2200 runs on the author's desk. The simulator's AIHWKIT cross-check (`paper/revision/aihwkit_curves.py`) ran on CPU on a pod with `aihwkit 1.1.0`.

## Warning: the same seed is NOT the same experiment on a different GPU model

Finding of independent review 4 (`paper/reviews/REVIEW-4-chatgpt-20261027-full.md`), confirmed by the author (`paper/RESPONSE-TO-REVIEW-4.md`): the simulator draws its random numbers on the GPU, and PyTorch's CUDA random kernels size their grid from the GPU's multiprocessor count, so the Philox subsequence of every drawn element follows the grid. One seed therefore draws a different weight initialisation and a different `torch.randperm` example order on a GPU of another size, even with the same code and the same torch build. In the records, the initialisation and (on MNIST) the order hashes differ between the A4000, the P2000 and the P2200, while some orders agree between two GPU models. A rerun of a training run on other hardware is a fresh realisation of the experiment, not a reproduction of the record; the published comparisons pair arms that ran on the same GPU model and share initialisation and order by hash. The deposit's reproduction (`reproduce_all.py`) therefore starts from the saved records and the saved pulse draws and re-trains nothing.


## Clean-room verification (the author's check of this deposit)

- cuda_visible_to_children: False
- matplotlib: 3.9.2
- numpy: 2.5.2
- pillow: 13.0.0
- platform: Windows-11-10.0.26200-SP0
- python: 3.13.15
- torch: 2.7.1+cu126

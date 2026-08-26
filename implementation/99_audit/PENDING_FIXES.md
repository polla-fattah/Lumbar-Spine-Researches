# Pending fixes — apply AFTER the running campaign, not during

`run_ladder.py` launches every rung as a fresh subprocess, so editing the
trainer mid-campaign means earlier rungs ran with one behaviour and later rungs
with another. That inconsistency is worse than the defect and is invisible in
the output. Anything here waits for the campaign to finish.

---

## 1. E0 encodes all three sequences and discards two

**Where:** `amog_train.py`, `AMOGNet.encode()`

```python
for m in range(imgs.shape[1]):
    enc = self.encoders[m if len(self.encoders) > 1 else 0]
```

For E0 there is one encoder, so all three modalities pass through it, and
`forward_target` then keeps only `feats[:, ann_slot]`.

**Two consequences, one of which matters scientifically.**

*Wasted compute.* E0 does 3x the forward passes it needs. E1 (three encoders,
all used) ran FASTER than E0 (one encoder, two thirds discarded): 25.8 min
against 29.4 min.

*Contaminated statistics.* resnet18 has 20 BatchNorm2d layers. In training mode
they update running statistics from every batch they see, so E0's normalisation
is estimated from sequences the rung never reads. Measured on constructed
inputs with deliberately different per-modality distributions:

    running_mean, encoding all three : [0.0046, 0.0816, -0.0000, 0.1315]
    running_mean, annotated slot only: [0.0010, -0.0218,  0.0000, -0.0758]

Chapter 3 `sec:method-e0` defines E0 as grading each target "from its
anatomically localised input", independently. Statistics borrowed from the
other two sequences weakens that independence, and E0 is the baseline beneath
the E5-vs-E0 comparison ("relational message passing vs independent heads").

**Fix:** in `encode()`, when the rung is not multi-sequence, encode only the
annotated slot. Then re-run E0 and any comparison that uses it.

**Status:** found during the quick campaign. The quick E0 number is therefore
provisional and must not be reported.

---

## 2. The ACSSL checkpoint is not fingerprint-checked

`run_ladder` reuses `data/checkpoints/acssl_encoders.pt` whenever it exists.
Rung results now carry a `run_config` fingerprint and are re-run when the
configuration changes; the pretraining checkpoint has no equivalent, so a
changed pretraining configuration would be silently reused.

`load_acssl` does validate backbone and feature dim, so a mismatch cannot
corrupt weights — but a different temperature, epoch count or split would pass
unnoticed.

**Fix:** record the pretraining configuration in the checkpoint and compare it
in `run_ladder` the same way rung results are compared.

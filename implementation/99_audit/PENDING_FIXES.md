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

---

## 3. Router gate weights are discarded, so Contribution II cannot be evidenced

**Where:** `amog_train.py`, `run_epoch()`

```python
entropies.append(float(DiseaseConditionedRouter.gate_entropy(g, m2)))
...
m["gate_entropy"] = float(np.mean(entropies))
```

The gate tensor `g` is (B, M) -- one weight per sequence per target. Only its
mean entropy survives; the weights themselves are thrown away. The saved
predictions file holds `patient_id, y_true, y_pred, y_prob, logits` and nothing
about allocation.

**Why this blocks a contribution rather than merely losing detail.**

Chapter 3 `sec:method-routing-interpretation` requires two things, and neither
is computable from a scalar:

> "aggregate routing weights are summarised **by target**. The expected pattern
> is that foraminal targets allocate more weight to sagittal T1 and
> subarticular/canal targets more to axial T2"

> "controlled input ablation tests whether removing the sequence with high
> routing weight causes a greater performance loss than removing a low-weight
> sequence"

Contribution II claims routing is *disease-conditioned*. Demonstrating that
needs the per-condition allocation. The quick campaign measured mean gate
entropy at 0.936 for E2 and 0.919 for E3 -- close to uniform -- which is
consistent EITHER with a router that does not differentiate at all, OR with one
that differentiates sharply per condition while averaging near-uniform across
the cohort. Those are opposite conclusions about the contribution and the
current output cannot separate them.

**Fix:** save the mean gate vector per (condition, level) alongside the
predictions, and add the input-ablation comparison. Both are needed before the
full campaign, or it will finish without the evidence Contribution II requires.

**Status:** the quick campaign will not be able to evidence RQ3/Contribution II
beyond the aggregate scalar.

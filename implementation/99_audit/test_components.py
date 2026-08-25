#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Behavioural tests for the AMOG-Net components, against Chapter 3.

These are not smoke tests. Each one states a property Chapter 3 requires and
then tries to falsify it on constructed inputs whose correct answer is known
independently of the implementation.

Run:  python implementation/99_audit/test_components.py
"""
from __future__ import annotations

import inspect
import os
import sys

import numpy as np
import torch
import torch.nn.functional as F

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from amog_models import (  # noqa: E402
    OrdinalCORNHead, clinical_cost_matrix, expected_cost_loss, build_edges,
    DiseaseConditionedRouter, apply_modality_dropout, info_nce,
    TemperatureScaler, N_TARGETS, N_LEVELS, N_CONDITIONS, node_id,
    BILATERAL_PAIRS,
)
import rsna_data  # noqa: E402

PASS, FAIL = [], []


def check(name, condition, detail=""):
    (PASS if condition else FAIL).append(name)
    mark = "PASS" if condition else "FAIL"
    print(f"  [{mark}] {name}" + (f"\n         {detail}" if detail and not condition else ""))
    return condition


# --------------------------------------------------------------------------- #
print("\n1. Ordinal head -- Chapter 3 sec:method-ordinal")
print("-" * 70)

torch.manual_seed(0)
logits = torch.randn(500, 2)
probs = OrdinalCORNHead.to_probs(logits)

check("probabilities sum to 1",
      bool(torch.allclose(probs.sum(1), torch.ones(500), atol=1e-5)),
      f"max deviation {float((probs.sum(1) - 1).abs().max()):.2e}")
check("probabilities are non-negative", bool((probs >= 0).all()))

# Ordering: P(y>0) must be >= P(y>1). Feed a violating pair and confirm the
# cummin repairs it rather than emitting a negative probability.
bad = torch.tensor([[-3.0, 3.0]])          # sigmoid: 0.047 then 0.953 -- violates
bad_p = OrdinalCORNHead.to_probs(bad)
check("ordering violation cannot produce a negative probability",
      bool((bad_p >= 0).all()),
      f"got {bad_p.tolist()}")

# Independent re-derivation of the intended mapping.
p_gt = torch.sigmoid(logits)
p_gt_mono, _ = torch.cummin(p_gt, dim=-1)
manual = torch.stack([1 - p_gt_mono[:, 0],
                      p_gt_mono[:, 0] - p_gt_mono[:, 1],
                      p_gt_mono[:, 1]], dim=1)
check("cumulative->categorical matches an independent derivation",
      bool(torch.allclose(probs, manual.clamp(min=1e-8), atol=1e-6)))

# A confident logit pattern must decode to the right class.
for y, lg in [(0, [-8.0, -8.0]), (1, [8.0, -8.0]), (2, [8.0, 8.0])]:
    pred = int(OrdinalCORNHead.to_probs(torch.tensor([lg])).argmax())
    check(f"logits {lg} decode to grade {y}", pred == y, f"decoded {pred}")

# The loss is CORAL/cumulative-link (independent binary CE), NOT CORN
# (which chains conditional probabilities). Verify which one is implemented.
y = torch.tensor([0, 1, 2])
lg = torch.randn(3, 2)
t = torch.stack([(y > k).float() for k in range(2)], dim=-1)
expected_coral = F.binary_cross_entropy_with_logits(lg, t)
check("loss is the cumulative-link (CORAL-style) objective",
      bool(torch.allclose(OrdinalCORNHead.loss(lg, y), expected_coral)),
      "class is named CORN but implements independent binary CE")

# --------------------------------------------------------------------------- #
print("\n2. Clinical cost matrix -- Chapter 3 sec:method-cost")
print("-" * 70)

C = clinical_cost_matrix()
check("under-grading Severe costs more than mis-grading it Moderate (c20 > c21)",
      float(C[2, 0]) > float(C[2, 1]), f"C[2,0]={C[2,0]} C[2,1]={C[2,1]}")
check("diagonal is zero", bool((C.diag() == 0).all()))
check("row index is TRUTH and column index is PREDICTION",
      float(C[2, 0]) == 4.0 and float(C[0, 2]) == 1.0,
      f"C[true=2,pred=0]={C[2,0]}, C[true=0,pred=2]={C[0,2]}")

# Expected cost: a distribution concentrated on the true class costs 0; one
# concentrated on the worst error costs c20.
p_right = torch.tensor([[0.0, 0.0, 1.0]])
p_wrong = torch.tensor([[1.0, 0.0, 0.0]])
yv = torch.tensor([2])
check("expected cost of a perfect prediction is 0",
      abs(float(expected_cost_loss(p_right, yv, C))) < 1e-6)
check("expected cost of the decisive error equals c20",
      abs(float(expected_cost_loss(p_wrong, yv, C)) - 4.0) < 1e-6,
      f"got {float(expected_cost_loss(p_wrong, yv, C))}")

# --------------------------------------------------------------------------- #
print("\n3. Graph topology and the shuffled control -- Chapter 3 sec:method-graph")
print("-" * 70)

ei, et = build_edges()
E = ei.size(1)
check("node count is 5 levels x 5 conditions = 25", N_TARGETS == 25)
check("node_id is a bijection over (level, condition)",
      sorted(node_id(l, c) for l in range(N_LEVELS)
             for c in range(N_CONDITIONS)) == list(range(25)))

real_set = {(int(a), int(b)) for a, b in zip(ei[0], ei[1])}
check("anatomical graph is symmetric (every edge has its reverse)",
      all((b, a) in real_set for a, b in real_set))
check("anatomical graph has no self-loops",
      not any(a == b for a, b in real_set))

# Uniqueness must be checked on (src, dst, type), not (src, dst). In an R-GCN a
# node pair may legitimately carry more than one relation: the 20 bilateral
# edges also appear as same-level cross-condition edges, and the two relations
# are meant to be learned separately.
real_trip = {(int(a), int(b), int(t)) for a, b, t in zip(ei[0], ei[1], et)}
check("anatomical graph has no duplicate (src, dst, type) edges",
      len(real_trip) == E, f"{E} edges but {len(real_trip)} unique triples")

# Bilateral edges must connect the intended condition pairs.
bil = {(int(a), int(b)) for a, b, t in zip(ei[0], ei[1], et) if int(t) == 2}
expect_bil = set()
for l in range(N_LEVELS):
    for a, b in BILATERAL_PAIRS:
        expect_bil.add((node_id(l, a), node_id(l, b)))
        expect_bil.add((node_id(l, b), node_id(l, a)))
check("bilateral edge family links exactly the left/right counterparts",
      bil == expect_bil, f"{len(bil)} vs expected {len(expect_bil)}")

# Adjacent-level edges must never cross conditions.
adj = [(int(a), int(b)) for a, b, t in zip(ei[0], ei[1], et) if int(t) == 0]
check("adjacent-level edges keep the condition fixed",
      all(a % N_CONDITIONS == b % N_CONDITIONS for a, b in adj))

# THE CONTROL. Chapter 3 and run_ladder.py both say E6 vs E6_shuffled is the
# comparison that decides whether anatomy matters. For that comparison to be
# fair the shuffled graph must differ from the anatomical one ONLY in which
# endpoints the edges join -- same edge count, same per-type counts, same
# symmetry, same degree regularity.
si, st = build_edges(shuffled=True, seed=0)
shuf_set = {(int(a), int(b)) for a, b in zip(si[0], si[1])}

check("control preserves the total edge count", si.size(1) == E,
      f"{si.size(1)} vs {E}")
check("control preserves per-type edge counts",
      bool(torch.equal(torch.bincount(st, minlength=3),
                       torch.bincount(et, minlength=3))))
sym_ok = all((b, a) in shuf_set for a, b in shuf_set)
check("control graph is symmetric, as the anatomical graph is", sym_ok,
      "shuffled edges are drawn independently, so a->b rarely has b->a; the "
      "control is a DIRECTED graph compared against an UNDIRECTED one")
shuf_trip = {(int(a), int(b), int(t)) for a, b, t in zip(si[0], si[1], st)}
check("control graph has no duplicate (src, dst, type) edges",
      len(shuf_trip) == si.size(1),
      f"{si.size(1)} edges but {len(shuf_trip)} unique triples -- independent "
      f"randint draws collide, so the control has fewer distinct edges than the "
      f"anatomical graph it is compared against")

deg_real = torch.bincount(ei[0], minlength=N_TARGETS)
deg_shuf = torch.bincount(si[0], minlength=N_TARGETS)
check("control preserves the degree sequence",
      bool(torch.equal(deg_real.sort().values, deg_shuf.sort().values)),
      f"real degrees {deg_real.tolist()}\n         shuffled  {deg_shuf.tolist()}")


# Chapter 3 sec:method-graph: h_i = 0 where e_{p,i} = 0. Masking the input once
# is not enough, because every layer ends in a LayerNorm and LayerNorm(0) != 0.
from amog_models import HeterogeneousRGCN, HomogeneousGNN  # noqa: E402

torch.manual_seed(0)
_x = torch.randn(1, N_TARGETS, 16)
_masked = node_id(1, 2)
_ev = torch.ones(1, N_TARGETS)
_ev[0, _masked] = 0
_xm = _x * _ev.unsqueeze(-1)

for _name, _g in [("heterogeneous (E6)", HeterogeneousRGCN(16, 16, layers=2, gated=True)),
                  ("heterogeneous ungated", HeterogeneousRGCN(16, 16, layers=2, gated=False)),
                  ("homogeneous (E5 control)", HomogeneousGNN(16, 16, layers=2))]:
    _g.eval()
    with torch.no_grad():
        _h = _g(_xm, ei, et, evidence=_ev)
    check(f"evidence-free node stays exactly zero through {_name}",
          float(_h[0, _masked].abs().max()) < 1e-8,
          f"max |h| = {float(_h[0, _masked].abs().max()):.4e}; LayerNorm(0) = beta, "
          f"so a node with no image re-acquires a state and broadcasts it")

# The mask must be applied identically in E5 and E6, or the control differs from
# the treatment for a reason unrelated to edge typing.
check("E5 and E6 both accept and honour the evidence mask",
      "evidence" in inspect.signature(HomogeneousGNN.forward).parameters
      and "evidence" in inspect.signature(HeterogeneousRGCN.forward).parameters)

# The ungated ablation must not carry the gate's parameters, or it overstates
# the capacity of the control that isolates the gate's contribution.
_gp = lambda gated: sum(p.numel() for n, p in HeterogeneousRGCN(
    16, 16, layers=2, gated=gated).named_parameters() if "gates" in n)
check("the ungated control allocates no gate parameters",
      _gp(False) == 0 and _gp(True) > 0,
      f"ungated carries {_gp(False)} gate parameters")

# --------------------------------------------------------------------------- #
print("\n4. Disease-conditioned router -- Chapter 3 sec:method-routing")
print("-" * 70)

torch.manual_seed(0)
router = DiseaseConditionedRouter(dim=16, emb=4, hidden=8).eval()
B, M, D = 8, 3, 16
feats = torch.randn(B, M, D)
mask = torch.ones(B, M)
mask[0, 1] = 0
mask[1, :2] = 0
cond = torch.randint(0, N_CONDITIONS, (B,))
lvl = torch.randint(0, N_LEVELS, (B,))

with torch.no_grad():
    fused, g = router(feats, mask, cond, lvl)

check("gate weights sum to 1 per row",
      bool(torch.allclose(g.sum(1), torch.ones(B), atol=1e-5)))
check("unavailable sequences receive exactly zero weight",
      float(g[0, 1]) == 0.0 and float(g[1, :2].sum()) == 0.0,
      f"g[0,1]={float(g[0,1]):.3e}, g[1,:2]={g[1, :2].tolist()}")
check("a masked sequence cannot influence the fused vector",
      bool(torch.allclose(fused[0], (feats[0] * g[0].unsqueeze(-1)).sum(0), atol=1e-6)))

# A row with nothing available must not emit NaN.
mask_empty = torch.zeros(1, M)
with torch.no_grad():
    fe, ge = router(feats[:1], mask_empty, cond[:1], lvl[:1])
check("a fully-unavailable row produces no NaN",
      bool(torch.isfinite(fe).all() and torch.isfinite(ge).all()))

# Masking must happen BEFORE the softmax: changing a masked sequence's features
# must not change the gate over the available ones.
feats_alt = feats.clone()
feats_alt[0, 1] = torch.randn(D) * 50
with torch.no_grad():
    _, g_alt = router(feats_alt, mask, cond, lvl)
check("a masked sequence's content cannot alter the surviving gate weights",
      bool(torch.allclose(g[0], g_alt[0], atol=1e-6)),
      "renormalisation must occur after masking, not before")

# Modality dropout must never empty a study.
torch.manual_seed(3)
m_in = torch.ones(2000, 3)
m_out = apply_modality_dropout(m_in, p_drop=0.9, training=True)
check("modality dropout never removes the last sequence",
      bool((m_out.sum(1) > 0).all()),
      f"{int((m_out.sum(1) == 0).sum())} rows emptied")
check("modality dropout is a no-op at eval time",
      bool(torch.equal(apply_modality_dropout(m_in, 0.9, training=False), m_in)))

# --------------------------------------------------------------------------- #
print("\n5. Cross-sequence InfoNCE -- Chapter 3 sec:method-acssl")
print("-" * 70)

z = F.normalize(torch.randn(32, 8), dim=1)
loss_same = float(info_nce(z, z.clone()))
loss_rand = float(info_nce(z, F.normalize(torch.randn(32, 8), dim=1)))
check("perfectly aligned views give a lower loss than unrelated ones",
      loss_same < loss_rand, f"aligned {loss_same:.4f} vs random {loss_rand:.4f}")
check("InfoNCE is symmetric in its two views",
      abs(float(info_nce(z, z.roll(1, 0))) - float(info_nce(z.roll(1, 0), z))) < 1e-5)

# --------------------------------------------------------------------------- #
print("\n6. Temperature scaling -- Chapter 3 sec:method-calibration")
print("-" * 70)

torch.manual_seed(0)
true_y = torch.randint(0, 3, (2000,))
sharp = F.one_hot(true_y, 3).float() * 6.0
noise_idx = torch.randperm(2000)[:700]
sharp[noise_idx] = sharp[noise_idx].roll(1, dims=-1)      # make it over-confident
ts = TemperatureScaler()
T = ts.fit(sharp, true_y)
check("fitted temperature is positive and finite",
      np.isfinite(T) and T > 0, f"T={T}")
check("an over-confident model is softened (T > 1)", T > 1.0, f"T={T:.3f}")
nll_before = float(F.cross_entropy(sharp, true_y))
nll_after = float(F.cross_entropy(sharp / T, true_y))
check("temperature scaling does not increase validation NLL",
      nll_after <= nll_before + 1e-6, f"{nll_before:.4f} -> {nll_after:.4f}")

# --------------------------------------------------------------------------- #
print("\n7. Patient-level splitting -- Chapter 3 sec:method-patient-split")
print("-" * 70)

import pandas as pd  # noqa: E402
idx = pd.DataFrame({"study_id": np.repeat(np.arange(200), 25)})
tr, va, te = rsna_data.patient_split(idx, seed=1)
check("splits are disjoint at patient level",
      not (tr & va) and not (tr & te) and not (va & te))
check("splits cover every patient",
      len(tr | va | te) == 200, f"covered {len(tr | va | te)} of 200")
tr2, va2, te2 = rsna_data.patient_split(idx, seed=1)
check("splitting is deterministic for a fixed seed",
      (tr, va, te) == (tr2, va2, te2))
tr3, _, _ = rsna_data.patient_split(idx, seed=2)
check("a different seed gives a different split (so the seed is load-bearing)",
      tr != tr3)

# --------------------------------------------------------------------------- #
print("\n8. ROI geometry -- Chapter 3 sec:method-roi")
print("-" * 70)

src = open(os.path.join(os.path.dirname(__file__), "..", "rsna_data.py"),
           encoding="utf-8").read()
check("ROI crop is defined in physical millimetres, not fixed pixels",
      "PixelSpacing" in src,
      "Chapter 3 sec:method-roi: 'Crops are defined in physical dimensions "
      "where possible... This avoids a fixed 100-pixel crop representing "
      "different anatomical widths on scanners with different pixel spacing.' "
      "decode_roi() uses half = crop // 2, a fixed 128-pixel box.")
check("2.5D stack radius matches the Chapter 3 reference configuration r=2",
      "(-2, -1, 0, 1, 2)" in src or "range(-2, 3)" in src,
      "Chapter 3 sec:method-roi names a five-slice stack (r=2) as the initial "
      "reference; decode_roi() uses (-1, 0, 1), i.e. r=1.")
check("ROI definition is conditioned on anatomical compartment",
      "condition_key" in src and "crop_for_condition" in src,
      "Chapter 3 sec:method-roi requires compartment-specific, side-aware crops "
      "(canal vs foraminal vs subarticular). decode_roi() applies one uniform "
      "crop to every condition.")

# --------------------------------------------------------------------------- #
print("\n9. Metrics -- Chapter 3 sec:method-metrics")
print("-" * 70)

from amog_modes import compute_metrics  # noqa: E402
from sklearn.metrics import (  # noqa: E402
    cohen_kappa_score, f1_score, accuracy_score, balanced_accuracy_score)

rng = np.random.default_rng(0)
ok_qwk = ok_f1 = ok_acc = True
for _ in range(5):
    yt = rng.integers(0, 3, 3000)
    yp = rng.integers(0, 3, 3000)
    m = compute_metrics(yt, yp)
    ok_qwk &= abs(m["qwk"] - cohen_kappa_score(yt, yp, weights="quadratic")) < 1e-9
    ok_f1 &= abs(m["macro_f1"] - f1_score(yt, yp, average="macro")) < 1e-9
    ok_acc &= abs(m["accuracy"] - accuracy_score(yt, yp)) < 1e-12
check("QWK matches sklearn cohen_kappa_score(weights='quadratic')", ok_qwk)
check("macro F1 matches sklearn f1_score(average='macro')", ok_f1)
check("accuracy matches sklearn accuracy_score", ok_acc)

yt = rng.integers(0, 3, 1000)
mc = compute_metrics(yt, np.zeros(1000, dtype=int))
check("a constant prediction yields QWK exactly 0",
      abs(mc["qwk"]) < 1e-12, f"got {mc['qwk']}")

yt = rng.integers(0, 3, 3000); yp = rng.integers(0, 3, 3000)
mb = compute_metrics(yt, yp)
if "balanced_accuracy" in mb:
    check("balanced accuracy matches sklearn",
          abs(mb["balanced_accuracy"] - balanced_accuracy_score(yt, yp)) < 1e-9)
else:
    check("balanced accuracy is reported alongside accuracy", False,
          "Chapter 3 sec:method-macrof1 requires balanced accuracy; the majority "
          "class is 77.3%, so accuracy alone is not interpretable.")

# --------------------------------------------------------------------------- #
print("\n10. Statistics -- Chapter 3 sec:method-stats")
print("-" * 70)

from amog_stats import (  # noqa: E402
    patient_bootstrap_ci, paired_bootstrap_diff, benjamini_hochberg)


def acc_fn(a, b, prob=None):
    return float((np.asarray(a) == np.asarray(b)).mean())


pid = np.repeat(np.arange(150), 10)
yt = rng.integers(0, 3, 1500)
yp = yt.copy()
flip = rng.choice(1500, 300, replace=False)
yp[flip] = (yp[flip] + 1) % 3

res = patient_bootstrap_ci(pid, yt, yp, acc_fn, n_boot=400, seed=0)
point, lo, hi = float(res[0]), float(res[1]), float(res[2])
check("bootstrap CI brackets the point estimate",
      lo <= point <= hi, f"{lo:.4f} <= {point:.4f} <= {hi:.4f}")
check("bootstrap point estimate equals the observed metric",
      abs(point - acc_fn(yt, yp)) < 1e-9, f"{point} vs {acc_fn(yt, yp)}")

dres = paired_bootstrap_diff(pid, yt, yp, yp.copy(), acc_fn, n_boot=400, seed=0)
d, dlo, dhi = dres["diff"], dres["lo"], dres["hi"]
check("a model compared against itself has zero difference",
      abs(d) < 1e-12, f"got {d}")
check("that difference CI contains 0", dlo <= 0 <= dhi, f"[{dlo}, {dhi}]")
check("a self-comparison is not declared significant",
      dres["p_value"] > 0.05, f"p={dres['p_value']}")

# A genuinely better model must produce a positive difference and a CI that
# excludes zero, or the test has no power and every ablation would read null.
better = yt.copy()
worse = yt.copy()
w = rng.choice(1500, 600, replace=False)
worse[w] = (worse[w] + 1) % 3
bres = paired_bootstrap_diff(pid, yt, better, worse, acc_fn, n_boot=400, seed=0)
check("a clearly better model yields a positive paired difference",
      bres["diff"] > 0, f"got {bres['diff']}")
check("and a CI that excludes zero", bres["lo"] > 0,
      f"[{bres['lo']}, {bres['hi']}]")

pv = np.array([0.001, 0.008, 0.039, 0.041, 0.042, 0.06, 0.074, 0.205])
rej, adj = benjamini_hochberg(pv, alpha=0.05)
rej, adj = np.asarray(rej), np.asarray(adj)
check("BH adjusted p-values never fall below the raw p-values",
      bool(np.all(adj >= pv - 1e-12)))
check("BH adjusted p-values are monotone in the sorted p-values",
      bool(np.all(np.diff(adj[np.argsort(pv)]) >= -1e-12)))
check("BH rejects the strongest hypothesis at alpha=0.05", bool(rej[0]))
check("BH does not reject the weakest hypothesis at alpha=0.05", not bool(rej[-1]))
check("BH rejects nothing when no p-value is small",
      not bool(np.any(np.asarray(benjamini_hochberg(np.linspace(0.2, 0.99, 20),
                                                    0.05)[0]))))

# --------------------------------------------------------------------------- #
print("\n11. Ladder integrity -- every rung must implement what it claims")
print("-" * 70)

import inspect  # noqa: E402
import json  # noqa: E402
import amog_train  # noqa: E402
from amog_train import AMOGNet, N_MODALITIES  # noqa: E402

train_src = inspect.getsource(amog_train)


def used_outside_import(src, name):
    """True if `name` appears somewhere other than an import statement."""
    return any(name in ln and not ln.strip().startswith(("from ", "import ", "#"))
               and not ln.strip().endswith(",")
               for ln in src.splitlines())


# E4 is Core Contribution I. Chapter 3 defines it as E3 PLUS anatomical
# pretraining, so E4 and E3 are meant to share an architecture -- the difference
# is the encoder initialisation, not the module list. The earlier version of
# this test asserted the opposite and was checking the wrong property; what was
# actually broken was that nothing transferred and a dead projector sat in the
# model pretending otherwise.
sig3 = {n: tuple(p.shape) for n, p in AMOGNet("E3", "smallcnn", 64).named_parameters()}
sig4 = {n: tuple(p.shape) for n, p in AMOGNet("E4", "smallcnn", 64).named_parameters()}
check("E4 carries no dead parameters relative to E3",
      sig3 == sig4,
      "E4 holds parameters E3 does not; a block that no forward path uses "
      "inflates the reported capacity of the rung")

check("no unused ACSSL projector remains in the supervised model",
      not any(n.startswith("projector") for n, _ in AMOGNet("E4", "smallcnn", 64)
              .named_parameters()),
      "Chapter 3 sec:method-ssl-projection: the projection head is discarded "
      "after pretraining")

import amog_acssl  # noqa: E402
check("the ACSSL contrastive objective is actually called",
      used_outside_import(inspect.getsource(amog_acssl), "info_nce("),
      "no self-supervised pretraining loop invokes info_nce anywhere")

check("E4 refuses to run without pretrained encoders",
      "allow_untrained_e4" in train_src and "return 2" in train_src,
      "E4 minus the pretraining is E3; running it silently would produce a CC I "
      "number that measures nothing")

# The transfer must be verified to CHANGE weights, not merely to execute.
_m4 = AMOGNet("E4", "smallcnn", 64)
_before = {k: v.clone() for k, v in _m4.encoders.state_dict().items()}

def _perturb(v):
    """Change every tensor, including BatchNorm's integer num_batches_tracked."""
    return torch.randn_like(v) if v.is_floating_point() else v + 1


_fake = {k: _perturb(v) for k, v in _before.items()}
import tempfile  # noqa: E402
with tempfile.TemporaryDirectory() as _td:
    _p = os.path.join(_td, "acssl.pt")
    torch.save({"encoders_state_dict": _fake, "backbone": "smallcnn", "dim": 64,
                "best_val_infonce": 1.0, "chance_infonce": 2.0, "mode": "smoke"}, _p)
    _info = _m4.load_acssl(_p)
    _changed = sum(1 for k in _before
                   if not torch.equal(_before[k], _m4.encoders.state_dict()[k]))
    check("load_acssl actually replaces the encoder weights",
          _changed == len(_before) and _info["tensors_changed"] == _changed,
          f"only {_changed} of {len(_before)} tensors changed")

    # A no-op load must raise rather than leave E4 silently equal to E3.
    _m5 = AMOGNet("E4", "smallcnn", 64)
    torch.save({"encoders_state_dict": _m5.encoders.state_dict(),
                "backbone": "smallcnn", "dim": 64}, _p)
    try:
        _m5.load_acssl(_p)
        check("a no-op ACSSL load is rejected", False,
              "loading identical weights was accepted, so E4 could silently be E3")
    except RuntimeError:
        check("a no-op ACSSL load is rejected", True)

    # A backbone mismatch must be named, not surface as a size-mismatch trace.
    _m6 = AMOGNet("E4", "smallcnn", 64)
    torch.save({"encoders_state_dict": _fake, "backbone": "resnet18", "dim": 64}, _p)
    try:
        _m6.load_acssl(_p)
        check("a backbone mismatch is refused", False)
    except RuntimeError as _e:
        check("a backbone mismatch is refused", "backbone" in str(_e))

check("pretraining uses the development partition only",
      "load_frozen_split" in inspect.getsource(amog_acssl)
      and "held_out" in inspect.getsource(amog_acssl),
      "Chapter 3 sec:method-ssl-leakage: a model pretrained on held-out patients "
      "has already seen their anatomy")

check("modality dropout is not applied during pretraining",
      "apply_modality_dropout" not in inspect.getsource(amog_acssl),
      "Chapter 3 sec:method-training-phases phase 2 disables it, because "
      "dropping a sequence would delete the positive pair the loss is defined on")

# E7 claims "ordinal/cost-sensitive/CALIBRATED heads" in the Chapter 3 ladder.
check("temperature scaling is applied during training/selection",
      used_outside_import(train_src, "TemperatureScaler("),
      "TemperatureScaler is imported and never used. ECE is reported but never "
      "corrected, so E7's calibration claim has no implementation.")

# Chapter 3 sec:method-augmentation specifies an augmentation programme.
aug_terms = ("flip", "gamma", "bias_field", "elastic", "augment")
check("training augmentation exists",
      any(used_outside_import(train_src, t) for t in aug_terms),
      "Chapter 3 sec:method-augmentation specifies intensity scaling, gamma, "
      "bias-field, noise, small rotation/translation and LATERALITY-AWARE flips "
      "that swap left/right labels and graph node identity. None is implemented.")

# Chapter 3 sec:method-patient-split: split lists are version-controlled and the
# loaders consume the fixed lists.
check("a frozen split file is committed to the repository",
      os.path.exists(rsna_data.SPLIT_FILE),
      f"Chapter 3 sec:method-patient-split requires a version-controlled split "
      f"record. Expected {rsna_data.SPLIT_FILE}")

check("training loads the frozen split instead of drawing one",
      "load_frozen_split(" in train_src and "patient_split(" not in train_src,
      "amog_train.py must consume the committed list, not re-derive it")

check("the split seed is decoupled from the training seed",
      "seed=args.seed" not in inspect.getsource(amog_train.make_datasets),
      "make_datasets must not pass the training seed to any partitioning or "
      "subsampling call, or a multi-seed campaign redraws the cohort")

if os.path.exists(rsna_data.SPLIT_FILE):
    rec = pd.read_csv(rsna_data.SPLIT_FILE)
    idx_all = pd.DataFrame({"study_id": rec["study_id"]})
    loads = [rsna_data.load_frozen_split(idx_all) for _ in range(3)]
    check("repeated loads return an identical test set",
          loads[0][2] == loads[1][2] == loads[2][2])
    tr_, va_, te_ = loads[0]
    check("the frozen split has no patient in two partitions",
          not (tr_ & va_) and not (tr_ & te_) and not (va_ & te_))
    check("the frozen split covers the whole cohort",
          len(tr_ | va_ | te_) == rec["study_id"].nunique())

    # A subset run must intersect the frozen partitions, never redraw them,
    # or a --max_targets run and a full run are not comparable.
    sub = idx_all.head(len(idx_all) // 3)
    check("a subset run intersects the frozen split rather than redrawing",
          rsna_data.load_frozen_split(sub)[2] <= te_)

    # A cohort that has grown must fail loudly: silently assigning new patients
    # would change the partitions every published number was computed on.
    grown = pd.DataFrame({"study_id": list(rec["study_id"][:5]) + [10 ** 12]})
    try:
        rsna_data.load_frozen_split(grown)
        check("an unknown patient is refused, not silently assigned", False,
              "load_frozen_split accepted a study absent from the split file")
    except ValueError:
        check("an unknown patient is refused, not silently assigned", True)

    meta_p = rsna_data.SPLIT_META
    if os.path.exists(meta_p):
        with open(meta_p, encoding="utf-8") as fh:
            meta = json.load(fh)
        check("the recorded sha256 matches the split file",
              rsna_data._split_digest(rec) == meta.get("sha256"),
              "the split file has been edited since it was written")
        flipped = rec.copy()
        flipped.loc[0, "partition"] = (
            "test" if flipped.loc[0, "partition"] == "train" else "train")
        check("moving one patient changes the digest",
              rsna_data._split_digest(flipped) != meta.get("sha256"))

# --------------------------------------------------------------------------- #
print("\n12. Optimisation protocol -- Chapter 3 sec:method-optimiser")
print("-" * 70)

# "warm-up and cosine decay or a plateau scheduler used consistently across the
# main ablation."
sched_terms = ("lr_scheduler", "CosineAnnealing", "OneCycle", "ReduceLROnPlateau",
               "get_last_lr", "warmup")
check("a learning-rate schedule is used",
      any(used_outside_import(train_src, t) for t in sched_terms),
      "Chapter 3 sec:method-optimiser requires warm-up and cosine decay, or a "
      "plateau scheduler, applied consistently across the main ablation. "
      "amog_train.py constructs AdamW with a constant lr and never steps a "
      "scheduler, so the LR is flat for the whole run.")

# Early stopping was REMOVED on 2026-08-25 by supervisor decision, so that the
# training budget is identical across every rung and no ladder comparison is
# partly a comparison of training length. This test pins that decision: it fails
# if a patience counter reappears without the ladder-comparability question
# being settled. Chapter 3 sec:method-optimiser still asks for early stopping
# and must be amended to match.
check("training runs a fixed budget with no early-stopping break",
      "epochs_since_best" not in train_src and "stopped_early" not in train_src,
      "an early-stopping counter has reappeared; if that is intended, decide how "
      "the ladder stays budget-comparable and update Chapter 3 "
      "sec:method-optimiser, which currently requires early stopping")

check("model selection still runs (selection is not early stopping)",
      "best_epoch = ep" in train_src and "load_state_dict" in train_src,
      "removing early stopping must not remove best-checkpoint selection; the "
      "held-out test must still run on the best validation epoch")

check("the selection metric is prevalence-robust, not raw accuracy",
      'vm["macro_f1"] > best' in train_src,
      "best-checkpoint tracking must key on macro-F1 or weighted kappa")

# The decisive one: the best checkpoint must be RESTORED before the held-out
# test, or model selection has no effect on the reported result.
check("the best checkpoint is restored into the model before testing",
      "load_state_dict" in train_src,
      "amog_train.py saves the best-macro-F1 checkpoint, re-reads it into `rl`, "
      "asserts it round-trips, and then never calls model.load_state_dict(). "
      "run_epoch(test_loader) is executed on the FINAL-epoch weights. Chapter 3 "
      "sec:method-model-selection makes validation the basis of selection; as "
      "written, selection is computed, saved, and discarded.")

# --------------------------------------------------------------------------- #
print("\n" + "=" * 70)
print(f"  {len(PASS)} passed, {len(FAIL)} failed")
print("=" * 70)
if FAIL:
    print("\nFailures:")
    for f in FAIL:
        print(f"  - {f}")
sys.exit(1 if FAIL else 0)

"""Does model performance track READER reliability across conditions?

Chapter 2 sec:lr-reliability reports Lurie et al.: inter-reader kappa 0.73 for
central canal, 0.58 foraminal, 0.49 subarticular, and observes that agreement is
"systematically worse for the lateral compartments than for the central
canal -- the same ordering that later appears in automated model performance".

That is a prediction, and it is checkable against this study's own results. If
the model's per-condition ordering matches the readers' ordering, the
label-reliability ceiling is a live explanation for why structural priors bought
so little. If it does not, that explanation weakens.

Target rungs only: the graph rungs reach forward_target through forward_graph
with a different batch layout.
"""
import argparse, os, sys
import numpy as np
from scipy.stats import spearmanr

sys.path.insert(0, os.path.join(os.getcwd(), 'implementation'))
import torch
from torch.utils.data import DataLoader

from amog_modes import CONDITIONS, resolve_mode
from amog_train import (AMOGNet, make_datasets, suggest_batch, loader_kwargs,
                        configure_backend, compute_metrics)
from amog_input_ablation import infer, per_condition

LURIE = {'central_canal': 0.73, 'left_foraminal': 0.58, 'right_foraminal': 0.58,
         'left_subarticular': 0.49, 'right_subarticular': 0.49}

ctx = resolve_mode(argparse.Namespace(mode='real', seed=42, epochs=None, lr=None,
                                      device=None, max_samples=None, batch_size=None))
gpu = configure_backend()
SEEDS = (42, 43, 44)
out = {}

for stage in ('E0', 'E2', 'E4'):
    per_seed = []
    for seed in SEEDS:
        ck = os.path.join(ctx.checkpoint_dir, '%s_real_seed%d_best.pt' % (stage, seed))
        if not os.path.exists(ck):
            continue
        torch.manual_seed(seed); np.random.seed(seed)
        da = argparse.Namespace(
            stage=stage, seed=seed, shuffled=False, ungated=False,
            shuffle_labels=False, workers=0, batch_size=0, cache_in_ram='auto',
            subset=None, p_drop=0.0, max_targets=None, _augment=None,
            aug_intensity=0.0, aug_gamma=0.0, aug_noise=0.0, aug_bias=0.0,
            aug_translate=0.0, aug_rotate=0.0, aug_prob=0.0)
        _, _, test_ds, _ = make_datasets(ctx, stage, da)
        bs = suggest_batch(False, gpu['vram_gb'], 0)
        loader = DataLoader(test_ds, batch_size=bs, shuffle=False,
                            **loader_kwargs(0, cuda=str(ctx.device).startswith('cuda')))
        sd = torch.load(ck, map_location=ctx.device, weights_only=False)
        model = AMOGNet(stage, sd.get('backbone') or 'resnet18', 256, False, False,
                        seed, pretrained=False).to(ctx.device)
        model.load_state_dict(sd['model_state_dict'], strict=True)
        model.eval()
        yt, yp, cc, _ = infer(model, loader, ctx.device, drop=None)
        per_seed.append(per_condition(yt, yp, cc, 'qwk'))
    if per_seed:
        out[stage] = {c: float(np.mean([d[c] for d in per_seed if c in d]))
                      for c in CONDITIONS if any(c in d for d in per_seed)}

print()
print('%-22s %8s %10s %10s %10s' % ('condition', 'Lurie k', 'E0 QWK', 'E2 QWK', 'E4 QWK'))
conds = [c for c in CONDITIONS if c in out.get('E0', {})]
for c in conds:
    print('%-22s %8.2f %10.4f %10.4f %10.4f' % (
        c, LURIE[c], out['E0'].get(c, np.nan), out.get('E2', {}).get(c, np.nan),
        out.get('E4', {}).get(c, np.nan)))

print()
for st in out:
    k = [LURIE[c] for c in conds]
    m = [out[st][c] for c in conds]
    rho, p = spearmanr(k, m)
    print('%s : Spearman rho vs reader kappa = %+.3f  (p = %.3f)' % (st, rho, p))

print()
print('Grouped: central canal vs the four lateral compartments')
for st in out:
    cen = out[st]['central_canal']
    lat = np.mean([out[st][c] for c in conds if c != 'central_canal'])
    print('  %s  central %.4f   lateral mean %.4f   difference %+.4f'
          % (st, cen, lat, cen - lat))
print('  readers    central 0.73     lateral mean %.2f   difference %+.2f'
      % (np.mean([0.58, 0.58, 0.49, 0.49]), 0.73 - np.mean([0.58, 0.58, 0.49, 0.49])))

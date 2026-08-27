"""Does message passing diffuse the attribution, or is the probe broken?

Graph rungs score 0.36-0.38 against 0.46-0.58 for the target rungs, and E7 sits
at its random-init floor. Two candidate explanations:

  (a) THE PROBE. Backpropagating the SUM of all node logits means node k's
      encoder activations receive gradient from every node its features reach
      through the GNN, not from node k's own logit. For E0-E4 there is no GNN,
      so the sum decomposes exactly and the attribution is clean.

  (b) THE MODEL. Graph rungs genuinely spread their evidence.

These are distinguishable. Backpropagate ONE node's logit alone and measure the
concentration of that node's own CAM. If (a), single-node attribution should be
markedly sharper than the summed version. If (b), it should not change.
"""
import argparse, os, sys
import numpy as np
import torch
import torch.nn.functional as F
from torch.utils.data import DataLoader

sys.path.insert(0, os.path.join(os.getcwd(), 'implementation'))
from amog_modes import resolve_mode
from amog_train import (AMOGNet, make_datasets, suggest_batch, loader_kwargs,
                        configure_backend)
from amog_attribution import CROP, cam_layer, central_disc, dataset_args
from amog_attribution_graph import CONDITION_SLOT

STAGE = sys.argv[1] if len(sys.argv) > 1 else 'E6'
SEED = 42
ctx = resolve_mode(argparse.Namespace(mode='real', seed=SEED, epochs=None,
                                      lr=None, device=None, max_samples=None,
                                      batch_size=None))
gpu = configure_backend()
torch.manual_seed(SEED); np.random.seed(SEED)
_, _, test_ds, _ = make_datasets(ctx, STAGE, dataset_args(STAGE, SEED, 0, 0))
loader = DataLoader(test_ds, batch_size=2, shuffle=False,
                    **loader_kwargs(0, cuda=str(ctx.device).startswith('cuda')))
ck = os.path.join(ctx.checkpoint_dir, '%s_real_seed%d_best.pt' % (STAGE, SEED))
sd = torch.load(ck, map_location=ctx.device, weights_only=False)
model = AMOGNet(STAGE, sd.get('backbone') or 'resnet18', 256, False, False,
                SEED, pretrained=False).to(ctx.device)
model.load_state_dict(sd['model_state_dict'], strict=True)
model.eval()
layers = [cam_layer(e, 'layer3') for e in model.encoders]
disc, area = central_disc(0.5)
dm = torch.from_numpy(disc.astype(np.float32)).to(ctx.device)


def cams(imgs, mask, ev, mode, node=None):
    acts, grads, handles = {}, {}, []

    def mk(i):
        def f(_m, _i, o): acts[i] = o
        def b(_m, _gi, go): grads[i] = go[0]
        return f, b
    for i, lay in enumerate(layers):
        f, b = mk(i)
        handles.append(lay.register_forward_hook(f))
        handles.append(lay.register_full_backward_hook(b))
    try:
        model.zero_grad(set_to_none=True)
        with torch.enable_grad():
            logits, _ = model.forward_graph(imgs, mask, ev)
            B, N, C = logits.shape
            flat = logits.reshape(-1, C)
            if getattr(model, 'use_ordinal', False):
                sc = flat.sum(dim=1)
            else:
                sc = flat.gather(1, flat.argmax(1, keepdim=True)).squeeze(1)
            if mode == 'sum':
                sc.sum().backward()
            else:
                sel = torch.zeros_like(sc)
                idx = torch.arange(B, device=sc.device) * N + node
                sel[idx] = 1.0
                (sc * sel).sum().backward()
        out = {}
        for i in acts:
            if i not in grads:
                continue
            w = grads[i].mean(dim=(2, 3), keepdim=True)
            c = F.relu((w * acts[i]).sum(dim=1, keepdim=True))
            out[i] = F.interpolate(c.float(), (CROP, CROP), mode='bilinear',
                                   align_corners=False)[:, 0]
        return out, logits.shape
    finally:
        for h in handles:
            h.remove()


def conc(m):
    f = m.reshape(m.shape[0], -1)
    t = f.sum(1, keepdim=True)
    f = torch.where(t > 0, f / t, torch.full_like(f, 1.0 / f.size(1)))
    return ((f.reshape(-1, CROP, CROP) * dm).sum(dim=(1, 2)))


batch = next(iter(loader))
imgs, mask, y, lmask, ev, pid = [b.to(ctx.device) for b in batch]
B, N = imgs.shape[:2]

print('stage %s   batch %d patients x %d nodes' % (STAGE, B, N))
print()
res = {}
for node in (2, 7, 12):                      # canal at L1-L2, L2-L3, L3-L4
    slot = CONDITION_SLOT[node % 5]
    m_sum, _ = cams(imgs, mask, ev, 'sum')
    m_one, _ = cams(imgs, mask, ev, 'one', node=node)
    idx = torch.arange(B, device=imgs.device) * N + node
    cs = conc(m_sum[slot][idx]).mean().item()
    co = conc(m_one[slot][idx]).mean().item()
    res[node] = (cs, co)
    print('node %2d (cond %d, encoder %d): summed %.3f   single-node %.3f   delta %+.3f'
          % (node, node % 5, slot, cs, co, co - cs))

print()
print('disc area (chance) %.3f' % area)
d = np.mean([b - a for a, b in res.values()])
print('mean improvement from single-node attribution: %+.3f' % d)
print()
if d > 0.05:
    print('-> THE PROBE. Summing node logits smears gradient across the graph;')
    print('   graph-rung numbers from the summed version understate concentration.')
else:
    print('-> THE MODEL. Single-node attribution is no sharper, so the lower')
    print('   concentration is a property of the graph rungs, not of the probe.')

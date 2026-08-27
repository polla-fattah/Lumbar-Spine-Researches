"""How many Grad-CAM maps are all-zero after ReLU, per rung?

A CAM of ReLU(sum_c w_c * A_c) is empty when the gradient-weighted combination
is negative everywhere. The attribution code replaces an empty map with a
uniform one so the normalisation is defined -- and a uniform map scores exactly
the disc area, i.e. chance. If a rung produces many empty maps, its reported
concentration is a blend of real attribution and chance, and the number is not a
statement about where that model looks.
"""
import argparse, os, sys
import numpy as np, torch, torch.nn.functional as F
from torch.utils.data import DataLoader
sys.path.insert(0, os.path.join(os.getcwd(), 'implementation'))
from amog_modes import resolve_mode
from amog_train import (AMOGNet, make_datasets, suggest_batch, loader_kwargs,
                        configure_backend)
from amog_attribution import CROP, cam_layer, dataset_args
from amog_attribution_graph import CONDITION_SLOT, _cam_for_node

SEED=42
ctx = resolve_mode(argparse.Namespace(mode='real', seed=SEED, epochs=None, lr=None,
                                      device=None, max_samples=None, batch_size=None))
gpu = configure_backend()
print('%-6s %10s %12s' % ('rung','nodes','empty CAMs'))
for stage in ('E5','E6','E7'):
    torch.manual_seed(SEED); np.random.seed(SEED)
    _,_,ds,_ = make_datasets(ctx, stage, dataset_args(stage, SEED, 0, 0))
    loader = DataLoader(ds, batch_size=2, shuffle=False,
                        **loader_kwargs(0, cuda=str(ctx.device).startswith('cuda')))
    ck = os.path.join(ctx.checkpoint_dir, '%s_real_seed42_best.pt'%stage)
    sd = torch.load(ck, map_location=ctx.device, weights_only=False)
    model = AMOGNet(stage, sd.get('backbone') or 'resnet18', 256, False, False,
                    SEED, pretrained=False).to(ctx.device)
    model.load_state_dict(sd['model_state_dict'], strict=True); model.eval()
    layers = [cam_layer(e,'layer3') for e in model.encoders]
    it = iter(loader)
    tot = empty = 0
    for _ in range(3):
        try: batch = next(it)
        except StopIteration: break
        imgs, mask, y, lmask, ev, pid = [b.to(ctx.device) for b in batch]
        B,N = imgs.shape[:2]
        for node in range(N):
            maps = _cam_for_node(model, imgs, mask, ev, layers, node)
            if not maps: continue
            m = maps.get(int(CONDITION_SLOT[node%5]), next(iter(maps.values())))
            idx = torch.arange(B, device=imgs.device)*N + node
            sel = m[idx]
            s = sel.reshape(sel.shape[0],-1).sum(1)
            tot += int(s.numel()); empty += int((s <= 0).sum())
    print('%-6s %10d %8d (%4.0f%%)' % (stage, tot, empty, 100*empty/max(tot,1)))

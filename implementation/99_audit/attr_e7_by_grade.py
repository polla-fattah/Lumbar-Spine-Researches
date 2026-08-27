"""Does E7's attribution depend on the target's grade?

E7 sits BELOW chance concentration while E6 sits well above it. The two differ
only in the head: E7 explains an ordinal severity score rather than a class
logit. 77% of targets are Normal/Mild, and explaining "how severe is this"
on a target with no pathology highlights the absence of evidence, which has no
reason to be centred.

If that is the mechanism, concentration should rise with true grade. If it does
not, the probe is simply failing on this head and no number should be reported.
"""
import argparse, os, sys
import numpy as np, torch, torch.nn.functional as F
from torch.utils.data import DataLoader
sys.path.insert(0, os.path.join(os.getcwd(), 'implementation'))
from amog_modes import resolve_mode, CONDITIONS
from amog_train import (AMOGNet, make_datasets, loader_kwargs, configure_backend)
from amog_attribution import CROP, cam_layer, central_disc, dataset_args
from amog_attribution_graph import CONDITION_SLOT, _cam_for_node

GRADES = ['Normal/Mild','Moderate','Severe']
ctx = resolve_mode(argparse.Namespace(mode='real', seed=42, epochs=None, lr=None,
                                      device=None, max_samples=None, batch_size=None))
gpu = configure_backend()
disc, area = central_disc(0.5)

for stage in ('E6','E7'):
    torch.manual_seed(42); np.random.seed(42)
    _,_,ds,_ = make_datasets(ctx, stage, dataset_args(stage, 42, 0, 0))
    loader = DataLoader(ds, batch_size=4, shuffle=False,
                        **loader_kwargs(0, cuda=str(ctx.device).startswith('cuda')))
    ck = os.path.join(ctx.checkpoint_dir, '%s_real_seed42_best.pt'%stage)
    sd = torch.load(ck, map_location=ctx.device, weights_only=False)
    model = AMOGNet(stage, sd.get('backbone') or 'resnet18', 256, False, False,
                    42, pretrained=False).to(ctx.device)
    model.load_state_dict(sd['model_state_dict'], strict=True); model.eval()
    layers = [cam_layer(e,'layer3') for e in model.encoders]
    dm = torch.from_numpy(disc.astype(np.float32)).to(ctx.device)

    by = {0:[],1:[],2:[]}
    it = iter(loader)
    for _ in range(8):
        try: batch = next(it)
        except StopIteration: break
        imgs, mask, y, lmask, ev, pid = [b.to(ctx.device) for b in batch]
        B,N = imgs.shape[:2]
        yf = y.reshape(-1); lf = lmask.reshape(-1)
        for node in range(N):
            maps = _cam_for_node(model, imgs, mask, ev, layers, node)
            if not maps: continue
            m = maps.get(int(CONDITION_SLOT[node%5]), next(iter(maps.values())))
            idx = torch.arange(B, device=imgs.device)*N + node
            sel = m[idx]
            f = sel.reshape(sel.shape[0],-1); t = f.sum(1,keepdim=True)
            f = torch.where(t>0, f/t, torch.full_like(f,1.0/f.size(1)))
            conc = ((f.reshape(-1,CROP,CROP)*dm).sum((1,2))).detach().cpu().numpy()
            gg = yf[idx].detach().cpu().numpy(); kk = lf[idx].detach().cpu().numpy()
            for c,g,k in zip(conc, gg, kk):
                if k>0 and int(g) in by: by[int(g)].append(float(c))
    print('%s  (chance %.3f)' % (stage, area))
    for g in (0,1,2):
        v = by[g]
        if v: print('   %-12s n=%-5d concentration %.3f' % (GRADES[g], len(v), np.mean(v)))
    print()

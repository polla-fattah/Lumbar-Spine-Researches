"""Is E7's low attribution real, or an artefact of which scalar is explained?

Grad-CAM explains ONE scalar. A categorical head makes that choice obvious.
E7's ordinal head emits two cumulative logits, P(y>0) and P(y>1), and there is
no single obvious scalar. If the answer depends strongly on that choice, the
number should not be reported as a property of the model.

Tested: their sum, each alone, and the one corresponding to the threshold the
model actually crossed.
"""
import argparse, os, sys
import numpy as np, torch, torch.nn.functional as F
from torch.utils.data import DataLoader
sys.path.insert(0, os.path.join(os.getcwd(), 'implementation'))
from amog_modes import resolve_mode
from amog_train import (AMOGNet, make_datasets, suggest_batch, loader_kwargs,
                        configure_backend)
from amog_attribution import CROP, cam_layer, central_disc, dataset_args
from amog_attribution_graph import CONDITION_SLOT

SEED = 42
ctx = resolve_mode(argparse.Namespace(mode='real', seed=SEED, epochs=None, lr=None,
                                      device=None, max_samples=None, batch_size=None))
gpu = configure_backend(); torch.manual_seed(SEED); np.random.seed(SEED)
_, _, ds, _ = make_datasets(ctx, 'E7', dataset_args('E7', SEED, 0, 0))
loader = DataLoader(ds, batch_size=2, shuffle=False,
                    **loader_kwargs(0, cuda=str(ctx.device).startswith('cuda')))
ck = os.path.join(ctx.checkpoint_dir, 'E7_real_seed42_best.pt')
sd = torch.load(ck, map_location=ctx.device, weights_only=False)
model = AMOGNet('E7', sd.get('backbone') or 'resnet18', 256, False, False, SEED,
                pretrained=False).to(ctx.device)
model.load_state_dict(sd['model_state_dict'], strict=True); model.eval()
layers = [cam_layer(e, 'layer3') for e in model.encoders]
disc, area = central_disc(0.5)
dm = torch.from_numpy(disc.astype(np.float32)).to(ctx.device)

def run(imgs, mask, ev, node, mode):
    acts, grads, hs = {}, {}, []
    def mk(i):
        def f(_m,_i,o): acts[i]=o
        def b(_m,_g,go): grads[i]=go[0]
        return f,b
    for i,l in enumerate(layers):
        f,b = mk(i); hs += [l.register_forward_hook(f), l.register_full_backward_hook(b)]
    try:
        model.zero_grad(set_to_none=True)
        with torch.enable_grad():
            lg,_ = model.forward_graph(imgs, mask, ev)
            B,N,C = lg.shape; flat = lg.reshape(-1,C)
            if mode=='sum':   sc = flat.sum(1)
            elif mode=='t0':  sc = flat[:,0]
            elif mode=='t1':  sc = flat[:,1]
            else:
                p = torch.sigmoid(flat)
                k = (p>0.5).sum(1).clamp(max=C-1)
                sc = flat.gather(1,k.unsqueeze(1)).squeeze(1)
            pick = torch.zeros_like(sc)
            pick[torch.arange(B,device=sc.device)*N+node] = 1.0
            (sc*pick).sum().backward()
        i = CONDITION_SLOT[node%5]
        if i not in acts or i not in grads: return None
        w = grads[i].mean((2,3),keepdim=True)
        cam = F.relu((w*acts[i]).sum(1,keepdim=True))
        cam = F.interpolate(cam.float(),(CROP,CROP),mode='bilinear',align_corners=False)[:,0]
        idx = torch.arange(B,device=imgs.device)*N+node
        c = cam[idx]; f2 = c.reshape(c.shape[0],-1); t = f2.sum(1,keepdim=True)
        f2 = torch.where(t>0, f2/t, torch.full_like(f2,1.0/f2.size(1)))
        return ((f2.reshape(-1,CROP,CROP)*dm).sum((1,2))).mean().item()
    finally:
        for h in hs: h.remove()

batch = next(iter(loader))
imgs, mask, y, lmask, ev, pid = [b.to(ctx.device) for b in batch]
print('E7 seed 42, disc area (chance) %.3f' % area)
print()
print('%-10s %8s %8s %8s %8s' % ('node','sum','P(y>0)','P(y>1)','crossed'))
acc = {m: [] for m in ('sum','t0','t1','crossed')}
for node in (2,7,12,1,3):
    vals = {}
    for m in ('sum','t0','t1','crossed'):
        v = run(imgs, mask, ev, node, m)
        vals[m] = v
        if v is not None: acc[m].append(v)
    print('node %-5d %8.3f %8.3f %8.3f %8.3f' % (node, vals['sum'], vals['t0'],
                                                  vals['t1'], vals['crossed']))
print()
means = {m: float(np.mean(v)) for m,v in acc.items() if v}
print('means:', {k: round(v,3) for k,v in means.items()})
spread = max(means.values()) - min(means.values())
print('spread across scalar choices: %.3f' % spread)
print()
if spread > 0.08:
    print('-> THE CHOICE MATTERS. E7 attribution is not a single well-defined')
    print('   number; report the sensitivity rather than one value.')
else:
    print('-> ROBUST to the choice. E7 genuinely attends less than E6.')

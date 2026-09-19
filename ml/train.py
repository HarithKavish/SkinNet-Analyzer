"""Train the three-model ensemble served by classify.py and report honest accuracy.

    python train.py --data path/to/data/train path/to/data/test

Each --data root holds one sub-folder per class (e.g. "BA- cellulitis", "FU-ringworm").
The roots are merged, exact duplicates dropped, and near-duplicate photos (the Kaggle set
is full of flipped/rotated/resized copies of the same picture) are grouped so a group never
straddles train, validation and test. Weights are written as state_dicts to --out.
"""
import argparse
import glob
import hashlib
import json
import math
import os
import random
import time

import cv2
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
import torchvision.models as tvm
import torchvision.transforms as T
from PIL import Image

# Order must match classify.py and models/class_indices.pkl
CLASSES = ["Cellulitis", "Impetigo", "Athlete-foot", "Nail-fungus", "Ringworm",
           "Cutaneous-larva-migrans", "Chickenpox", "Shingles"]
FOLDER_KEYS = [c.lower() for c in CLASSES]
ARCHS = ("efficientnet", "resnet", "mobilenet")
NEAR_DUP_BITS = 12  # 16x16 average-hash distance; no cross-class pair exists at or below this
NORM = T.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
EVAL_TF = T.Compose([T.Resize((224, 224)), T.ToTensor(), NORM])  # identical to classify.py
MEAN = torch.tensor([0.485, 0.456, 0.406]).view(1, 3, 1, 1)
STD = torch.tensor([0.229, 0.224, 0.225]).view(1, 3, 1, 1)
CACHE_SIZE = 256


def uint8_cache(items):
    """All training images as one (N,3,S,S) uint8 tensor so augmentation can run on the GPU."""
    arr = np.stack([np.asarray(it["img"].resize((CACHE_SIZE, CACHE_SIZE), Image.BILINEAR)) for it in items])
    return torch.from_numpy(arr).permute(0, 3, 1, 2).contiguous()


def gpu_augment(x):
    """Random resized crop, rotation +-20deg, flips, brightness/contrast jitter - batched, on device.
    (CPU/PIL augmentation left the GPU idle on this 4-core laptop.)"""
    B, dev = x.size(0), x.device
    x = x.float() / 255

    def u(lo, hi):
        return torch.empty(B, device=dev).uniform_(lo, hi)

    ratio = torch.exp(u(math.log(0.75), math.log(1.33)))
    area = u(0.5, 1.0)
    w, h = torch.sqrt(area * ratio).clamp(max=1.0), torch.sqrt(area / ratio).clamp(max=1.0)
    ang = u(-20, 20) * math.pi / 180
    fx, fy = (torch.rand(B, device=dev) < 0.5).float() * 2 - 1, (torch.rand(B, device=dev) < 0.5).float() * 2 - 1
    sx, sy, c, s_ = w * fx, h * fy, torch.cos(ang), torch.sin(ang)
    theta = torch.zeros(B, 2, 3, device=dev)
    theta[:, 0, 0], theta[:, 0, 1], theta[:, 0, 2] = c * sx, -s_ * sy, u(-1, 1) * (1 - w)
    theta[:, 1, 0], theta[:, 1, 1], theta[:, 1, 2] = s_ * sx, c * sy, u(-1, 1) * (1 - h)
    grid = F.affine_grid(theta, (B, 3, 224, 224), align_corners=False)
    out = F.grid_sample(x, grid, mode="bilinear", padding_mode="reflection", align_corners=False)
    out = out * u(0.8, 1.2).view(B, 1, 1, 1)
    mean = out.mean((1, 2, 3), keepdim=True)
    out = ((out - mean) * u(0.8, 1.2).view(B, 1, 1, 1) + mean).clamp(0, 1)
    return (out - MEAN.to(dev)) / STD.to(dev)


def build(arch, pretrained):
    if arch == "efficientnet":
        m = tvm.efficientnet_b0(weights=tvm.EfficientNet_B0_Weights.IMAGENET1K_V1 if pretrained else None)
        m.classifier[1] = nn.Linear(1280, len(CLASSES))
    elif arch == "resnet":
        m = tvm.resnet18(weights=tvm.ResNet18_Weights.IMAGENET1K_V1 if pretrained else None)
        m.fc = nn.Linear(512, len(CLASSES))
    else:
        m = tvm.mobilenet_v2(weights=tvm.MobileNet_V2_Weights.IMAGENET1K_V1 if pretrained else None)
        m.classifier[1] = nn.Linear(1280, len(CLASSES))
    return m


def is_head(name):
    return name.startswith(("classifier", "fc."))


# ----------------------------------------------------------------------------- data
def load_dataset(roots):
    items, seen = [], set()
    for root in roots:
        for folder in sorted(os.listdir(root)):
            y = next((i for i, k in enumerate(FOLDER_KEYS) if k in folder.lower()), None)
            if y is None:
                continue
            for path in sorted(glob.glob(os.path.join(root, folder, "*"))):
                digest = hashlib.md5(open(path, "rb").read()).hexdigest()
                bgr = cv2.imdecode(np.fromfile(path, np.uint8), cv2.IMREAD_COLOR)  # same decode as app.py
                if digest in seen or bgr is None:
                    continue
                seen.add(digest)
                h, w = bgr.shape[:2]
                if min(h, w) > 320:  # cache smaller; augmentation crops from this
                    s = 320 / min(h, w)
                    bgr = cv2.resize(bgr, (round(w * s), round(h * s)), interpolation=cv2.INTER_AREA)
                items.append({"path": path, "y": y, "img": Image.fromarray(cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB))})
    return items


def near_duplicate_groups(items):
    """Union-find over images whose 16x16 average hashes match under any flip/rotation."""
    def gray(it):
        g = cv2.cvtColor(np.asarray(it["img"]), cv2.COLOR_RGB2GRAY)
        return cv2.resize(g, (16, 16), interpolation=cv2.INTER_AREA).astype(np.float32)

    grays = [gray(it) for it in items]
    base = np.array([(g > g.mean()).ravel() for g in grays], dtype=np.float32) * 2 - 1
    var = np.array([[(v > v.mean()).ravel() for f in (g, g[:, ::-1]) for v in (np.rot90(f, k) for k in range(4))]
                    for g in grays], dtype=np.float32) * 2 - 1
    n = len(items)
    dist = ((256 - base @ var.reshape(n * 8, 256).T) / 2).reshape(n, n, 8).min(2)
    parent = list(range(n))

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    for i, j in zip(*np.where(np.triu(dist <= NEAR_DUP_BITS, 1))):
        if items[i]["y"] == items[j]["y"]:
            parent[find(i)] = find(j)
    return [find(i) for i in range(n)]


def grouped_split(items, groups, seed, val_frac=0.2, test_frac=0.2):
    rng = random.Random(seed)
    split = [None] * len(items)
    for y in range(len(CLASSES)):
        by_group = {}
        for i, it in enumerate(items):
            if it["y"] == y:
                by_group.setdefault(groups[i], []).append(i)
        members = list(by_group.values())
        rng.shuffle(members)
        total, count = sum(len(m) for m in members), {"test": 0, "val": 0}
        for m in members:
            name = "test" if count["test"] < test_frac * total else "val" if count["val"] < val_frac * total else "train"
            if name != "train":
                count[name] += len(m)
            for i in m:
                split[i] = name
    return split


# ------------------------------------------------------------------------ training
def eval_tensor(items):
    """Eval-time preprocessing, identical to classify.py: Resize((224,224)) + ImageNet normalisation."""
    return torch.stack([EVAL_TF(it["img"]) for it in items])


@torch.no_grad()
def logits_from(model, x, device):
    model.eval()
    logits = torch.cat([model(x[i:i + 64].to(device)).float().cpu() for i in range(0, len(x), 64)])
    if not torch.isfinite(logits).all():
        raise RuntimeError("non-finite logits - training diverged")
    return logits


def logits_of(model, items, device):
    return logits_from(model, eval_tensor(items), device)


def train_one(arch, train_items, val_items, device, seed, epochs=30, warmup=3, patience=10, fixed_epochs=None):
    torch.manual_seed(seed)
    model = build(arch, pretrained=True).to(device)
    total = fixed_epochs or epochs
    xs, ys = uint8_cache(train_items), torch.tensor([it["y"] for it in train_items])
    batch = 16 if arch == "efficientnet" else 32  # efficientnet is the one that needs the 2GB card's headroom
    val_x = eval_tensor(val_items) if val_items else None
    head = [p for n, p in model.named_parameters() if is_head(n)]
    body = [p for n, p in model.named_parameters() if not is_head(n)]
    opt = torch.optim.AdamW([{"params": head, "lr": 1e-3}, {"params": body, "lr": 1e-4}], weight_decay=1e-2)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=max(total - warmup, 1))
    counts = np.bincount([it["y"] for it in train_items], minlength=len(CLASSES)).clip(min=1)
    weights = torch.tensor(counts.sum() / (len(CLASSES) * counts), dtype=torch.float32, device=device)
    loss_fn = nn.CrossEntropyLoss(weight=weights, label_smoothing=0.1)  # photos per class are very uneven
    y_val = torch.tensor([it["y"] for it in val_items]) if val_items else None
    best_score, best_state, best_ep, stale = (-1.0, -1e9), None, 0, 0

    for ep in range(1, total + 1):
        for p in body:  # warm-up trains only the new head
            p.requires_grad = ep > warmup
        model.train()
        perm = torch.randperm(len(ys))
        for i in range(0, len(ys) - batch + 1, batch):
            idx = perm[i:i + batch]
            x, y = gpu_augment(xs[idx].to(device)), ys[idx].to(device)
            opt.zero_grad()
            loss_fn(model(x), y).backward()
            opt.step()
        if ep > warmup:
            sched.step()
        if val_items:
            lg = logits_from(model, val_x, device)
            score = ((lg.argmax(1) == y_val).float().mean().item(), -nn.functional.cross_entropy(lg, y_val).item())
            if score > best_score:  # higher accuracy wins, lower loss breaks ties
                best_score, best_ep, stale = score, ep, 0
                best_state = {k: v.detach().cpu().clone() for k, v in model.state_dict().items()}
            else:
                stale += 1
            print(f"  {arch} ep{ep:02d} val_acc={score[0]:.3f} val_loss={-score[1]:.3f}", flush=True)
            if stale >= patience:
                break
    if best_state is not None:
        model.load_state_dict(best_state)
    return model, best_ep, (best_score[0] if val_items else None)


# ------------------------------------------------------------------------ reporting
def summarize(items, logits_by_arch, title):
    y = np.array([it["y"] for it in items])
    ens = torch.stack([logits_by_arch[a] for a in ARCHS]).mean(0)  # same averaging as classify.py
    probs = torch.softmax(ens, 1)
    pred = probs.argmax(1).numpy()
    conf = probs.max(1).values.numpy()
    top3 = np.mean([y[i] in probs[i].topk(3).indices.tolist() for i in range(len(y))])
    print(f"\n=== {title} (n={len(y)}) ===")
    res = {"n": len(y), "per_model_top1": {a: float((logits_by_arch[a].argmax(1).numpy() == y).mean()) for a in ARCHS},
           "ensemble_top1": float((pred == y).mean()), "ensemble_top3": float(top3),
           "mean_confidence": float(conf.mean()),
           "confidence_correct_p10": float(np.percentile(conf[pred == y], 10)) if (pred == y).any() else None,
           "confidence_wrong_median": float(np.median(conf[pred != y])) if (pred != y).any() else None}
    print("per-model:", {a: f"{v:.1%}" for a, v in res["per_model_top1"].items()})
    print(f"ensemble top1={res['ensemble_top1']:.1%} top3={res['ensemble_top3']:.1%} mean conf={conf.mean():.2f}")
    per_class = {}
    for c, name in enumerate(CLASSES):
        m = y == c
        wrong = np.bincount(pred[m & (pred != c)], minlength=len(CLASSES))
        conf_to = CLASSES[int(wrong.argmax())] if wrong.any() else "-"
        per_class[name] = {"recall": float((pred[m] == c).mean()) if m.any() else None, "n": int(m.sum()), "confused_with": conf_to}
        print(f"  {name:26s} {int((pred[m] == c).sum()):3d}/{int(m.sum()):3d}  most confused with: {conf_to}")
    res["per_class"] = per_class
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", nargs="+", required=True)
    ap.add_argument("--out", default="models")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--epochs", type=int, default=30)
    ap.add_argument("--no-refit", action="store_true", help="skip retraining on train+val")
    args = ap.parse_args()

    random.seed(args.seed)
    np.random.seed(args.seed)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print("device:", device)

    items = load_dataset(args.data)
    groups = near_duplicate_groups(items)
    split = grouped_split(items, groups, args.seed)
    part = {s: [it for it, sp in zip(items, split) if sp == s] for s in ("train", "val", "test")}
    # one representative per near-duplicate group for a fair test score (copies of one photo count once)
    seen, unique_test = set(), []
    for i, (it, sp) in enumerate(zip(items, split)):
        if sp == "test" and groups[i] not in seen:
            seen.add(groups[i])
            unique_test.append(it)
    info = {"unique_files": len(items), "near_duplicate_groups": len(set(groups)),
            **{f"{s}_files": len(v) for s, v in part.items()}, "test_unique_photos": len(unique_test),
            "per_class_groups": {c: len({groups[i] for i, it in enumerate(items) if it["y"] == k}) for k, c in enumerate(CLASSES)}}
    print(json.dumps(info, indent=1))

    os.makedirs(args.out, exist_ok=True)
    val_lg, test_lg, uniq_lg, models_out = {}, {}, {}, {}
    for arch in ARCHS:
        t0 = time.time()
        model, best_ep, val_acc = train_one(arch, part["train"], part["val"], device, args.seed, args.epochs)
        print(f"{arch}: best val acc {val_acc:.3f} at epoch {best_ep} ({time.time() - t0:.0f}s)")
        val_lg[arch] = logits_of(model, part["val"], device)
        if not args.no_refit:  # final model sees train+val for the epoch count chosen on val
            model, _, _ = train_one(arch, part["train"] + part["val"], [], device, args.seed, fixed_epochs=max(best_ep, 8))
        test_lg[arch] = logits_of(model, part["test"], device)
        uniq_lg[arch] = logits_of(model, unique_test, device)
        models_out[arch] = {k: v.detach().cpu() for k, v in model.state_dict().items()}
        torch.save(models_out[arch], os.path.join(args.out, f"{arch}.pth"))

    metrics = {"dataset": info, "seed": args.seed, "refit_on_train_val": not args.no_refit,
               "validation_files": summarize(part["val"], val_lg, "validation (used for epoch selection)"),
               "test_unique_photos": summarize(unique_test, uniq_lg, "TEST - one image per photo group"),
               "test_all_files": summarize(part["test"], test_lg, "TEST - all files")}
    with open(os.path.join(args.out, "metrics.json"), "w") as f:
        json.dump(metrics, f, indent=1)


if __name__ == "__main__":
    main()

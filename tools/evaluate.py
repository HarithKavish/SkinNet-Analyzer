"""Reproduce the evaluation numbers in the README.

    python tools/evaluate.py pipeline --data DATA/train DATA/test   # full pipeline, perfect answers, seen vs unseen
    python tools/evaluate.py noise    --data DATA/train DATA/test   # pipeline with wrong symptom answers
    python tools/evaluate.py live     --data DATA/train DATA/test   # the deployed website, over HTTP (needs `requests`)

Run from the repository root. Needs the packages in ml/requirements.txt.

It uses the app's real code (ml/classify.py and backend/services/*) and the same
near-duplicate grouping and split as train.py (default --seed 0), so "unseen" photos are ones
the models never trained on, nor any flipped/rotated copy of. Every photo counts once.
The "perfect patient" answers Yes to exactly the symptoms in SYMPTOM_MAPPING for the true disease.
"""
import argparse
import io
import os
import sys
from collections import defaultdict

import numpy as np

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, os.path.join(ROOT, "ml"))
sys.path.insert(0, os.path.join(ROOT, "backend"))

import classify as c                                        # ml/classify.py, the served classifier
import train as t                                           # ml/train.py: same data loading, grouping and split
from services import symptoms as sy                         # backend/services: the real question/scoring logic
from services.out_of_class import THRESHOLD, detect_unknown_disease

sy.print = lambda *a, **k: None   # the backend logs every call; keep the report readable

PRODUCTION = "https://skinnet-analyzer-backend-latest.onrender.com"
CORS_ORIGIN = "https://harithkavish.com"


def load_photos(roots, seed, splits):
    """One representative image per near-duplicate group, per split, from the requested splits."""
    items = t.load_dataset(roots)
    groups = t.near_duplicate_groups(items)
    split = t.grouped_split(items, groups, seed)
    photos, seen = [], set()
    for i, (it, sp) in enumerate(zip(items, split)):
        if sp in splits and (sp, groups[i]) not in seen:
            seen.add((sp, groups[i]))
            photos.append({"split": sp, "truth": t.CLASSES[it["y"]], "img": it["img"], "path": it["path"]})
    return photos


def prepare(photo):
    """Run the image model and build the symptom questions exactly as POST /api/upload does."""
    top3 = c.ensemble_classify(photo["img"])
    photo.update(top3=top3, names=[n for n, _ in top3], probs=[p for _, p in top3],
                 rejected=detect_unknown_disease(top3), questions=None)
    if not photo["rejected"]:
        questions, keys = sy.confirm_disease_with_symptoms(top3)
        photo.update(questions=list(questions), keys=keys,
                     ideal=np.array([q in sy.SYMPTOM_MAPPING[photo["truth"]] for q in questions]))
    return photo


def answer(photo, answers_bool):
    """The shipped scoring function, as /api/confirm_symptoms calls it."""
    return sy.process_user_responses(
        photo["keys"], {q: "1" if a else "0" for q, a in zip(photo["questions"], answers_bool)}, photo["probs"])


# ---------------------------------------------------------------------------- pipeline
def run_pipeline(args):
    photos = [prepare(p) for p in load_photos(args.data, args.seed, ("train", "val", "test"))]
    print(f"rejection threshold in use: {THRESHOLD}\n")
    titles = (("train", "SEEN (training photos)"), ("val", "UNSEEN - validation photos (used to pick the epoch)"),
              ("test", "UNSEEN - test photos (never touched)"))
    failures = []
    for sp, title in titles:
        print(f"=== {title} ===")
        print(f"{'disease':26s} {'photos':>6s} {'image top1':>11s} {'image top3':>11s} {'PIPELINE':>9s}  rejected")
        tot = defaultdict(int)
        for d in t.CLASSES:
            rows = [p for p in photos if p["split"] == sp and p["truth"] == d]
            r = dict(n=len(rows), top1=sum(p["names"][0] == d for p in rows), top3=sum(d in p["names"] for p in rows),
                     rej=sum(p["rejected"] for p in rows), ok=0)
            for p in rows:
                if not p["rejected"]:
                    final, _ = answer(p, p["ideal"])
                    r["ok"] += final == d
                    if final != d and sp != "train":
                        failures.append((sp, d, p["names"], final))
            for k, v in r.items():
                tot[k] += v
            n = max(r["n"], 1)
            print(f"{d:26s} {r['n']:6d} {r['top1'] / n:11.0%} {r['top3'] / n:11.0%} {r['ok'] / n:9.0%}  {r['rej']}")
        n = max(tot["n"], 1)
        print(f"{'ALL':26s} {tot['n']:6d} {tot['top1'] / n:11.1%} {tot['top3'] / n:11.1%} {tot['ok'] / n:9.1%}  {tot['rej']}\n")
    unseen = [p for p in photos if p["split"] != "train"]
    ok = sum(answer(p, p["ideal"])[0] == p["truth"] for p in unseen if not p["rejected"])
    print(f"UNSEEN (validation + test) combined: {len(unseen)} photos, photo only top-1 = "
          f"{np.mean([p['names'][0] == p['truth'] for p in unseen]):.1%}, top-3 = "
          f"{np.mean([p['truth'] in p['names'] for p in unseen]):.1%}, pipeline = {ok / len(unseen):.1%}")
    print("\nfailures on unseen photos (photo rejected by the cutoff is not listed):")
    for sp, truth, names, final in failures:
        print(f"  [{sp}] true={truth:24s} photo top3={names} -> pipeline said {final}")


# ------------------------------------------------------------------------------ noise
def corrupt(kind, ideal, prob, rng):
    r = rng.random(len(ideal)) < prob
    if kind == "flip":       # any answer can be wrong
        return ideal ^ r
    if kind == "forget":     # says No to symptoms they have
        return ideal & ~r
    return ideal | (~ideal & r)   # over-report: says Yes to symptoms they lack


def run_noise(args):
    photos = [prepare(p) for p in load_photos(args.data, args.seed, ("val", "test"))]
    photo_only = np.mean([p["names"][0] == p["truth"] for p in photos])
    print(f"{len(photos)} unseen photos; photo alone (no questions) = {photo_only:.1%}; {args.trials} random trials per photo\n")
    rng = np.random.default_rng(args.seed)
    kinds = (("flip", "RANDOM FLIPS"), ("forget", "FORGETFUL (says No to symptoms they have)"),
             ("over", "OVER-REPORTING (says Yes to symptoms they lack)"))
    for kind, title in kinds:
        print(f"--- {title}: disease correct  [user sees a correct report, i.e. not 'Out of Class'] ---")
        for prob in (0.0, 0.10, 0.20, 0.30, 0.50):
            ok = usable = total = 0
            for p in photos:
                if p["rejected"]:
                    total += args.trials
                    continue
                for _ in range(args.trials):
                    final, severity = answer(p, corrupt(kind, p["ideal"], prob, rng))
                    good = final == p["truth"]
                    ok += good
                    usable += good and severity != "Out of Class"
                    total += 1
            print(f"  {prob:4.0%} wrong answers: {ok / total:6.1%}  [{usable / total:6.1%}]")
        print()


# ------------------------------------------------------------------------------- live
def run_live(args):
    import requests
    from PIL import Image
    photos = load_photos(args.data, args.seed, ("test",))
    print(f"{len(photos)} unseen test photos sent to {args.url}\n", flush=True)
    headers = {"Origin": CORS_ORIGIN}
    rng = np.random.default_rng(1)
    res = defaultdict(lambda: defaultdict(int))
    for n, p in enumerate(photos, 1):
        truth = p["truth"]
        raw, ext = open(p["path"], "rb").read(), os.path.splitext(p["path"])[1].lower()
        if ext not in (".jpg", ".jpeg", ".png"):   # the ML service accepts only JPEG/PNG
            buf = io.BytesIO()
            Image.open(io.BytesIO(raw)).convert("RGB").save(buf, "JPEG")
            raw, ext = buf.getvalue(), ".jpg"
        r = requests.post(args.url + "/api/upload", headers=headers, timeout=120,
                          files={"file": ("photo" + ext, raw, "image/png" if ext == ".png" else "image/jpeg")})
        d = res[truth]
        d["n"] += 1
        if r.status_code != 200:
            d["upload_error"] += 1
            continue
        up = r.json()
        if "questions" not in up:
            d["rejected"] += 1
            continue
        d["top1"] += up["diseases"][0] == truth
        ideal = {q: q in sy.SYMPTOM_MAPPING[truth] for q in up["questions"]}

        def confirm(answers):
            return requests.post(args.url + "/api/confirm_symptoms", headers=headers, timeout=60, json={
                "answers": {q: "1" if v else "0" for q, v in answers.items()},
                "diseases": up["diseases"], "probabilities": up["probabilities"]}).json()

        d["ideal_ok"] += confirm(ideal)["disease"] == truth
        for _ in range(3):   # about 20% of answers wrong, random flips
            noisy = {q: v ^ bool(rng.random() < 0.2) for q, v in ideal.items()}
            out = confirm(noisy)
            d["noisy_ok"] += out["disease"] == truth
            d["noisy_n"] += 1
            d["noisy_ooc"] += out["severity"] == "Out of Class"
        if n % 20 == 0:
            print(f"  ...{n}/{len(photos)}", flush=True)

    tot = defaultdict(int)
    print(f"\n{'disease':26s} {'photos':>6s} {'photo top1':>10s} {'ideal answers':>14s} {'20% wrong answers':>18s}")
    for d_name in t.CLASSES:
        d = res[d_name]
        for k, v in d.items():
            tot[k] += v
        print(f"{d_name:26s} {d['n']:6d} {d['top1'] / max(d['n'], 1):10.0%} {d['ideal_ok'] / max(d['n'], 1):14.0%} "
              f"{d['noisy_ok'] / max(d['noisy_n'], 1):18.0%}")
    n = max(tot["n"], 1)
    print(f"{'ALL':26s} {tot['n']:6d} {tot['top1'] / n:10.1%} {tot['ideal_ok'] / n:14.1%} "
          f"{tot['noisy_ok'] / max(tot['noisy_n'], 1):18.1%}")
    print(f"\nrejected by the confidence cutoff: {tot['rejected']} | upload errors: {tot['upload_error']} | "
          f"'Out of Class' under noise: {tot['noisy_ooc']}/{tot['noisy_n']}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("mode", choices=("pipeline", "noise", "live"))
    ap.add_argument("--data", nargs="+", required=True, help="dataset roots, one sub-folder per class (same as train.py)")
    ap.add_argument("--seed", type=int, default=0, help="must match the seed used to train, to reproduce the split")
    ap.add_argument("--trials", type=int, default=100, help="noise mode: random trials per photo per setting")
    ap.add_argument("--url", default=PRODUCTION, help="live mode: backend base URL")
    args = ap.parse_args()
    {"pipeline": run_pipeline, "noise": run_noise, "live": run_live}[args.mode](args)


if __name__ == "__main__":
    main()

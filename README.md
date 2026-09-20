# SkinNet Analyzer

A full-stack web app that identifies one of **8 common skin conditions** from a photo, narrows the result down with a few symptom questions, and produces a report with care instructions and nearby hospitals.

> **Demonstration project only. Not for real medical use.** Nothing here is a diagnosis. See a doctor.

**Live site:** https://harithkavish.com/SkinNet-Analyzer/

Conditions covered: Cellulitis, Impetigo, Athlete-foot, Nail-fungus, Ringworm, Cutaneous-larva-migrans, Chickenpox, Shingles.

---

## Contents

1. [How it works](#how-it-works)
2. [Testing guide: symptom answers](#testing-guide-symptom-answers) (start here to test the app)
3. [The classifier: training and results](#the-classifier-training-and-results)
4. [Evaluation results](#evaluation-results)
5. [Architecture and deployment](#architecture-and-deployment)
6. [API](#api)
7. [Running locally](#running-locally)
8. [Configuration](#configuration)
9. [Project structure](#project-structure)
10. [Known limitations](#known-limitations)
11. [References and license](#references-and-license)

---

## How it works

```
 photo ──▶ ML service (3-CNN ensemble) ──▶ top-3 candidate diseases + confidences
                                                   │
             confidence < 0.30 ? ──▶ "could not identify, try a clearer photo"
                                                   │
                      symptom questions (only those relevant to the 3 candidates)
                                                   │
        photo confidence  +  the user's Yes/No answers  ──▶  confirmed disease + severity
                                                   │
      AI-written care text (NVIDIA NIM)  +  nearby hospitals (geocode + OpenStreetMap data)
                                                   │
                                        report on screen / PDF download
```

1. **Photo → candidates.** Three image networks (EfficientNet-B0, ResNet-18, MobileNetV2) each score the photo; the scores are averaged and the top 3 diseases are returned with their probabilities.
2. **Confidence cutoff.** If the best probability is below **0.30** the app asks for a clearer photo instead of guessing. This only catches *uncertain* predictions; it cannot catch a confident call on a disease outside the 8 classes.
3. **Symptom questions.** The user is asked Yes/No questions about the symptoms of the 3 candidates (each disease has 2-5 symptoms; see the [table below](#per-disease-answers-what-to-tick-for-each-disease)).
4. **Combining photo and answers.** Each candidate scores `log(photo probability) + agreement of the answers with that disease's symptom list`, assuming a given answer is right 70% of the time (`ANSWER_RELIABILITY = 0.7` in `backend/services/symptoms.py`). A Yes for a symptom the disease has, or a No for one it lacks, counts as agreement. Unanswered questions are ignored. The highest score wins, so a few wrong answers cannot overturn a confident photo, and correct answers can rescue a wrong top-1 photo guess.
5. **Severity** is a heuristic from the answers, not from the image: the share of the confirmed disease's listed symptoms answered Yes: at least 75% is Severe, above 50% is Moderate, 25% to 50% is Mild. Below 25% it is "Mild" if the photo was confident (probability ≥ 0.5) and **"Out of Class"** (no report) if the photo was unsure too.
6. **Report.** Care information comes from NVIDIA NIM (`mistralai/mistral-nemotron`) with a hard 35-second budget; if it is slow or down, built-in general information for each disease is shown instead (labelled as such), so the report always renders. Hospitals are found by geocoding the typed location (Open-Meteo) and searching OpenStreetMap-based services (Photon, then Nominatim, then Overpass mirrors), nearest first, cached for an hour per area.

---

## Testing guide: symptom answers

Use this to test the app or to reproduce the evaluation. The idea: for a photo of disease **X**, answer **Yes** to exactly X's symptoms and **No** to every other question that is asked.

There are **14 symptom questions** in total, but each photo only asks the union of its 3 candidates' symptoms, so you will see between 5 and 11 of them. If the true disease is among the candidates (it is ~98% of the time), all of its symptoms are always shown.

### Per-disease answers: what to tick for each disease

Answer **Yes** to the listed symptoms, **No** to everything else.

| Disease | Answer **Yes** to | # |
|---|---|---|
| **Cellulitis** | fever, pain, redness, swelling/inflammation, warm skin | 5 |
| **Impetigo** | blisters, burning/itching, crusting, sores | 4 |
| **Ringworm** | burning/itching, redness, skin texture changes, swelling/inflammation | 4 |
| **Athlete-foot** | blisters, burning/itching, skin texture changes | 3 |
| **Nail-fungus** | bad odor, nail changes | 2 |
| **Cutaneous-larva-migrans** | burning/itching, pain, thread/ring like pattern | 3 |
| **Chickenpox** | blisters, burning/itching, fatigue/tiredness, fever | 4 |
| **Shingles** | blisters, burning/itching, pain | 3 |

With these answers and a photo the model puts in its top 3, the app confirms that disease with severity **"Severe"** (100% of its symptoms matched). These lists live in `SYMPTOM_MAPPING` in `backend/services/symptoms.py`, which is the source of truth; if you change that file, update this table.

### Common (shared) symptoms

These symptoms appear in several diseases, so ticking them alone does not identify anything. This is why the questions are asked about the 3 candidates together.

| Symptom | # diseases | Diseases that have it |
|---|---|---|
| burning/itching | 6 | Impetigo, Ringworm, Athlete-foot, Cutaneous-larva-migrans, Chickenpox, Shingles |
| blisters | 4 | Impetigo, Athlete-foot, Chickenpox, Shingles |
| pain | 3 | Cellulitis, Cutaneous-larva-migrans, Shingles |
| fever | 2 | Cellulitis, Chickenpox |
| redness | 2 | Cellulitis, Ringworm |
| skin texture changes | 2 | Ringworm, Athlete-foot |
| swelling/inflammation | 2 | Cellulitis, Ringworm |

### Distinctive symptoms (unique to one disease)

The most useful answers for telling diseases apart.

| Symptom | Disease |
|---|---|
| warm skin | Cellulitis |
| crusting, sores | Impetigo |
| thread/ring like pattern | Cutaneous-larva-migrans |
| fatigue/tiredness | Chickenpox |
| bad odor, nail changes | Nail-fungus |

### Regression images

`SkinNet-Analyzer-Test-Images/` holds 18 hand-collected photos. Results on the live ML service (17 of 18 correct):

| File | Truth | Predicted (confidence) |
|---|---|---|
| Athlete-foot.jpeg | Athlete-foot | Athlete-foot (0.77) |
| cellulitis.jpg | Cellulitis | Cellulitis (0.83) |
| cp.jpeg | Chickenpox | Chickenpox (0.55) |
| cp.jpg | Chickenpox | Chickenpox (0.90) |
| cp2.jpg | Chickenpox | **Shingles (0.46), known miss** |
| cutaneous-larva-migrans.jpg | Cutaneous-larva-migrans | Cutaneous-larva-migrans (0.98) |
| i2.jpg | Impetigo | Impetigo (0.84) |
| impetigo.jpg | Impetigo | Impetigo (0.96) |
| nf.jpg | Nail-fungus | Nail-fungus (0.42) |
| nf2.jpg | Nail-fungus | Nail-fungus (0.35) |
| r1.jpg, r2.jpg, r3.jpg | Ringworm | Ringworm (0.95, 0.99, 0.96) |
| ringworm.jpg | Ringworm | Ringworm (0.95) |
| shingles.jpg | Shingles | Shingles (0.60) |
| x1.jpg, x2.jpg, x3.jpg | Cutaneous-larva-migrans | Cutaneous-larva-migrans (0.97, 0.96, 0.89) |

(`x1`-`x3` were unlabeled; all three are the classic winding larva-migrans track, checked by eye.)

---

## The classifier: training and results

### Data

- Source: [Skin Disease Dataset (Kaggle)](https://www.kaggle.com/datasets/subirbiswas19/skin-disease-dataset?resource=download), 8 class folders (`BA- cellulitis`, `BA-impetigo`, `FU-athlete-foot`, `FU-nail-fungus`, `FU-ringworm`, `PA-cutaneous-larva-migrans`, `VI-chickenpox`, `VI-shingles`). The dataset is not stored in this repo.
- **The dataset is heavily augmented.** Real photos were hard to collect, so it was expanded with flipped, rotated and resized copies. Of 1,159 files, 30 are exact byte-for-byte duplicates and about 71% have a near-identical twin (allowing for flips and rotations). There are only **539 distinct photos**:

| Class | Distinct photos |
|---|---|
| Nail-fungus | 159 |
| Cellulitis | 130 |
| Impetigo | 56 |
| Ringworm | 55 |
| Cutaneous-larva-migrans | 49 |
| Athlete-foot | 34 |
| Shingles | 33 |
| Chickenpox | 23 |

- **Consequence for evaluation:** the dataset's own train/test folders contain copies of the same photos, so accuracy measured on that split is inflated. `ml/train.py` therefore groups near-duplicates (16x16 average hash compared under all flips and rotations, distance ≤ 12 bits; no group contains two classes) and splits by group, so a photo and its copies always land on the same side. Split: 654 train / 239 validation / 236 test files (112 distinct test photos). Any accuracy figure computed on the dataset's original split should be treated as optimistic.

### Models

Three ImageNet-pretrained networks, each with its last layer replaced by an 8-way classifier (transfer learning), then fine-tuned:

| Network | Idea | Parameters |
|---|---|---|
| ResNet-18 | Skip connections (`output = layer(x) + x`) let deep networks train | 11M |
| EfficientNet-B0 | Architecture found by search, balanced depth/width/resolution | 5M |
| MobileNetV2 | Cheap depthwise convolutions, built for phones | 3.5M |

Their raw scores are averaged and passed through softmax (`ml/classify.py`). Weights are plain PyTorch `state_dict`s loaded with `weights_only=True`, verified under the pinned `torch 2.7.0` / `torchvision 0.22.0`.

### Training recipe (`ml/train.py`)

- Mini-batches (16 for EfficientNet, 32 otherwise) with GPU-side augmentation: random resized crop, rotation up to ±20°, horizontal and vertical flips, brightness/contrast jitter.
- Loss: cross-entropy with label smoothing 0.1 and **class weights** (photos per class are very uneven).
- Optimiser: AdamW. **3 warm-up epochs** train only the new head (backbone frozen), then everything is fine-tuned with learning rate 1e-4 for the backbone and 1e-3 for the head, cosine-decayed. 15 epochs total.
- The validation set is scored every epoch and the **best checkpoint is kept**; the test set is used once at the end.
- Full precision (fp32). Mixed precision produced NaNs and was slower on the GeForce MX450 used for training.

Retrain with:

```bash
cd ml
python train.py --data path/to/data/train path/to/data/test --out models --epochs 15 --no-refit
```

It writes `efficientnet.pth`, `resnet.pth`, `mobilenet.pth` and `metrics.json` (all numbers below come from that file plus the checks described under [Evaluation results](#evaluation-results)). About 50 minutes on the laptop GPU. `--no-refit` skips retraining on train+validation after choosing the epoch.

---

## Evaluation results

All accuracy figures below are on **distinct photos** (a photo and its copies count once). "Unseen" means the model never trained on the photo or any copy of it.

**Reproduce them** with `tools/evaluate.py`, which drives the app's real code (`ml/classify.py`, `backend/services/`) and the same dataset split as `train.py` (default `--seed 0`):

```bash
# run from the repository root
python tools/evaluate.py pipeline --data DATA/train DATA/test   # section 2: full pipeline, perfect answers, seen vs unseen
python tools/evaluate.py noise    --data DATA/train DATA/test   # section 3: wrong symptom answers (about 3 minutes)
pip install requests
python tools/evaluate.py live     --data DATA/train DATA/test   # section 4: the deployed website over HTTP (about 6 minutes)
```

`DATA` is the extracted Kaggle dataset (see [Data](#data)). Sections 2-4 are exactly the output of these commands; section 1 is `ml/models/metrics.json`, written by `train.py`.

### 1. Image model alone

| | EfficientNet-B0 | ResNet-18 | MobileNetV2 | **Ensemble (live)** |
|---|---|---|---|---|
| Test, 112 unseen photos, top-1 | 88.4% | 94.6% | 89.3% | **94.6%** |
| Test, ensemble top-3 | | | | **98.2%** |
| Validation, 239 files, top-1 | 86.2% | 91.6% | 88.3% | 92.9% (top-3 97.9%) |

The ensemble ties ResNet-18 alone on the test set (and is slightly ahead on validation). The test set is small: expect roughly ±4 points of uncertainty.

Ensemble recall per class on the 112 test photos:

| Cellulitis | Impetigo | Athlete-foot | Nail-fungus | Ringworm | Larva migrans | Chickenpox | Shingles |
|---|---|---|---|---|---|---|---|
| 27/28 | 11/11 | 6/6 | 32/32 | 10/10 | 11/12 | 4/4 | **5/9** |

**Shingles is the weak class** (33 distinct training photos; it is often confused with larva migrans, cellulitis and chickenpox). Chickenpox (23 photos) and Athlete-foot (34) are also thin: their perfect scores rest on 4 and 6 test photos.

### 2. Full pipeline with perfect answers

Every photo run through the real code (photo → top 3 → questions → answers from the [table above](#per-disease-answers-what-to-tick-for-each-disease) → confirmed disease):

| Disease | Seen photos (training) | Unseen photos | Unseen: photo only | Unseen: with questions |
|---|---|---|---|---|
| Cellulitis | 76, 100% | 54 | 96% | 100% |
| Impetigo | 30, 100% | 26 | 96% | 96% |
| Athlete-foot | 21, 100% | 13 | 100% | 100% |
| Nail-fungus | 94, 100% | 65 | 100% | 100% |
| Ringworm | 34, 100% | 21 | 95% | 100% |
| Larva migrans | 27, 100% | 22 | 95% | 100% |
| Chickenpox | 13, 100% | 10 | 100% | 100% |
| Shingles | 17, 100% | 16 | 56% | 81% |
| **All** | **312, 100%** | **227** | **94.7%** | **98.2%** |

- "Unseen" combines the validation and test photos. On the untouched test photos alone the pipeline scores **97.3%** (109 of 112).
- "Seen" is a sanity check only; the model trained on those photos.
- With perfect answers the questions can only re-rank the top 3, so the ceiling is the top-3 recall (98.7% on these 227 photos). The failures are three Shingles photos where Shingles was not among the candidates, plus one correct Impetigo photo dropped by the 0.30 confidence cutoff.

### 3. Robustness to wrong answers

Real users make mistakes, so answers were corrupted at random and each photo run 100 times per setting (227 unseen photos, the shipped scoring function). Re-running gives figures within a few tenths of a point (random draws). Figures are the share of photos where the **disease is chosen correctly**; the photo alone would give 94.7%.

| Answers wrong | Random flips | Forgetful (says No to symptoms they have) | Over-reporting (says Yes to symptoms they lack) |
|---|---|---|---|
| 0% | 98.2% | 98.2% | 98.2% |
| 10% | 97.9% | 98.2% | 98.1% |
| 20% | 96.8% | 98.0% | 97.9% |
| 30% | 93.9% | 97.8% | 97.7% |
| 50% (random answers) | 80.1% | 97.1% | 96.3% |

- The questions help while random errors stay below about 25-30%. Beyond that a wrong-answering user does worse than the photo alone; forgetting or over-reporting symptoms stays safe even at 50%.
- Users seeing a correct report (not blocked by "Out of Class") when they forget half their symptoms: 96.1%.
- The answer-reliability setting (0.7) was compared against 0.8 and 0.9 on the same photos and the lowest did best; it was chosen after seeing those results, so the gains are slightly optimistic. Errors were simulated as independent per question; real mistakes are correlated (users are systematically unsure about jargon like "thread/ring like pattern") and were not measured.
- **Why not just count Yes answers?** An earlier rule that only counted Yes matches and ignored the photo fell below the photo-alone accuracy at about 12% wrong answers (89.4% at 20% random errors, 77.3% at 30%), which is what this rule replaced.

### 4. Live production check

The 112 unseen test photos were sent to the deployed site over HTTP (upload, then answers via `/api/confirm_symptoms`):

| | Result |
|---|---|
| Photo alone, top-1 (1 photo dropped by the confidence cutoff) | 93.8% |
| With perfect answers | **97.3%** |
| With ~20% of answers wrong (333 trials) | **96.4%** (an earlier identical run gave 95.2%) |
| "Out of Class" dead ends under noise | 0 of 333 |
| Upload errors | 0 |

### 5. Model history

The classifier weights shipped before September 2026 were never trained (stock ImageNet networks with a random output layer, about 13% accuracy, i.e. chance) and the old training script could not have produced them. They were replaced by the retrained models described here.

---

## Architecture and deployment

| Part | Tech | Hosted on |
|---|---|---|
| Frontend | React (hash routing), static build | GitHub Pages (`gh-pages` branch), reached at `harithkavish.com/SkinNet-Analyzer/` |
| Backend | FastAPI, 2 uvicorn workers (image is ~22 pip packages) | Render (free tier) |
| ML service | FastAPI + PyTorch (pinned `torch 2.7.0`, `torchvision 0.22.0`) | Hugging Face Space (Docker) |
| AI care text | NVIDIA NIM, `mistralai/mistral-nemotron` | NVIDIA API |
| Hospitals | Open-Meteo geocoding; Photon, Nominatim, Overpass (OpenStreetMap data) | public services |

- **CI/CD** (`.github/workflows/docker-build-push.yml`): every push to `main` detects which of `backend/`, `ml/`, `frontend/` changed, builds and pushes Docker images to Docker Hub, redeploys Render (deploy hook + env vars), restarts the Hugging Face Space, and publishes the frontend build to the `gh-pages` branch. The backend deploys in about a minute.
- **Keep-alive** (`keep-servers-alive.yml`): a scheduled workflow pings both services. GitHub's scheduler runs it far less often than its 12-minute setting, so Render's free tier still sleeps after ~15 idle minutes; the frontend therefore shows "Waking up the server..." and retries for up to ~2 minutes before saying offline.
- **Why two backend workers:** Render's health check (5 s timeout) restarts a container that stops answering. A second worker keeps `/api/status` responsive during slow outbound calls. Because of this, no request state is kept in server memory: `/api/upload` returns the candidate diseases and their probabilities, and the browser sends them back with the answers.
- **CORS** (`backend/main.py`) allows `harithkavish.com`, `www.harithkavish.com`, `harithkavish.github.io` and `localhost:3000`.
- **Resilience:** the NVIDIA call has a 35 s total budget and a 2-minute circuit breaker (after a failure the built-in fallback text is used immediately); hospital lookup tries four providers in turn; a failed report request shows a message with a **Retry** button.

---

## API

### Backend (`/api`)

| Method & path | Request | Response |
|---|---|---|
| `GET /api/status` | | `{status, deployed_at, checked_at}` |
| `POST /api/upload` | multipart `file` (JPEG/PNG) | `{questions, diseases, probabilities}`, or `{message}` if the photo was too uncertain |
| `POST /api/confirm_symptoms` | `{answers: {symptom: "1"\|"0"}, diseases: [...], probabilities?: [...]}` | `{disease, severity, message}` |
| `POST /api/get_disease_info` | `{disease, severity, location}` | `{disease, severity, location, symptoms_care, hospitals: [{name, location, maps_url}]}`, or `{out_of_class: true}` |

`probabilities` is optional so older cached copies of the web page keep working (candidates then start equal and only the answers decide).

### ML service

| Method & path | Request | Response |
|---|---|---|
| `GET /` | | health check |
| `POST /` | multipart `file` (**JPEG or PNG only**) | `{predictions: [[disease, probability] x 3]}` |

---

## Running locally

Prerequisites: Python 3.12, Node.js and npm.

**ML service**

```bash
cd ml
pip install -r requirements.txt
uvicorn app:app --host 0.0.0.0 --port 7860
```

**Backend**

```bash
cd backend
pip install -r requirements.txt
mkdir logs                       # the route modules open logs/app.log when imported
export NVIDIA_API_KEY=...        # optional: without it the report uses the built-in text
export ML_API_URL=http://localhost:7860/
uvicorn main:app --port 8000
```

**Frontend**

```bash
cd frontend
echo "REACT_APP_BACKEND_API_URL=http://localhost:8000" > .env
npm install
npm start                        # http://localhost:3000
```

---

## Configuration

| Where | Name | Purpose |
|---|---|---|
| Backend env | `ML_API_URL` | URL of the ML service's `POST /` endpoint |
| Backend env | `NVIDIA_API_KEY` | NVIDIA NIM key for the care text (optional; fallback text is used without it) |
| Frontend build | `REACT_APP_BACKEND_API_URL` | Backend base URL, baked in at build time |
| GitHub Actions secrets | `DOCKER_USERNAME`, `DOCKER_PASSWORD`, `RENDER_API_KEY`, `RENDER_SERVICE_ID`, `RENDER_DEPLOY_HOOK_URL`, `NVIDIA_API_KEY`, `ML_API_URL`, `FRONTEND_BACKEND_API_URL`, `HF_TOKEN`, `DISCORD_WEBHOOK_*` | CI/CD and keep-alive alerts |

Never commit keys. The workflow copies the secrets into Render's environment on each deploy.

---

## Project structure

```
.github/workflows/         CI/CD (docker-build-push.yml), keep-alive, PR review
backend/
  main.py                  app, CORS, router registration
  routes/                  status_routes.py, diagnosis_routes.py, info_routes.py
  services/                symptoms.py (questions + scoring), out_of_class.py, fallback_info.py
  apis/                    nim_api.py, city_coordinates_api.py, nearby_hospitals_api.py
  Dockerfile, requirements.txt
frontend/src/components/   Upload.js (the whole diagnosis flow), Home.js, Navbar.js, ...
ml/
  app.py                   FastAPI wrapper (POST / -> top-3)
  classify.py              loads the 3 networks, ensemble prediction
  train.py                 dataset grouping, training, honest evaluation
  models/                  efficientnet.pth, resnet.pth, mobilenet.pth, class_indices.pkl,
                           metrics.json, severity_model.pth (untrained, unused)
tools/evaluate.py          reproduces the README results (pipeline / noise / live modes)
SkinNet-Analyzer-Test-Images/   18 regression photos (see the testing guide)
```

---

## Known limitations

- **Small real dataset:** 539 distinct photos, only 23-34 for Chickenpox, Shingles and Athlete-foot. Test-set results carry roughly ±4 points of uncertainty and the per-class numbers on 4-9 photos are indicative only. More original photos, especially for those classes, would help more than more tuning.
- **Shingles** is the weakest class (56% top-1, 78-81% with questions).
- **Photos unlike the training set** (different lighting, skin tones, other conditions) can produce confident wrong answers. The 0.30 cutoff cannot detect diseases outside the 8 classes.
- **Severity is a heuristic** from symptom answers, not measured from the image. `ml/models/severity_model.pth` is untrained and unused.
- **Image formats:** the ML service accepts only JPEG and PNG; other formats (for example `.webp`) fail with an error.
- **Care text** depends on NVIDIA NIM availability (its model catalogue is account-specific and it has had multi-day outages); the built-in fallback covers this but is generic.
- **Hospital search** uses free public services that can rate-limit shared cloud IPs; results are nearest-first but not verified opening hours or specialties.
- **Cold starts:** Render's free tier sleeps when idle; the first visit after a quiet period can take up to a minute.
- **Evaluation caveats:** noise experiments simulate independent answer errors; the 0.7 answer-reliability value was picked after seeing results; the live check is 112 photos and its wrong-answer figure (333 trials) varies by about a point between runs (95.2% and 96.4% in two runs; the server orders the questions differently after each restart, so the same random flips hit different questions).

---

## References and license

- [IJIRT Journal Paper](https://ijirt.org/Article?manuscript=174480)
- Dataset: [Skin Disease Dataset (Kaggle)](https://www.kaggle.com/datasets/subirbiswas19/skin-disease-dataset?resource=download)
- Video Preview:
  <video src="https://github.com/user-attachments/assets/c673a823-58a9-444b-bcb8-493a14a104c1" controls width="600">
    Your browser does not support the video tag.
  </video>

For demonstration and educational purposes only. Not for real medical use.

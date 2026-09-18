# Algorithm Architecture — How to Design the Model

## The core structure

The algorithm has three jobs:
1. **Score** a shot (regression: input features → quality score)
2. **Explain** the score (which features drove it up or down)
3. **Recommend** an adjustment (what should the barista change next)

These need different approaches. Don't try to solve all three with one model.

---

## Stage 1: Feature Engineering (before any ML)

Raw sensor data must be processed into features. This is where domain knowledge earns its keep.

**From pressure time series:**
- `time_to_9bar` — how fast pressure ramps up
- `peak_pressure` — max recorded pressure
- `pressure_stability` — standard deviation during extraction plateau
- `pressure_drop_rate` — how fast it falls at end
- `pre_infusion_duration` — time at low pressure before full ramp

**From flow rate time series:**
- `mean_flow_rate` — average grams/second
- `flow_rate_cv` — coefficient of variation (consistency measure)
- `blonding_onset_second` — extracted from camera color analysis
- `channeling_score` — 0–1 from camera tiger-striping detection

**From camera (crema):**
- `crema_hue_mean` — golden vs. pale vs. dark (HSV color space)
- `crema_thickness_px` — measured in pixels, calibrated to mm
- `crema_persistence_seconds` — time until crema dissipates 50%

**Why this matters:** Raw time series (150+ data points per shot) fed directly into a model will overfit with small datasets. Engineered features (~20–25 values) are tractable with 200–500 labeled shots.

---

## Stage 2: Scoring Model Options

### Option A: Weighted linear scoring (start here)

```
score = w1*extraction_time_dev + w2*brew_ratio_dev + w3*pressure_stability + ...
```

- Weights are hand-tuned by a coffee expert or set empirically
- Completely transparent — barista can understand why
- No data needed to start (good for cold start)
- Limitation: misses non-linear interactions

**Use as the baseline.** Ship this on day one.

### Option B: Gradient Boosted Trees (GBDT) — e.g. XGBoost, LightGBM

After 300–500 labeled shots:
- Trains on `{feature_vector, barista_rating}` pairs
- Handles non-linear interactions automatically
- Feature importance is built in — directly usable for "what to change" recommendations
- Robust to missing features (sensor failures)
- Interpretable via SHAP values

**This is the recommended production model.** It's the right tool for:
- Small-to-medium dataset (100–10,000 shots)
- Tabular features (not raw time series)
- Need for explainability

### Option C: Neural network (later stage)

If you want to process raw time series directly (pressure curve + flow curve as inputs):
- 1D CNN or LSTM on the raw curves
- Potentially more accurate
- Requires more data (2,000+ labeled shots)
- Harder to explain

**Only consider this after the GBDT is working well.** The accuracy gain is usually marginal for this problem scale.

---

## Stage 3: Recommendation Engine

Given a shot score and feature importances, produce: *"change X to improve your next shot."*

Two approaches:

**A: Feature importance + deviation direction**
```
if (extraction_time < target_low) and (feature_importance[grind_size] is high):
    recommend("Grind finer by 1 step")
```
Rules-based. Transparent. Works immediately. Build a lookup table of 15–20 common conditions and recommendations.

**B: Counterfactual explanation**
For each shot, ask: "what is the nearest input vector that would score ≥85?"
The difference = the recommendation.
Requires a trained model. More precise but harder to implement.

**Start with A. Add B later.**

---

## Full pipeline (per shot)

```
Raw sensor data
    ↓
Feature engineering (deterministic transforms)
    ↓
Recipe deviation score (deterministic, no ML)
    ↓
Quality prediction score (GBDT model)
    ↓
SHAP explanation: which features drove the score
    ↓
Recommendation engine: "change X"
    ↓
Display to barista
    ↓
Barista rates the shot (optional but valuable)
    ↓
Labeled data point added to training set
    ↓
Periodic model retraining
```

---

## Technology choices for Raspberry Pi

Given the hardware constraint (Raspberry Pi, edge compute):

| Component | Recommended tool |
|-----------|-----------------|
| Feature engineering | Python + NumPy |
| Baseline scoring | Python (simple weighted formula) |
| GBDT model | LightGBM (lightest GBDT, runs well on Pi) |
| SHAP explanations | `shap` library (Python) |
| Camera analysis | OpenCV (Python) |
| Data storage | SQLite (local) + periodic sync to cloud |
| Model retraining | Cloud (not on Pi) — sync new model weights to Pi |

**Key architecture point:** Run inference on the Pi (fast, offline). Run training in the cloud (computationally heavy). Ship new model weights to the Pi weekly or when data crosses a threshold.

---

## Model versioning and A/B testing

Each business location should eventually have a *personalized* model — trained on their beans, their water, their baristas' preferences. But start with a shared global model for the first 6 months. Personalization comes after enough per-business data accumulates.

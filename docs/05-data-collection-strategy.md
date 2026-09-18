# Data Collection Strategy

## How much data do you actually need?

A common mistake: waiting for thousands of data points before doing anything useful.

Reality:
- Weighted linear baseline: **0 labeled shots** (works immediately)
- Basic GBDT model: **200–500 labeled shots**
- Reliable GBDT with validation: **500–1,000 labeled shots**
- Personalized per-business model: **2,000+ shots per location**

At 50 labeled shots/day (reasonable for a busy café), you reach 500 shots in 10 days. The model can be meaningfully useful very fast.

---

## What a data record looks like

Every shot produces one row in the training dataset:

```json
{
  "shot_id": "2026-09-11T09:23:14-outlet01-bar03",
  "timestamp": "2026-09-11T09:23:14",
  "outlet_id": "outlet-01",
  "barista_id": "barista-07",
  "bean_batch_id": "batch-2026-09-01",

  // Phase 1: prep
  "dose_weight_g": 18.3,
  "tamp_pressure_kg": 19.8,
  "distribution_score": 0.81,
  "time_grind_to_pull_s": 23,

  // Phase 2: extraction features
  "time_to_9bar_s": 4.2,
  "peak_pressure_bar": 9.4,
  "pressure_stability": 0.18,
  "extraction_time_s": 26,
  "blonding_onset_s": 21,
  "channeling_detected": false,
  "channeling_score": 0.07,
  "brew_ratio": 2.4,
  "yield_weight_g": 43.9,
  "water_temp_c": 93.2,

  // Phase 3: post-extraction
  "crema_hue_mean": 42.1,
  "crema_thickness_mm": 3.8,
  "crema_persistence_s": 90,

  // Labels
  "barista_rating": 7,
  "barista_id_rater": "barista-07",
  "customer_feedback": null,
  "tds_pct": 1.31
}
```

Every field is a column. Every shot is a row. This goes into SQLite locally, synced to cloud.

---

## The annotation workflow (keeping it zero-friction)

Baristas will not rate shots if it takes more than 3 seconds. Design the rating interface accordingly.

**Ideal flow:**
1. Shot finishes → device shows "Rate this shot"
2. Barista taps 1–5 (one tap, no typing)
3. Optional: one tap to flag "channeling" or "grind issue" (categorical)
4. Done

**Do not ask:** "Please describe the flavor profile in 3 sentences." You will get no data.

**Do ask:** "Was this shot above or below your usual standard?" → This binary label, aggregated over thousands of shots, is extremely powerful.

---

## Controlling for confounders

The algorithm needs to learn what *the barista controls* affects quality, not confounders like:
- Bean age (older beans extract differently)
- Grinder temperature (grinders heat up over a shift, affecting grind size)
- Ambient humidity (affects grind and extraction)
- Time of day (machine not fully warmed up in the morning)

**Strategy:** Log everything, even if not in the initial model. Record timestamp, grinder temperature (if available), bean roast date, ambient temperature/humidity (cheap sensors). These become features if the model underperforms.

**Bean batch ID is critical.** A model trained on one batch of beans will give wrong recommendations when a new batch arrives. Either:
- Include batch as a categorical feature (requires enough data per batch)
- Retrain when batch changes (preferred if each batch lasts 2+ weeks)

---

## Train / validation / test split

Never evaluate the model on data it was trained on. Split:
- **70% train** — model learns from this
- **15% validation** — used during training to prevent overfitting
- **15% test** — held out, never touched until final evaluation

**Important:** Split by *time*, not randomly. A random split lets the model "see the future" — shots from Wednesday in training, Monday in test. Real deployment is always predicting forward in time. Use the last 15% chronologically as test set.

---

## Monitoring for data drift

Bean batches change. Grinders wear. Baristas get replaced. The model's input distribution will shift over time.

Simple monitoring:
- Track the mean and variance of each feature weekly
- Alert if any feature drifts more than 2 standard deviations from its training distribution
- Trigger retraining when drift is detected or when 500 new labeled shots accumulate

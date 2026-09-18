# Espresso Quality Algorithm — Full Brief

*A consulting brief for a robotic espresso quality measurement startup.*
*Focus: algorithm design, scoring, and feedback loop. Not coffee science, not hardware.*

---

## 1. Project Framing

### The core problem

A barista pulls 50–200 shots a day. Each shot has a slightly different outcome. They have no reliable signal for *why* one shot is better than another. They adjust by intuition and memory, which doesn't scale across a team or a multi-outlet business.

The founder's insight: **if we instrument the process, we can give the barista a signal they can act on.** The hardware exists. The question is: what algorithm turns sensor data into a useful score?

### What this project is about

- How to design an algorithm that scores espresso quality from sensor inputs
- How that score gets generated, validated, and improved over time
- How the score becomes a feedback signal baristas can actually use

### The fundamental algorithm question

> Given a vector of sensor readings from a single espresso pull, produce a score (or set of scores) that correlates with human-judged quality — and tell the barista which input to change next.

This is a **supervised regression problem** with a feedback loop. It requires:
1. Defining the inputs (sensor parameters)
2. Defining the output (score design)
3. Defining the ground truth (how do we label "good"?)
4. Choosing the model architecture
5. Designing the feedback loop that improves the model over time

### Why this is hard (the honest version)

1. **Ground truth is subjective.** One barista's 8/10 is another's 6/10. The model needs to reconcile this.
2. **Coffee changes.** Same parameters + different bean origin/roast date → different outcome. The algorithm must account for product-level variance.
3. **Sensors are noisy.** Pressure spikes, camera occlusion, inconsistent tamping surfaces — noise in inputs propagates to noise in scores.
4. **Cold start.** The model has no data at deployment. It needs a strategy for the first 500 shots.

### One-sentence version of the approach

Collect labeled shot data (sensor readings + barista rating) → train a scoring model → use the model's feature importances to tell the barista *which lever to pull* → collect more labeled data as they adjust → retrain.

---

## 2. Input Parameters — What the Sensors Measure

Every espresso pull has three distinct phases, each with its own set of measurable parameters. The algorithm needs inputs from all three.

### Phase 1: Pre-extraction (Prep)

These happen *before* water touches coffee. They are the highest-leverage variables — a bad prep cannot be rescued by a perfect extraction.

| Parameter | Sensor | Why it matters |
|-----------|--------|----------------|
| Grind size | Camera + particle analysis or laser diffraction | Controls surface area → extraction rate |
| Dose weight | Load cell (scale) | Controls brew ratio — too little = weak, too much = choking |
| Tamp pressure | Pressure sensor under portafilter | Uneven tamp creates channels → inconsistent extraction |
| Distribution evenness | Top-down camera of puck surface | Lumps/divots → channeling |
| Time from grind to tamp | Timer | Stale grounds degas, affecting flow |
| Time from tamp to extraction | Timer | Extended wait = moisture absorption → resistance change |

**Algorithm note:** Phase 1 parameters are the *inputs the barista controls*. They are the levers. The score feedback should map back to these most directly.

### Phase 2: During Extraction (The Pull)

These are *time series*, not single values. A pressure reading at second 5 is different from pressure at second 20. The algorithm must treat these as curves, not scalars.

| Parameter | Sensor | Why it matters |
|-----------|--------|----------------|
| Pressure profile (full curve) | Pressure sensor | Ideal: 9 bar for most of extraction; early spike or drop = problem |
| Flow rate profile (full curve) | Flow meter or camera of stream | Controls TDS; too fast = under-extracted, too slow = over-extracted |
| Extraction time (total) | Timer | Target: 25–35 seconds for most recipes |
| First drop time | Camera (visual detection) | Measures pre-infusion effectiveness |
| Blonding onset time | Camera (color change in stream) | Golden → blond = extraction complete; continuing past this dilutes |
| Channeling events | Camera of stream/puck | Tiger striping pattern = uneven flow paths → inconsistent cup |
| Pre-infusion duration | Pressure sensor | Low-pressure saturation before full pressure; reduces channeling |
| Water temperature | Thermocouple | Light roasts need higher temp; dark roasts lower |
| Yield weight (ongoing) | Scale below cup | Allows calculation of brew ratio in real time |

**Key insight from the research:** The *shape* of the extraction curve matters more than any single value. A pressure that ramps up smoothly is different from one that spikes then drops, even if the average is identical.

**Algorithm implication:** You need to extract **features from the time series** — not just use raw curves. Examples:
- Time to reach 9 bar
- Duration at peak pressure
- Rate of pressure decline
- Area under the flow curve
- Slope of blonding onset

### Phase 3: Post-Extraction (The Brew)

| Parameter | Sensor | Why it matters |
|-----------|--------|----------------|
| Crema color | Camera (RGB/HSV analysis) | Golden-brown = ideal; pale = under-extracted, dark = over |
| Crema thickness | Camera | Richer crema = fresher beans + good extraction |
| Crema persistence | Camera (time series) | Fast dissipation = older beans or channeling |
| Cup color / tone | Camera | Visual proxy for strength |
| Final yield weight | Scale | Confirms brew ratio |
| TDS (if sensor available) | Refractometer / TDS sensor | Most direct measure of extraction yield |
| Shot volume | Camera or volumetric | Cross-check with weight |

### The full input vector (simplified)

When you flatten everything into features for the algorithm:

```
[dose_weight, grind_size_proxy, tamp_pressure, distribution_score,
 time_grind_to_pull, pre_infusion_duration,
 time_to_first_drop, time_to_peak_pressure, peak_pressure,
 pressure_stability_score, flow_rate_mean, flow_rate_variance,
 blonding_onset_time, channeling_detected (bool), total_extraction_time,
 yield_weight, brew_ratio, water_temp,
 crema_color_score, crema_thickness, crema_persistence,
 tds (optional)]
```

**~20–25 features** per shot. This is tractable for classical ML. A neural net would handle the raw time series.

### Parameters you can control vs. parameters you observe

| Controllable (levers) | Observable (outcomes) |
|----------------------|----------------------|
| Grind size | Pressure curve shape |
| Dose | Blonding time |
| Tamp pressure | Crema quality |
| Distribution | Extraction time |
| Water temp | TDS |
| Pre-infusion time | Channeling events |

The algorithm's job: learn the mapping from **levers → outcomes** and use it to recommend lever adjustments.

---

## 3. Output Design — What Score Do We Produce?

### The central design decision

**Single composite score** (e.g. 0–100) vs **multi-dimensional scores** (e.g. Extraction / Consistency / Appearance)?

Both are valid. The right answer depends on what the barista does with the output.

### Option A: Single composite score

**Example:** Shot #47 → 76/100

**Pros:** Simple to understand; easy to track over time; one number to optimize.

**Cons:** Hides *what* went wrong — a 76 from bad crema looks identical to a 76 from channeling. Hard to act on without knowing which dimension pulled the score down.

**When to use:** Business-level reporting (owner dashboard, shift summaries), not barista feedback in the moment.

### Option B: Multi-dimensional scores

**Example:**
```
Extraction quality:  82/100  ← was it properly extracted?
Process consistency: 71/100  ← did parameters match the target recipe?
Appearance:          89/100  ← crema, color, visual quality
Overall:             80/100  ← weighted composite
```

**Pros:** Barista can see *where* the problem is. Maps to actionable feedback. Easier to build trust — the barista can verify "yes, the crema looked off."

**Cons:** More complex to model. Dimensions may correlate.

**Recommended for barista-facing UI.**

### Option C: Deviation from target recipe

Rather than scoring against an abstract ideal, score each parameter against *that business's target recipe*.

**Example:**
```
Target brew ratio: 1:2.5 (18g dose → 45g yield)
Actual brew ratio: 1:2.1 → score deduction: -8 points

Target extraction time: 28s
Actual: 23s → score deduction: -11 points

Target pressure: 9 bar ± 0.5
Actual: peaked at 10.8 bar → score deduction: -6 points
```

**Why this is powerful:** No need to define universal "good espresso" — every business defines their own target. Feedback is immediately actionable: "your extraction was 5 seconds short — grind finer."

**Limitation:** Still needs a ground truth model to learn *which deviations matter most*.

### Recommended architecture: Hybrid

```
Layer 1: Recipe deviation scores (objective, deterministic)
         → calculated directly from sensor readings vs. target recipe

Layer 2: Quality prediction score (learned, probabilistic)
         → ML model predicts barista rating from sensor features

Layer 3: Composite display
         → show both: "Your recipe score: 78 | Predicted quality: 74"
```

The recipe deviation score is transparent and always explainable. The quality prediction score captures the non-linear interactions the deviation score misses.

### What the barista interface should show

**Primary:** Current shot score + direction vs. last shot (up/down/same)

**Secondary:** Which dimension drove the change ("Extraction -8 vs. last shot")

**On demand:** "What to change next" — ranked list of highest-impact adjustments
```
1. Grind finer by ~1 step (extraction time was 22s, target 28s)
2. Distribute more evenly (channeling detected on left side)
3. Temperature within range ✓
```

**Over a shift:** Trend chart — are scores improving, degrading, or flat?

### What the owner/manager interface should show

- Average score by barista per shift
- Score variance (consistency matters as much as average)
- Which parameters drift most across the day
- Alert: shift average dropped >5 points → investigate

---

## 4. Algorithm Architecture — How to Design the Model

### The core structure

The algorithm has three jobs:
1. **Score** a shot (regression: input features → quality score)
2. **Explain** the score (which features drove it up or down)
3. **Recommend** an adjustment (what should the barista change next)

These need different approaches. Don't try to solve all three with one model.

### Stage 1: Feature Engineering (before any ML)

Raw sensor data must be processed into features first.

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

### Stage 2: Scoring Model Options

**Option A: Weighted linear scoring — start here**
```
score = w1*extraction_time_dev + w2*brew_ratio_dev + w3*pressure_stability + ...
```
Weights are hand-tuned. Completely transparent. No data needed to start. Limitation: misses non-linear interactions. **Ship this on day one.**

**Option B: Gradient Boosted Trees (GBDT) — the production model**

After 300–500 labeled shots:
- Trains on `{feature_vector, barista_rating}` pairs
- Handles non-linear interactions automatically
- Feature importance is built in — directly usable for "what to change" recommendations
- Robust to missing features (sensor failures)
- Interpretable via SHAP values

Recommended tools: XGBoost or LightGBM. **This is the right tool for small-to-medium tabular datasets that need explainability.**

**Option C: Neural network — later stage only**

If processing raw time series directly (pressure curve + flow curve as inputs): 1D CNN or LSTM. Requires 2,000+ labeled shots. Harder to explain. The accuracy gain is usually marginal for this problem scale.

### Stage 3: Recommendation Engine

**A: Feature importance + deviation direction (start here)**
```
if (extraction_time < target_low) and (feature_importance[grind_size] is high):
    recommend("Grind finer by 1 step")
```
Rules-based. Transparent. Works immediately. Build a lookup table of 15–20 common conditions.

**B: Counterfactual explanation (later)**
For each shot, ask: "what is the nearest input vector that would score ≥85?" The difference = the recommendation. More precise but harder to implement.

### Full pipeline (per shot)

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

### Technology stack for Raspberry Pi

| Component | Recommended tool |
|-----------|-----------------|
| Feature engineering | Python + NumPy |
| Baseline scoring | Python (simple weighted formula) |
| GBDT model | LightGBM (lightest GBDT, runs well on Pi) |
| SHAP explanations | `shap` library (Python) |
| Camera analysis | OpenCV (Python) |
| Data storage | SQLite (local) + periodic sync to cloud |
| Model retraining | Cloud — sync new weights to Pi weekly |

**Key architecture point:** Run inference on the Pi (fast, offline). Run training in the cloud. Ship new model weights to the Pi on a schedule.

---

## 5. The Ground Truth Problem — How Do We Know What "Good" Is?

This is the single most important design decision in the project. A beautiful model trained on bad labels is useless.

### The labeling options

**Option 1: Barista rating (most practical)**

After each shot, the barista rates it: 1–5 stars or 1–10 score.

*Pros:* Immediate, zero friction, captures expert judgment.

*Cons:* One barista's 7 is another's 9. Ratings drift with mood and fatigue. Confirmation bias — if the sensors look bad, the barista rates lower before tasting.

*Mitigation:* Blind-ish labeling. Don't show the sensor scores to the barista before they rate. Show the score only after they submit.

**Option 2: Customer feedback (secondary signal)**

If a customer returns a shot, that's a strong negative. NPS surveys tied to specific shots via receipt timestamp.

*Limitation:* Sparse, lagged, confounded. Use to validate, not as primary labels.

**Option 3: Q-grader tasting (expensive, gold-standard)**

A certified Q-grader evaluates samples using the SCAA protocol (~$100–300/hour). Doesn't scale. **Use for a single calibration session** (50 shots rated by Q-grader + baristas simultaneously). This anchors the barista rating scale.

**Option 4: TDS measurement as proxy**

SCA defines ideal extraction yield as 18–22% and ideal TDS as 1.2–1.45%. Fully objective. Limitation: TDS in the ideal range doesn't guarantee the shot tastes good. **Use as one input feature, not as sole ground truth.**

### The inter-rater reliability problem

If two baristas rate the same shot differently, the model gets contradictory training signals.

**Solution: Weekly calibration sessions.** Pull 5 shots and have every barista rate them. Calculate inter-rater agreement (Cohen's kappa). If below 0.6, run a calibration discussion with concrete examples. This is how clinical research handles inter-rater reliability.

### What to do when labels are noisy

- **Collect 3+ ratings per shot** when possible
- **Use the median**, not the mean — resistant to outliers
- **Weight labels by rater reliability** — a consistent barista's ratings count more
- **Flag diverged ratings** (one rated 8, another rated 3) — informative edge cases for human review

### Cold start label strategy

**Week 1–2:** Controlled test environment. Two experienced baristas taste and rate every shot. Target: 100–200 labeled examples. Use to calibrate the hand-tuned baseline model.

**Week 3–4:** Deploy at one location. Baristas rate in real workflow. Target: 10 labeled shots/day minimum.

**Month 2:** Train GBDT on accumulated labels. Validate against held-out shots.

**Month 3+:** Model is live. Barista ratings are the ongoing label source. Model retrains monthly.

---

## 6. Data Collection Strategy

### How much data do you actually need?

| Model stage | Labeled shots needed |
|-------------|---------------------|
| Weighted linear baseline | 0 — works immediately |
| Basic GBDT model | 200–500 |
| Reliable GBDT with validation | 500–1,000 |
| Personalized per-business model | 2,000+ per location |

At 50 labeled shots/day (reasonable for a busy café), you reach 500 shots in 10 days.

### What a data record looks like

Every shot is one row in the training dataset:

```json
{
  "shot_id": "2026-09-11T09:23:14-outlet01-bar03",
  "timestamp": "2026-09-11T09:23:14",
  "outlet_id": "outlet-01",
  "barista_id": "barista-07",
  "bean_batch_id": "batch-2026-09-01",
  "dose_weight_g": 18.3,
  "tamp_pressure_kg": 19.8,
  "distribution_score": 0.81,
  "time_grind_to_pull_s": 23,
  "time_to_9bar_s": 4.2,
  "peak_pressure_bar": 9.4,
  "pressure_stability": 0.18,
  "extraction_time_s": 26,
  "blonding_onset_s": 21,
  "channeling_detected": false,
  "brew_ratio": 2.4,
  "yield_weight_g": 43.9,
  "water_temp_c": 93.2,
  "crema_hue_mean": 42.1,
  "crema_thickness_mm": 3.8,
  "crema_persistence_s": 90,
  "barista_rating": 7,
  "tds_pct": 1.31
}
```

### The annotation workflow (keeping it zero-friction)

Baristas will not rate shots if it takes more than 3 seconds.

**Ideal flow:**
1. Shot finishes → device shows "Rate this shot"
2. Barista taps 1–5 (one tap, no typing)
3. Optional: one tap to flag "channeling" or "grind issue"
4. Done

Do not ask: "describe the flavor profile." You will get no data.

Do ask: "Was this shot above or below your usual standard?" This binary label, aggregated over thousands of shots, is extremely powerful.

### Controlling for confounders

Log everything, even if not in the initial model: timestamp, grinder temperature, bean roast date, ambient temperature/humidity. These become features if the model underperforms.

**Bean batch ID is critical.** A model trained on one batch will give wrong recommendations when a new batch arrives. Either include batch as a categorical feature, or retrain when batch changes.

### Train / validation / test split

- 70% train, 15% validation, 15% test
- **Split by time, not randomly.** A random split lets the model "see the future." Real deployment always predicts forward in time.

### Monitoring for data drift

Track the mean and variance of each feature weekly. Alert if any feature drifts more than 2 standard deviations from its training distribution. Trigger retraining when drift is detected or when 500 new labeled shots accumulate.

---

## 7. The Feedback Loop — How the Model Gets Smarter

### Why the feedback loop is the product

The hardware is a commodity. The algorithm is defensible. But the *feedback loop* — the data flywheel — is the actual moat.

More shots → more labels → better model → more useful recommendations → baristas trust it more → more shots get rated → more data. Design this explicitly from day one.

### The loop, step by step

```
1. Shot pulled
       ↓
2. Sensor readings captured + features computed
       ↓
3. Current model scores the shot
       ↓
4. Score + recommendation shown to barista
       ↓
5. Barista adjusts and pulls next shot
       ↓
6. Barista rates the shot they just pulled
       ↓
7. Rating stored with feature vector
       ↓
8. [Weekly/threshold trigger] Retrain model on accumulated data
       ↓
9. New model weights deployed to Pi
       ↓
    Back to step 3 (with smarter model)
```

### Exploration vs. exploitation

- **Mostly exploit** (90%+ of shots): give the barista the best known recommendation. Don't experiment on paying customers.
- **Occasional explore** (controlled conditions): during off-peak hours or internal test sessions, run protocol variations.
- **Capture natural exploration:** baristas naturally deviate. When they do, log it with their rating. Natural deviation is free exploration data.

### What the model learns over time

**Short term (first 500 shots):** Which parameters are most predictive of barista rating at this specific location.

**Medium term (500–5,000 shots):** Non-linear interactions. E.g., "a 27-second extraction at 93°C with this bean is fine, but at 91°C it needs 30 seconds."

**Long term (5,000+ shots):** Seasonality, barista-specific drift patterns, equipment aging effects.

### Multi-location learning

Train a *global base model* on all locations' data, then *fine-tune* a per-location model on local data. This is transfer learning applied to espresso. New locations start with a useful model immediately (global), then personalize over 4–6 weeks.

### Preventing overfitting to one barista's preferences

If one barista provides 80% of labels, the model learns their preferences, not universal quality.

- Weight labels by barista when training
- Run cross-validation by barista: train on A, B, C; validate on D
- Periodically re-anchor with Q-grader calibration

### The retraining trigger

Recommended: **data-based** — every 500 new labeled shots or every 2 weeks, whichever comes first. Transition to drift-based monitoring in year 2.

---

## 8. Open Questions — Decisions the Founder Needs to Make

These are unresolved design choices. Each one has a recommended default, but the founder should explicitly decide before building.

### Algorithm design

**Q1: Single score or multi-dimensional?**
Recommended: Multi-dimensional (Extraction / Consistency / Appearance) with composite for owner reporting. Decision needed: specialty café vs. chain?

**Q2: What is the scoring range?**
Recommended: 0–10. Maps to professional coffee/wine evaluation. Easier to display on a small screen.

**Q3: How transparent should the algorithm be to the barista?**
- Option A: Score only
- Option B: Score + top 3 contributing factors *(recommended)*
- Option C: Full feature breakdown

**Q4: Should the algorithm recommend a specific adjustment?**
Recommended: Yes. "Grind 1 step finer" is actionable. "Your extraction was short" is not.

### Data and labeling

**Q5: Who does the labeling?**
Recommended: Any barista who tastes the shot within 60 seconds of pulling.

**Q6: Is labeling mandatory or optional?**
Recommended: Optional but encouraged. Gamify it (barista leaderboard for rating consistency).

**Q7: When barista rating and customer feedback conflict, who wins?**
Recommended: Customer return overrides. Customer is the actual evaluator.

### Product and business

**Q8: What is the target customer?**
Specialty café (peak quality) vs. chain/franchise (consistency)? These require different UX and model objectives. Pick one for v1.

**Q9: How does the product handle different bean origins?**
Recommended: Bean batch as a categorical feature + retrain when batch changes. Require customers to log bean purchases.

**Q10: Data privacy/sharing model?**
Recommended: Pooled with anonymization. Position as "your data makes the product better for everyone." Be explicit in T&Cs.

### Technical

**Q11: How does the model handle sensor failures?**
Recommended: Score with reduced confidence. Flag "incomplete data." Don't discard the shot.

**Q12: How often does the model retrain?**
Recommended: Every 500 new labeled shots or every 2 weeks.

**Q13: Where does training happen?**
Recommended: Cloud. Pi runs inference only.

---

## The one question that supersedes all others

> Who is the person using this every day, and what would make them trust a number from a machine enough to change their behavior?

A skeptical expert barista needs explainability and the ability to override. A franchise trainee needs simplicity and a clear "do this" instruction. These are different products. The founder should pick one primary user for v1.

# The Ground Truth Problem — How Do We Know What "Good" Is?

## Why this is the hardest part

The algorithm learns to predict quality. But it needs examples of what quality *is*. Someone has to provide the labels. And that someone is human, subjective, and inconsistent.

This is the single most important design decision in the project. A beautiful model trained on bad labels is useless.

---

## The labeling options

### Option 1: Barista rating (most practical)

After each shot, the barista rates it on a simple scale.
- "Did this shot meet your standard?" → Yes / No / Marginal
- Or: 1–5 stars
- Or: 1–10 score

**Pros:** Immediate, zero friction, captures expert judgment, happens at point of production

**Cons:**
- One barista's 7 is another's 9
- Baristas rate fast and often without tasting (especially during rush)
- Ratings drift over time (barista mood, fatigue)
- Confirmation bias: if the sensors look bad, they rate lower before tasting

**Mitigation:** Blind-ish labeling. Don't show the sensor scores to the barista before they rate. Show them the score only after they submit the rating.

### Option 2: Customer feedback (valuable but lagged)

If a customer returns a shot, that's a strong negative signal. If they compliment it, weak positive. NPS surveys tied to specific shots (via receipt number + timestamp) could work at scale.

**Limitation:** Signal is sparse (most customers don't give feedback), lagged by minutes (by then the barista has pulled 5 more shots), and confounded (was it the shot or the service?).

**Use as a secondary signal** to validate, not as primary labels.

### Option 3: Professional Q-grader tasting (expensive, high quality)

A certified Q-grader (professional coffee taster) evaluates a sample of shots using the SCAA protocol (scoring on acidity, body, sweetness, aftertaste, balance, etc.).

**Pros:** Gold-standard labels, consistent, documented methodology

**Cons:** Expensive (~$100–300/hour), doesn't scale to 200 shots/day, not available at most businesses

**Use for calibration.** Bring in a Q-grader for a single calibration session (e.g., 50 shots rated by Q-grader + baristas simultaneously). Use this to anchor the barista rating scale.

### Option 4: TDS measurement as proxy (objective but incomplete)

Total Dissolved Solids (measured via refractometer) gives a direct read on extraction yield. The SCA defines ideal extraction yield as 18–22% and ideal strength (TDS) as 1.2–1.45%.

**Pros:** Fully objective, no human judgment required, scientifically grounded

**Cons:** TDS in the ideal range doesn't guarantee the shot tastes good (variety, origin, roast all affect what "ideal" means). It's necessary but not sufficient.

**Use TDS as one input feature**, not as the sole ground truth.

---

## The inter-rater reliability problem

If two baristas rate the same shot differently, the model gets contradictory training signals.

**Solution: Calibration sessions**
Once a week, pull 5 shots in sequence and have every barista rate them. Calculate inter-rater agreement (Cohen's kappa). If it's below 0.6, run a calibration discussion to align the team on the rating scale with concrete examples.

This is how clinical research handles inter-rater reliability. Apply the same principle.

---

## What to do when labels are noisy

Noisy labels are expected. The algorithm must be robust to them.

- **Collect 3+ ratings per shot** when possible (different baristas sample the same batch)
- **Use the median**, not the mean — resistant to outliers
- **Weight labels by rater reliability** — a barista with high inter-rater consistency gets their ratings weighted more
- **Flag shots where ratings diverged** (e.g., one rated 8, another rated 3) — these are informative edge cases for human review

---

## The cold start label strategy

Day 1, you have zero labels. Here's a practical sequence:

**Week 1–2:** Pull shots in a controlled test environment. Two experienced baristas taste and rate every shot. Collect 100–200 labeled examples. Use these to calibrate the hand-tuned baseline model.

**Week 3–4:** Deploy at one location. Baristas rate shots in real workflow. Target: 10 labeled shots/day minimum.

**Month 2:** Start training GBDT with accumulated labels. Compare GBDT predictions vs. barista labels on held-out shots.

**Month 3+:** Model is live. Barista ratings become the ongoing label source. Model retrains monthly.

# The Feedback Loop — How the Model Gets Smarter

## Why the feedback loop is the product

The hardware is a commodity (anyone can attach sensors to an espresso machine). The algorithm is defensible. But the *feedback loop* — the data flywheel — is the actual moat.

More shots → more labels → better model → more useful recommendations → baristas trust it more → more shots get rated → more data. This is the compounding engine.

Design it explicitly from day one.

---

## The loop, step by step

```
1. Shot pulled
       ↓
2. Sensor readings captured + features computed
       ↓
3. Current model scores the shot
       ↓
4. Score + recommendation shown to barista
       ↓
5. Barista adjusts (or not) and pulls next shot
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

---

## The exploration vs. exploitation tension

**Exploitation:** The model recommends what it's confident works. Barista follows the recommendation. Quality is high and consistent.

**Exploration:** The model tries something different to learn if it's better. Quality may vary, but the model gains information.

This is the classic reinforcement learning tension. In practice:

- **Mostly exploit** (90%+ of shots): Give the barista the best known recommendation. Don't experiment on paying customers.
- **Occasional explore** (controlled conditions): During off-peak hours or internal test sessions, run protocol variations to expand the model's knowledge base.
- **Capture natural exploration:** Baristas naturally deviate. When they do, log it with their rating. Natural deviation is free exploration data.

---

## What the model learns over time

**Short term (first 500 shots):** Which parameters are most predictive of barista rating at this specific location.

**Medium term (500–5,000 shots):** Non-linear interactions. E.g., "a 27-second extraction at 93°C with this bean is fine, but at 91°C it needs 30 seconds." Single-parameter models can't capture this.

**Long term (5,000+ shots per location):** Seasonality (beans change twice a year), barista-specific patterns (each barista has different calibration drift tendencies), equipment aging effects (grinder burrs dull over months).

---

## Multi-location learning

A business with 5 locations generates 5x the data. But each location has different:
- Water hardness (affects extraction chemistry)
- Bean freshness (transit times differ)
- Barista skill level

**Architecture:** Train a *global base model* on all locations' data, then *fine-tune* a per-location model on local data. This is transfer learning applied to espresso. The global model learns universal espresso physics; the local model learns location-specific nuances.

**Benefit:** New locations start with a useful model immediately (global), then personalize over 4–6 weeks of local data.

---

## Closing the customer feedback loop

Customer feedback is sparse but high-value. Design collection carefully:

**Option A: QR code on receipt**
Timestamp on receipt → customer scans → rates the shot → timestamped rating linked to specific shot record.
Works for sit-in cafes. Attrition rate: 2–8%.

**Option B: Return/remake as signal**
If a customer returns a shot, that's an automatic 1/5. This is 100% capture rate for very negative outcomes.

**Option C: Staff observation**
Barista observes "customer left half the shot" — logs this as implicit negative. Requires discipline.

**Don't over-engineer customer feedback early.** Barista labels are sufficient for the first phase. Customer feedback becomes important when you want to disconnect from barista taste preferences and optimize for *customer* preferences (which may differ).

---

## Preventing overfitting to one barista's preferences

If one barista does 80% of the labeling, the model learns *their* preferences, not universal quality.

**Mitigations:**
- Weight labels by barista when training. If barista A provides 80% of labels, down-weight their labels to reduce their influence.
- Run cross-validation by barista: train on baristas A, B, C; validate on barista D. Low accuracy = model overfit to specific raters.
- Periodically re-anchor with Q-grader calibration (see ground-truth file).

---

## The retraining trigger

Retrain the model when:
1. **Time-based:** Every 2 weeks (simple, predictable)
2. **Data-based:** Every 500 new labeled shots (faster early, slower later)
3. **Performance-based:** Validation accuracy drops below threshold (reactive)
4. **Drift-based:** Input distribution shifts significantly (proactive)

Recommendation: Use **data-based** trigger for the first year. Transition to **drift-based** when you have enough historical data to define what "normal" drift looks like.

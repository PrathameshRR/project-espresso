# Output Design — What Score Do We Produce?

## The central design decision

**Single composite score** (e.g. 0–100) vs **multi-dimensional scores** (e.g. Extraction / Consistency / Appearance as separate numbers)?

Both are valid. The right answer depends on what the barista does with the output.

---

## Option A: Single composite score

**Example:** Shot #47 → 76/100

**Pros:**
- Simple to understand and communicate
- Easy to track over time ("our average is going up")
- One number to optimize

**Cons:**
- Hides *what* went wrong — a 76 from bad crema looks identical to a 76 from channeling
- Hard to act on without knowing which dimension pulled the score down

**When to use:** For business-level reporting (owner dashboard, shift summaries), not for barista feedback in the moment.

---

## Option B: Multi-dimensional scores

**Example:**
```
Extraction quality:  82/100  ← was it properly extracted?
Process consistency: 71/100  ← did parameters match the target recipe?
Appearance:          89/100  ← crema, color, visual quality
Overall:             80/100  ← weighted composite
```

**Pros:**
- Barista can see *where* the problem is
- Maps to actionable feedback ("your extraction score is low → grind finer")
- Easier to build trust — the barista can verify "yes, the crema looked off"

**Cons:**
- More complex to model (three separate models or a multi-output model)
- Dimensions may correlate — appearance and extraction are not always independent

**Recommended for barista-facing UI.**

---

## Option C: Deviation from target recipe (the cleaner mental model)

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

**Why this is powerful:**
- No need to define universal "good espresso" — every business defines their own target
- The algorithm's job becomes: measure deviation from spec
- Feedback is immediately actionable: "your extraction was 5 seconds short — grind finer"

**Limitation:** Still needs a ground truth model to learn *which deviations matter most*. A 2-second short pull may not matter; a 7-second short pull definitely does.

---

## Recommended architecture: Hybrid

```
Layer 1: Recipe deviation scores (objective, deterministic)
         → calculated directly from sensor readings vs. target recipe

Layer 2: Quality prediction score (learned, probabilistic)
         → ML model predicts barista rating from sensor features

Layer 3: Composite display
         → show both: "Your recipe score: 78 | Predicted quality: 74"
```

The recipe deviation score is transparent and always explainable. The quality prediction score captures the non-linear interactions the deviation score misses (e.g., two small deviations in the same direction compound badly).

---

## What the barista interface should show

**Primary:** Current shot score + direction vs. last shot (up/down/same)

**Secondary:** Which dimension drove the change ("Extraction -8 vs. last shot")

**On demand:** "What to change next" — ranked list of highest-impact adjustments
```
1. Grind finer by ~1 step (extraction time was 22s, target 28s)
2. Distribute more evenly (channeling detected on left side)
3. Temperature within range ✓
```

**Over a shift:** Trend chart — are scores improving, degrading, or flat?

---

## What the owner/manager interface should show

- Average score by barista per shift
- Score variance (consistency matters as much as average)
- Which parameters drift most across the day (grind dose tends to drift if the grinder isn't checked)
- Alert: shift average dropped >5 points → investigate

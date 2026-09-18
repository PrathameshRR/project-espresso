# Espresso Quality Algorithm — Project Framing

## The core problem

A barista pulls 50–200 shots a day. Each shot has a slightly different outcome. They have no reliable signal for *why* one shot is better than another. They adjust by intuition and memory, which doesn't scale across a team or a multi-outlet business.

The founder's insight: **if we instrument the process, we can give the barista a signal they can act on.** The hardware exists. The question is: what algorithm turns sensor data into a useful score?

---

## What this project is NOT about

- Deep coffee science (the papers cover this; we don't need to re-derive it)
- Hardware design choices
- Business model or GTM

## What this project IS about

- How to design an algorithm that scores espresso quality from sensor inputs
- How that score gets generated, validated, and improved over time
- How the score becomes a feedback signal baristas can actually use

---

## The fundamental algorithm question

> Given a vector of sensor readings from a single espresso pull, produce a score (or set of scores) that correlates with human-judged quality — and tell the barista which input to change next.

This is a **supervised regression problem** with a feedback loop. It requires:
1. Defining the inputs (sensor parameters)
2. Defining the output (score design)
3. Defining the ground truth (how do we label "good"?)
4. Choosing the model architecture
5. Designing the feedback loop that improves the model over time

Each of these is a separate design decision. See the other files in this folder.

---

## Why this is hard (the honest version)

1. **Ground truth is subjective.** One barista's 8/10 is another's 6/10. The model needs to reconcile this.
2. **Coffee changes.** Same parameters + different bean origin/roast date → different outcome. The algorithm must account for product-level variance.
3. **Sensors are noisy.** Pressure spikes, camera occlusion, inconsistent tamping surfaces — noise in inputs propagates to noise in scores.
4. **Cold start.** The model has no data at deployment. It needs a strategy for the first 500 shots.

---

## One-sentence version of the approach

Collect labeled shot data (sensor readings + barista rating) → train a scoring model → use the model's feature importances to tell the barista *which lever to pull* → collect more labeled data as they adjust → retrain.

---

## Files in this folder

| File | What it covers |
|------|----------------|
| `01-input-parameters.md` | Every measurable parameter, grouped by phase |
| `02-output-design.md` | Single score vs multi-dimensional; what the barista sees |
| `03-algorithm-architecture.md` | Model options, tradeoffs, recommended path |
| `04-ground-truth-problem.md` | How to label shots; resolving barista disagreement |
| `05-data-collection-strategy.md` | Cold start, labeling workflow, data volume needed |
| `06-feedback-loop.md` | How the model improves over time |
| `07-open-questions.md` | Decisions the founder needs to make |

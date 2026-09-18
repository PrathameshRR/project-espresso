# Project Espresso

Espresso quality scoring algorithm for a robotic espresso measurement system. Turns sensor data into actionable scores and recommendations for baristas.

## What this does

Given sensor readings from a single espresso pull (dose, pressure, flow rate, extraction time, crema analysis, etc.), the algorithm:

1. **Scores** the shot across three dimensions: Extraction Quality, Process Consistency, and Appearance
2. **Explains** which parameters drove the score up or down
3. **Recommends** what the barista should change next ("Grind finer by 1 step")

## Quick start

```bash
python espresso_scorer_v1.py
```

No dependencies required -- runs on standard Python 3.10+. Simulates 10 espresso shots with varying quality levels and scores each one.

## Architecture

The algorithm has two planned layers:

- **Layer 1 (v1, shipped now):** Deterministic weighted-deviation scoring. Compares each sensor reading against a target recipe, applies tolerance bands, and computes weighted penalty scores. No ML, no training data needed.
- **Layer 2 (future):** Gradient Boosted Trees (LightGBM) trained on barista-rated shots. Captures non-linear interactions the deterministic model misses. Needs ~500 labeled shots to start.

## Scoring output

Each shot produces:
- Composite score (0-10)
- Sub-scores: Extraction / Consistency / Appearance
- Top contributing factors per dimension
- Ranked actionable recommendations

## Project docs

Detailed briefs on each aspect of the system:

| Doc | Topic |
|-----|-------|
| [Full Brief](docs/full-brief.md) | Complete algorithm design document |
| [Project Framing](docs/00-project-framing.md) | Problem definition and approach |
| [Input Parameters](docs/01-input-parameters.md) | Sensor inputs and feature engineering |
| [Output Design](docs/02-output-design.md) | Score structure and display |
| [Algorithm Architecture](docs/03-algorithm-architecture.md) | Model pipeline and tech stack |
| [Ground Truth](docs/04-ground-truth-problem.md) | Labeling strategy and calibration |
| [Data Collection](docs/05-data-collection-strategy.md) | Data requirements and annotation workflow |
| [Feedback Loop](docs/06-feedback-loop.md) | How the model improves over time |
| [Open Questions](docs/07-open-questions.md) | Decisions to make before building |

## Roadmap

- [x] Deterministic scoring algorithm (v1)
- [ ] Simulated barista rating collection
- [ ] LightGBM model training pipeline
- [ ] SHAP-based explanation engine
- [ ] Counterfactual recommendation engine
- [ ] Multi-location transfer learning

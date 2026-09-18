# Running the Algorithm

## Prerequisites

- Python 3.10 or higher
- No external dependencies required (uses only standard library: `random`, `math`, `dataclasses`)

## Quick start

```bash
python espresso_scorer_v1.py
```

This simulates 10 espresso shots with varying quality levels (good, mediocre, bad) and scores each one. Output goes to stdout.

## What the output shows

For each simulated shot, you'll see:

1. **Composite score** (0-10) with a visual bar
2. **Three sub-scores:**
   - **Extraction** -- was the coffee properly extracted? (extraction time, brew ratio, pressure, flow rate, temperature)
   - **Consistency** -- did parameters match the target recipe? (dose, grind, tamp, distribution)
   - **Appearance** -- visual quality (crema color, thickness, persistence)
3. **Contributing factors** -- which parameters pulled the score down, with actual vs target values
4. **Key parameters** -- the raw sensor readings at a glance
5. **Recommendations** -- actionable changes ranked by impact ("Adjust dose: -1.1g")

At the end, a **shift summary** shows average score, best/worst, standard deviation, and a distribution chart.

## Customizing the run

### Change the random seed

In `espresso_scorer_v1.py`, the last lines are:

```python
if __name__ == "__main__":
    random.seed(42)
    run_shift_simulation(10)
```

- Change `42` to any integer for a different set of simulated shots
- Change `10` to simulate more or fewer shots

### Force a specific quality level

To see what bad shots look like, modify the `simulate_shot` call inside `run_shift_simulation`:

```python
shot = simulate_shot("bad")     # all bad shots
shot = simulate_shot("good")    # all good shots
shot = simulate_shot("mediocre")  # all mediocre
shot = simulate_shot("random")  # mixed (default)
```

### Change the target recipe

Edit the `TARGET` dictionary at the top of the file. For example, for a ristretto:

```python
TARGET = {
    "dose_weight_g": 18.0,
    "brew_ratio": 1.5,        # shorter ratio
    "extraction_time_s": 22.0, # faster pull
    "yield_weight_g": 27.0,   # less output
    # ... rest stays the same
}
```

### Adjust scoring sensitivity

Edit the `TOLERANCE` dictionary to make scoring stricter or more forgiving. Smaller values = stricter scoring, larger = more forgiving.

Edit the `WEIGHTS` dictionary to change how much each parameter matters to each dimension.

## Sample output

See [sample-run-output.txt](sample-run-output.txt) for the full output of a 10-shot simulation run (seed 42).

## How the scoring works

For each parameter:

1. Calculate how far the actual reading is from the target
2. If within the tolerance band, no penalty
3. If outside, penalty scales linearly from 0 to 1 (capped at 1)
4. Each penalty is weighted by how important that parameter is to each dimension
5. Dimension score = 10 * (1 - total weighted penalty)
6. Composite = 45% extraction + 30% consistency + 25% appearance

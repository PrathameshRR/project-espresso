"""
Espresso Quality Scoring Algorithm -- v1 Prototype
Deterministic weighted-deviation scoring with simulated sensor data.
"""

import random
import math
from dataclasses import dataclass


# ─── Target Recipe (configurable per business) ───────────────────────────────

TARGET = {
    "dose_weight_g": 18.0,
    "grind_size": 5.0,            # arbitrary scale 1-10 (fine to coarse)
    "tamp_pressure_kg": 20.0,
    "distribution_score": 1.0,    # 0-1, 1 = perfectly even
    "time_grind_to_pull_s": 15,
    "pre_infusion_duration_s": 3.0,
    "extraction_time_s": 28.0,
    "peak_pressure_bar": 9.0,
    "pressure_stability": 0.0,    # std dev — lower is better
    "flow_rate_mean_gs": 2.0,     # grams/second
    "brew_ratio": 2.5,            # yield / dose
    "yield_weight_g": 45.0,
    "water_temp_c": 93.0,
    "crema_hue_mean": 40.0,       # HSV hue — golden-brown
    "crema_thickness_mm": 4.0,
    "crema_persistence_s": 120.0,
}

# Acceptable tolerance bands (± from target before penalty kicks in)
TOLERANCE = {
    "dose_weight_g": 0.3,
    "grind_size": 0.3,
    "tamp_pressure_kg": 1.5,
    "distribution_score": 0.08,
    "time_grind_to_pull_s": 5,
    "pre_infusion_duration_s": 0.5,
    "extraction_time_s": 2.0,
    "peak_pressure_bar": 0.3,
    "pressure_stability": 0.08,
    "flow_rate_mean_gs": 0.15,
    "brew_ratio": 0.15,
    "yield_weight_g": 2.0,
    "water_temp_c": 0.5,
    "crema_hue_mean": 3.0,
    "crema_thickness_mm": 0.5,
    "crema_persistence_s": 15.0,
}

# Weights per dimension — how much each parameter matters to each sub-score
# Higher weight = more penalty when off-target
WEIGHTS = {
    "extraction": {
        "extraction_time_s": 25,
        "brew_ratio": 20,
        "peak_pressure_bar": 15,
        "flow_rate_mean_gs": 15,
        "water_temp_c": 10,
        "pre_infusion_duration_s": 8,
        "pressure_stability": 7,
    },
    "consistency": {
        "dose_weight_g": 20,
        "grind_size": 20,
        "tamp_pressure_kg": 15,
        "distribution_score": 20,
        "time_grind_to_pull_s": 10,
        "pressure_stability": 15,
    },
    "appearance": {
        "crema_hue_mean": 35,
        "crema_thickness_mm": 30,
        "crema_persistence_s": 20,
        "yield_weight_g": 15,
    },
}

# Which parameters the barista can actually change (for recommendations)
LEVER_ACTIONS = {
    "dose_weight_g": ("Adjust dose", "g"),
    "grind_size": ("Adjust grind", "steps"),
    "tamp_pressure_kg": ("Adjust tamp pressure", "kg"),
    "distribution_score": ("Distribute more evenly", None),
    "water_temp_c": ("Adjust water temperature", "C"),
    "pre_infusion_duration_s": ("Adjust pre-infusion time", "s"),
    "time_grind_to_pull_s": ("Reduce time between grind and pull", "s"),
}


# ─── Scoring Engine ──────────────────────────────────────────────────────────

def compute_deviation(actual, target, tolerance):
    """How far off is actual from target, as a 0-1 penalty (0 = perfect, 1 = very bad)."""
    raw_diff = abs(actual - target)
    if raw_diff <= tolerance:
        return 0.0
    excess = raw_diff - tolerance
    max_excess = tolerance * 3 if tolerance > 0 else 1.0
    return min(excess / max_excess, 1.0)


def score_dimension(shot: dict, dimension: str) -> tuple[float, list[tuple[str, float, float]]]:
    """
    Score one dimension (extraction / consistency / appearance).
    Returns (score_0_to_10, [(param, deviation, weighted_penalty), ...]).
    """
    weights = WEIGHTS[dimension]
    total_weight = sum(weights.values())
    total_penalty = 0.0
    breakdowns = []

    for param, weight in weights.items():
        dev = compute_deviation(shot[param], TARGET[param], TOLERANCE[param])
        penalty = dev * (weight / total_weight)
        total_penalty += penalty
        if dev > 0:
            breakdowns.append((param, dev, penalty))

    score = round(10.0 * (1.0 - total_penalty), 1)
    score = max(0.0, min(10.0, score))
    breakdowns.sort(key=lambda x: -x[2])
    return score, breakdowns


def score_shot(shot: dict) -> dict:
    """Full scoring pipeline for one shot."""
    extraction_score, extraction_detail = score_dimension(shot, "extraction")
    consistency_score, consistency_detail = score_dimension(shot, "consistency")
    appearance_score, appearance_detail = score_dimension(shot, "appearance")

    composite = round(
        extraction_score * 0.45
        + consistency_score * 0.30
        + appearance_score * 0.25,
        1,
    )

    return {
        "composite": composite,
        "extraction": {"score": extraction_score, "detail": extraction_detail},
        "consistency": {"score": consistency_score, "detail": consistency_detail},
        "appearance": {"score": appearance_score, "detail": appearance_detail},
    }


def generate_recommendations(shot: dict, result: dict, top_n: int = 3) -> list[str]:
    """Turn the biggest penalties into actionable recommendations."""
    all_penalties = []
    for dim in ["extraction", "consistency", "appearance"]:
        for param, dev, penalty in result[dim]["detail"]:
            if param in LEVER_ACTIONS:
                actual = shot[param]
                target = TARGET[param]
                diff = actual - target
                all_penalties.append((param, dev, penalty, diff))

    seen = set()
    unique = []
    for item in sorted(all_penalties, key=lambda x: -x[2]):
        if item[0] not in seen:
            seen.add(item[0])
            unique.append(item)

    recs = []
    for param, dev, penalty, diff in unique[:top_n]:
        action_label, unit = LEVER_ACTIONS[param]
        if unit and param != "distribution_score":
            direction = "+" if diff < 0 else "-"
            amount = round(abs(diff), 1)
            recs.append(f"{action_label}: {direction}{amount} {unit} (current: {shot[param]}, target: {TARGET[param]})")
        else:
            recs.append(f"{action_label} (current: {round(shot[param], 2)}, target: {TARGET[param]})")

    return recs


# ─── Shot Simulator ──────────────────────────────────────────────────────────

def simulate_shot(quality: str = "random") -> dict:
    """
    Generate a simulated shot with realistic sensor readings.
    quality: "good", "mediocre", "bad", or "random"
    """
    if quality == "random":
        quality = random.choice(["good", "good", "mediocre", "mediocre", "bad"])

    noise = {"good": 0.6, "mediocre": 1.2, "bad": 2.5}[quality]

    def vary(target, tolerance, scale=noise):
        return round(target + random.gauss(0, tolerance * scale), 2)

    def vary_positive(target, tolerance, scale=noise):
        return round(max(0.01, target + random.gauss(0, tolerance * scale)), 2)

    dose = vary(TARGET["dose_weight_g"], TOLERANCE["dose_weight_g"])
    grind = vary(TARGET["grind_size"], TOLERANCE["grind_size"])
    tamp = vary(TARGET["tamp_pressure_kg"], TOLERANCE["tamp_pressure_kg"])
    dist = round(min(1.0, max(0.0, vary(TARGET["distribution_score"], TOLERANCE["distribution_score"]))), 2)
    time_gtp = max(3, round(vary(TARGET["time_grind_to_pull_s"], TOLERANCE["time_grind_to_pull_s"])))
    pre_inf = vary_positive(TARGET["pre_infusion_duration_s"], TOLERANCE["pre_infusion_duration_s"])

    extraction = vary_positive(TARGET["extraction_time_s"], TOLERANCE["extraction_time_s"])
    peak_p = vary(TARGET["peak_pressure_bar"], TOLERANCE["peak_pressure_bar"])
    p_stab = round(abs(random.gauss(0, 0.1 * noise)), 2)
    flow = vary_positive(TARGET["flow_rate_mean_gs"], TOLERANCE["flow_rate_mean_gs"])
    yield_w = round(dose * vary(TARGET["brew_ratio"], TOLERANCE["brew_ratio"]) / TARGET["brew_ratio"] * TARGET["brew_ratio"], 1)
    brew_r = round(yield_w / dose, 2) if dose > 0 else 0
    temp = vary(TARGET["water_temp_c"], TOLERANCE["water_temp_c"])

    crema_hue = vary(TARGET["crema_hue_mean"], TOLERANCE["crema_hue_mean"])
    crema_thick = vary_positive(TARGET["crema_thickness_mm"], TOLERANCE["crema_thickness_mm"])
    crema_pers = vary_positive(TARGET["crema_persistence_s"], TOLERANCE["crema_persistence_s"])

    channeling = random.random() < (0.05 if quality == "good" else 0.3 if quality == "mediocre" else 0.6)
    blonding = round(extraction * random.uniform(0.65, 0.85), 1)
    first_drop = round(random.uniform(2.5, 5.0), 1)

    return {
        "dose_weight_g": dose,
        "grind_size": grind,
        "tamp_pressure_kg": tamp,
        "distribution_score": dist,
        "time_grind_to_pull_s": time_gtp,
        "pre_infusion_duration_s": pre_inf,
        "extraction_time_s": extraction,
        "peak_pressure_bar": peak_p,
        "pressure_stability": p_stab,
        "flow_rate_mean_gs": flow,
        "brew_ratio": brew_r,
        "yield_weight_g": yield_w,
        "water_temp_c": temp,
        "crema_hue_mean": crema_hue,
        "crema_thickness_mm": crema_thick,
        "crema_persistence_s": crema_pers,
        "channeling_detected": channeling,
        "blonding_onset_s": blonding,
        "first_drop_s": first_drop,
        "_quality_preset": quality,
    }


# ─── Display ─────────────────────────────────────────────────────────────────

def bar(score, width=20):
    filled = round(score / 10 * width)
    return "#" * filled + "." * (width - filled)


def display_shot(shot: dict, result: dict, shot_number: int, recs: list[str]):
    print(f"\n{'='*60}")
    print(f"  SHOT #{shot_number}   (simulated: {shot['_quality_preset']})")
    print(f"{'='*60}")

    print(f"\n  +-- COMPOSITE SCORE --------------------------+")
    print(f"  |                                            |")
    print(f"  |         {result['composite']:>4.1f} / 10.0                    |")
    print(f"  |         {bar(result['composite'])}          |")
    print(f"  |                                            |")
    print(f"  +--------------------------------------------+")

    for dim_name in ["extraction", "consistency", "appearance"]:
        dim = result[dim_name]
        print(f"\n  {dim_name.upper():>12}:  {dim['score']:>4.1f}  {bar(dim['score'])}")
        if dim["detail"]:
            for param, dev, penalty in dim["detail"][:3]:
                direction = "v" if shot[param] < TARGET[param] else "^"
                print(f"                  {direction} {param}: {shot[param]} (target: {TARGET[param]})")

    print(f"\n  -- KEY PARAMETERS --")
    print(f"     Dose: {shot['dose_weight_g']}g -> Yield: {shot['yield_weight_g']}g (ratio {shot['brew_ratio']})")
    print(f"     Extraction: {shot['extraction_time_s']}s | Pressure: {shot['peak_pressure_bar']} bar")
    print(f"     Temp: {shot['water_temp_c']}C | Channeling: {'YES' if shot['channeling_detected'] else 'no'}")
    print(f"     Crema: hue {shot['crema_hue_mean']}, {shot['crema_thickness_mm']}mm thick, {shot['crema_persistence_s']}s persist")

    if recs:
        print(f"\n  -- WHAT TO CHANGE NEXT --")
        for i, rec in enumerate(recs, 1):
            print(f"     {i}. {rec}")

    print()


def run_shift_simulation(num_shots: int = 10):
    """Simulate a barista's shift and show scored output."""
    print("\n" + "=" * 60)
    print("  ESPRESSO QUALITY ALGORITHM -- v1 PROTOTYPE")
    print("  Deterministic weighted-deviation scoring")
    print("=" * 60)
    print(f"\n  Target recipe: {TARGET['dose_weight_g']}g dose -> {TARGET['yield_weight_g']}g yield")
    print(f"  Brew ratio: 1:{TARGET['brew_ratio']} | Extraction: {TARGET['extraction_time_s']}s")
    print(f"  Pressure: {TARGET['peak_pressure_bar']} bar | Temp: {TARGET['water_temp_c']}C")

    scores = []
    for i in range(1, num_shots + 1):
        shot = simulate_shot("random")
        result = score_shot(shot)
        recs = generate_recommendations(shot, result)
        display_shot(shot, result, i, recs)
        scores.append(result["composite"])

    print("\n" + "=" * 60)
    print("  SHIFT SUMMARY")
    print("=" * 60)
    print(f"  Shots pulled:     {num_shots}")
    print(f"  Average score:    {sum(scores) / len(scores):.1f} / 10.0")
    print(f"  Best shot:        {max(scores):.1f}")
    print(f"  Worst shot:       {min(scores):.1f}")
    print(f"  Std deviation:    {(sum((s - sum(scores)/len(scores))**2 for s in scores) / len(scores)) ** 0.5:.2f}")
    print(f"  Scores > 8.0:     {sum(1 for s in scores if s >= 8.0)}/{num_shots}")
    print(f"  Scores < 5.0:     {sum(1 for s in scores if s < 5.0)}/{num_shots}")

    print(f"\n  Score distribution:")
    for i, s in enumerate(scores):
        label = f"  Shot {i+1:>2}: {s:>4.1f}  "
        print(label + "#" * round(s / 10 * 30))
    print()


if __name__ == "__main__":
    random.seed(42)
    run_shift_simulation(10)

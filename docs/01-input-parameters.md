# Input Parameters — What the Sensors Measure

## The three phases of a shot

Every espresso pull has three distinct phases, each with its own set of measurable parameters. The algorithm needs inputs from all three.

---

## Phase 1: Pre-extraction (Prep)

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

---

## Phase 2: During Extraction (The Pull)

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

**Key insight from the papers:** The *shape* of the extraction curve matters more than any single value. A pressure that ramps up smoothly is different from one that spikes then drops, even if the average is identical.

**Algorithm implication:** You need to extract **features from the time series** — not just use raw curves. Examples:
- Time to reach 9 bar
- Duration at peak pressure
- Rate of pressure decline
- Area under the flow curve
- Slope of blonding onset

---

## Phase 3: Post-Extraction (The Brew)

These are observations of the finished shot.

| Parameter | Sensor | Why it matters |
|-----------|--------|----------------|
| Crema color | Camera (RGB/HSV analysis) | Golden-brown = ideal; pale = under-extracted, dark = over |
| Crema thickness | Camera | Richer crema = fresher beans + good extraction |
| Crema persistence | Camera (time series) | Fast dissipation = older beans or channeling |
| Cup color / tone | Camera | Visual proxy for strength |
| Final yield weight | Scale | Confirms brew ratio |
| TDS (if sensor available) | Refractometer / TDS sensor | Most direct measure of extraction yield |
| Shot volume | Camera or volumetric | Cross-check with weight |

---

## The full input vector (simplified)

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

---

## Parameters you can control vs. parameters you observe

| Controllable (levers) | Observable (outcomes) |
|----------------------|----------------------|
| Grind size | Pressure curve shape |
| Dose | Blonding time |
| Tamp pressure | Crema quality |
| Distribution | Extraction time |
| Water temp | TDS |
| Pre-infusion time | Channeling events |

The algorithm's job: learn the mapping from **levers → outcomes** and use it to recommend lever adjustments.

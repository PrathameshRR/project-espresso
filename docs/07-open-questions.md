# Open Questions — Decisions the Founder Needs to Make

These are the unresolved design choices. Each one has a recommended default, but the founder should explicitly decide.

---

## Algorithm design

**Q1: Single score or multi-dimensional?**
Recommended default: Multi-dimensional (Extraction / Consistency / Appearance) with a composite for owner reporting.
Decision needed: What dimensions matter most to the target customer (specialty café vs. chain)?

**Q2: What is the scoring range?**
0–100 mimics school grades (familiar, but carries "pass/fail" connotations).
0–10 mimics professional wine/coffee evaluation (feels more premium).
Recommended: 0–10. Easier to map to a SCAA-style rubric and easier to display on a small screen.

**Q3: How transparent should the algorithm be to the barista?**
Option A: Show score only. Barista trusts the machine.
Option B: Show score + top 3 contributing factors. Barista understands why.
Option C: Show full feature breakdown. Barista can verify and override.
Recommended: Option B. Trust builds faster when reasons are visible.

**Q4: Should the algorithm recommend a specific adjustment?**
("Grind 1 step finer" is much more useful than "your extraction was short.")
Recommended: Yes. Without a specific recommendation, the score is interesting but not actionable.

---

## Data and labeling

**Q5: Who does the labeling?**
Only the pulling barista? Any barista who tastes? Dedicated taster?
Recommended: Any barista who tastes the shot within 60 seconds of pulling, with pulling barista as default.

**Q6: Is labeling mandatory or optional?**
Mandatory labels = more data, lower quality (baristas rate without tasting when busy).
Optional labels = less data, higher quality.
Recommended: Optional but encouraged. Gamify it (barista leaderboard for rating consistency).

**Q7: How do you handle disagreements between barista rating and customer feedback?**
Customer returned a shot that the barista rated 8/10. Whose label wins?
Recommended: Customer return overrides. Customer is the actual evaluator.

---

## Product and business

**Q8: What is the target customer?**
Specialty café with trained baristas who care about craft?
Or: chain/franchise that wants consistency and cost reduction?
These require different UX and different model objectives. The specialty café cares about peak quality; the franchise cares about consistency.

**Q9: How does the product handle different bean origins?**
A model trained on Colombian espresso will perform poorly on Ethiopian natural process.
Recommended: Bean batch as a categorical feature + retrain when batch changes. Require that customers log their bean purchases.

**Q10: What's the privacy/data sharing model?**
Does data from one business's shots stay private, or pool into a shared model?
Pooled data = better global model = better cold start for new customers.
Private data = better product story for some buyers.
Recommended: Pooled with anonymization. Position as "your data makes the product better for everyone." But the founder needs to be explicit about this in T&Cs.

---

## Technical

**Q11: How does the model handle sensor failures?**
If the pressure sensor drops out mid-shot, does the shot still get scored?
Recommended: Score with reduced confidence. Flag "incomplete data" in the output. Don't discard the shot — partial data is still useful.

**Q12: How often does the model retrain?**
Recommended: Every 500 new labeled shots or every 2 weeks, whichever comes first.

**Q13: Where does training happen?**
On-device (Pi) or cloud?
Recommended: Cloud. Pi runs inference only. This allows better hardware for training and easier model management.

---

## The one question that supersedes all others

> Who is the person using this every day, and what would make them trust a number from a machine enough to change their behavior?

Everything in the algorithm design should flow from the answer to that question. A skeptical expert barista needs explainability and the ability to override. A franchise trainee needs simplicity and a clear "do this" instruction. These are different products.

The founder should pick one primary user for v1.

# Silver labelling guidelines (team bartle)

Silver labels are our own criterion-level labels for public sample cases. They are a stand-in for
the experts' labels, used only to measure and tune the module. They are not expert labels.

## What to decide, per criterion (checklist APCTT-2026-CHECKLIST-v1)

- `met`: the report itself states it, about the **assessment target** (not about another tool,
  the parent project, or someone else's earlier work).
- `not met`: the report shows it is not the case (for example "has not been validated", "planned",
  "future work", "preliminary").
- `insufficient evidence`: the report is silent or too vague.
- Judge every criterion on its own. Do not mark a lower ladder level met just because a higher one
  is, and do not mark one met just to match a TRL.
- A sentence that only states a TRL number is never evidence.

## How we read each criterion for report-type technologies (models, methods, maps, networks)

| Criterion | Met when the report states that... |
|---|---|
| C01 basic principles | the scientific or physical basis of the target (equations, processes, theory), with citations or observations |
| C02 concept formulated | the practical application of the target and how it is meant to work in it (purpose, intended use, users) |
| C03 proof of concept | analytical or simulation results show the target's key function works (for example model output, sensitivity results, method results) |
| C04 laboratory validation | the target, or a low-fidelity version of it, was tested in a **laboratory or controlled** setting (lab analyses, benchmark or synthetic tests, flume tests, verification against analytical solutions). Field work alone does not count. |
| C05 relevant-environment validation | the target was tested in a relevant or simulated environment with results reported: calibration or validation against **observed field data** from a setting like the intended one |
| C06 prototype in relevant environment | a representative version of the target was **applied or demonstrated** in a relevant environment (for example the calibrated model run for the study area to produce results) |
| C07 prototype in operational environment | a near-final version was demonstrated in the **actual operational environment**: real-time or routine use by its users, products delivered to the public or agencies, operational networks |
| C08 system qualified | the **final** system was completed and qualified against its requirements (formal release, acceptance, certification, approval, QA against stated requirements) |
| C09 proven in operation | the final system was used successfully in **actual operations over a stated period** (for example "operated since 2005", "used for N years") |
| C10 quantified results vs requirements | measured performance is compared with **stated** criteria, targets or requirements, and the report says whether they were met (statistics alone, with no criterion, are not enough) |
| C11 environment and test article defined | the test conditions and the configuration or fidelity of what was tested are described (study area and period, boundary conditions, model version and setup) |
| C12 evidence matches the target | the evidence concerns the assessed target itself; met when the report's main evidence is about the target, not only about a different element or the parent project |

## Gold pages

- PDF page index (1 = first page of the file), never the printed page number.
- List every page that clearly supports a `met` criterion (usually 1 to 4), strongest first.
  Abstract and summary pages count when they state it directly.
- Never cite cover, credits, contents, conversion-factor or reference pages.
- Quote one short sentence from the strongest page, copied exactly.

## File format (`data/silver/<case_id>.json`)

```json
{
  "case_id": "USGS-SDG-061",
  "labeler": "assistant draft",
  "mode": "blind | assisted",
  "reviewed_by": null,
  "trl_opinion": 6,
  "criteria": {
    "APCTT-C05": {"status": "met", "gold_pages": [{"document_id": "D001", "page": 23}],
                   "quote": "...", "note": "..."}
  },
  "notes": "..."
}
```

`mode: blind` means the labeller read the report without looking at the module's candidates.
`reviewed_by` is filled in by the human who spot-checked the file.

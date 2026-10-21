# trl-evidence-module (team bartle)

TRL assessment package for the 2nd APCTT Hackathon 2026. CPU only, offline, deterministic.

## What it does

For each case it reads the PDF reports and returns, for every checklist criterion, `met`,
`not met` or `insufficient evidence`. Each `met` criterion cites up to three distinct pages, best
first, each with a supporting span quoted verbatim from that page. It also returns a TRL from 1 to 9.

1. **Reading** (`pdf_text.py`). Page text is extracted with pypdfium2, with pypdf as a fallback.
   Running headers and page numbers are removed, wrapped lines are joined, and the text is split
   into sentences that recognise abbreviations. Equations, map labels and table debris are dropped.
   OCR is used only for scanned-looking documents. Page numbers are always PDF page indices.
2. **Structure** (`structure.py`). Every page gets a role: front matter, contents, abstract,
   introduction, methods, results, summary, references or appendix. Front matter, contents and
   reference pages are never cited.
3. **Criteria** (`criteria.py`). Each criterion's kind is read from the checklist description.
   It is either a TRL level parsed from "(TRL k)" or a theme: requirements, test article or target
   match. Team-written cues and queries (`assets/criteria_profiles.json`) are keyed by kind, never
   by criterion ID.
4. **Retrieval** (`retrieve.py`, `semantic.py`). BM25 is combined with domain cues, page-role
   weights and overlap with the target description. MiniLM sentence embeddings widen each
   criterion's candidate pool. Sentences that state a TRL number are never evidence.
5. **Decisions** (`decide.py`). Cumulative logistic models (`assets/trl_model.json`) and a
   target-type prior (`assets/trl_prior.json`) give a TRL distribution. The reported TRL maximises
   the expected part-A score. The TRL and the per-level criteria are decided together, so no level
   above the reported TRL is claimed `met`.
6. **Safety** (`result.py`, `safety.py`). Every result is checked against the result contract
   and repaired if needed. Internal errors fall back to a prior-based result, and the module stops
   early when the time budget runs short.

## How it was built

Development used the 99 public sample cases and the organizer's estimated TRLs (see
`declaration.json`). Leave-one-out validation of the TRL model gives a part-A proxy of 0.813,
against 0.778 for the prior alone. All public cases produce contract-valid results, at about 10 s
per case on an Apple M4 with 4 threads; the largest report takes 28 s through the kit server.

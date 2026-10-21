# Third-party notices

This package contains only the team's own code and assets (MIT License, see `LICENSE`).
No third-party source code is copied into `participant_module/`.

At run time the module uses components that are not shipped in this package:

| Component | Version | Licence | Provided by |
|---|---|---|---|
| Common base environment (Python 3.12, torch, transformers, numpy, pypdfium2, pypdf, rapidocr-onnxruntime, ...) | `base_id` apctt-base-9e7fe1324bb6 | per package, see the kit's base lock files | organizer |
| sentence-transformers/all-MiniLM-L6-v2 (catalogue `all-minilm-l6-v2`) | revision 1110a243fdf4706b3f48f1d95db1a4f5529b4d41 | Apache-2.0 | organizer model store |

Optional stages, disabled in this version's settings and not loaded:
cross-encoder/ms-marco-MiniLM-L6-v2 (Apache-2.0) and MoritzLaurer/deberta-v3-base-zeroshot-v2.0-c (MIT).

Data credit: development used the public sample cases, reports of the U.S. Geological Survey
(Credit: U.S. Geological Survey). No report content is shipped in this package.

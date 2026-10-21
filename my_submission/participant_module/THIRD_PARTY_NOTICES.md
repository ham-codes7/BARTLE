# Third-party notices

This package contains only the team's own code (MIT License, see `LICENSE`).
No third-party source code is copied into `participant_module/`.

At run time the module uses:

- Python packages of the organizer's common base environment (`base_id` in `submission.json`);
  they are installed by the organizer and are not shipped in this package.
- Public models of the organizer's model catalogue, loaded read-only from `APCTT_MODEL_STORE`;
  they are listed by `catalog_id` in `submission.json` and are not shipped in this package.

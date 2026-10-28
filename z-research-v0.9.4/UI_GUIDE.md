# Z-Research UI Guide

A clean, light research dashboard modeled after the user's target visual: indigo-purple gradient hero, dark slate sidebar, six functional feature cards, live metrics, interactive PLS model canvas and a direct dataset import area.

**Brand:** Z-Research. **Product stage:** personal Mac MVP. **Frontend:** static HTML, vanilla CSS/JavaScript; **Backend:** FastAPI and Python. No remote frontend assets are necessary.

- `app/static/index.html`: all screens, input controls and navigation links.
- `app/static/zresearch.css`: Z-Research colors, cards, hero, typography and responsive layout.
- `app/static/zresearch.js`: dashboard quick actions, demo-data uploader, live conceptual-model preview.
- `app/static/app.js`: retained v0.2 logic: local auth, datasets, analytics, AI, model controls.
- `app/static/v05.js`: retained v0.5 PLS-SEM, article discovery and chapter actions.
- `app/sem_engine.py`: experimental PLS-SEM computation.

All dashboard quick-action buttons navigate to functioning workspace screens. **Try sample data** uploads a clearly labeled *synthetic* sample dataset through the normal dataset API, then selects it as the active dataset.

**Important:** preview numbers and example hero model are for illustration only and deliberately marked; they are not research findings.

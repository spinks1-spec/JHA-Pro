# JHA Builder V2

V2 adds an offline, deployable JHA generation workflow using a built-in hazard/control library.

## Features
- Plain-language work description
- Built-in templates for:
  - Scaffolding
  - Hot Work
  - Lifting / Rigging
  - Excavation
  - General Maintenance
- Keyword-based custom JHA starter generation
- Fully editable generated rows
- Pre and post Likelihood/Severity
- Automatic risk scoring and classification
- High/Critical review warnings
- 5x5 risk matrix
- Excel and PDF export
- No external API key required

## Deploy
Upload `app.py` and `requirements.txt` to GitHub and deploy `app.py` with Streamlit Community Cloud.

## Local run
pip install -r requirements.txt
streamlit run app.py

## Important
The generator produces a starting point. It does not independently determine whether a task is safe or whether controls meet a legal, regulatory, engineering, client, or company requirement.

# JHA Builder V3 — Web-Verified

This version uses the OpenAI Responses API built-in web-search tool to research free public safety information before generating the JHA.

## Features
- Free-form job description
- Jurisdiction selection
- Live web research
- Priority for government, CCOHS, OSHA/NIOSH, manufacturers and recognized safety organizations
- Automatic Job Steps, Hazards, Controls, Pre Likelihood, Pre Severity, Post Likelihood and Post Severity
- Automatic Risk Score and Risk Rating
- Source URLs stored with each job step
- Fully editable JHA
- High/Critical residual-risk warnings
- Excel and CSV export
- Offline-readable source/risk methodology in the UI

## Important risk-rating note
Hazards and controls are supported by web research, but risk ratings are estimates generated from the application's 5×5 Likelihood × Severity method. A web page does not establish the correct rating for your particular site. Review every rating against your organization's approved matrix, actual conditions, exposure, frequency, people affected, existing controls and applicable requirements.

The application is not a substitute for legislation, regulations, permits, engineering requirements, manufacturer instructions, competent-person review or a site-specific risk assessment.

## Deploy
Upload `app.py` and `requirements.txt` to GitHub and deploy `app.py` with Streamlit Community Cloud. Add `OPENAI_API_KEY` as a Streamlit secret.

The OpenAI Responses API supports built-in web search and URL citations. API and web-search usage may incur charges.

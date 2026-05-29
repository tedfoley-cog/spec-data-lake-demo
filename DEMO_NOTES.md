# Demo Cheat Sheet — Automotive Spec Data Lake

## Setup (do this before joining the call)
- [ ] Open the repo in a Devin session, run `uv run uvicorn dashboard.app:app --port 5001`
- [ ] Open `localhost:5001` in the Browser tab — confirm empty data lake state

## Demo Flow
1. Open one of the source document diagrams (`source_documents/pdf_specs/diagrams/pcm_state_machine.png`) — "This is what engineers are manually parsing through today. State machines, flow diagrams, dense tables across PDFs, Excel, and Word files. Root cause analysis takes about a week of Ctrl+F searching."
2. Show the upload dashboard — drag a `.extracted.json` file into the upload zone and watch the pipeline stages progress in real-time (Ingest → Extract → Classify → Structure → Validate → Integrate)
3. Point out the data lake browser populating — expandable categories (Signals, States, Requirements, DTCs, Parameters) with structured entries traced back to source documents
4. Trigger full pipeline processing — "Now imagine a new spec revision drops. Devin picks it up continuously, spins up child sessions to process each document type in parallel, and integrates everything into the data lake without human intervention."
5. Show the Jira integration — Devin creates user stories for each category of findings and closes the triggering Jira ticket with a summary of what was processed
6. Key message: "What used to take a week of manual searching is now 15 minutes of automated, continuous data integration — and it scales with every new document that comes in."

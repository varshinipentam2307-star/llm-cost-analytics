# LLM API Cost & Usage Analytics

A data analyst project that investigates a problem more and more companies now face:
**they're spending real money on AI/LLM API calls, with little visibility into where that money is going.**

This project simulates 6 months of internal LLM API usage logs for a mid-size company, analyzes
spending patterns, and surfaces concrete, dollar-backed recommendations for cutting waste — packaged
as an interactive dashboard.

**➡️ [View the live dashboard](dashboard/index.html)** *(open locally — see instructions below)*

---

## The Problem

Teams across a company (Engineering, Sales, Support, Marketing, etc.) use AI features built into internal
tools — a chatbot, a code review assistant, a meeting-notes summarizer, and more. Every call to an LLM
(GPT-4o, Claude, etc.) costs money based on how much text goes in and comes out. Nobody is watching this
spend closely, and there's no visibility into:

- Which features/teams/models are driving the bill
- Whether that spend is justified, or just inefficient defaults
- Where money is being wasted outright

## What I Did

1. **Generated a realistic synthetic dataset** — 30,000 API call logs across 120 users, 6 teams, 7 product
   features, and 4 models, with intentional realistic patterns baked in (power users, feature-specific
   token profiles, occasional bloated prompts, a small error/timeout rate).
2. **Defined business questions up front** across four themes: cost breakdown, usage concentration, waste
   & inefficiency, and system health — rather than just poking at the data with no direction.
3. **Analyzed the data in Python (pandas)** to answer those questions with real numbers.
4. **Built an interactive dashboard** (HTML + Chart.js) to make the findings scannable at a glance.
5. **Wrote up findings and recommendations** as a business story, not just a wall of charts.

## Key Findings

| # | Finding | So what? |
|---|---|---|
| 1 | `gpt-4o` is only **25%** of all API calls but drives **51%** of total cost | It's not used more than other models — it's just far pricier per call. This is the single biggest cost lever in the data. |
| 2 | `sales_call_transcription` is the most expensive feature overall | Not because it's called more often, but because each call involves long transcripts (naturally token-heavy). |
| 3 | Only **2.5%** of calls are "bloated" prompts, but they account for **6.7%** of total cost | A small number of oversized prompts punch well above their weight in cost. |
| 4 | Routing simple tasks (chatbot support, internal search) off `gpt-4o` onto a cheaper model could save an estimated **~$5.49** in this sample — a pattern that scales significantly at real company volumes | Model choice, not usage volume, is the actionable lever. |
| 5 | ~3.3% of total spend went to **failed calls** (errors/timeouts) | Pure waste — money spent for zero delivered value. |
| 6 | Monthly spend stayed roughly flat over the 6-month period | This isn't a runaway-growth problem — it's an efficiency problem, and the best time to fix it is now, before volume scales up. |

Full write-up: [`analysis/findings.md`](analysis/findings.md)

## Recommendations

1. Set model-routing rules so simple, low-complexity features default to a cheaper model instead of `gpt-4o`.
2. Add a prompt-length cap or warning for features prone to bloated inputs.
3. Investigate the root cause of errors/timeouts to reduce wasted spend on failed calls.
4. Prioritize this efficiency work now, while spend is flat — the same inefficiencies get more expensive as usage grows.

## Project Structure

```
llm-cost-analytics/
├── data/
│   ├── generate_data.py       # synthetic data generator (30,000 rows)
│   └── llm_api_usage.csv      # generated dataset
├── analysis/
│   ├── analysis.py            # pandas analysis -> findings.md + dashboard/data.json
│   └── findings.md            # full written findings report
├── dashboard/
│   ├── index.html             # interactive dashboard (Chart.js, self-contained)
│   └── data.json              # aggregated data consumed by the dashboard
└── README.md
```

## How to Run This Yourself

**Requirements:** Python 3.9+, pandas

```bash
# 1. Clone the repo
git clone https://github.com/<your-username>/llm-cost-analytics.git
cd llm-cost-analytics

# 2. Install dependencies
pip install pandas

# 3. (Optional) regenerate the synthetic dataset
python data/generate_data.py

# 4. Run the analysis — this refreshes findings.md and dashboard/data.json
python analysis/analysis.py

# 5. View the dashboard
# Browsers block local file fetches, so serve it with a simple local server:
cd dashboard
python -m http.server 8000
# then open http://localhost:8000 in your browser
```

## Tech Stack

- **Python / pandas** — data generation and analysis
- **HTML / CSS / JavaScript / Chart.js** — self-contained, dependency-free interactive dashboard
- **No external services required** — the whole project runs locally

## What I'd Do With Real Data / More Time

- Connect to an actual API gateway's logs (OpenAI/Anthropic usage exports) instead of synthetic data
- Add cost forecasting (e.g., "at this growth rate, we hit $X/month by Q3")
- Segment "bloated prompt" causes further — is it a specific feature, team, or a handful of repeat users?
- A/B test actual quality impact of routing simple tasks to cheaper models, not just assume no quality loss
- Add anomaly alerting (e.g., Slack alert if a single user's daily spend spikes abnormally)

---

*This project uses a synthetic dataset generated for portfolio purposes. The patterns (power users,
feature cost profiles, error rates) are intentionally realistic but do not represent any real company's data.*

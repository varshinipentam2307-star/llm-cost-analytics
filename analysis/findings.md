# Findings: LLM API Cost & Usage Analysis

**Total spend analyzed:** $175.78 across 30,000 API calls

## 1. Cost Breakdown

- **Most expensive feature:** `sales_call_transcription` at $47.5561 (4,316 calls, $0.0110/call average)

- **Model driving the most spend:** `gpt-4o` — 25.0% of all calls but 51.0% of total cost. It is used at the same rate as other models, but costs far more per call.

## 2. Waste & Inefficiency

- **Bloated prompts:** 2.5% of calls are abnormally large for their feature, yet they account for 6.7% of total cost ($11.7).

- **Model mismatch on simple tasks:** 2125 calls to simple features (chatbot support, internal search) used the premium `gpt-4o` model, costing $10.64. Routing these to a cheaper model (`claude-haiku`) could save an estimated $5.49.

- **Failed calls still cost money:** $5.73 was spent on calls that errored out or timed out, delivering zero value.

## 3. System Health

- Monthly spend stayed roughly flat ($26.89 - $30.85 per full month) — no runaway growth. The cost problem here is inefficiency, not scale.

## Recommendations

1. Set model-routing rules so simple, low-complexity features default to a cheaper model instead of gpt-4o.

2. Add a prompt-length cap or warning for features prone to bloated inputs.

3. Investigate the root cause of errors/timeouts to reduce wasted spend on failed calls.

4. Since spend is flat, prioritize efficiency work now — before usage scales up and the same inefficiencies get more expensive.

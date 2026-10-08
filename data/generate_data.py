"""
Synthetic LLM API Usage Data Generator
---------------------------------------
Generates a realistic dataset simulating a company's internal LLM API usage
logs (e.g. calls made through an internal gateway to OpenAI/Anthropic/etc).

Output: llm_api_usage.csv

Columns:
    timestamp        - when the API call was made
    user_id           - unique user making the call
    team              - department/team the user belongs to
    feature           - product feature that triggered the call
    model             - which LLM model was used
    input_tokens      - tokens sent in the prompt
    output_tokens     - tokens generated in the response
    latency_ms        - response time in milliseconds
    cost_usd          - cost of this single API call
    status            - success / error / timeout
"""

import csv
import random
from datetime import datetime, timedelta

random.seed(42)  # reproducible results

# ----------------------------
# CONFIG - tweak these to change the "shape" of your data
# ----------------------------

NUM_ROWS = 30000
START_DATE = datetime(2026, 2, 1)
END_DATE = datetime(2026, 8, 1)

TEAMS = ["Product", "Customer Support", "Engineering", "Sales", "Marketing", "Data Science"]

FEATURES = [
    "chatbot_support",
    "email_summarizer",
    "code_review_assistant",
    "sales_call_transcription",
    "content_generator",
    "internal_search_qa",
    "meeting_notes",
]

# Models with realistic per-1K-token pricing (input, output) in USD
# (approximate, illustrative pricing - not meant to be exact real-world rates)
MODELS = {
    "gpt-4o":        {"in": 0.005,  "out": 0.015,  "weight": 0.25, "latency_base": 900},
    "gpt-4o-mini":   {"in": 0.00015,"out": 0.0006, "weight": 0.30, "latency_base": 400},
    "claude-sonnet": {"in": 0.003,  "out": 0.015,  "weight": 0.25, "latency_base": 700},
    "claude-haiku":  {"in": 0.0008, "out": 0.004,  "weight": 0.20, "latency_base": 300},
}

# Some features are naturally "chattier" (longer prompts/responses) than others
FEATURE_TOKEN_PROFILE = {
    "chatbot_support":          {"in_mean": 300,  "out_mean": 150},
    "email_summarizer":         {"in_mean": 900,  "out_mean": 120},
    "code_review_assistant":    {"in_mean": 1800, "out_mean": 400},
    "sales_call_transcription": {"in_mean": 2500, "out_mean": 600},
    "content_generator":        {"in_mean": 400,  "out_mean": 700},
    "internal_search_qa":       {"in_mean": 600,  "out_mean": 200},
    "meeting_notes":            {"in_mean": 2000, "out_mean": 350},
}

NUM_USERS = 120

STATUS_WEIGHTS = {"success": 0.94, "error": 0.04, "timeout": 0.02}


def random_timestamp():
    """Random timestamp between START_DATE and END_DATE, weighted toward business hours."""
    delta_days = (END_DATE - START_DATE).days
    day_offset = random.randint(0, delta_days)
    date = START_DATE + timedelta(days=day_offset)

    # Weight hours toward 9am-6pm on weekdays (simulate real work patterns)
    if date.weekday() < 5:
        hour = random.choices(
            population=list(range(24)),
            weights=[1,1,1,1,1,1,2,4,7,9,10,10,8,9,10,10,9,7,5,3,2,1,1,1],
        )[0]
    else:
        hour = random.choices(
            population=list(range(24)),
            weights=[1]*24,
        )[0]

    minute = random.randint(0, 59)
    second = random.randint(0, 59)
    return date.replace(hour=hour, minute=minute, second=second)


def pick_model():
    models = list(MODELS.keys())
    weights = [MODELS[m]["weight"] for m in models]
    return random.choices(models, weights=weights)[0]


def generate_users():
    """Assign each user a team and a 'usage intensity' so some users are power users."""
    users = []
    for i in range(1, NUM_USERS + 1):
        users.append({
            "user_id": f"user_{i:04d}",
            "team": random.choice(TEAMS),
            # most users are normal; a small % are heavy users (long tail)
            "intensity": random.choices([1, 3, 8], weights=[0.80, 0.15, 0.05])[0],
        })
    return users


def generate_rows(users):
    rows = []
    # Build a weighted pool of users based on intensity so heavy users appear more often
    user_pool = []
    for u in users:
        user_pool.extend([u] * u["intensity"])

    for _ in range(NUM_ROWS):
        user = random.choice(user_pool)
        feature = random.choice(FEATURES)
        model = pick_model()
        profile = FEATURE_TOKEN_PROFILE[feature]

        # Token counts with natural variance (never negative)
        input_tokens = max(20, int(random.gauss(profile["in_mean"], profile["in_mean"] * 0.35)))
        output_tokens = max(10, int(random.gauss(profile["out_mean"], profile["out_mean"] * 0.35)))

        # Occasionally inject a "bloated prompt" outlier (simulates inefficiency worth finding)
        if random.random() < 0.03:
            input_tokens = int(input_tokens * random.uniform(3, 6))

        model_cfg = MODELS[model]
        cost = (input_tokens / 1000) * model_cfg["in"] + (output_tokens / 1000) * model_cfg["out"]

        latency = max(50, int(random.gauss(model_cfg["latency_base"], model_cfg["latency_base"] * 0.3)))
        # Bigger prompts -> a bit more latency
        latency += int(input_tokens * 0.05)

        status = random.choices(list(STATUS_WEIGHTS.keys()), weights=list(STATUS_WEIGHTS.values()))[0]
        if status != "success":
            # failed calls still cost something (partial processing) but produce less/no output
            output_tokens = int(output_tokens * 0.1)
            cost = (input_tokens / 1000) * model_cfg["in"] + (output_tokens / 1000) * model_cfg["out"]

        rows.append({
            "timestamp": random_timestamp().strftime("%Y-%m-%d %H:%M:%S"),
            "user_id": user["user_id"],
            "team": user["team"],
            "feature": feature,
            "model": model,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "latency_ms": latency,
            "cost_usd": round(cost, 6),
            "status": status,
        })

    # Sort by timestamp so it reads like a real log
    rows.sort(key=lambda r: r["timestamp"])
    return rows


def main():
    users = generate_users()
    rows = generate_rows(users)

    fieldnames = [
        "timestamp", "user_id", "team", "feature", "model",
        "input_tokens", "output_tokens", "latency_ms", "cost_usd", "status",
    ]

    output_path = "llm_api_usage.csv"
    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    total_cost = sum(r["cost_usd"] for r in rows)
    print(f"Generated {len(rows)} rows -> {output_path}")
    print(f"Total simulated spend: ${total_cost:,.2f}")
    print(f"Date range: {START_DATE.date()} to {END_DATE.date()}")


if __name__ == "__main__":
    main()

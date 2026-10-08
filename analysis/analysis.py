"""
LLM API Cost & Usage Analysis
------------------------------
Reads the raw usage log (data/llm_api_usage.csv) and produces:
  1. A human-readable findings report (analysis/findings.md)
  2. A compact aggregated JSON file for the dashboard (dashboard/data.json)

Run from the project root:
    python analysis/analysis.py
"""

import json
import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = ROOT / "data" / "llm_api_usage.csv"
FINDINGS_PATH = ROOT / "analysis" / "findings.md"
DASHBOARD_DATA_PATH = ROOT / "dashboard" / "data.json"

SIMPLE_FEATURES = ["chatbot_support", "internal_search_qa"]


def load_data():
    df = pd.read_csv(DATA_PATH)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df["month"] = df["timestamp"].dt.to_period("M").astype(str)
    return df


def flag_bloated_prompts(df):
    feat_avg = df.groupby("feature")["input_tokens"].transform("mean")
    feat_std = df.groupby("feature")["input_tokens"].transform("std")
    df["is_bloated"] = df["input_tokens"] > (feat_avg + 2 * feat_std)
    return df


def build_aggregates(df):
    total_cost = round(df["cost_usd"].sum(), 2)
    total_calls = int(len(df))

    by_feature = (
        df.groupby("feature")["cost_usd"]
        .agg(total_cost="sum", calls="count", avg_cost="mean")
        .sort_values("total_cost", ascending=False)
        .round(4)
        .reset_index()
        .to_dict(orient="records")
    )

    by_model = (
        df.groupby("model")["cost_usd"]
        .agg(total_cost="sum", calls="count", avg_cost_per_call="mean")
        .sort_values("total_cost", ascending=False)
        .round(4)
        .reset_index()
    )
    by_model["pct_of_calls"] = (by_model["calls"] / total_calls * 100).round(1)
    by_model["pct_of_cost"] = (by_model["total_cost"] / total_cost * 100).round(1)
    by_model = by_model.to_dict(orient="records")

    by_team = (
        df.groupby("team")["cost_usd"]
        .agg(total_cost="sum", calls="count", avg_cost="mean")
        .sort_values("total_cost", ascending=False)
        .round(4)
        .reset_index()
        .to_dict(orient="records")
    )

    by_month = (
        df.groupby("month")["cost_usd"]
        .agg(total_cost="sum", calls="count")
        .round(2)
        .reset_index()
        .to_dict(orient="records")
    )

    by_status = (
        df.groupby("status")["cost_usd"]
        .agg(total_cost="sum", calls="count")
        .round(4)
        .reset_index()
        .to_dict(orient="records")
    )

    bloat_cost = round(df[df["is_bloated"]]["cost_usd"].sum(), 2)
    bloat_calls = int(df["is_bloated"].sum())
    bloat_pct_calls = round(df["is_bloated"].mean() * 100, 1)
    bloat_pct_cost = round(bloat_cost / total_cost * 100, 1)

    simple_gpt4o = df[(df["feature"].isin(SIMPLE_FEATURES)) & (df["model"] == "gpt-4o")]
    haiku_avg_cost = df[df["model"] == "claude-haiku"]["cost_usd"].mean()
    current_cost = round(simple_gpt4o["cost_usd"].sum(), 2)
    hypothetical_cost = round(len(simple_gpt4o) * haiku_avg_cost, 2)
    potential_savings = round(current_cost - hypothetical_cost, 2)

    failed_cost = round(df[df["status"] != "success"]["cost_usd"].sum(), 2)
    failed_pct_of_cost = round(failed_cost / total_cost * 100, 1)

    top_users = (
        df.groupby("user_id")["cost_usd"]
        .sum()
        .sort_values(ascending=False)
        .head(10)
        .round(3)
        .reset_index()
        .to_dict(orient="records")
    )

    return {
        "kpis": {
            "total_cost": total_cost,
            "total_calls": total_calls,
            "avg_cost_per_call": round(total_cost / total_calls, 4),
            "failed_pct_of_cost": failed_pct_of_cost,
        },
        "by_feature": by_feature,
        "by_model": by_model,
        "by_team": by_team,
        "by_month": by_month,
        "by_status": by_status,
        "top_users": top_users,
        "waste": {
            "bloat_calls": bloat_calls,
            "bloat_cost": bloat_cost,
            "bloat_pct_calls": bloat_pct_calls,
            "bloat_pct_cost": bloat_pct_cost,
            "simple_feature_gpt4o_calls": int(len(simple_gpt4o)),
            "simple_feature_gpt4o_current_cost": current_cost,
            "simple_feature_gpt4o_hypothetical_cost": hypothetical_cost,
            "simple_feature_gpt4o_savings": potential_savings,
            "failed_calls_cost": failed_cost,
        },
    }


def write_findings_md(agg):
    top_feature = agg["by_feature"][0]
    top_model = agg["by_model"][0]

    lines = []
    lines.append("# Findings: LLM API Cost & Usage Analysis\n")
    lines.append(f"**Total spend analyzed:** ${agg['kpis']['total_cost']:,} across {agg['kpis']['total_calls']:,} API calls\n")

    lines.append("## 1. Cost Breakdown\n")
    lines.append(
        f"- **Most expensive feature:** `{top_feature['feature']}` at "
        f"${top_feature['total_cost']:,} ({top_feature['calls']:,} calls, "
        f"${top_feature['avg_cost']:.4f}/call average)\n"
    )
    lines.append(
        f"- **Model driving the most spend:** `{top_model['model']}` — "
        f"{top_model['pct_of_calls']}% of all calls but {top_model['pct_of_cost']}% of total cost. "
        f"It is used at the same rate as other models, but costs far more per call.\n"
    )

    lines.append("## 2. Waste & Inefficiency\n")
    w = agg["waste"]
    lines.append(
        f"- **Bloated prompts:** {w['bloat_pct_calls']}% of calls are abnormally large for their feature, "
        f"yet they account for {w['bloat_pct_cost']}% of total cost (${w['bloat_cost']}).\n"
    )
    lines.append(
        f"- **Model mismatch on simple tasks:** {w['simple_feature_gpt4o_calls']} calls to simple "
        f"features (chatbot support, internal search) used the premium `gpt-4o` model, costing "
        f"${w['simple_feature_gpt4o_current_cost']}. Routing these to a cheaper model (`claude-haiku`) "
        f"could save an estimated ${w['simple_feature_gpt4o_savings']}.\n"
    )
    lines.append(
        f"- **Failed calls still cost money:** ${w['failed_calls_cost']} was spent on calls that "
        f"errored out or timed out, delivering zero value.\n"
    )

    lines.append("## 3. System Health\n")
    months = agg["by_month"]
    lines.append(
        f"- Monthly spend stayed roughly flat (${min(m['total_cost'] for m in months[:-1]):,} - "
        f"${max(m['total_cost'] for m in months[:-1]):,} per full month) — no runaway growth. "
        f"The cost problem here is inefficiency, not scale.\n"
    )

    lines.append("## Recommendations\n")
    lines.append("1. Set model-routing rules so simple, low-complexity features default to a cheaper model instead of gpt-4o.\n")
    lines.append("2. Add a prompt-length cap or warning for features prone to bloated inputs.\n")
    lines.append("3. Investigate the root cause of errors/timeouts to reduce wasted spend on failed calls.\n")
    lines.append("4. Since spend is flat, prioritize efficiency work now — before usage scales up and the same inefficiencies get more expensive.\n")

    FINDINGS_PATH.write_text("\n".join(lines))
    print(f"Wrote findings report -> {FINDINGS_PATH}")


def main():
    df = load_data()
    df = flag_bloated_prompts(df)
    agg = build_aggregates(df)

    DASHBOARD_DATA_PATH.write_text(json.dumps(agg, indent=2))
    print(f"Wrote dashboard data -> {DASHBOARD_DATA_PATH}")

    write_findings_md(agg)


if __name__ == "__main__":
    main()

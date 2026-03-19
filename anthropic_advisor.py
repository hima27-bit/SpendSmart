import pandas as pd
import requests
import os
from dotenv import load_dotenv

# ── Load API key from .env file ───────────────────────────────────────────────
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"


def build_summary(df: pd.DataFrame) -> str:
    """Build a concise spending summary to send to Groq."""
    df = df.copy()
    df["Date"] = pd.to_datetime(df["Date"])
    df["Month"] = df["Date"].dt.to_period("M")

    total = df["Amount"].sum()
    by_cat = df.groupby("Category")["Amount"].sum().sort_values(ascending=False)
    by_month = df.groupby("Month")["Amount"].sum()

    lines = [
        f"Total spending across all time: ₹{total:,.2f}",
        "",
        "Spending by category:",
    ]
    for cat, amt in by_cat.items():
        pct = (amt / total) * 100
        lines.append(f"  - {cat}: ₹{amt:,.2f} ({pct:.1f}%)")

    lines += ["", "Monthly totals:"]
    for month, amt in by_month.items():
        lines.append(f"  - {month}: ₹{amt:,.2f}")

    avg_monthly = by_month.mean()
    latest_month = by_month.iloc[-1] if len(by_month) > 0 else 0
    lines += [
        "",
        f"Average monthly spend: ₹{avg_monthly:,.2f}",
        f"Latest month spend: ₹{latest_month:,.2f}",
        f"Top spending category: {by_cat.index[0]} (₹{by_cat.iloc[0]:,.2f})",
    ]
    return "\n".join(lines)


def get_advice(summary: str) -> str:
    """Call Groq API and return formatted HTML advice."""

    if not GROQ_API_KEY:
        return "<em><b>API key not found.</b> Please create a <code>.env</code> file with your GROQ_API_KEY.</em>"

    prompt = f"""You are SpendSmart, a friendly and sharp personal finance advisor for a college student in India.

Here is the user's spending summary:
{summary}

Provide concise, actionable financial advice in exactly this structure (use plain text, no markdown, no asterisks):

1. SPENDING SNAPSHOT (2-3 sentences summarising key patterns)
2. TOP CONCERN (the single biggest spending red flag and why)
3. QUICK WINS (3 specific, practical tips to reduce spending this month)
4. SAVINGS GOAL (suggest a realistic monthly savings target based on their spending)
5. ONE SMART MOVE (one longer-term financial habit they should start now)

Keep the tone encouraging, specific to their data, and practical for a student. Total response: around 200 words."""

    try:
        response = requests.post(
            GROQ_URL,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {GROQ_API_KEY}"
            },
            json={
                "model": "llama-3.1-8b-instant",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 600,
                "temperature": 0.7
            },
            timeout=30
        )

        data = response.json()

        # Surface API errors clearly
        if response.status_code != 200:
            error_msg = data.get("error", {}).get("message", str(data))
            return f"<em><b>API Error {response.status_code}:</b> {error_msg}</em>"

        # Extract text from Groq response (OpenAI-compatible format)
        try:
            raw = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError):
            return f"<em><b>Unexpected response format:</b> {str(data)}</em>"

        # Format into readable HTML
        lines = raw.strip().split("\n")
        html_lines = []
        for line in lines:
            line = line.strip()
            if not line:
                html_lines.append("<br>")
            elif len(line) > 0 and line[0].isdigit() and "." in line[:3]:
                html_lines.append(f"<strong>{line}</strong>")
            else:
                html_lines.append(line)
        return "<br>".join(html_lines)

    except requests.exceptions.Timeout:
        return "<em><b>Request timed out.</b> Groq servers took too long. Try again.</em>"
    except requests.exceptions.ConnectionError:
        return "<em><b>No internet connection.</b> Please check your network and try again.</em>"
    except Exception as e:
        return f"<em><b>Unexpected error:</b> {str(e)}</em>"

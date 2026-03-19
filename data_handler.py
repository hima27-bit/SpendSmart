import pandas as pd
import os
from datetime import datetime, timedelta
import random

DATA_FILE = "expenses.csv"

COLUMNS = ["Date", "Category", "Amount", "Description"]

def load_data() -> pd.DataFrame:
    if os.path.exists(DATA_FILE):
        try:
            df = pd.read_csv(DATA_FILE, parse_dates=["Date"])
            return df
        except Exception:
            pass
    return pd.DataFrame(columns=COLUMNS)

def save_data(df: pd.DataFrame):
    df.to_csv(DATA_FILE, index=False)

def add_expense(df: pd.DataFrame, date: str, category: str, amount: float, description: str) -> pd.DataFrame:
    new_row = pd.DataFrame([{
        "Date": pd.to_datetime(date),
        "Category": category,
        "Amount": amount,
        "Description": description
    }])
    return pd.concat([df, new_row], ignore_index=True)

def delete_expense(df: pd.DataFrame, index: int) -> pd.DataFrame:
    if 0 <= index < len(df):
        df = df.drop(index=index).reset_index(drop=True)
    return df

def get_sample_data() -> pd.DataFrame:
    """Generate 3 months of realistic sample expense data."""
    today = datetime.today()
    categories = {
        "Food & Dining": (800, 3000),
        "Transport": (200, 800),
        "Shopping": (500, 4000),
        "Entertainment": (300, 1500),
        "Utilities": (1000, 3000),
        "Healthcare": (200, 2000),
        "Education": (500, 2500),
        "Others": (100, 1000),
    }
    descriptions = {
        "Food & Dining": ["Swiggy order", "Zomato delivery", "Restaurant dinner", "Grocery run", "Coffee shop", "Mess bill"],
        "Transport": ["Uber ride", "Metro pass", "Bus ticket", "Ola cab", "Petrol fill"],
        "Shopping": ["Amazon order", "Clothes", "Electronics", "Books", "Accessories"],
        "Entertainment": ["Netflix", "Movie tickets", "Spotify", "Gaming", "OTT subscription"],
        "Utilities": ["Electricity bill", "Internet plan", "Mobile recharge", "Water bill"],
        "Healthcare": ["Pharmacy", "Doctor visit", "Lab tests", "Vitamins"],
        "Education": ["Online course", "Textbooks", "Udemy course", "Stationery"],
        "Others": ["Miscellaneous", "Donation", "Gift", "ATM withdrawal"],
    }
    rows = []
    for days_back in range(90, 0, -1):
        date = today - timedelta(days=days_back)
        # 0–3 expenses per day
        num = random.choices([0, 1, 2, 3], weights=[0.3, 0.4, 0.2, 0.1])[0]
        for _ in range(num):
            cat = random.choice(list(categories.keys()))
            lo, hi = categories[cat]
            amt = round(random.uniform(lo * 0.3, hi * 0.7), 2)
            desc = random.choice(descriptions[cat])
            rows.append({"Date": date.strftime("%Y-%m-%d"), "Category": cat, "Amount": amt, "Description": desc})

    df = pd.DataFrame(rows, columns=COLUMNS)
    df["Date"] = pd.to_datetime(df["Date"])
    return df

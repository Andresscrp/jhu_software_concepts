"""
visualization.py

Loads, cleans, and visualizes the dataset.
"""

import os

import matplotlib.pyplot as plt
import pandas as pd
import plotly.express as px
import seaborn as sns


def load_data():
    return pd.read_csv("data/ds_salaries.csv")


def filter_ai_roles(df):
    keywords = [
        "Data Scientist",
        "Data Engineer",
        "Machine Learning",
        "AI",
        "Analytics",
    ]

    return df[df["job_title"].str.contains("|".join(keywords), case=False)]


def group_roles(title):
    title = title.lower()

    if "data scientist" in title:
        return "Data Scientist"
    if "data engineer" in title:
        return "Data Engineer"
    if "machine learning" in title:
        return "ML Engineer"
    if "ai" in title:
        return "AI Roles"
    if "analytics" in title:
        return "Analytics"

    return "Other"


def preprocess_data(df):
    df = df[df["employment_type"] == "FT"]
    df = filter_ai_roles(df)

    exp_map = {
        "EN": "Entry",
        "MI": "Mid",
        "SE": "Senior",
        "EX": "Executive",
    }

    df["experience_level"] = df["experience_level"].map(exp_map)
    df["role_group"] = df["job_title"].apply(group_roles)

    return df


def create_plot_1(df):
    """
    Seaborn plot: Salary vs Experience Level
    """
    os.makedirs("plots", exist_ok=True)

    plt.figure(figsize=(10, 6))

    sns.boxplot(
    data=df,
    x="experience_level",
    y="salary_in_usd",
    order=["Entry", "Mid", "Senior", "Executive"])

    plt.title("Salary Distribution by Experience Level")
    plt.xlabel("Experience Level")
    plt.ylabel("Salary (USD)")
    plt.ylim(0, 400000)

    plt.savefig("plots/plot_1_experience_salary.png")
    plt.close()


def create_plot_2(df):
    """
    Seaborn plot: Salary by Role Group
    """
    os.makedirs("plots", exist_ok=True)

    plt.figure(figsize=(10, 6))

    sns.boxplot(
        data=df,
        x="role_group",
        y="salary_in_usd",
        order=["Data Scientist", "Data Engineer", "ML Engineer", "AI Roles", "Analytics"]
    )

    plt.title("Salary Distribution by Role")
    plt.xlabel("Role Group")
    plt.ylabel("Salary (USD)")

    plt.xticks(rotation=30)

    plt.ylim(0, 400000)

    plt.savefig("plots/plot_2_role_salary.png")
    plt.close()


def create_plot_3(df):
    """
    Plotly interactive scatter: Salary vs Remote Ratio
    """
    os.makedirs("plots", exist_ok=True)

    fig = px.scatter(
        df,
        x="remote_ratio",
        y="salary_in_usd",
        color="role_group",
        title="Salary vs Remote Work by Role",
        labels={
            "remote_ratio": "Remote Work (%)",
            "salary_in_usd": "Salary (USD)"
        },
        hover_data=["job_title", "experience_level"]
    )

    fig.write_html("plots/plot_3_interactive.html")


if __name__ == "__main__":
    data = load_data()
    clean_data = preprocess_data(data)

    create_plot_1(clean_data)
    create_plot_2(clean_data)
    create_plot_3(clean_data)

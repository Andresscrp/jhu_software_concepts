"""
dashboard.py

Dash dashboard for exploring salary trends in AI-related careers.
"""

import base64

import pandas as pd
import plotly.express as px
from dash import Dash, dcc, html


def load_data():
    """
    Load the salaries dataset.
    """
    return pd.read_csv("data/ds_salaries.csv")


def filter_ai_roles(df):
    """
    Keep only AI-related roles.
    """
    keywords = [
        "Data Scientist",
        "Data Engineer",
        "Machine Learning",
        "AI",
        "Analytics",
    ]
    return df[df["job_title"].str.contains("|".join(keywords), case=False)]


def group_roles(title):
    """
    Group job titles into broader role categories.
    """
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
    """
    Clean and prepare the dataset.
    """
    df = df[df["employment_type"] == "FT"].copy()
    df = filter_ai_roles(df).copy()

    exp_map = {
        "EN": "Entry",
        "MI": "Mid",
        "SE": "Senior",
        "EX": "Executive",
    }

    df["experience_level"] = df["experience_level"].map(exp_map)
    df["role_group"] = df["job_title"].apply(group_roles)

    return df


def encode_image(image_path):
    """
    Convert a PNG file to a base64 string for Dash display.
    """
    with open(image_path, "rb") as image_file:
        encoded = base64.b64encode(image_file.read()).decode("utf-8")
    return f"data:image/png;base64,{encoded}"


def build_plotly_figure(df):
    """
    Build the interactive Plotly chart for remote work vs salary.
    """
    fig = px.scatter(
        df,
        x="remote_ratio",
        y="salary_in_usd",
        color="role_group",
        title="Salary vs Remote Work by Role",
        labels={
            "remote_ratio": "Remote Work (%)",
            "salary_in_usd": "Salary (USD)",
        },
        hover_data=["job_title", "experience_level"],
    )
    return fig


data = preprocess_data(load_data())

PLOT_1_SRC = encode_image("plots/plot_1_experience_salary.png")
PLOT_2_SRC = encode_image("plots/plot_2_role_salary.png")
PLOT_3_FIG = build_plotly_figure(data)

app = Dash(__name__)

app.layout = html.Div(
    style={"fontFamily": "Arial, sans-serif", "margin": "20px"},
    children=[
        html.H1(
            "How do salary levels vary across experience levels, job roles, "
            "and remote work opportunities in AI-related careers?"
        ),
        html.P(
            "This dashboard explores compensation patterns across AI-related careers. "
            "The first chart shows that salaries generally rise with experience. "
            "The second compares salary distributions across role groups, while the "
            "interactive chart examines how remote work relates to compensation."
        ),
        html.H2("Salary by Experience Level"),
        html.Img(src=PLOT_1_SRC, style={"width": "80%", "display": "block"}),
        html.H2("Salary by Role Group"),
        html.Img(src=PLOT_2_SRC, style={"width": "80%", "display": "block"}),
        html.H2("Remote Work and Salary"),
        dcc.Graph(figure=PLOT_3_FIG),
    ],
)

if __name__ == "__main__":
    app.run(debug=True)

"""Module 9 — KMeans clustering and analysis of GradCafe program data."""
from __future__ import annotations

from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.feature_extraction.text import TfidfVectorizer

import matplotlib.pyplot as plt
import pandas as pd


def load_and_prepare_data(filepath: str) -> pd.DataFrame:
    """Load the GradCafe dataset and prepare program/university columns."""
    df = pd.read_json(filepath)

    df = df[df["program"].notna()].copy()

    df["program"] = (
        df["program"]
        .astype(str)
        .str.strip()
        .str.replace(r"\s+", " ", regex=True)
    )

    split_cols = df["program"].str.split(",", n=1, expand=True)

    df["Program"] = split_cols[0].str.strip()

    if split_cols.shape[1] > 1:
        df["University"] = split_cols[1].str.strip()
    else:
        df["University"] = ""

    print(f"Number of Entries: {len(df)}")
    print(f"Number of Unique Program Input Names: {df['Program'].nunique()}")

    return df


def vectorize_programs(df: pd.DataFrame):
    """Convert program names into TF-IDF vectors."""
    vectorizer = TfidfVectorizer(stop_words="english")
    tfidf_matrix = vectorizer.fit_transform(df["Program"])

    print("TF-IDF matrix shape:", tfidf_matrix.shape)
    print("TF-IDF matrix type:", type(tfidf_matrix))
    print("Nonzero entries:", tfidf_matrix.nnz)

    return vectorizer, tfidf_matrix


def run_initial_clustering(tfidf_matrix):
    """Reduce TF-IDF matrix to 2D and run initial KMeans clustering."""
    pca_2d = PCA(n_components=2, random_state=42)
    reduced_data = pca_2d.fit_transform(tfidf_matrix.toarray())

    kmeans = KMeans(n_clusters=50, max_iter=100, n_init=5, random_state=42)
    cluster_labels = kmeans.fit_predict(reduced_data)

    plt.figure(figsize=(10, 8))
    plt.scatter(
        reduced_data[:, 0],
        reduced_data[:, 1],
        c=cluster_labels,
        cmap="tab20",
        s=20,
    )
    plt.title("Kmeans Clustering of Programs")
    plt.xlabel("KMeans Distance Direction 1")
    plt.ylabel("KMeans Distance Direction 2")
    plt.tight_layout()
    plt.savefig("initial_cluster.png")
    plt.close()

    return cluster_labels


def attach_clusters(df: pd.DataFrame, cluster_labels) -> pd.DataFrame:
    """Attach cluster labels back to the dataframe and print preview."""
    df = df.copy()
    df["cluster"] = cluster_labels

    print("\nClustered DataFrame preview:")
    print(df[["Program", "University", "cluster"]].head(100).to_string())

    return df


def make_elbow_plot(tfidf_matrix) -> None:
    """Create elbow plot using PCA-reduced TF-IDF features."""
    pca_many = PCA(n_components=75, random_state=42)
    reduced_data = pca_many.fit_transform(tfidf_matrix.toarray())

    inertias = []
    k_values = range(1, 101)

    for k in k_values:
        kmeans = KMeans(n_clusters=k, max_iter=100, n_init=5, random_state=42)
        kmeans.fit(reduced_data)
        inertias.append(kmeans.inertia_)

    plt.figure(figsize=(10, 6))
    plt.plot(k_values, inertias, marker="x")
    plt.title("The Elbow Method using Inertia")
    plt.xlabel("Values of K")
    plt.ylabel("Inertia")
    plt.tight_layout()
    plt.savefig("elbow.png")
    plt.close()

    print("\nElbow plot saved as elbow.png")


def make_major_plots(df: pd.DataFrame) -> None:
    """Create GRE/GRE V plots for Philosophy and Computer Science clusters."""
    df = df.copy()
    df["GRE"] = pd.to_numeric(df.get("gre_general"), errors="coerce")
    df["GRE V"] = pd.to_numeric(df.get("gre_verbal"), errors="coerce")

    # Keep only realistic modern GRE-style values for plotting
    df = df[
        (df["GRE"].notna()) & (df["GRE V"].notna()) &
        (df["GRE"].between(130, 170)) &
        (df["GRE V"].between(130, 170))
    ].copy()

    # Philosophy cluster
    philosophy_rows = df[df["Program"].str.contains("Philosophy", case=False, na=False)]
    philosophy_cluster = philosophy_rows["cluster"].mode().iloc[0]
    philosophy_df = df[df["cluster"] == philosophy_cluster].copy()

    print("\nPhilosophy cluster preview:")
    print(
        philosophy_df[
            ["Program", "University", "cluster", "GRE", "GRE V"]
        ].head(20).to_string()
    )

    plt.figure(figsize=(8, 6))
    plt.boxplot(
        [philosophy_df["GRE"], philosophy_df["GRE V"]],
        tick_labels=["GRE", "GRE V"],
    )
    plt.title("GRE and GRE Verbal Scores for Philosophy Majors")
    plt.xlabel("GRE Component")
    plt.ylabel("Score")
    plt.tight_layout()
    plt.savefig("philosophy.png")
    plt.close()

    # Computer Science cluster
    cs_rows = df[df["Program"].str.contains("Computer Science", case=False, na=False)]
    cs_cluster = cs_rows["cluster"].mode().iloc[0]
    cs_df = df[df["cluster"] == cs_cluster].copy()

    print("\nComputer Science cluster preview:")
    print(
        cs_df[
            ["Program", "University", "cluster", "GRE", "GRE V"]
        ].head(20).to_string()
    )

    plt.figure(figsize=(8, 6))
    plt.boxplot(
        [cs_df["GRE"], cs_df["GRE V"]],
        tick_labels=["GRE", "GRE V"],
    )
    plt.title("GRE and GRE Verbal Scores for Computer Science Majors")
    plt.xlabel("GRE Component")
    plt.ylabel("Score")
    plt.tight_layout()
    plt.savefig("computer_science.png")
    plt.close()

    # Find the dominant cluster for Computer Science
    cs_rows = df[df["Program"].str.contains("Computer Science", case=False, na=False)]
    cs_cluster = cs_rows["cluster"].mode().iloc[0]
    cs_df = df[df["cluster"] == cs_cluster].copy()

    print("\nComputer Science cluster preview:")
    print(cs_df[["Program", "University", "cluster", "GRE", "GRE V"]].head(20).to_string())

    cs_scores = cs_df[["GRE", "GRE V"]].dropna()

    plt.figure(figsize=(8, 6))
    plt.boxplot(
        [cs_scores["GRE"], cs_scores["GRE V"]],
        labels=["GRE", "GRE V"],
    )
    plt.title("GRE and GRE Verbal Scores for Computer Science Majors")
    plt.xlabel("GRE Component")
    plt.ylabel("Score")
    plt.tight_layout()
    plt.savefig("computer_science.png")
    plt.close()


def main() -> None:
    """Run the full Module 9 clustering workflow."""
    df = load_and_prepare_data("../module_8/cleaned_gradcafe.json")
    print(df[["Program", "University"]].head(10).to_string())

    _, tfidf_matrix = vectorize_programs(df)
    cluster_labels = run_initial_clustering(tfidf_matrix)

    print("Initial clustering complete.")
    print("Number of cluster labels:", len(cluster_labels))

    clustered_df = attach_clusters(df, cluster_labels)
    print("\nLast 5 rows:")
    print(clustered_df[["Program", "University", "cluster"]].tail(5).to_string())

    make_elbow_plot(tfidf_matrix)
    make_major_plots(clustered_df)


if __name__ == "__main__":
    main()

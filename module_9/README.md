# Module 9 — Text Clustering (TF-IDF, KMeans, PCA, Boxplots)

**Name:** Andres Sanchez-Castellanos  
**JHED ID:** asanch69  
**Course:** EN.605.256 Modern Software Concepts in Python  
**Module:** Module 9 — Text Clustering

---

# Sources

- Course lecture materials  
- Real Python — Indexing and Slicing  
- Real Python — KMeans Clustering in Python  
- scikit-learn documentation  
- pandas documentation  
- matplotlib documentation  
- ChatGPT  

---

# Overview

Module 9 extends the GradCafe dataset into a machine learning workflow by applying **text vectorization and clustering** techniques.

This module introduces:

1. **Text Feature Engineering (TF-IDF)**  
Program names are converted into numerical vectors using Term Frequency–Inverse Document Frequency (TF-IDF).

2. **Unsupervised Learning (KMeans Clustering)**  
Programs are grouped into clusters based on textual similarity.

3. **Dimensionality Reduction (PCA)**  
High-dimensional TF-IDF vectors are reduced to 2D for visualization.

4. **Data Analysis via Visualization**  
Clusters are analyzed using:
- Scatter plots
- Elbow method
- Boxplots for GRE comparisons

---

# Data Preparation

The dataset used:

cleaned_gradcafe.json (from Module 8)

Processing steps:

- Removed rows with missing program values  
- Cleaned whitespace and formatting  
- Split "program" column into:
  - Program  
  - University  

This produced:

- 4315 entries  
- 864 unique program names  

---

# TF-IDF Vectorization

Program names were converted into numerical vectors using:

    TfidfVectorizer(stop_words="english")

Result:

- Matrix shape: (4315, 620)  
- Sparse matrix representation  
- 7794 nonzero values  

This transforms text into a machine-readable format where similar programs have similar vector representations.

---

# KMeans Clustering

KMeans clustering was applied to group programs into similar categories.

Configuration:

- n_clusters = 50  
- max_iter = 100  
- n_init = 5  

Each program is assigned a cluster label.

Example output:

Program | University | Cluster

Clustering allows grouping similar academic programs such as:
- Engineering disciplines  
- Social sciences  
- STEM fields  

---

# PCA Visualization

Because TF-IDF vectors are high-dimensional, PCA was used to reduce data to 2D.

Plot generated:

initial_cluster.png

This visualization shows:
- Cluster groupings  
- Separation between program types  
- Density of similar programs  

---

# Elbow Method

The elbow method was used to evaluate optimal cluster size.

Plot generated:

elbow.png

Observation:

- Inertia decreases rapidly at first  
- Curve begins to flatten → diminishing returns  
- Indicates reasonable clustering structure  

---

# Boxplot Analysis (GRE Scores)

Two clusters were analyzed:

1. Philosophy  
2. Computer Science  

Plots generated:

- philosophy.png  
- computer_science.png  

---

## Philosophy

- GRE median ~162  
- GRE Verbal median ~167  
- Narrow distribution  
- One lower outlier (~154)  

Interpretation:

Philosophy applicants tend to have:
- Strong verbal scores  
- Moderate GRE scores  

---

## Computer Science

- GRE median ~167–168  
- GRE Verbal median ~158–160  
- Slightly wider spread  
- Multiple minor outliers  

Interpretation:

Computer Science applicants tend to have:
- Higher quantitative-oriented GRE performance  
- Lower verbal relative to philosophy  

---

# Key Observations

- TF-IDF effectively captures textual similarity between programs  
- KMeans groups related disciplines without supervision  
- PCA visualization confirms meaningful clustering  
- GRE distributions differ significantly between fields  
- Outliers represent real variation in applicant data  

---

# Repository Structure

module_9/

kmeans.py  
README.md  

initial_cluster.png  
elbow.png  
philosophy.png  
computer_science.png  

---

# Running the Code

    python kmeans.py

This will:

- Load and clean data  
- Generate TF-IDF matrix  
- Perform clustering  
- Create plots  
- Output cluster previews  

---

# Final Deliverables

Submitted to Canvas:

module_9.zip

GitHub repository contains:

- Clustering implementation  
- Visualizations  
- Analysis of results  
- README documentation  

---

# Summary

This module demonstrates a complete machine learning pipeline:

- Text preprocessing  
- Feature extraction (TF-IDF)  
- Unsupervised learning (KMeans)  
- Dimensionality reduction (PCA)  
- Data visualization and interpretation  

The GradCafe dataset is successfully transformed into a structured clustering system that reveals meaningful academic program groupings and applicant trends. :contentReference[oaicite:0]{index=0}
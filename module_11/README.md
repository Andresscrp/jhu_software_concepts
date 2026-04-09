# Module 11 — MLOps Pipeline (MLflow, KMeans, Experiment Tracking)

**Name:** Andres Sanchez-Castellanos  
**JHED ID:** asanch69  
**Course:** EN.605.256 Modern Software Concepts in Python  
**Module:** Module 11 — MLOps Pipeline

---

# Sources

- Course lecture materials  
- Medium — Managing ML lifecycle with MLflow  
- AWS Prescriptive Guidance — Data Persistence Patterns  
- scikit-learn documentation  
- pandas documentation  
- matplotlib documentation  
- MLflow documentation  
- Weights & Biases documentation  
- ChatGPT  

---

# Overview

Module 11 extends the clustering work from Module 9 into a **production-style machine learning workflow** using MLflow and optionally Weights & Biases (wandb).

This module introduces:

1. **Experiment Tracking (MLflow / wandb)**  
Tracks parameters, metrics, and outputs of machine learning runs.

2. **Model Logging and Registration**  
Stores trained models and registers them for reuse.

3. **Reproducibility**  
Ensures experiments can be rerun with identical configurations.

4. **MLOps Concepts**  
Bridges development and deployment practices for machine learning systems.

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
- ~895 unique program names  

---

# TF-IDF Vectorization

Program names were converted into numerical vectors using:

    TfidfVectorizer(stop_words="english")

Result:

- Matrix shape: (4315, 647)  
- Sparse matrix representation  
- 7974 nonzero values  

---

# PCA Dimensionality Reduction

- PCA applied to TF-IDF features  
- Reduced to 2 components  

Used for:

- Visualization  
- Faster clustering  

---

# KMeans Clustering

Configuration:

- n_clusters = 25  
- max_iter = 500  
- n_init = 5  
- random_state = 42  

Each program is assigned a cluster label based on textual similarity.

---

# MLflow Experiment Tracking

Tracked elements:

### Parameters
- max_iter  
- n_clusters  
- n_init  
- random_state  

### Metrics
- inertia  

### Artifacts
- Trained KMeans model  

---

# Model Registration

The trained model was registered in MLflow:

- Model Name: Clustering  
- Version: v1  

---

# MLflow Visualizations

### cluster_run.png
Shows experiment and run list

### cluster_details.png
Shows parameters and inertia metric

### model_details.png
Shows registered model and version

---

# Optional Extension — Weights & Biases (wandb)

This project also supports experiment tracking using **Weights & Biases (wandb)** as an alternative to MLflow.

---

## Setup Steps Completed

1. Installed wandb:
    pip install wandb

2. Created a free wandb account

3. Authenticated locally:
    wandb login

4. Updated pipeline to support wandb tracking

---

## wandb Tracking Implementation

The pipeline includes a toggle:

    USE_WANDB = True

This allows switching between:
- MLflow
- wandb

---

## Logged Information (wandb)

### Parameters
- max_iter  
- n_clusters  
- n_init  
- random_state  

### Metrics
- inertia  

### Artifacts
- Trained KMeans model (.pkl file)

---

## wandb Outputs

A successful run includes:

- Run configuration (parameters)
- Tracked inertia metric
- Saved model artifact

---

## wandb Screenshots

The following files demonstrate successful tracking:

- wandb_run.png  
  → Shows successful run dashboard  

- wandb_details.png  
  → Shows parameters and inertia metric  

- wandb_artifact.png  
  → Shows saved model artifact  

---

## Running wandb Version

Run:

    python kmeans_mlops_pipeline.py

Ensure:

    USE_WANDB = True

wandb will automatically:

- Track the run  
- Log parameters and metrics  
- Save model artifact  

---

# Key Observations

- MLflow enables structured experiment tracking and model registry  
- wandb provides a modern alternative with intuitive UI  
- Both tools support reproducibility and experiment comparison  
- Clustering pipeline is now production-ready  

---

# Repository Structure

module_11/

kmeans_mlops_pipeline.py  
README.md  
requirements.txt  

cluster_run.png  
cluster_details.png  
model_details.png  

wandb_run.png  
wandb_details.png  
wandb_artifact.png  

---

# Running the Code

### MLflow

Start server:

    mlflow server --host localhost --port 8080

Run:

    python kmeans_mlops_pipeline.py

---

### wandb

Ensure:

    USE_WANDB = True

Run:

    python kmeans_mlops_pipeline.py

---

# Final Deliverables

Submitted:

- module_11.zip (Canvas)  
- GitHub repository  

Includes:

- MLOps pipeline  
- MLflow tracking  
- wandb tracking (extra credit)  
- Model registration  
- Visual screenshots  
- README  

---

# Summary

This module transforms a machine learning workflow into a full **MLOps pipeline**.

Key components:

- Data preprocessing  
- TF-IDF feature extraction  
- KMeans clustering  
- PCA visualization  
- MLflow experiment tracking  
- Model registry  
- wandb experiment tracking (extra credit)

The GradCafe dataset is now part of a **reproducible, trackable, and production-ready ML system**.
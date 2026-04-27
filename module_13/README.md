# Module 13 — Transformer-Based Admissions Prediction (DistilBERT)

**Name:** Andres Sanchez-Castellanos  
**JHED ID:** asanch69  
**Course:** EN.605.256 Modern Software Concepts in Python  
**Module:** Module 13 — Transformer Model + Deployment

---

# Sources

- Course lecture materials  
- PyTorch Documentation  
- HuggingFace Transformers Documentation  
- DistilBERT Model Card  
- Flask Documentation  
- NumPy / pandas / scikit-learn documentation  
- ChatGPT  

---

# Overview

Module 13 builds a **deep learning admissions prediction system** using a pretrained transformer (**DistilBERT**) and deploys it through a **Flask web application**.

This module introduces:

1. Transformer-based modeling using text input  
2. Fine-tuning a pretrained model (DistilBERT)  
3. Model evaluation using classification metrics  
4. Model saving and reloading  
5. Deployment through a user-facing web interface  

---

# Data Preparation

Dataset used:

llm_extend_applicant_data.json

Processing steps:

- Filtered to:
  - Accepted
  - Rejected

- Removed duplicates

- Converted structured + unstructured data into a **single unified text format**

Example model input:

Program: Computer Science, Johns Hopkins University  
Comments: Strong programming background and AI research experience.  
GPA: 3.90  
GRE: 330  
GRE Verbal: 162  
GRE AW: 4.5  
Degree: PhD  
Citizenship: International  

- Missing values replaced with "Unknown"

---

# Dataset Summary

- Original rows: 49,960  
- Rows after filtering: 36,914  

Train/Test Split:

- Training rows: 29,531  
- Test rows: 7,383  

Class balance:

- Rejected: ~52%  
- Accepted: ~48%  

---

# Model Architecture

Model used:

DistilBERT (distilbert-base-uncased)

This pretrained transformer is designed for:

- Text classification  
- Efficient training compared to full BERT  

---

# Training Configuration

- Max sequence length: 256  
- Batch size: 8  
- Learning rate: 2e-5  
- Optimizer: AdamW  
- Epochs: 1  
- Device: GPU (CUDA — RTX 4080 Super)

---

# Training Results

Final Evaluation:

- Accuracy: 0.7749  
- Precision: 0.7571  
- Recall: 0.7761  
- F1 Score: 0.7665  

Confusion Matrix:

[[3343  525]  
 [1116 2399]]

---

# Model Interpretation

Observations:

- Model significantly outperforms random guessing (~50%)
- Balanced precision and recall indicate no extreme bias
- Model learns patterns from:
  - Program names  
  - Applicant comments  
  - Structured inputs  

Important:

The model reflects **patterns in GradCafe data**, not true admissions logic.

This includes:
- Noisy self-reported data  
- Missing values  
- Real-world inconsistencies  

---

# Model Persistence

The trained model is saved using:

model.save_pretrained()  
tokenizer.save_pretrained()

Saved directory:

saved_admissions_model/

The model is then reloaded to verify:

- No retraining required  
- Inference works independently  

---

# Inference Pipeline

inference.py handles:

- Model loading  
- Input formatting  
- Tokenization  
- Prediction  

Returns:

- prediction (Accepted / Rejected)  
- accepted_probability  
- model_input  

---

# Web Application (Flask)

Route:

/will-you-get-in

Features:

- User input form  
- Real-time prediction  
- Probability score  
- Display of model input  

---

# Example Output

Example prediction:

- Prediction: Rejected  
- Model score: 0.4792  

Interpretation:

- Score near 0.5 indicates uncertainty  
- Reflects ambiguity in dataset patterns  

---

# Key Observations

- Transformer model improves performance (~67% → ~77%)  
- Text provides strong predictive signal  
- Dataset noise impacts predictions  
- Model learns correlations, not causation  
- GPU training drastically improves speed  

---

# Running the Code

Train model:

    python train_model.py

Run inference:

    python inference.py

Run Flask app:

    python run.py

Then open:

    http://127.0.0.1:5000/will-you-get-in

---

# Reflection

This module demonstrates a full modern ML pipeline:

- Data preparation  
- Transformer fine-tuning  
- Model evaluation  
- Model persistence  
- Deployment  

Lessons learned:

- Pretrained models significantly improve performance  
- Text-based modeling is powerful  
- Deployment is critical in ML systems  
- Data quality heavily influences outcomes  

---

# Summary

This module implements a complete transformer-based admissions prediction system.

The model achieves approximately **77% test accuracy** and demonstrates strong predictive performance on real-world noisy data, along with a fully functional deployment through a Flask web application.
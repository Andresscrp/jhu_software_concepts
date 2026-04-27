"""
Module 13 — Inference helper for the admissions prediction model.

This file loads the saved fine-tuned transformer model and exposes
a reusable prediction function for the Flask website.
"""

from __future__ import annotations

import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer

MODEL_DIRECTORY = "saved_admissions_model"
MAX_LENGTH = 256


def format_form_value(value: str | None) -> str:
    """Return a clean string value for model input formatting."""
    # -------------------------------------------------------------
    # Empty form values should not crash the model.
    # Represent missing values consistently as Unknown.
    # -------------------------------------------------------------
    if value is None or value.strip() == "":
        return "Unknown"

    return value.strip()


def build_applicant_input(form_data: dict[str, str]) -> str:
    """Build the same unified input template used during training."""
    # -------------------------------------------------------------
    # This template must match the training-time format.
    # Do not include the target label because users do not provide it.
    # -------------------------------------------------------------
    return (
        f"Program: {format_form_value(form_data.get('program'))}\n"
        f"Comments: {format_form_value(form_data.get('comments'))}\n"
        f"GPA: {format_form_value(form_data.get('gpa'))}\n"
        f"GRE: {format_form_value(form_data.get('gre'))}\n"
        f"GRE Verbal: {format_form_value(form_data.get('gre_v'))}\n"
        f"GRE AW: {format_form_value(form_data.get('gre_aw'))}\n"
        f"Degree: {format_form_value(form_data.get('degree'))}\n"
        f"Citizenship: {format_form_value(form_data.get('citizenship'))}"
    )


def load_model() -> tuple[AutoTokenizer, AutoModelForSequenceClassification, torch.device]:
    """Load the saved tokenizer and model for inference."""
    # -------------------------------------------------------------
    # Use GPU if available, otherwise CPU.
    # -------------------------------------------------------------
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    # -------------------------------------------------------------
    # Load the tokenizer and trained model from disk.
    # This avoids retraining when the Flask page is used.
    # -------------------------------------------------------------
    tokenizer = AutoTokenizer.from_pretrained(MODEL_DIRECTORY)
    model = AutoModelForSequenceClassification.from_pretrained(MODEL_DIRECTORY)

    model.to(device)
    model.eval()

    return tokenizer, model, device


def predict_admission(
    form_data: dict[str, str],
    tokenizer: AutoTokenizer,
    model: AutoModelForSequenceClassification,
    device: torch.device,
) -> dict[str, str | float]:
    """Predict admissions status from user form data."""
    # -------------------------------------------------------------
    # Convert form inputs into the same unified text format used
    # during model training.
    # -------------------------------------------------------------
    applicant_text = build_applicant_input(form_data)

    # -------------------------------------------------------------
    # Tokenize the input exactly like training/inference examples.
    # -------------------------------------------------------------
    encoded = tokenizer(
        applicant_text,
        truncation=True,
        padding="max_length",
        max_length=MAX_LENGTH,
        return_tensors="pt",
    )

    encoded = {
        key: value.to(device)
        for key, value in encoded.items()
        if key in ["input_ids", "attention_mask"]
    }

    # -------------------------------------------------------------
    # Run prediction without gradients.
    # -------------------------------------------------------------
    with torch.no_grad():
        outputs = model(**encoded)
        probabilities = torch.softmax(outputs.logits, dim=1)

    accepted_probability = float(probabilities[0, 1].cpu())
    predicted_label = int(torch.argmax(probabilities, dim=1).cpu())
    predicted_status = "Accepted" if predicted_label == 1 else "Rejected"

    return {
        "prediction": predicted_status,
        "accepted_probability": accepted_probability,
        "model_input": applicant_text,
    }


if __name__ == "__main__":
    tokenizer_obj, model_obj, device_obj = load_model()

    sample_form = {
        "program": "Computer Science, Johns Hopkins University",
        "comments": "Strong programming background and AI research experience.",
        "gpa": "3.90",
        "gre": "330",
        "gre_v": "162",
        "gre_aw": "4.5",
        "degree": "PhD",
        "citizenship": "International",
    }

    result = predict_admission(
        form_data=sample_form,
        tokenizer=tokenizer_obj,
        model=model_obj,
        device=device_obj,
    )

    print(result)
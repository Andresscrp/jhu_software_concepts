"""
Module 13 — Flask website for the admissions prediction model.

This app creates a "Will You Get In?" webpage where a user can enter
applicant information and receive a model-generated prediction.
"""

from __future__ import annotations

from flask import Flask, render_template, request

from inference import load_model, predict_admission

app = Flask(__name__)

# -------------------------------------------------------------
# Load the saved model once when the Flask app starts.
# This prevents retraining or reloading on every request.
# -------------------------------------------------------------
TOKENIZER, MODEL, DEVICE = load_model()


@app.route("/", methods=["GET", "POST"])
@app.route("/will-you-get-in", methods=["GET", "POST"])
def will_you_get_in() -> str:
    """Display the prediction form and return model results after submission."""
    prediction_result = None

    # -------------------------------------------------------------
    # If the form was submitted, collect user inputs and run inference.
    # Missing or blank values are handled inside inference.py.
    # -------------------------------------------------------------
    if request.method == "POST":
        form_data = {
            "program": request.form.get("program", ""),
            "comments": request.form.get("comments", ""),
            "gpa": request.form.get("gpa", ""),
            "gre": request.form.get("gre", ""),
            "gre_v": request.form.get("gre_v", ""),
            "gre_aw": request.form.get("gre_aw", ""),
            "degree": request.form.get("degree", ""),
            "citizenship": request.form.get("citizenship", ""),
        }

        prediction_result = predict_admission(
            form_data=form_data,
            tokenizer=TOKENIZER,
            model=MODEL,
            device=DEVICE,
        )

    # -------------------------------------------------------------
    # Render the form page. If POST happened, also show prediction.
    # -------------------------------------------------------------
    return render_template(
        "will_you_get_in.html",
        prediction_result=prediction_result,
    )


if __name__ == "__main__":
    # -------------------------------------------------------------
    # Run the app locally for testing.
    # -------------------------------------------------------------
    app.run(debug=True)
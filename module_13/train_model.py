"""
Module 13 — Fine-tune and evaluate a pretrained transformer admissions model.

This script loads and cleans the admissions dataset, creates unified text
inputs, fine-tunes DistilBERT for binary admissions prediction, and evaluates
the model using accuracy, precision, recall, F1, and a confusion matrix.
"""

from __future__ import annotations

import re

import numpy as np
import pandas as pd
import torch
from sklearn.metrics import accuracy_score, confusion_matrix, precision_score, recall_score, f1_score
from sklearn.model_selection import train_test_split
from torch.optim import AdamW
from torch.utils.data import DataLoader, Dataset
from transformers import AutoModelForSequenceClassification, AutoTokenizer

MODEL_NAME = "distilbert-base-uncased"
MAX_LENGTH = 256
BATCH_SIZE = 8
LEARNING_RATE = 2e-5
EPOCHS = 1
TRAIN_PROGRESS_INTERVAL = 100
TEST_PROGRESS_INTERVAL = 100


def extract_numeric_value(value: object) -> float:
    """
    Extract the first numeric value from a mixed string.

    Examples:
    - "GPA 3.57" -> 3.57
    - "GRE 327" -> 327.0
    - "GRE AW 3.50" -> 3.50
    """
    # -------------------------------------------------------------
    # Preserve missing values as NaN.
    # -------------------------------------------------------------
    if value is None or pd.isna(value):
        return np.nan

    # -------------------------------------------------------------
    # Convert the value to text so regex can search consistently.
    # -------------------------------------------------------------
    text_value = str(value).strip()

    # -------------------------------------------------------------
    # Extract the first integer or decimal number found.
    # -------------------------------------------------------------
    match = re.search(r"-?\d+(?:\.\d+)?", text_value)

    if match is None:
        return np.nan

    return float(match.group())


def format_value(value: object) -> str:
    """
    Convert missing values into a consistent text placeholder.

    This keeps the transformer input format stable and readable.
    """
    # -------------------------------------------------------------
    # Missing values are represented explicitly instead of dropped.
    # -------------------------------------------------------------
    if value is None or pd.isna(value):
        return "Unknown"

    return str(value)


def build_model_input(row: pd.Series) -> str:
    """
    Convert one applicant row into a unified text input.

    This combines both text and non-text fields into the same
    human-readable template used for training and inference.
    """
    # -------------------------------------------------------------
    # The target label is intentionally not included in this text.
    # -------------------------------------------------------------
    return (
        f"Program: {format_value(row['program'])}\n"
        f"Comments: {format_value(row['comments'])}\n"
        f"GPA: {format_value(row['gpa'])}\n"
        f"GRE: {format_value(row['gre'])}\n"
        f"GRE Verbal: {format_value(row['gre_v'])}\n"
        f"GRE AW: {format_value(row['gre_aw'])}\n"
        f"Degree: {format_value(row['masters_or_phd'])}\n"
        f"Citizenship: {format_value(row['citizenship'])}"
    )


def load_and_prepare_dataframe(filepath: str) -> pd.DataFrame:
    """Load, clean, and prepare the admissions dataframe."""
    # -------------------------------------------------------------
    # Load newline-delimited JSON admissions data.
    # -------------------------------------------------------------
    df = pd.read_json(filepath, lines=True)

    print("Number of rows in original dataset:")
    print(len(df))

    # -------------------------------------------------------------
    # Keep only Accepted / Rejected rows for binary classification.
    # -------------------------------------------------------------
    df = df[df["applicant_status"].isin(["Accepted", "Rejected"])].copy()

    # -------------------------------------------------------------
    # Remove duplicate entries using URL to reduce repeated examples.
    # -------------------------------------------------------------
    df = df.drop_duplicates(subset=["url"]).copy()

    # -------------------------------------------------------------
    # Normalize text fields into consistent strings.
    # -------------------------------------------------------------
    text_columns = ["program", "comments"]
    for column in text_columns:
        df[column] = df[column].fillna("None").astype(str).str.strip()

    # -------------------------------------------------------------
    # Convert string-encoded numeric fields into real numeric values.
    # -------------------------------------------------------------
    numeric_columns = ["gpa", "gre", "gre_v", "gre_aw"]
    for column in numeric_columns:
        df[column] = df[column].apply(extract_numeric_value)

    # -------------------------------------------------------------
    # Treat non-positive numeric values as invalid placeholders.
    # -------------------------------------------------------------
    df.loc[df["gpa"] <= 0, "gpa"] = np.nan
    df.loc[df["gre"] <= 0, "gre"] = np.nan
    df.loc[df["gre_v"] <= 0, "gre_v"] = np.nan
    df.loc[df["gre_aw"] <= 0, "gre_aw"] = np.nan

    # -------------------------------------------------------------
    # Normalize categorical fields for consistent model input text.
    # -------------------------------------------------------------
    df["masters_or_phd"] = (
        df["masters_or_phd"].fillna("Unknown").astype(str).str.strip()
    )
    df["citizenship"] = df["citizenship"].fillna("Unknown").astype(str).str.strip()

    # -------------------------------------------------------------
    # Create binary target:
    # Accepted = 1, Rejected = 0.
    # -------------------------------------------------------------
    df["label"] = (df["applicant_status"] == "Accepted").astype(int)

    # -------------------------------------------------------------
    # Create one unified text input per applicant.
    # -------------------------------------------------------------
    df["model_input"] = df.apply(build_model_input, axis=1)

    print("\nNumber of rows after filtering and deduplication:")
    print(len(df))

    print("\nAccepted rows:")
    print(int((df["label"] == 1).sum()))

    print("\nRejected rows:")
    print(int((df["label"] == 0).sum()))

    print("\nFull list of fields used for modeling:")
    print(
        [
            "program",
            "comments",
            "gpa",
            "gre",
            "gre_v",
            "gre_aw",
            "masters_or_phd",
            "citizenship",
            "label",
        ]
    )

    print("\nExact unified input template used:")
    print(
        "Program: {program}\n"
        "Comments: {comments}\n"
        "GPA: {gpa}\n"
        "GRE: {gre}\n"
        "GRE Verbal: {gre_v}\n"
        "GRE AW: {gre_aw}\n"
        "Degree: {masters_or_phd}\n"
        "Citizenship: {citizenship}"
    )

    print("\nThree sample unified model inputs:")
    for example_index, model_input in enumerate(df["model_input"].head(3), start=1):
        print(f"\nExample {example_index}:")
        print(model_input)

    return df


class AdmissionsDataset(Dataset):
    """
    PyTorch Dataset for admissions classification.

    Each item contains tokenized applicant text plus the binary label.
    """

    def __init__(
        self,
        dataframe: pd.DataFrame,
        tokenizer: AutoTokenizer,
        max_length: int,
    ) -> None:
        """Store the dataframe, tokenizer, and max sequence length."""
        # -------------------------------------------------------------
        # Reset row indices so PyTorch can access examples by position.
        # -------------------------------------------------------------
        self.dataframe = dataframe.reset_index(drop=True)
        self.tokenizer = tokenizer
        self.max_length = max_length

    def __len__(self) -> int:
        """Return the total number of examples."""
        return len(self.dataframe)

    def __getitem__(self, index: int) -> dict[str, torch.Tensor]:
        """Return one tokenized applicant example and its label."""
        # -------------------------------------------------------------
        # Pull one applicant row.
        # -------------------------------------------------------------
        row = self.dataframe.iloc[index]

        # -------------------------------------------------------------
        # Tokenize the unified text input.
        # -------------------------------------------------------------
        encoded = self.tokenizer(
            row["model_input"],
            truncation=True,
            padding="max_length",
            max_length=self.max_length,
            return_tensors="pt",
        )

        # -------------------------------------------------------------
        # Return tensors expected by Hugging Face sequence classifiers.
        # -------------------------------------------------------------
        return {
            "input_ids": encoded["input_ids"].squeeze(0),
            "attention_mask": encoded["attention_mask"].squeeze(0),
            "labels": torch.tensor(row["label"], dtype=torch.long),
        }


def train_one_epoch(
    model: AutoModelForSequenceClassification,
    train_loader: DataLoader,
    optimizer: AdamW,
    device: torch.device,
) -> float:
    """Train the model for one epoch and return average training loss."""
    # -------------------------------------------------------------
    # Training mode enables dropout and gradient updates.
    # -------------------------------------------------------------
    model.train()
    total_train_loss = 0.0
    total_train_batches = len(train_loader)

    print("\nStarting training loop...")

    for batch_index, batch in enumerate(train_loader, start=1):
        # ---------------------------------------------------------
        # Move tensors to CPU/GPU.
        # ---------------------------------------------------------
        batch = {key: value.to(device) for key, value in batch.items()}

        # ---------------------------------------------------------
        # Clear old gradients.
        # ---------------------------------------------------------
        optimizer.zero_grad()

        # ---------------------------------------------------------
        # Forward pass.
        # ---------------------------------------------------------
        outputs = model(**batch)
        loss = outputs.loss

        # ---------------------------------------------------------
        # Backpropagation and optimizer update.
        # ---------------------------------------------------------
        loss.backward()
        optimizer.step()

        batch_loss = float(loss.item())
        total_train_loss += batch_loss

        # ---------------------------------------------------------
        # Print progress so long CPU runs do not look frozen.
        # ---------------------------------------------------------
        if batch_index % TRAIN_PROGRESS_INTERVAL == 0 or batch_index == total_train_batches:
            print(
                f"Training batch {batch_index}/{total_train_batches} | "
                f"Current batch loss: {batch_loss:.6f}"
            )

    return total_train_loss / total_train_batches


def evaluate_model(
    model: AutoModelForSequenceClassification,
    test_loader: DataLoader,
    device: torch.device,
) -> tuple[float, list[int], list[int], list[float]]:
    """
    Evaluate the model and return loss, true labels, predictions, and probabilities.
    """
    # -------------------------------------------------------------
    # Evaluation mode disables dropout and avoids training behavior.
    # -------------------------------------------------------------
    model.eval()

    total_test_loss = 0.0
    total_test_batches = len(test_loader)

    true_labels: list[int] = []
    predicted_labels: list[int] = []
    accepted_probabilities: list[float] = []

    print("\nStarting evaluation loop...")

    with torch.no_grad():
        for batch_index, batch in enumerate(test_loader, start=1):
            # -----------------------------------------------------
            # Move tensors to the selected device.
            # -----------------------------------------------------
            batch = {key: value.to(device) for key, value in batch.items()}

            # -----------------------------------------------------
            # Run forward pass without gradients.
            # -----------------------------------------------------
            outputs = model(**batch)
            loss = outputs.loss
            logits = outputs.logits

            # -----------------------------------------------------
            # Convert logits into probabilities using softmax.
            # Column 1 is probability-like score for Accepted.
            # -----------------------------------------------------
            probabilities = torch.softmax(logits, dim=1)
            predictions = torch.argmax(probabilities, dim=1)

            total_test_loss += float(loss.item())

            true_labels.extend(batch["labels"].cpu().tolist())
            predicted_labels.extend(predictions.cpu().tolist())
            accepted_probabilities.extend(probabilities[:, 1].cpu().tolist())

            # -----------------------------------------------------
            # Print progress for long CPU evaluation loops.
            # -----------------------------------------------------
            if batch_index % TEST_PROGRESS_INTERVAL == 0 or batch_index == total_test_batches:
                print(
                    f"Evaluation batch {batch_index}/{total_test_batches} | "
                    f"Current batch loss: {float(loss.item()):.6f}"
                )

    average_test_loss = total_test_loss / total_test_batches

    return average_test_loss, true_labels, predicted_labels, accepted_probabilities


def print_evaluation_summary(
    test_df: pd.DataFrame,
    true_labels: list[int],
    predicted_labels: list[int],
    accepted_probabilities: list[float],
) -> None:
    """Print required evaluation metrics and example predictions."""
    # -------------------------------------------------------------
    # Compute classification metrics required by the assignment.
    # -------------------------------------------------------------
    accuracy = accuracy_score(true_labels, predicted_labels)
    precision = precision_score(true_labels, predicted_labels, zero_division=0)
    recall = recall_score(true_labels, predicted_labels, zero_division=0)
    f1 = f1_score(true_labels, predicted_labels, zero_division=0)
    matrix = confusion_matrix(true_labels, predicted_labels)

    print("\nFinal Model Evaluation Metrics")
    print(f"Accuracy:  {accuracy:.4f}")
    print(f"Precision: {precision:.4f}")
    print(f"Recall:    {recall:.4f}")
    print(f"F1 Score:  {f1:.4f}")

    print("\nConfusion Matrix")
    print("Rows = Actual, Columns = Predicted")
    print(matrix)

    print("\nClass distribution in test set:")
    print(pd.Series(true_labels).value_counts(normalize=True).sort_index())

    # -------------------------------------------------------------
    # Build a small dataframe for reviewing example predictions.
    # -------------------------------------------------------------
    results_df = test_df.reset_index(drop=True).copy()
    results_df["true_label"] = true_labels
    results_df["predicted_label"] = predicted_labels
    results_df["accepted_probability"] = accepted_probabilities

    results_df["true_status"] = np.where(
        results_df["true_label"] == 1,
        "Accepted",
        "Rejected",
    )
    results_df["predicted_status"] = np.where(
        results_df["predicted_label"] == 1,
        "Accepted",
        "Rejected",
    )

    print("\nProbability Examples")
    print(
        results_df[
            [
                "program",
                "true_status",
                "predicted_status",
                "accepted_probability",
            ]
        ]
        .head(5)
        .to_string(index=False)
    )

    print("\nCorrectly Classified Examples")
    correct_examples = results_df[results_df["true_label"] == results_df["predicted_label"]]
    print(
        correct_examples[
            [
                "program",
                "true_status",
                "predicted_status",
                "accepted_probability",
            ]
        ]
        .head(3)
        .to_string(index=False)
    )

    print("\nIncorrectly Classified Examples")
    incorrect_examples = results_df[results_df["true_label"] != results_df["predicted_label"]]
    print(
        incorrect_examples[
            [
                "program",
                "true_status",
                "predicted_status",
                "accepted_probability",
            ]
        ]
        .head(3)
        .to_string(index=False)
    )

    print("\nEvaluation Interpretation")
    print(
        "The model is compared against a held-out test set that was not used "
        "during training. Accuracy, precision, recall, F1, and the confusion "
        "matrix help show whether the model is learning meaningful patterns "
        "or leaning too heavily toward one class."
    )


def main() -> None:
    """Run preprocessing, fine-tuning, and final evaluation."""
    # -------------------------------------------------------------
    # Load and prepare the data.
    # -------------------------------------------------------------
    df = load_and_prepare_dataframe(
        "../module_6/src/llm_extend_applicant_data.json"
    )

    # -------------------------------------------------------------
    # Create stratified train/test split.
    # -------------------------------------------------------------
    train_df, test_df = train_test_split(
        df,
        test_size=0.2,
        random_state=42,
        shuffle=True,
        stratify=df["label"],
    )

    print("\nTraining set size:")
    print(len(train_df))

    print("\nTest set size:")
    print(len(test_df))

    print("\nClass balance in training set:")
    print(train_df["label"].value_counts(normalize=True).sort_index())

    print("\nClass balance in test set:")
    print(test_df["label"].value_counts(normalize=True).sort_index())

    print("\nWhy train/test separation matters:")
    print(
        "Train/test separation prevents us from evaluating the model on the "
        "same examples it learned from. This is especially important for a "
        "public-facing admissions webpage, because the deployed model should "
        "be judged on unseen examples rather than memorized ones."
    )

    # -------------------------------------------------------------
    # Load tokenizer and create datasets / dataloaders.
    # -------------------------------------------------------------
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)

    train_dataset = AdmissionsDataset(train_df, tokenizer, MAX_LENGTH)
    test_dataset = AdmissionsDataset(test_df, tokenizer, MAX_LENGTH)

    train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True)
    test_loader = DataLoader(test_dataset, batch_size=BATCH_SIZE, shuffle=False)

    # -------------------------------------------------------------
    # Select CPU or GPU.
    # -------------------------------------------------------------
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    print("\nChosen model:")
    print(MODEL_NAME)

    print("\nChosen tokenizer:")
    print(MODEL_NAME)

    print("\nMaximum sequence length:")
    print(MAX_LENGTH)

    print("\nBatch size:")
    print(BATCH_SIZE)

    print("\nDevice used:")
    print(device)

    # -------------------------------------------------------------
    # Load pretrained model with binary classification head.
    # -------------------------------------------------------------
    model = AutoModelForSequenceClassification.from_pretrained(
        MODEL_NAME,
        num_labels=2,
    )
    model.to(device)

    # -------------------------------------------------------------
    # Create optimizer for fine-tuning.
    # -------------------------------------------------------------
    optimizer = AdamW(model.parameters(), lr=LEARNING_RATE)

    print("\nLearning rate:")
    print(LEARNING_RATE)

    print("\nEpochs:")
    print(EPOCHS)

    print("\nOptimizer:")
    print("AdamW")

    # -------------------------------------------------------------
    # Train for the configured number of epochs.
    # -------------------------------------------------------------
    for epoch in range(1, EPOCHS + 1):
        print(f"\nEpoch {epoch}/{EPOCHS}")
        average_train_loss = train_one_epoch(model, train_loader, optimizer, device)
        print(f"Average training loss after epoch {epoch}: {average_train_loss:.6f}")

    # -------------------------------------------------------------
    # Evaluate after training.
    # -------------------------------------------------------------
    average_test_loss, true_labels, predicted_labels, accepted_probabilities = evaluate_model(
        model,
        test_loader,
        device,
    )

    print("\nRepresentative training output:")
    print(f"Average test loss after training: {average_test_loss:.6f}")

    print_evaluation_summary(
        test_df=test_df,
        true_labels=true_labels,
        predicted_labels=predicted_labels,
        accepted_probabilities=accepted_probabilities,
    )

    save_and_reload_model(
        model=model,
        tokenizer=tokenizer,
        device=device,
    )

def save_and_reload_model(
    model: AutoModelForSequenceClassification,
    tokenizer: AutoTokenizer,
    device: torch.device,
) -> None:
    """Save the trained model, reload it, and test inference on two examples."""
    # -------------------------------------------------------------
    # Save the fine-tuned model and tokenizer so the website can use
    # them later without retraining.
    # -------------------------------------------------------------
    save_directory = "saved_admissions_model"

    model.save_pretrained(save_directory)
    tokenizer.save_pretrained(save_directory)

    print("\nSaved Model")
    print(f"Model and tokenizer saved to: {save_directory}")

    # -------------------------------------------------------------
    # Reload the saved model and tokenizer from disk.
    # This proves that inference can happen later without retraining.
    # -------------------------------------------------------------
    reloaded_tokenizer = AutoTokenizer.from_pretrained(save_directory)
    reloaded_model = AutoModelForSequenceClassification.from_pretrained(
        save_directory
    )
    reloaded_model.to(device)
    reloaded_model.eval()

    print("\nReloaded Model")
    print("Reloaded model and tokenizer successfully.")

    # -------------------------------------------------------------
    # Create two realistic examples for post-reload inference.
    # These examples use the same unified input format as training.
    # -------------------------------------------------------------
    inference_examples = [
        (
            "Program: Computer Science, Johns Hopkins University\n"
            "Comments: Strong programming background and AI research experience.\n"
            "GPA: 3.90\n"
            "GRE: 330\n"
            "GRE Verbal: 162\n"
            "GRE AW: 4.5\n"
            "Degree: PhD\n"
            "Citizenship: International"
        ),
        (
            "Program: English, State University\n"
            "Comments: Interested in literature and teaching.\n"
            "GPA: 3.20\n"
            "GRE: Unknown\n"
            "GRE Verbal: Unknown\n"
            "GRE AW: Unknown\n"
            "Degree: Masters\n"
            "Citizenship: American"
        ),
    ]

    print("\nReloaded Model Inference Examples")

    # -------------------------------------------------------------
    # Run prediction for each example.
    # -------------------------------------------------------------
    with torch.no_grad():
        for example_index, example_text in enumerate(inference_examples, start=1):
            encoded = reloaded_tokenizer(
                example_text,
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

            outputs = reloaded_model(**encoded)
            probabilities = torch.softmax(outputs.logits, dim=1)

            accepted_probability = float(probabilities[0, 1].cpu())
            predicted_label = int(torch.argmax(probabilities, dim=1).cpu())
            predicted_status = "Accepted" if predicted_label == 1 else "Rejected"

            print(f"\nExample {example_index}")
            print(example_text)
            print(f"Predicted probability of Accepted: {accepted_probability:.4f}")
            print(f"Predicted label: {predicted_label}")
            print(f"Predicted status: {predicted_status}")

if __name__ == "__main__":
    main()
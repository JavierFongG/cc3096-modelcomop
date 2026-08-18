import os

import numpy as np
import pandas as pd
import streamlit as st

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
TEST_LABELS_PATH = os.path.join(DATA_DIR, "test_labels.csv")
RESULTS_PATH = os.path.join(DATA_DIR, "submissions.xlsx")

st.set_page_config(page_title="Predictions RMSE Leaderboard", layout="centered")
st.title("Predictions RMSE Leaderboard")


def load_results() -> pd.DataFrame:
    if os.path.exists(RESULTS_PATH):
        return pd.read_excel(RESULTS_PATH)
    return pd.DataFrame(columns=["Submitter", "RMSE", "Timestamp"])


def save_results(df: pd.DataFrame) -> None:
    df.to_excel(RESULTS_PATH, index=False)


def compute_rmse(predictions_df: pd.DataFrame) -> float:
    test_labels = pd.read_csv(TEST_LABELS_PATH)

    merged = test_labels.merge(predictions_df, on="Id", how="inner")
    if merged.empty:
        raise ValueError("No matching Ids found between predictions.csv and test_labels.csv.")

    errors = merged["Prediction"] - merged["SalePrice"]
    return float(np.sqrt(np.mean(errors ** 2)))


submitter = st.text_input("Submit Identifier (e.g. your name)")
uploaded_file = st.file_uploader("Upload predictions.csv", type="csv")

submit_disabled = not submitter or uploaded_file is None
if not submitter:
    st.caption("Enter a submit identifier before submitting.")

if st.button("Submit", disabled=submit_disabled):
    try:
        predictions_df = pd.read_csv(uploaded_file)
        missing_cols = {"Id", "Prediction"} - set(predictions_df.columns)
        if missing_cols:
            raise ValueError(f"predictions.csv is missing required columns: {', '.join(sorted(missing_cols))}")

        rmse = compute_rmse(predictions_df)

        results_df = load_results()
        new_row = pd.DataFrame(
            [{
                "Submitter": submitter,
                "RMSE": rmse,
                "Timestamp": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
            }]
        )
        results_df = pd.concat([results_df, new_row], ignore_index=True)
        save_results(results_df)

        st.success(f"Submission recorded. RMSE = {rmse:,.4f}")
    except Exception as e:
        st.error(f"Failed to process submission: {e}")

st.subheader("Leaderboard")
if not os.path.exists(RESULTS_PATH):
    st.info("No submissions yet.")
else:
    with open(RESULTS_PATH, "rb") as f:
        st.download_button(
            "Download submissions.xlsx",
            data=f.read(),
            file_name="submissions.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

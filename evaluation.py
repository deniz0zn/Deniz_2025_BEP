import pandas as pd
import random
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from config import __RANDOM_SEED__

class CompletenessEvaluator:
    def __init__(self, event_log_path, case_output_path):
        """
        Initialize the CompletenessEvaluator with paths to the event log and case output CSVs.

        :param event_log_path: Path to the original event log file (event-level granularity).
        :param case_output_path: Path to the case output file (case-level completeness results).
        """
        self.event_log = pd.read_csv(event_log_path)
        self.event_log.rename(columns={"case": "case_id"}, inplace=True)  # Standardize column name
        self.case_output = pd.read_csv(case_output_path)
        self.critical_events = ["BILLED", "FIN", "RELEASE", "CODE OK"]  # Define critical events here

    def has_critical_events(self, case_id):
        """
        Check if a case has all critical events in the event log.

        :param case_id: The ID of the case to check.
        :return: True if the case has all critical events, False otherwise.
        """
        case_events = self.event_log[self.event_log["case_id"] == case_id]["event"].unique()
        return all(event in case_events for event in self.critical_events)

    def sample_cases(self, sample_size):
        """
        Randomly sample cases from the event log and retrieve their events.

        :param sample_size: Number of unique cases to sample.
        :return: A DataFrame containing all events for the sampled cases.
        """
        random.seed(__RANDOM_SEED__)
        sampled_case_ids = random.sample(self.event_log["case_id"].unique().tolist(), sample_size)
        sampled_events = self.event_log[self.event_log["case_id"].isin(sampled_case_ids)]
        return sampled_events, sampled_case_ids

    def manually_label_cases(self, sampled_events):
        """
        Manually label sampled cases as complete or incomplete based on domain rules.

        :param sampled_events: DataFrame containing events for sampled cases.
        :return: A DataFrame with manually labeled cases.
        """
        # Get the last event for each case
        last_events = sampled_events.sort_values(by="completeTime").groupby("case_id").last()

        # Label cases manually based on rules
        last_events["complete"] = last_events.apply(
            lambda row: row["state"] == "Billed" and self.has_critical_events(row.name) and not row["isCancelled"], axis=1
        )

        return last_events.reset_index()

    def evaluate_predictions(self, sampled_case_ids, manually_labeled_cases):
        """
        Evaluate the rule-based predictions against manually labeled cases.

        :param sampled_case_ids: List of sampled case IDs.
        :param manually_labeled_cases: DataFrame containing manually labeled cases.
        :return: Evaluate metrics (accuracy, precision, recall, F1-score).
        """
        # Extract the predictions from the case output log for the sampled cases
        predictions = self.case_output[self.case_output["case_id"].isin(sampled_case_ids)]

        # Merge predictions with manual labels
        merged = pd.merge(predictions, manually_labeled_cases, on="case_id", suffixes=("_predicted", "_manual"))

        # Ensure columns exist
        if "isComplete_manual" not in merged.columns or "isComplete_predicted" not in merged.columns:
            raise ValueError("Required columns for evaluation are missing in the merged dataset.")

        # Extract ground truth and predictions
        y_true = merged["isComplete_manual"].astype(int)  # Convert to binary (0/1)
        y_pred = merged["isComplete_predicted"].astype(int)  # Convert to binary (0/1)

        # Calculate evaluation metrics
        metrics = {
            "accuracy": accuracy_score(y_true, y_pred),
            "precision": precision_score(y_true, y_pred),
            "recall": recall_score(y_true, y_pred),
            "f1_score": f1_score(y_true, y_pred)
        }
        return metrics

    def generate_report(self, metrics):
        """
        Generate a report summarizing the evaluation.

        :param metrics: Dictionary of evaluation metrics.
        :return: A string report summarizing the results.
        """
        report = (
            f"Evaluate Report:\n"
            f"-------------------\n"
            f"Accuracy: {metrics['accuracy']:.2f}\n"
            f"Precision: {metrics['precision']:.2f}\n"
            f"Recall: {metrics['recall']:.2f}\n"
            f"F1 Score: {metrics['f1_score']:.2f}\n"
        )
        return report




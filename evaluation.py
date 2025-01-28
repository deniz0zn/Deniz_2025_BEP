import pandas as pd
import ast

from matplotlib import pyplot as plt
import seaborn as sns
from config import test_eval

def evaluate(delta_stats: pd.DataFrame, case_stats: pd.DataFrame) -> pd.DataFrame:
    case_dict = case_stats[["case_id", "final_status"]].set_index("case_id").to_dict()["final_status"]
    delta_stats = delta_stats[["delta_file_name", "complete_cases", "incomplete_cases", "complete_count", "incomplete_count"]]
    evaluation_metrics = {
        "Delta": [],
        "TP": [],
        "FP": [],
        "TN": [],
        "FN": [],
        "Accuracy": [],
        "Precision": [],
        "Recall": [],
        "F1-Score": [],
        "Traces Classified": []
    }

    for delta_index, delta_row in delta_stats.iterrows():
        delta_id = delta_row["delta_file_name"]
        complete_case_ids = set(delta_row["complete_cases"])
        incomplete_case_ids = set(delta_row["incomplete_cases"])

        tp, fp, tn, fn = 0, 0, 0, 0
        for case_id in complete_case_ids:
            if case_dict.get(case_id) == "COMPLETE":
                tp += 1
            else:
                fp += 1
        for case_id in incomplete_case_ids:
            if case_dict.get(case_id) == "INCOMPLETE":
                tn += 1
            else:
                fn += 1

        total_cases = tp + fp + tn + fn
        accuracy = round((tp + tn) / total_cases, 2) if total_cases else 0.0
        precision = round(tp / (tp + fp), 2) if (tp + fp) else 0.0
        recall = round(tp / (tp + fn), 2) if (tp + fn) else 0.0
        f1_score = round((2 * precision * recall) / (precision + recall), 2) if (precision + recall) else 0.0

        evaluation_metrics["Delta"].append(delta_id)
        evaluation_metrics["TP"].append(tp)
        evaluation_metrics["FP"].append(fp)
        evaluation_metrics["TN"].append(tn)
        evaluation_metrics["FN"].append(fn)
        evaluation_metrics["Accuracy"].append(accuracy)
        evaluation_metrics["Precision"].append(precision)
        evaluation_metrics["Recall"].append(recall)
        evaluation_metrics["F1-Score"].append(f1_score)
        evaluation_metrics["Traces Classified"].append(total_cases)

    evaluation_df = pd.DataFrame(evaluation_metrics)


    # plt.figure(figsize=(12, 6))
    # evaluation_df["Traces Classified"].plot(kind="bar")
    # plt.show()

    return evaluation_df


def calculate_weighted_metrics(evaluation_df: pd.DataFrame) -> dict:
    """Calculate weighted macro average for Accuracy, Precision, Recall, and F1-Score."""

    total_cases = evaluation_df["Traces Classified"].sum()
    weighted_accuracy = (
        evaluation_df["Accuracy"].multiply(evaluation_df["Traces Classified"]).sum() / total_cases
        if total_cases else 0
    )
    weighted_precision = (
        evaluation_df["Precision"].multiply(evaluation_df["Traces Classified"]).sum() / total_cases
        if total_cases else 0
    )
    weighted_recall = (
        evaluation_df["Recall"].multiply(evaluation_df["Traces Classified"]).sum() / total_cases
        if total_cases else 0
    )
    weighted_f1 = (
        evaluation_df["F1-Score"].multiply(evaluation_df["Traces Classified"]).sum() / total_cases
        if total_cases else 0
    )

    return {
        "Weighted Accuracy": round(weighted_accuracy, 2),
        "Weighted Precision": round(weighted_precision, 2),
        "Weighted Recall": round(weighted_recall, 2),
        "Weighted F1-Score": round(weighted_f1, 2),
    }


def avg_cm_per_delta(evaluation_df: pd.DataFrame, save_path: str):
    """
    Calculate weighted averages of TP, FP, TN, FN and plot the confusion matrix.

    Args:
        evaluation_df (pd.DataFrame): DataFrame containing evaluation metrics for deltas.
        save_path (str): Path to save the confusion matrix plot.
    """

    tp = round(evaluation_df["TP"].sum() / len(evaluation_df), 0)
    fp = round(evaluation_df["FP"].sum() / len(evaluation_df), 0)
    tn = round(evaluation_df["TN"].sum() / len(evaluation_df), 0)
    fn = round(evaluation_df["FN"].sum() / len(evaluation_df), 0)

    matrix = [
        [tp, fn],
        [fp, tn]
    ]
    labels = ["Complete", "Incomplete"]

    plt.figure(figsize=(8, 6))
    sns.heatmap(
        matrix,
        annot=True,
        cmap="Blues",
        fmt= '.0f',
        xticklabels=labels,
        yticklabels=labels,
        cbar=True
    )
    plt.title("Expected Confusion Matrix per Delta")
    plt.xlabel("Predicted Labels")
    plt.ylabel("True Labels")
    plt.tight_layout()
    plt.savefig(save_path)
    plt.close()

    print("\n AVG. Confusion Matrix Values:")
    print(f"TP: {tp}, FN: {fn}")
    print(f"FP: {fp}, TN: {tn}")

    total_cases = tp + fp + tn + fn
    accuracy = round((tp + tn) / total_cases, 2) if total_cases else 0.0
    precision = round(tp / (tp + fp), 2) if (tp + fp) else 0.0
    recall = round(tp / (tp + fn), 2) if (tp + fn) else 0.0
    f1_score = round((2 * precision * recall) / (precision + recall), 2) if (precision + recall) else 0.0

    # print(f"\nMetrics Calculated by Avg. of TP, FP, TN, FN"
    #       f"\nAccuracy: {accuracy}\n"
    #       f"Precision: {precision}\n"
    #       f"Recal: {recall}\n"
    #       f"F1 Score: {f1_score}\n")


# def calculate_and_plot_weighted_confusion_matrix(evaluation_df: pd.DataFrame, save_path: str):
#     """
#     Calculate weighted averages of TP, FP, TN, FN and plot the confusion matrix.
#
#     Args:
#         evaluation_df (pd.DataFrame): DataFrame containing evaluation metrics for deltas.
#         save_path (str): Path to save the confusion matrix plot.
#     """
#     total_cases = evaluation_df["Traces Classified"].sum()
#
#     # Calculate weighted confusion matrix values
#     weighted_tp = (
#         evaluation_df["TP"].multiply(evaluation_df["Traces Classified"]).sum() / total_cases)
#     weighted_fp = (
#         evaluation_df["FP"].multiply(evaluation_df["Traces Classified"]).sum() / total_cases)
#     weighted_tn = (
#         evaluation_df["TN"].multiply(evaluation_df["Traces Classified"]).sum() / total_cases)
#     weighted_fn = (
#         evaluation_df["FN"].multiply(evaluation_df["Traces Classified"]).sum() / total_cases)
#
#     # Prepare confusion matrix for plotting
#     matrix = [
#         [weighted_tp, weighted_fn],
#         [weighted_fp, weighted_tn]
#     ]
#     labels = ["Positive (Complete)", "Negative (Incomplete)"]
#
#     # Plot the confusion matrix
#     plt.figure(figsize=(8, 6))
#     sns.heatmap(
#         matrix,
#         annot=True,
#         fmt=".0f",
#         cmap="Blues",
#         xticklabels=labels,
#         yticklabels=labels,
#         cbar=True
#     )
#     plt.title("Weighted Confusion Matrix")
#     plt.xlabel("Predicted Labels")
#     plt.ylabel("True Labels")
#     plt.tight_layout()
#     plt.savefig(save_path)
#     plt.close()
#
#     # Print weighted confusion matrix values
#     print("\nWeighted Confusion Matrix Values:")
#     print(f"TP: {weighted_tp:.2f}, FN: {weighted_fn:.2f}")
#     print(f"FP: {weighted_fp:.2f}, TN: {weighted_tn:.2f}")
#
#     tp, fp, tn, fn = weighted_tp, weighted_fp, weighted_tn, weighted_fn
#     total_cases = tp + fp + tn + fn
#     accuracy = round((tp + tn) / total_cases, 2) if total_cases else 0.0
#     precision = round(tp / (tp + fp), 2) if (tp + fp) else 0.0
#     recall = round(tp / (tp + fn), 2) if (tp + fn) else 0.0
#     f1_score = round((2 * precision * recall) / (precision + recall), 2) if (precision + recall) else 0.0
#
#     print(f"\nMetrics Calculated by Weighted Macro Avg. of TP, FP, TN, FN"
#           f"\nAccuracy: {accuracy}\n"
#           f"Precision: {precision}\n"
#           f"Recal: {recall}\n"
#           f"F1 Score: {f1_score}\n")

if test_eval:
    deltas = pd.read_csv("Dataset/Hospital Billing Delta Logs/Delta Stats/delta_stats_weekly_(1).csv",
                         keep_default_na=False,
                         na_values=['NaN', "", " "],
                         converters = {"complete_cases": ast.literal_eval,"incomplete_cases": ast.literal_eval,})
    cases = pd.read_csv("Dataset/Hospital Billing Delta Logs/cases_output/cases_output_weekly_(1).csv")

    evaluation_df = evaluate(deltas, cases)
    weighted_metrics = calculate_weighted_metrics(evaluation_df)

    print("\nWeighted Metrics:")
    for metric, value in weighted_metrics.items():
        print(f"{metric}: {value:.2f}")

    avg_cm_per_delta(evaluation_df, "VIS/confusion_matrix.png")





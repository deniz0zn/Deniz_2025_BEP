import pm4py
import os

def load_xes_file(xes_file_path):
    """Load an XES file and return the DataFrame."""
    log = pm4py.read_xes(xes_file_path)
    return log


def save_to_csv(log, csv_output_path):
    """Save the DataFrame (log) to a CSV file."""
    # Inspect the log to check its structure
    print("Log structure:", log.columns)
    print(log.head())  # Print the first few rows to see the structure

    # Save the DataFrame as CSV directly
    log.to_csv(csv_output_path, index=False)
    print(f"Event log saved to {csv_output_path}")


if __name__ == "__main__":
    xes_file_path = "Dataset/xes/BPI_Challenge_2019.xes"
    filename = os.path.splitext(os.path.basename(xes_file_path))[0]
    csv_output_path = f"Dataset/csv/{filename}.csv"
    log = load_xes_file(xes_file_path)
    save_to_csv(log, csv_output_path)

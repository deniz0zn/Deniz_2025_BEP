import os
import pandas as pd
from datetime import timedelta
import pm4py
from xes_to_csv import load_xes_file, save_to_csv


def split_event_log_from_xes(xes_file_path, frequency='weekly', initial_months=3, start_date=None, end_date=None):
    """
    Splits an XES event log into an initial log and delta logs based on the chosen frequency, with optional filtering by date.

    :param xes_file_path: Path to the XES file containing the event log data.
    :param frequency: Splitting frequency ('daily', 'weekly', 'monthly').
    :param initial_months: Number of months to include in the initial log.
    :param start_date: Optional start date for filtering the event log (format 'YYYY-MM').
    :param end_date: Optional end date for filtering the event log (format 'YYYY-MM').
    """
    # Extract the filename without extension from the XES file path
    filename = os.path.splitext(os.path.basename(xes_file_path))[0]

    # Import the XES log file and convert it to a pandas DataFrame
    csv_path = f"Dataset/csv/{filename}.csv"
    if not os.path.isfile(csv_path):
        print("Extracting logs and saving as csv...")
        log = load_xes_file(xes_file_path)
        save_to_csv(log, csv_path)
    else:
        print("csv already exists.")
    df = pd.read_csv(csv_path)

    # Ensure the timestamp column is in datetime format and remove timezone info
    df['completeTime'] = pd.to_datetime(df['completeTime']).dt.tz_localize(None)  # Remove timezone information

    # Filter the event log based on start_date and end_date, if provided
    if start_date is not None and start_date.lower() != "none":
        df = df[df['completeTime'] >= pd.to_datetime(start_date)]

    if end_date is not None and end_date.lower() != "none":
        df = df[df['completeTime'] <= pd.to_datetime(end_date)]

    # Set the initial log based on the first `initial_months` months from the filtered log
    if not df.empty:
        initial_cutoff = df['completeTime'].min() + pd.DateOffset(months=initial_months)
        initial_log = df[df['completeTime'] < initial_cutoff]
    else:
        print("Filtered event log is empty. Please check the date range.")
        return

    # Save the initial log
    output_dir = f"Dataset/Hospital Billing Delta Logs/{filename}_{frequency}_({initial_months})"
    os.makedirs(output_dir, exist_ok=True)
    initial_log_path = os.path.join(output_dir, f"{filename}_initial_log.csv")
    initial_log.to_csv(initial_log_path, index=False)
    print(f"Initial log saved to: {initial_log_path}")

    # Filter the remaining events for the delta logs
    delta_logs = df[df['completeTime'] >= initial_cutoff]

    # Split based on frequency
    if frequency == 'daily':
        delta_logs['delta_period'] = delta_logs['completeTime'].dt.date  # Group by day
    elif frequency == 'weekly':
        delta_logs['delta_period'] = delta_logs['completeTime'].dt.to_period('W')  # Group by week
    elif frequency == 'monthly':
        delta_logs['delta_period'] = delta_logs['completeTime'].dt.to_period('M')  # Group by month
    else:
        raise ValueError("Frequency must be 'daily', 'weekly', or 'monthly'.")

    # Group the delta logs by the specified period and save each group
    for period, group in delta_logs.groupby('delta_period'):
        period_str = str(period).replace('/', '_')  # Format the period string for the filename
        delta_log_path = os.path.join(output_dir, f"{filename}_delta_log_{period_str}.csv")
        group.to_csv(delta_log_path, index=False)
        print(f"Delta log for {period} saved to: {delta_log_path}")





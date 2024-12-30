import os
import pandas as pd
from datetime import timedelta

def split_event_log(csv_file_path, frequency='weekly', initial_months=3):
    """
    Splits a CSV event log into an initial log and delta logs based on the chosen frequency.

    :param csv_file_path: Path to the CSV file containing the event log data.
    :param frequency: Splitting frequency ('daily', 'weekly', 'monthly').
    :param initial_months: Number of months to include in the initial log.
    """
    filename = os.path.splitext(os.path.basename(csv_file_path))[0]
    df = pd.read_csv(csv_file_path)
    df['completeTime'] = pd.to_datetime(df['completeTime']).dt.tz_localize(None)  # Remove timezone information


    if not df.empty:
        initial_cutoff = df['completeTime'].min() + pd.DateOffset(months=initial_months)
        initial_log = df[df['completeTime'] < initial_cutoff]
    else:
        print("Event log is empty. Please check the input file.")
        return

    # Save the initial log
    output_dir = f"Dataset/Hospital Billing Delta Logs/{filename}_{frequency}_({initial_months})"
    os.makedirs(output_dir, exist_ok=True)
    initial_log_path = os.path.join(output_dir, f"initial_log.csv")
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
        if frequency == 'weekly':
            # Format the period as "YYYY_wXX" for weekly frequency
            year = period.start_time.year
            week = period.start_time.isocalendar()[1]
            period_str = f"{year}_w{week:02}"
        else:
            # Use default period string for daily or monthly
            period_str = str(period).replace('/', '_')

        delta_log_path = os.path.join(output_dir, f"{period_str}_delta_log.csv")
        group.to_csv(delta_log_path, index=False)
        print(f"Delta log for {period_str} saved to: {delta_log_path}")

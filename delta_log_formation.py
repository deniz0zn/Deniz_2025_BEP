import os
import pandas as pd
from datetime import timedelta
from config import delta_dir_path


class EventLogSplitter:
    def __init__(self, csv_file_path, frequency='weekly', initial_months=3):
        """
        Initializes the EventLogSplitter with file path, frequency, and initial months.

        :param csv_file_path: Path to the CSV file containing the event log data.
        :param frequency: Splitting frequency ('daily', 'weekly', 'monthly').
        :param initial_months: Number of months to include in the initial log.
        """
        self.csv_file_path = csv_file_path
        self.frequency = frequency
        self.initial_months = initial_months
        self.filename = os.path.splitext(os.path.basename(csv_file_path))[0]
        self.output_dir = f"{delta_dir_path}{self.filename}_{frequency}_({initial_months})"
        self.dataframe = None

    def load_and_sort_event_log(self):
        """Loads and sorts the event log by 'completeTime'."""
        self.dataframe = pd.read_csv(self.csv_file_path, keep_default_na=False, na_values=['NaN', "", " "])
        self.dataframe["case"] = self.dataframe["case"].astype(str)

        

        self.dataframe['completeTime'] = pd.to_datetime(self.dataframe['completeTime']).dt.tz_localize(None)
        self.dataframe = self.dataframe.sort_values(by='completeTime')
        print("Event log loaded and sorted by 'completeTime'.")

    def split_initial_and_delta_logs(self):
        """Splits the event log into an initial log and delta logs."""
        if self.dataframe is None:
            raise ValueError("Event log is not loaded. Please call load_and_sort_event_log() first.")

        # Define initial and delta logs
        initial_cutoff = self.dataframe['completeTime'].min() + pd.DateOffset(months=self.initial_months)
        initial_log = self.dataframe[self.dataframe['completeTime'] < initial_cutoff]
        delta_logs = self.dataframe[self.dataframe['completeTime'] >= initial_cutoff]

        # Save initial log
        os.makedirs(self.output_dir, exist_ok=True)
        initial_log_path = os.path.join(self.output_dir, "initial_log.csv")
        initial_log.to_csv(initial_log_path, index=False)
        print(f"Initial log saved to: {initial_log_path}")

        return delta_logs

    def save_delta_logs(self, delta_logs):
        """Splits and saves delta logs based on the specified frequency."""
        if self.frequency == 'daily':
            delta_logs['delta_period'] = delta_logs['completeTime'].dt.date
        elif self.frequency == 'weekly':
            delta_logs['delta_period'] = delta_logs['completeTime'].dt.to_period('W')
        elif self.frequency == 'monthly':
            delta_logs['delta_period'] = delta_logs['completeTime'].dt.to_period('M')
        else:
            raise ValueError("Frequency must be 'daily', 'weekly', or 'monthly'.")

        for period, group in delta_logs.groupby('delta_period'):
            if self.frequency == 'weekly':
                # Correctly determine year and week based on the ISO week date system
                first_date = group['completeTime'].iloc[0]
                year, week, _ = first_date.isocalendar()
                period_str = f"{year}_w{week:02}"
            else:
                # Use default period string for daily or monthly
                period_str = str(period).replace('/', '_')

            delta_log_path = os.path.join(self.output_dir, f"{period_str}_delta_log.csv")
            group.to_csv(delta_log_path, index=False)
            print(f"Delta log for {period_str} saved to: {delta_log_path}")

    def run_splitting(self):
        """Executes the full splitting process."""
        self.load_and_sort_event_log()
        delta_logs = self.split_initial_and_delta_logs()
        self.save_delta_logs(delta_logs)

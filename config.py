import os

event_log_path = 'Dataset/csv/Hospital Billing - Event Log.csv'
initial_months = 1
frequency = 'weekly'  # 'daily', 'weekly', or 'monthly'

filename = os.path.splitext(os.path.basename(event_log_path))[0]
delta_log_dir = f'Dataset/Hospital Billing Delta Logs/{filename}_{frequency}_({initial_months})'

delta_dir_path = "Dataset/Hospital Billing Delta Logs/"
cases_output_path = f"Dataset/Hospital Billing Delta Logs/cases_output/cases_output_{frequency}_({initial_months}).csv"
delta_output_path = f"Dataset/Hospital Billing Delta Logs/Delta Stats/delta_stats_{frequency}_({initial_months}).csv"
evaluation_output_path = f"Dataset/Hospital Billing Delta Logs/evaluation/eval_{frequency}_({initial_months}).csv"

max_days = 190

sample_size = 100
__RANDOM_SEED__ = 31

test_eval = True  # DEFAULT: False

attributes_to_check = ["case", "event", "startTime", "completeTime",
                       "isCancelled", "blocked", "isClosed", "state"
                       ]

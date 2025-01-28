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

# Run the evaluation without running the model
# Change it to True only if the case_output and delta_stat datasets exist
test_eval = False


# Filters the Delta Logs you would like to observe before plotting the visualizations
focus_deltas = [] # ["2013_w46", "2013_w47", "2013_w48", "2013_w49", "2013_w50"]

attributes_for_miss_check = ["case", "event", "startTime", "completeTime",
                             "isCancelled", "blocked", "isClosed", "state",
                             ]



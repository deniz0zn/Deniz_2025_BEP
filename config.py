import os

dataset_path = 'Dataset/csv/Hospital Billing - Event Log.csv'
initial_months = 12
frequency = 'weekly'  # 'daily', 'weekly', or 'monthly'

filename = os.path.splitext(os.path.basename(dataset_path))[0]
output_dir = f'Dataset/Hospital Billing Delta Logs/{filename}_{frequency}_({initial_months})'

delta_dir_path = "Dataset/Hospital Billing Delta Logs/"
cases_output_path = f"Dataset/Hospital Billing Delta Logs/cases_output/cases_output_{filename}_{frequency}_({initial_months}).csv"
delta_output_path = f"Dataset/Hospital Billing Delta Logs/Delta Stats/delta_stats_{filename}_{frequency}_({initial_months}).csv"

max_days = 190
sample_size = 500
__RANDOM_SEED__ = 420

Evaluate = True
Plot = True

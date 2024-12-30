import os

dataset_path = 'Dataset/csv/Hospital Billing - Event Log.csv'
initial_months = 8
frequency = 'weekly'  # 'daily', 'weekly', or 'monthly'

filename = os.path.splitext(os.path.basename(dataset_path))[0]
output_dir = f'Dataset/Hospital Billing Delta Logs/{filename}_{frequency}_({initial_months})'

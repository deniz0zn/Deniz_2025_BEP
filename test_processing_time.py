import pandas as pd
import time
from process import ProcessManager

tests = {"initial_months": [1, 6, 12],
         "freq": ["daily", "weekly", "monthly"]}

results = {"month_freq": [], "duration": [], "total_seconds": []}



for month in tests["initial_months"]:
    for freq in tests["freq"]:
        print(f"Measuring time for the {month} months initial log and {freq} splitting frequency\n")

        output_dir = f'Dataset/Hospital Billing Delta Logs/Hospital Billing - Event Log_{freq}_({month})'
        process_manager = ProcessManager(month, freq, output_dir)

        start_time = time.time()
        process_manager.run()
        end_time = time.time()
        total_seconds = end_time - start_time
        m,s = divmod((total_seconds), 60)

        print(f"Measuring time for {month}_{freq} is {m} minutes {"%.2f" %s} seconds")
        results["month_freq"].append(f"{month}_{freq}")
        results["duration"].append(f"{m} minutes {"%.2f" %s} seconds")
        results["total_seconds"].append(total_seconds)

df_results = pd.DataFrame(results)
print(df_results)
df_results.to_csv('Dataset/Hospital Billing Delta Logs/run_time_results.csv')


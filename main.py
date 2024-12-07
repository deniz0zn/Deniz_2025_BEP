import os
from delta_log_formation import split_event_log_from_xes
import pandas as pd
from case import Case


# Define the paths
dataset_path = 'Dataset/xes/Hospital Billing - Event Log.xes'
initial_months = 12
frequency = 'weekly'  # 'daily', 'weekly', or 'monthly'

filename = os.path.splitext(os.path.basename(dataset_path))[0]
output_dir = f'Dataset/Hospital Billing Delta Logs/{filename}_{frequency}_({initial_months})'


def check_or_split_logs():
    """Check if the split logs already exist. If not, perform the splitting."""
    if not os.path.exists(output_dir):
        print(f"Splitting event log into {frequency} delta logs...")
        split_event_log_from_xes(dataset_path, frequency, initial_months)
        print(f"Splitting completed. Logs saved in {output_dir}.")
    else:
        print(f"{frequency.capitalize()} delta logs already exist in {output_dir}. Skipping splitting.")


def process_logs(path: str):
    print(f"[PROCESS LOGS] Loading log: {path}")
    event_log = pd.read_csv(path)

    for _,event in event_log.iterrows():
        case_id = event['case']

        # Update/Initialize the case in the dictionary:
        if case_id not in cases.keys():
            cases[case_id] = Case(event)
            print(f"[PROCESS LOGS] New Case added: {case_id}")

        else:
            cases[case_id].update(event)

    print(f"[PROCESS LOGS] Finished processing log: {path}")

    # Update time past since last event and check expirity
    current_T = event["completeTime"]
    for id, obj in cases.items():
        obj.update_time(current_T)




if __name__ == '__main__':
    cases = {}
    check_or_split_logs()

    initial_log_path = None
    delta_logs = []

    for file_name in os.listdir(output_dir):
        file_path = os.path.join(output_dir, file_name)
        if "initial_log" in file_name:  # Identify initial log
            initial_log_path = file_path
        elif "delta_log" in file_name:  # Identify delta logs
            delta_logs.append(file_path)

    # Process the Initial Log
    print(f"[MAIN] Processing the initial log file:")
    process_logs(initial_log_path)

    # Process all delta logs
    for file in delta_logs:
        print(f"[MAIN] Processing the delta log file: {file}")
        process_logs(file)

    # Convert the dictionary of Case objects to a dictionary of attributes
    case_dict = {
        case_id: vars(case_obj) for case_id, case_obj in cases.items()
    }

    # Create a DataFrame from the dictionary of attributes
    case_df = pd.DataFrame.from_dict(case_dict, orient="index")
    case_df = case_df.drop(["critical_events"], axis=1)

    size = len(case_df)
    complete_cases = case_df[case_df["isComplete"]]
    print(f"Number of Complete Cases: {len(complete_cases)}")

    finished_cases = case_df[case_df["finished"]]
    print(f"Number of Finished Cases: {len(finished_cases)}\nNumber of Unfinished cases: {size - len(finished_cases)}")

    expired_cases = case_df[case_df["expired"]]
    print(f"Number of Expired Cases: {len(expired_cases)}")


    Expired_Unfinished_cases = case_df[(case_df["expired"]) | (case_df["finished"] == False)]

    print(f"Number of expired or unfinished cases: {len(Expired_Unfinished_cases)}")

    complete_finished_cases = case_df[(case_df["finished"]) & (case_df["isComplete"])]
    print(f"Number of Finished Complete Cases: {len(complete_finished_cases)}")



    output_path = f"Dataset/Hospital Billing Delta Logs/cases_output_{filename}_{frequency}_({initial_months}.csv"
    # Save the DataFrame to a csv file
    case_df.to_csv(output_path, index=True)
    print(f"Final Results are saved into: {output_path}")





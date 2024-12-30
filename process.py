import os
import pandas as pd
from delta_log_formation import split_event_log
from case import Case
from delta import Delta
from config import dataset_path, initial_months, frequency, filename, output_dir


class ProcessManager:
    def __init__(self):
        self.cases = {}
        self.delta_stats_list = []
        self.output_dir = output_dir
        Delta.case_info = {"ongoing": [],
                                   "completed": [],
                                   "sleep": [],
                                   "incomplete": [],
                                   "cancelled": []
                                   }

    def check_or_split_logs(self):
        """Check if the split logs already exist. If not, perform the splitting."""
        if not os.path.exists(self.output_dir):
            print(f"Splitting event log into {frequency} delta logs...")
            split_event_log(dataset_path, frequency, initial_months)
            print(f"Splitting completed. Logs saved in {self.output_dir}.")
        else:
            print(f"{frequency.capitalize()} delta logs already exist in {self.output_dir}. Skipping splitting.")

    def process_logs(self, path: str, delta_name: str):
        """Process a single delta log."""
        event_log = pd.read_csv(path)
        delta = Delta(delta_name)

        for _, event in event_log.iterrows():
            case_id = event.get("case")

            # Initialize or update cases
            if self.cases.get(case_id) is None:
                self.cases[case_id] = Case(event, delta_name, delta)
            else:
                self.cases[case_id].update(event, delta)

        # Update statuses and time tracking for all cases
        current_T = event_log["completeTime"].iloc[-1]
        for case_id, case_obj in self.cases.items():
            case_obj.update_time(current_T, delta_name)
            delta.process_case_status(case_obj)

        self.delta_stats_list.append(delta.generate_report())

    def save_delta_statistics(self):
        """Save delta statistics to a CSV file."""
        delta_df = pd.DataFrame(self.delta_stats_list)
        delta_output_path = f"Dataset/Hospital Billing Delta Logs/Delta Stats/delta_stats_{filename}_{frequency}_({initial_months}).csv"
        delta_df.to_csv(delta_output_path, index=False)
        print(f"Delta Statistics saved to: {delta_output_path}")

    def save_case_statistics(self):
        """Save case-level statistics to a CSV file."""
        case_dict = {case_id: vars(case_obj) for case_id, case_obj in self.cases.items()}
        case_df = pd.DataFrame.from_dict(case_dict, orient="index").drop(["critical_events"], axis=1)

        # Output statistics
        processed_cases = len(case_df)
        cancelled_cases = case_df[case_df["cancelled"]]
        completed_cases = case_df[(case_df["isComplete"]) & (case_df["cancelled"] == False)]
        not_cancelled = case_df[(case_df["cancelled"] == False)]

        print(f"Number of Cases Processed: {processed_cases}")
        print(f"Numnber of Cancelled Cases: {len(cancelled_cases)}")
        print(f"Number of Complete Cases (Without Cancelled cases): {len(completed_cases)}")
        print(f"Ratio of Completeness out of not cancelled cases: {((len(completed_cases)/len(not_cancelled))*100):.2f}%")


        output_path = f"Dataset/Hospital Billing Delta Logs/cases_output/cases_output_{filename}_{frequency}_({initial_months}).csv"
        case_df.to_csv(output_path, index=True)
        print(f"Final Results saved to: {output_path}")

    def run(self):
        """Run the full processing pipeline."""
        self.check_or_split_logs()

        initial_log_path = None
        delta_logs = []

        # Identify initial and delta logs
        for file_name in os.listdir(self.output_dir):
            file_path = os.path.join(self.output_dir, file_name)
            if "initial_log" in file_name:
                initial_log_path = file_path
            elif "delta_log" in file_name:
                delta_logs.append((file_path, file_name))

        # Process initial log
        print("[PROCESS MANAGER] Processing initial log file...")
        self.process_logs(initial_log_path, delta_name="initial_log")

        # Process delta logs
        for file, delta_name in delta_logs:
            print(f"[PROCESS MANAGER] Processing delta log file: {file}")
            self.process_logs(file, delta_name)

        # Save results
        self.save_delta_statistics()
        self.save_case_statistics()

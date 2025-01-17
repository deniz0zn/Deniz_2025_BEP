import os
import pandas as pd
from tqdm import tqdm
import time
from delta_log_formation import EventLogSplitter
from case import Case
from delta import Delta
from config import (
    dataset_path, cases_output_path, delta_output_path,
    Evaluate, Plot, max_days, attributes_to_check
)


class ProcessManager:
    def __init__(self, initial_months, frequency, delta_log_dir):
        self.cases = {}
        self.delta_stats_list = []
        self.delta_log_dir = delta_log_dir
        self.delta_counts = pd.DataFrame(columns=["case_id", "count"]).set_index("case_id")
        self.initial = initial_months
        self.frequency = frequency
        self.cases_output_path = f"Dataset/Hospital Billing Delta Logs/cases_output/cases_output_{frequency}_({initial_months}).csv"
        self.delta_output_path = f"Dataset/Hospital Billing Delta Logs/Delta Stats/delta_stats_{frequency}_({initial_months}).csv"

    # ===================== Helper Functions ===================== #

    def increment_delta_counts(self):
        """Increment delta counts for all cases."""
        self.delta_counts["count"] += 1

    def reset_case_count(self, case_id):
        """Reset the delta count for a specific case."""
        self.delta_counts.loc[case_id, "count"] = 0

    def add_case_to_delta_counts(self, case_id):
        """Add a new case to the delta counts DataFrame."""
        temp_df = pd.DataFrame({"case_id": [case_id], "count": [0]}).set_index("case_id")
        self.delta_counts = pd.concat([self.delta_counts, temp_df])

    def perform_sleep_check(self, limit: int, delta_name: str):
        """Flag cases as sleep based on the delta count limit."""
        sleep_ids = set(self.delta_counts[(self.delta_counts["count"] > limit)].index)
        for case_id in sleep_ids:
            case = self.cases.get(case_id)
            if not (case.complete or case.cancelled):
                case.run_function_and_update_status(delta_name, case.final_status, case.update_sleep())

    def update_case_or_initialize(self, event, delta_name, delta):
        """Update an existing case or initialize a new one."""
        case_id = event.get("case")
        if self.cases.get(case_id) is None:
            self.cases[case_id] = Case(event, delta_name, delta)
            self.add_case_to_delta_counts(case_id)
        else:
            self.cases[case_id].update(event, delta, self.delta_counts)
            self.reset_case_count(case_id)



    # ===================== Core Functions ===================== #

    def check_or_split_logs(self):
        """Check if delta logs exist; if not, split the event log."""
        if not os.path.exists(self.delta_log_dir):
            print(f"Splitting event log into {self.frequency} delta logs...")
            splitter = EventLogSplitter(dataset_path, self.frequency, self.initial)
            splitter.run_splitting()
            print(f"Splitting completed. Logs saved in {self.delta_log_dir}.")
        else:
            print(f"{self.frequency.capitalize()} delta logs already exist in {self.delta_log_dir}. Skipping splitting.")



    def save_delta_statistics(self):
        """Save delta-level statistics to a CSV file."""
        delta_df = pd.DataFrame(self.delta_stats_list)
        delta_df.to_csv(self.delta_output_path, index=False)
        print(f"Delta Statistics saved to: {self.delta_output_path}")

    def save_case_statistics(self):
        """Save case-level statistics to a CSV file."""
        case_dict = {case_id: vars(case_obj) for case_id, case_obj in self.cases.items()}
        case_df = pd.DataFrame.from_dict(case_dict, orient="index").drop(["critical_events", "t_since_last_event","rejected_events"], axis=1)
        case_df["completion_time"] = case_df["last_event_time"] - case_df["first_event_time"]

        processed_cases = len(case_df)
        cancelled_cases = case_df[case_df["cancelled"]]
        completed_cases = case_df[(case_df["final_status"] == "COMPLETE")]
        ongoing_cases = case_df[(case_df["final_status"] == "ONGOING")]
        incomplete_cases = case_df[(case_df["final_status"] == "INCOMPLETE")]


        print(f"Number of Cases Processed: {processed_cases}")
        print(f"Number of Cancelled Cases: {len(cancelled_cases)}")
        print(f"Number of Complete Cases: {len(completed_cases)}")
        print(f"Number of Ongoing Cases: {len(ongoing_cases)}")
        print(f"Number of Incomplete Cases: {len(incomplete_cases)}")

        print(f"Ratio of Complete cases: {((len(completed_cases) / processed_cases) * 100):.2f}%\n")

        case_df.to_csv(self.cases_output_path, index=True)
        print(f"Final Results saved to: {self.cases_output_path}")

    def perform_evaluation(self, event_log_path, case_output_path):
        """Perform evaluation of completeness detection."""
        pass

    def process_logs(self, path, delta_name, limit):
        """Process events in a single delta log."""
        event_log = pd.read_csv(path, keep_default_na=False, na_values=['NaN', "", " "])
        delta = Delta(delta_name)
        cases_processed = event_log["case"].unique()
        delta.case_info = {
            "not_finished": set(),
            "complete": set(),
            "incomplete": set(),
            "cancelled": set()
        }

        self.increment_delta_counts()

        # Process each event
        for _, event in tqdm(event_log.iterrows(), total=len(event_log), desc=f"Processing events for {delta_name}"):
            self.update_case_or_initialize(event, delta_name, delta)
            case = self.cases.get(event.get("case"))
            case.check_missing_attributes(event)
        # Update delta attributes for processed cases
        for case_id in tqdm(cases_processed, desc=f"Updating delta attributes for {delta_name}"):
            case = self.cases.get(case_id)
            delta.process_case_status(case)

        self.perform_sleep_check(limit,delta_name)
        self.delta_stats_list.append(delta.generate_report())

    def run(self):
        """Run the entire process pipeline."""
        start_time = time.time()
        self.check_or_split_logs()

        initial_log_path = None
        delta_logs = []
        delta_limits = {
            "daily": max_days,
            "weekly": round(max_days / 7),
            "monthly": round(max_days / 30)
        }
        limit = delta_limits[self.frequency]

        # Identify logs
        for file_name in os.listdir(self.delta_log_dir):
            file_path = os.path.join(self.delta_log_dir, file_name)
            if "initial_log" in file_name:
                initial_log_path = file_path
            elif "delta_log" in file_name:
                delta_logs.append((file_path, file_name))

        # Process logs
        print(f"[PROCESS MANAGER] Limit for delta updates is set to: {limit}")
        print("[PROCESS MANAGER] Processing initial log file...")
        self.process_logs(initial_log_path, "initial_log", limit=limit)
        for file, delta_name in delta_logs:
            self.process_logs(file, delta_name, limit=limit)

        # Save results and evaluate
        self.save_delta_statistics()
        self.save_case_statistics()
        
        end_time = time.time()
        m,s = divmod((end_time - start_time), 60)
        print(f"Run Time: {m} minutes {"%.2f" %s} seconds")
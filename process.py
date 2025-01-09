import os
import pandas as pd
from tqdm import tqdm
import time
from delta_log_formation import EventLogSplitter
from evaluation import CompletenessEvaluator
from case import Case
from delta import Delta
from config import (
    dataset_path, initial_months, frequency, filename,
    output_dir, sample_size, cases_output_path, delta_output_path,
    Evaluate, Plot, max_days, attributes_to_check
)


class ProcessManager:
    def __init__(self):
        self.cases = {}
        self.delta_stats_list = []
        self.output_dir = output_dir
        self.delta_counts = pd.DataFrame(columns=["case_id", "count"]).set_index("case_id")


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

    def perform_sleep_check(self, limit):
        """Flag cases as sleep based on the delta count limit."""
        sleep_ids = set(self.delta_counts[(self.delta_counts["count"] > limit) and ()].index)
        for case_id in sleep_ids:
            case = self.cases.get(case_id)
            if not case.isComplete:
                case.update_sleep()

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
        if not os.path.exists(self.output_dir):
            print(f"Splitting event log into {frequency} delta logs...")
            splitter = EventLogSplitter(dataset_path, frequency, initial_months)
            splitter.run_splitting()
            print(f"Splitting completed. Logs saved in {self.output_dir}.")
        else:
            print(f"{frequency.capitalize()} delta logs already exist in {self.output_dir}. Skipping splitting.")

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

        self.perform_sleep_check(limit)
        self.delta_stats_list.append(delta.generate_report())


    def save_delta_statistics(self):
        """Save delta-level statistics to a CSV file."""
        delta_df = pd.DataFrame(self.delta_stats_list)
        delta_df.to_csv(delta_output_path, index=False)
        print(f"Delta Statistics saved to: {delta_output_path}")

    def save_case_statistics(self):
        """Save case-level statistics to a CSV file."""
        case_dict = {case_id: vars(case_obj) for case_id, case_obj in self.cases.items()}
        case_df = pd.DataFrame.from_dict(case_dict, orient="index").drop(["critical_events", "t_since_last_event"], axis=1)
        case_df["completion_time"] = case_df["last_event_time"] - case_df["first_event_time"]

        processed_cases = len(case_df)
        cancelled_cases = case_df[case_df["cancelled"]]
        completed_cases = case_df[(case_df["complete"]) & (~case_df["cancelled"])]
        not_cancelled = case_df[~case_df["cancelled"]]

        print(f"Number of Cases Processed: {processed_cases}")
        print(f"Number of Cancelled Cases: {len(cancelled_cases)}")
        print(f"Number of Complete Cases (Without Cancelled cases): {len(completed_cases)}")
        print(f"Ratio of Completeness out of not cancelled cases: {((len(completed_cases) / len(not_cancelled)) * 100):.2f}%")

        case_df.to_csv(cases_output_path, index=True)
        print(f"Final Results saved to: {cases_output_path}")

    def perform_evaluation(self, event_log_path, case_output_path):
        """Perform evaluation of completeness detection."""
        evaluator = CompletenessEvaluator(event_log_path, case_output_path)
        sampled_events, sampled_case_ids = evaluator.sample_cases(sample_size)
        manually_labeled_cases = evaluator.manually_label_cases(sampled_events)
        metrics = evaluator.evaluate_predictions(sampled_case_ids, manually_labeled_cases)
        return evaluator.generate_report(metrics)

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
        limit = delta_limits[frequency]

        # Identify logs
        for file_name in os.listdir(self.output_dir):
            file_path = os.path.join(self.output_dir, file_name)
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
        evaluation_report = self.perform_evaluation(dataset_path, cases_output_path)
        print(evaluation_report)

        end_time = time.time()
        m,s = divmod((end_time - start_time), 60)
        print(f"Run Time: {m} minutes {"%.2f" %s} seconds")
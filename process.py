import os
import pandas as pd
from tqdm import tqdm
from delta_log_formation import EventLogSplitter
from evaluation import CompletenessEvaluator
from case import Case
from delta import Delta
from config import (dataset_path, initial_months, frequency, filename,
                    output_dir, sample_size, cases_output_path, delta_output_path,
                    Evaluate, Plot)


class ProcessManager:
    def __init__(self):
        self.cases = {}
        self.delta_stats_list = []
        self.output_dir = output_dir
        Delta.case_info = {
            "ongoing": [],
            "completed": [],
            "sleep": [],
            "incomplete": [],
            "cancelled": []
        }

    def check_or_split_logs(self):
        """Check if the split logs already exist. If not, perform the splitting."""
        if not os.path.exists(self.output_dir):
            print(f"Splitting event log into {frequency} delta logs...")
            splitter = EventLogSplitter(dataset_path, frequency, initial_months)
            splitter.process_event_log()
            print(f"Splitting completed. Logs saved in {self.output_dir}.")
        else:
            print(f"{frequency.capitalize()} delta logs already exist in {self.output_dir}. Skipping splitting.")

    def process_logs(self, path: str, delta_name: str):
        """Process a single delta log."""
        event_log = pd.read_csv(path)
        delta = Delta(delta_name)

        current_T = event_log["completeTime"].iloc[-1]
        if delta_name != "initial_log":
            for case_id, case_obj in tqdm(self.cases.items(), desc=f"Processing cases for {delta_name}"):
                case_obj.increase_delta_counter()
                case_obj.update_time(current_T)
                delta.process_case_status(case_obj)

        for _, event in tqdm(event_log.iterrows(), total=len(event_log), desc=f"Processing events for {delta_name}"):
            case_id = event.get("case")
            # Initialize or update cases
            if self.cases.get(case_id) is None:
                self.cases[case_id] = Case(event, delta_name, delta)
            else:
                self.cases[case_id].update(event, delta)

        self.delta_stats_list.append(delta.generate_report())

    def save_delta_statistics(self):
        """Save delta statistics to a CSV file."""
        delta_df = pd.DataFrame(self.delta_stats_list)

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
        print(f"Number of Cancelled Cases: {len(cancelled_cases)}")
        print(f"Number of Complete Cases (Without Cancelled cases): {len(completed_cases)}")
        print(f"Ratio of Completeness out of not cancelled cases: {((len(completed_cases) / len(not_cancelled)) * 100):.2f}%")

        output_path = cases_output_path
        case_df.to_csv(output_path, index=True)
        print(f"Final Results saved to: {output_path}")

    def perform_evaluation(self, event_log_path, case_output_path):
        evaluator = CompletenessEvaluator(event_log_path, case_output_path)

        sampled_events, sampled_case_ids = evaluator.sample_cases(sample_size)
        manually_labeled_cases = evaluator.manually_label_cases(sampled_events)

        metrics = evaluator.evaluate_predictions(sampled_case_ids, manually_labeled_cases)
        report = evaluator.generate_report(metrics)
        return report



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
            print(f"[PROCESS MANAGER] Processing delta log file: {delta_name}")
            self.process_logs(file, delta_name)

        # Save results
        self.save_delta_statistics()
        self.save_case_statistics()

        evaluation_report = self.perform_evaluation(dataset_path ,cases_output_path)
        print(evaluation_report)


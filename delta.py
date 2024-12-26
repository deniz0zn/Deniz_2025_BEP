from collections import Counter

class Delta:

    def __init__(self, delta_file_name):
        # Initialize attributes to track statistics for the delta file
        self.delta_file_name = delta_file_name  # Name of the delta file
        self.event_counter = Counter()  # Counts occurrences of each event
        self.new_cases = 0  # Number of new cases opened in this delta file
        self.finished_cases = 0  # Number of cases finished in this delta file
        self.expired_cases = 0  # Number of cases expired in this delta file
        self.complete_cases = 0  # Number of cases marked as complete
        self.incomplete_cases = 0  # Number of cases marked as incomplete
        self.total_event = sum(dict(self.event_counter).values())
        self.processed_cases = set()
    def process_event(self, event):
        """
        Process an event from the delta file.

        :param event: A dictionary containing event data.
        """
        # Track the occurrence of the event
        event_name = event.get("event")
        self.event_counter[event_name] += 1


    def process_case_status(self, case):
        """
        Update delta statistics based on the status of a case.

        :param case: A `Case` object.
        """
        # Check case status and update counters
        if case.case_id in self.processed_cases:
            # Skip cases already processed in this delta
            return

        self.processed_cases.add(case.case_id)

        if case.last_delta == self.delta_file_name:
            if case.finished and case.case_id not in Delta.case_info["finished"]:
                self.finished_cases += 1
                Delta.case_info["finished"].append(case.case_id)

            if case.expired and case.case_id not in Delta.case_info["expired"]:
                self.expired_cases += 1
                Delta.case_info["expired"].append(case.case_id)

            if case.isComplete and (case.case_id not in Delta.case_info["completed"]):
                self.complete_cases += 1
                Delta.case_info["completed"].append(case.case_id)


            if not case.isComplete and case.case_id not in Delta.case_info["incomplete"]:
                self.incomplete_cases += 1
                Delta.case_info["incomplete"].append(case.case_id)

    def generate_report(self):
        """
        Generate a summary report of the delta statistics.

        :return: A dictionary containing the summary statistics.
        """
        return {
            "delta_file_name": self.delta_file_name,
            "event_counts": dict(self.event_counter),
            "new_cases": self.new_cases,
            "finished_cases": self.finished_cases,
            "expired_cases": self.expired_cases,
            "complete_cases": self.complete_cases,
            "incomplete_cases": self.incomplete_cases,
         }

    def __str__(self):
        """
        String representation of the delta statistics.

        :return: A formatted string summarizing the delta statistics.
        """
        report = self.generate_report()
        return (f"Delta File: {report['delta_file_name']}\n"
                f"Events: {report['event_counts']}\n"
                f"New Cases: {report['new_cases']}\n"
                f"Finished Cases: {report['finished_cases']}\n"
                f"Expired Cases: {report['expired_cases']}\n"
                f"Complete Cases: {report['complete_cases']}\n"
                f"Incomplete Cases: {report['incomplete_cases']}\n"
                f"Total Number of Events Occured: {report['total_events']}")

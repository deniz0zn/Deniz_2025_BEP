from collections import Counter

class Delta:

    def __init__(self, delta_file_name):
        # Initialize attributes to track statistics for the delta file
        self.delta_file_name = delta_file_name  # Name of the delta file
        self.event_counter = Counter()  # Counts occurrences of each event
        self.new_cases = 0  # Number of new cases opened in this delta file
        self.unfinished_cases = 0  # Number of cases ongoing in this delta file
        self.expired_cases = 0  # Number of cases sleep in this delta file
        self.complete_cases = 0  # Number of cases marked as complete
        self.incomplete_cases = 0  # Number of cases marked as incomplete
        self.cancelled = 0 # Number of cancelled cases
        self.total_event = sum(dict(self.event_counter).values())
        self.initialised_cases = set()
        self.ongoing_cases = set()

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

        if case.last_delta == self.delta_file_name:
            if case.ongoing and case.case_id not in Delta.case_info["ongoing"]:
                self.unfinished_cases += 1
                Delta.case_info["ongoing"].append(case.case_id)

            if case.sleep and case.case_id not in Delta.case_info["sleep"]:
                self.expired_cases += 1
                Delta.case_info["sleep"].append(case.case_id)

            if case.isComplete and (case.case_id not in Delta.case_info["completed"]):
                self.complete_cases += 1
                Delta.case_info["completed"].append(case.case_id)

            if not case.isComplete and case.case_id not in Delta.case_info["incomplete"]:
                self.incomplete_cases += 1
                Delta.case_info["incomplete"].append(case.case_id)

            if case.cancelled and case.case_id not in Delta.case_info["cancelled"]:
                self.cancelled += 1
                Delta.case_info["cancelled"].append(case.case_id)

    def generate_report(self):
        """
        Generate a summary report of the delta statistics.

        :return: A dictionary containing the summary statistics.
        """
        return {
            "delta_file_name": self.delta_file_name,
            "event_counts": dict(self.event_counter),
            "total_events": sum(dict(self.event_counter).values()),
            "unfinished_cases": self.unfinished_cases,
            "cancelled_cases": self.cancelled,
            "sleep_cases": self.expired_cases,
            "complete_cases": self.complete_cases,
            "incomplete_cases": self.incomplete_cases,
            "initialised cases": self.initialised_cases,
            "ongoing_cases": self.ongoing_cases,
            "new_cases": self.new_cases,
            "# ongoing cases": len(self.ongoing_cases),
            "cases_processed" : len(self.initialised_cases) + len(self.ongoing_cases)
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
                f"Finished Cases: {report['unfinished_cases']}\n"
                f"Expired Cases: {report['expired_cases']}\n"
                f"Complete Cases: {report['complete_cases']}\n"
                f"Incomplete Cases: {report['incomplete_cases']}\n"
                f"Total Number of Events Occured: {report['total_events']}")

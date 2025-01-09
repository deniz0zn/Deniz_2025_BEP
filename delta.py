from collections import Counter

class Delta:

    def __init__(self, delta_file_name):
        # Initialize attributes to track statistics for the delta file
        self.delta_file_name = delta_file_name
        self.event_counter = Counter()
        self.new_cases = 0
        self.not_finished = 0
        self.complete_cases = 0
        self.incomplete_cases = 0
        self.cancelled = 0
        self.total_event = sum(dict(self.event_counter).values())
        self.initialised_cases = set()
        self.ongoing_cases_count= set()



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
        case_info = self.case_info

        if (case.cancelled):
            case_info["cancelled"].add(case.case_id)
            self.cancelled = len(case_info["cancelled"])

        if (case.complete) and not (case.cancelled):
            case_info["complete"].add(case.case_id)
            self.complete_cases = len(case_info["complete"])

        if (case.ongoing):
            case_info["not_finished"].add(case.case_id)
            self.not_finished = len(case_info["not_finished"])

        if not(case.cancelled) and not (case.ongoing) and not(case.complete):
            case_info["incomplete"].add(case.case_id)
            self.incomplete_cases = len(case_info["incomplete"])

    def generate_report(self):
        """
        Generate a summary report of the delta statistics.

        :return: A dictionary containing the summary statistics.
        """
        print()
        return {
            "delta_file_name": self.delta_file_name,
            "event_counts": dict(self.event_counter),
            "total_events": sum(dict(self.event_counter).values()),
            "not_finished": self.not_finished,
            "cancelled_cases": self.cancelled,
            "complete_cases": self.complete_cases,
            "incomplete_cases": self.incomplete_cases,
            "initialised cases": self.initialised_cases,
            "ongoing_cases_count": self.ongoing_cases_count,
            "new_cases": self.new_cases,
            "# ongoing cases": len(self.ongoing_cases_count),
            "cases_processed" : len(self.initialised_cases) + len(self.ongoing_cases_count)
         }

    def __str__(self):
        report = self.generate_report()
        return (f"Delta File: {report['delta_file_name']}\n"
                f"Events: {report['event_counts']}\n"
                f"New Cases: {report['new_cases']}\n"
                f"Finished Cases: {report['not_finished']}\n"
                f"Complete Cases: {report['complete_cases']}\n"
                f"Incomplete Cases: {report['incomplete_cases']}\n"
                f"Total Number of Events Occured: {report['total_events']}")

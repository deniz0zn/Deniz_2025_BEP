from collections import Counter

class Delta:

    def __init__(self, delta_file_name):
        # Initialize attributes to track statistics for the delta file
        self.delta_file_name = delta_file_name[:8]
        self.event_counter = Counter()
        self.not_finished = set()
        self.complete_cases = set()
        self.incomplete_cases = set()
        self.cancelled = set()
        self.total_event = sum(dict(self.event_counter).values())
        self.initialised_cases = set()
        self.ongoing_cases_count = set()



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
        CANCELLED = (case.cancelled == True)
        COMPLETE = (case.final_status == "COMPLETE") and not (CANCELLED)
        ONGOING = (case.final_status == "ONGOING")

        case_info = self.case_info
        if CANCELLED:
            case_info["cancelled"].add(case.case_id)
            self.cancelled = case_info["cancelled"]

        if COMPLETE:
            case_info["complete"].add(case.case_id)
            self.complete_cases = case_info["complete"]

        if ONGOING:
            case_info["not_finished"].add(case.case_id)
            self.not_finished = case_info["not_finished"]

        # if not(CANCELLED) and not (ONGOING) and not(COMPLETE):
        #     case_info["incomplete"].add(case.case_id)
        #     self.incomplete_cases = len(case_info["incomplete"])

    def generate_report(self):
        """
        Generate a summary report of the delta statistics.

        :return: A dictionary containing the summary statistics.
        """
        return {
            "delta_file_name": self.delta_file_name,
            "event_counts": dict(self.event_counter),
            "total_events": sum(dict(self.event_counter).values()),
            "ongoing_count": len(self.not_finished),
            "cancelled_count": len(self.cancelled),
            "complete_count": len(self.complete_cases),
            "incomplete_count": len(self.incomplete_cases),
            "initialised_count": len(self.initialised_cases),
            "updated_count": len(self.ongoing_cases_count),
            "cases_processed": len(self.initialised_cases) + len(self.ongoing_cases_count),
            "initialised_cases": self.initialised_cases,
            "updated_cases": self.ongoing_cases_count,
            "complete_cases": self.complete_cases,
            "incomplete_cases": self.incomplete_cases,
            "cancelled_cases": self.cancelled,
            "ongoing_cases": self.not_finished,

         }


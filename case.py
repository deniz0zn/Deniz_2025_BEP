from datetime import timedelta, datetime
import pandas as pd

from delta import Delta
from config import attributes_to_check


class Case:
    def __init__(self, event, delta_name: str, delta: Delta):
        self.initialize_case_attributes(event, delta_name, delta)
        self.initialize_timestamps(event)
        self.register_new_case(delta, event)

    def initialize_case_attributes(self, event, delta_name: str, delta: Delta):
        """Initialize the primary attributes of the Case."""
        self.critical_events = {"BILLED", "FIN", "RELEASE", "CODE OK"}

        self.case_id = event.get("case")
        self.completeness_status = "ONGOING"
        self.status_transitions = []
        self.last_state = event.get("state")
        self.last_event = event.get("event")
        self.unique_events = {self.last_event}
        self.missing_events = {"BILLED", "FIN", "RELEASE", "CODE OK"}
        self.trace = [self.last_event]
        self.length = len(self.trace)


        self.cancelled = self.check_cancelled(event)
        self.complete = False
        self.incomplete = None
        self.isBilled = self.last_state == "Billed"
        self.have_crit_events = False
        self.issues = [f"Missing critical events: {self.missing_events}",
                       "Case is not billed.",
                       "Case is not finished.",
                       ]

        self.short = True
        self.t_since_last_event = timedelta(0)
        self.event_gaps = [self.t_since_last_event]
        self.avg_wait_time = None

        self.sleep = False
        self.ongoing = True

        self.first_delta = delta_name
        self.last_delta_update = delta_name
        self.delta_counts = [0]

        self.missing_attributes = {}
        self.n_events_w_missing_attr = 0

    def initialize_timestamps(self, event):
        """Initialize the timestamp attributes."""
        complete_time = event.get("completeTime")
        parsed_time = (datetime.strptime(complete_time, "%Y-%m-%d %H:%M:%S")
                       if isinstance(complete_time, str) else complete_time)

        self.first_event_time = parsed_time
        self.last_event_time = parsed_time

    def register_new_case(self, delta: Delta, event):
        """Register the case as a new case in the Delta object."""
        delta.new_cases += 1
        delta.initialised_cases.add(self.case_id)
        delta.process_event(event)


    def update(self, event, delta:Delta, delta_counts:pd.DataFrame):
        """Update the case attributes based on a new event."""
        self.update_event_attributes(event)
        self.update_case_status(event, delta)
        self.update_time_gap(event)
        self.run_function_and_update_status(delta.delta_file_name,self.completeness_status ,self.check_completeness())      #self.check_completeness()
        self.append_delta(delta, delta_counts)
        delta.process_event(event)
    def update_event_attributes(self, event):
        """Update attributes related to the event."""
        self.last_event = event.get('event')
        self.last_state = event.get('state')
        self.unique_events.add(self.last_event)
        self.trace.append(self.last_event)
        self.length = len(self.trace)

    def update_case_status(self, event, delta: Delta):
        """Update the case status attributes."""
        self.cancelled = self.run_function_and_update_status(delta.delta_file_name,
                                                             self.completeness_status,
                                                             self.check_cancelled(event))
        self.isBilled = self.last_state == "Billed"
        self.have_crit_events = self.crit_event_check()

        self.short = self.length < 5
        self.sleep = False
        self.ongoing = self.run_function_and_update_status(delta.delta_file_name,
                                                           self.completeness_status,
                                                           self.check_ongoing())

        if self.case_id not in delta.initialised_cases:
            delta.ongoing_cases_count.add(self.case_id)


    def update_time_gap(self, event):
        """Update the time gap between events."""
        complete_time = event.get("completeTime")
        current_time = (datetime.strptime(complete_time, "%Y-%m-%d %H:%M:%S")
                        if isinstance(complete_time, str) else complete_time)

        self.t_since_last_event = current_time - self.last_event_time
        self.event_gaps.append(self.t_since_last_event)
        self.avg_wait_time = sum(self.event_gaps, timedelta(0)) / len(self.event_gaps)
        self.last_event_time = current_time


    def append_delta(self,delta: Delta, delta_counts: pd.DataFrame):
        self.delta_counts.append(delta_counts.loc[self.case_id, "count"])
        self.last_delta_update = delta.delta_file_name



    def check_missing_attributes(self, event):
        missing = [attr for attr in attributes_to_check if not self.last_event] # List of Missing attributes in the event
        self.missing_attributes[self.last_event] = missing
        self.n_events_w_missing_attr += len(self.missing_attributes[self.last_event])


    def crit_event_check(self):
        """Check if all critical events are present."""
        not_missing = self.critical_events.issubset(self.unique_events)
        self.missing_events = self.critical_events - self.unique_events

        return not_missing

    def run_function_and_update_status(self, delta_name: str, previous_status ,function: callable ):
        value = function
        new_status = self.completeness_status
        transition = {
            "previous": previous_status,
            "new": new_status,
            "delta_name": delta_name
        }

        if previous_status!= new_status:
            self.status_transitions.append(transition)

        if value != None:
            return value
    def check_completeness(self, returning = False):
        """Evaluate whether the case is complete."""
        self.issues.clear()
        completeness = True

        if not self.cancelled:
            if not self.have_crit_events:
                completeness = False
                self.issues.append(f"Missing critical events: {self.missing_events}")

            # if not self.isBilled:
            #     completeness = False
            #     self.issues.append("Case is not billed.")

            if self.ongoing:
                completeness = False
                self.issues.append("Case is not finalised. (Not Billed or Cancelled)")
        # else:
        #     completeness = None

        self.complete = completeness
        if completeness:
            self.completeness_status = "COMPLETE"
            self.ongoing = False
            self.incomplete = False
        else:
            self.incomplete = None

        if self.cancelled:
            self.completeness_status = "CANCELLED"
            self.ongoing = False


        return completeness if returning else None

    def check_cancelled(self,event):
        iscancelled = event.get('isCancelled', False)
        self.cancelled = iscancelled
        if iscancelled:
            self.completeness_status = "CANCELLED"
        return iscancelled

    def check_ongoing(self):
        isOngoing = not (self.cancelled or self.isBilled)
        if isOngoing:
            self.completeness_status = "ONGOING"
        return isOngoing

    def update_sleep(self):
        self.sleep = True
        self.ongoing = False
        self.incomplete = True
        self.completeness_status = "INCOMPLETE"


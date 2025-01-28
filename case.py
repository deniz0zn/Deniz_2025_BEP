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
        self.rejected_events = {"STORNO", "REJECT", "SET STATUS"}

        self.case_id = event.get("case")
        self.final_status = "ONGOING"
        self.status_transitions = []
        self.transition_count = 0
        self.first_transition_to = None
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
        self.isUnbillable = self.last_state == "Unbillable"
        self.have_crit_events = False
        self.issues = "No updates received"

        self.short = True
        self.t_since_last_event = 0
        self.event_gaps = [self.t_since_last_event]
        self.avg_wait_time = None

        self.sleep = False
        self.ongoing = True

        self.first_delta = delta_name
        self.last_delta_update = delta_name[:8]
        self.delta_counts_array = [0]

        self.missing_attributes = {}
        self.n_events_w_missing_attr = 0
        self.status_trace = ["ONGOING"]

    def initialize_timestamps(self, event):
        """Initialize the timestamp attributes."""
        complete_time = event.get("completeTime")
        parsed_time = (datetime.strptime(complete_time, "%Y-%m-%d %H:%M:%S")
                       if isinstance(complete_time, str) else complete_time)

        self.first_event_time = parsed_time
        self.last_event_time = parsed_time

    def register_new_case(self, delta: Delta, event):
        """Register the case as a new case in the Delta object."""
        delta.initialised_cases.add(self.case_id)
        delta.process_event(event)


    def update(self, event, delta:Delta, delta_counts:pd.DataFrame):
        """Update the case attributes based on a new event."""
        self.update_event_attributes(event)
        self.update_case_status(event, delta)
        self.update_time_gap(event)
        self.run_function_and_update_status(delta.delta_file_name, self.final_status, self.check_completeness())
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
                                                             self.final_status,
                                                             self.check_cancelled(event))
        self.isBilled = self.last_state == "Billed"
        self.isUnbillable = self.last_state == "Unbillable"

        self.have_crit_events = self.crit_event_check()

        self.short = self.length < 5
        self.sleep = False
        self.ongoing = self.run_function_and_update_status(delta.delta_file_name,
                                                           self.final_status,
                                                           self.check_ongoing())


        if self.case_id not in delta.initialised_cases:
            delta.ongoing_cases_count.add(self.case_id)


    def update_time_gap(self, event):
        """Update the time gap between events."""
        complete_time = event.get("completeTime")
        current_time = (datetime.strptime(complete_time, "%Y-%m-%d %H:%M:%S")
                        if isinstance(complete_time, str) else complete_time)

        self.t_since_last_event = current_time - self.last_event_time
        self.event_gaps.append(self.t_since_last_event.total_seconds())
        self.avg_wait_time = sum(self.event_gaps) / len(self.event_gaps)
        self.last_event_time = current_time


    def append_delta(self,delta: Delta, delta_counts: pd.DataFrame):
        self.delta_counts_array.append(delta_counts.loc[self.case_id, "count"])
        self.last_delta_update = delta.delta_file_name



    def check_missing_attributes(self, event):
        missing = [attr for attr in attributes_to_check if not self.last_event] # List of Missing attributes in the event
        self.missing_attributes[self.last_event] = missing
        self.n_events_w_missing_attr += len(self.missing_attributes[self.last_event])


    def crit_event_check(self):
        """Check if all critical events are present."""
        if not self.isUnbillable:
            not_missing = self.critical_events.issubset(self.unique_events)
            self.missing_events = self.critical_events - self.unique_events
            return not_missing

        else:
            new_essential_events = self.rejected_events.union(self.critical_events)
            not_missing = (new_essential_events.issubset(self.unique_events))
            self.missing_events = new_essential_events - self.unique_events
            return not_missing



    def run_function_and_update_status(self, delta_name: str, previous_status ,function: callable ):
        value = function
        new_status = self.final_status
        transition = {
            "previous": previous_status,
            "new": new_status,
            "delta_name": delta_name
        }

        if previous_status!= new_status:
            self.status_transitions.append(transition)
            self.status_trace.append(new_status)
            self.transition_count += 1

        if (self.first_transition_to == None) and (self.transition_count > 0):
            self.first_transition_to = self.final_status

        if value != None:
            return value
    def check_completeness(self, returning = False):
        """Evaluate whether the case is complete."""
        self.issues = ""
        completeness = True

        if not self.cancelled:
            if self.ongoing:
                completeness = False
                self.issues = "Trace is not finalised"

            elif not self.have_crit_events:
                completeness = False
                self.issues = f"Missing events: {self.missing_events}"


        self.complete = completeness
        if completeness:
            self.final_status = "COMPLETE"
            self.ongoing = False
            self.incomplete = False
        else:
            self.incomplete = None

        # if self.cancelled:
        #     self.final_status = "CANCELLED"
        #     self.ongoing = False


        return completeness if returning else None

    def check_cancelled(self,event):
        iscancelled = event.get('isCancelled', False)
        self.cancelled = iscancelled
        if iscancelled:
            self.final_status = "COMPLETE"
        return iscancelled

    def check_ongoing(self):
        isOngoing = not (self.cancelled or self.isBilled or self.isUnbillable)
        if isOngoing:
            self.final_status = "ONGOING"
        return isOngoing

    def update_sleep(self):
        self.sleep = True
        self.ongoing = False
        self.incomplete = True
        self.final_status = "INCOMPLETE"


from datetime import timedelta, datetime
from delta import Delta

class Case:
    def __init__(self, event,delta_name: str, delta: Delta ):
        self.critical_events = {"BILLED", "FIN", "RELEASE", "CODE OK"}

        self.case_id = event.get("case")
        self.last_state = event.get("state")
        self.last_event = event.get("event")
        self.unique_events = {self.last_event}
        self.trace = [self.last_event]
        self.length = len(self.trace)
        self.issues = []
        self.cancelled = False

        self.isComplete = False
        self.isBilled = False
        self.short = True

        complete_time = event.get("completeTime")
        self.last_event_time = (
            datetime.strptime(complete_time, "%Y-%m-%d %H:%M:%S")
            if isinstance(complete_time, str)
            else complete_time
        )

        self.t_since_last_event = timedelta(0)
        self.expired = False

        self.have_crit_events = False
        self.finished = False

        self.last_delta = delta_name
        self.delta_counter = 0

        delta.new_cases += 1
        delta.process_event(event)

        # print(f"[INIT] Initialized Case: {self.case_id}")


    def update(self,event, delta: Delta):
        # print(f"[UPDATE EVENT] Updating Case {self.case_id} with event {event.get('event')}, time {event.get('completeTime')}, state {self.last_state}")

        self.last_event = event.get('event')
        self.last_state = event.get('state')
        self.unique_events.add(self.last_event)
        self.trace.append(self.last_event)

        self.cancelled = event.get('isCancelled')
        self.isBilled = self.last_state == "Billed"
        self.have_crit_events = self.event_check()
        self.length = len(self.trace)

        self.finished = self.cancelled or self.isBilled

        if self.length >= 5: self.short = False



        if self.last_delta != delta.delta_file_name:
            self.delta_counter = 0
            self.last_delta = delta.delta_file_name

        complete_time = event.get("completeTime")
        self.last_event_time = (
            datetime.strptime(complete_time, "%Y-%m-%d %H:%M:%S")
            if isinstance(complete_time, str)
            else complete_time
        )

        self.isComplete = self.is_complete()
        delta.process_event(event)

        # if self.last_state == "Invoice rejected":  self.isBilled = False

    def event_check(self):
        return self.critical_events.issubset(self.unique_events)

    def is_complete(self):
        self.issues.clear()  # Clear issues before re-evaluating
        completeness = True

        if not self.have_crit_events:
            completeness = False
            self.issues.append("Missing critical events.")

        if not self.isBilled:
            completeness = False
            self.issues.append("Case is not billed.")

        # if self.short:
        #     completeness = False
        #     self.issues.append("Trace is too short (less than 5 events).")

        if not self.finished:
            completeness = False
            self.issues.append("Case is not finished (not cancelled or billed).")

        # if self.expired:
        #     completeness = False
        #     self.issues.append("Case has expired (exceeds max duration).")

        # print(f"[IS COMPLETE] Case {self.case_id} completeness check: {completeness} | Issues: {self.issues}")
        return completeness




    def update_time(self, current_time: timedelta, delta_name: str):
        # print(f"[UPDATE TIME] Checking expiration for Case {self.case_id} at time {current_time}")
        if isinstance(current_time, str):
            current_time = datetime.strptime(current_time, "%Y-%m-%d %H:%M:%S")

        max_duration = timedelta(days= 190)
        self.t_since_last_event = current_time - self.last_event_time
        # print(f"[UPDATE TIME] Time since last event for Case {self.case_id}: {self.t_since_last_event}")

        if self.last_delta != delta_name:
            self.delta_counter += 1

        if (self.t_since_last_event > max_duration) & (not self.finished):
            self.expired = True
            # print(f"[UPDATE TIME] Case {self.case_id} marked as expired.")










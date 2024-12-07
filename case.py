from datetime import timedelta, datetime

class Case:
    def __init__(self, event):
        self.critical_events = {"BILLED", "FIN", "RELEASE", "CODE OK"}

        self.case_id = event.get("case")
        self.last_state = event.get("state")
        self.last_event = event.get("event")
        self.unique_events = {self.last_event}
        self.trace = [self.last_event]
        self.length = len(self.trace)
        # self.issues = []
        self.cancelled = False

        self.isComplete = False
        self.isBilled = False
        self.short = True

        complete_time = event.get("completeTime")
        self.t_1st_event = (
            datetime.strptime(complete_time, "%Y-%m-%d %H:%M:%S")
            if isinstance(complete_time, str)
            else complete_time
        )

        self.t_since_first_event = timedelta(0)
        self.expired = False

        self.have_crit_events = False
        self.finished = False

        print(f"[INIT] Initialized Case: {self.case_id}")

    def update(self,event):
        print(f"[UPDATE EVENT] Updating Case {self.case_id} with event {event.get('event')}, time {event.get('completeTime')}, state {self.last_state}")
        self.last_event = event.get('event')
        self.last_state = event.get('state')
        self.unique_events.add(self.last_event)
        self.trace.append(self.last_event)

        self.cancelled = event.get('isCancelled')
        self.isBilled = self.last_state == "Billed"
        self.have_crit_events = self.event_check()
        self.length = len(self.trace)

        self.isComplete = self.is_complete()
        self.finished = self.cancelled or self.isBilled

        if self.length >= 5: self.short = False

        # if self.last_state == "Invoice rejected":  self.isBilled = False

    def event_check(self):
        return self.critical_events.issubset(self.unique_events)

    def is_complete(self):
        completeness = (self.have_crit_events and self.isBilled and not self.short and self.finished) or (self.cancelled)
        print(f"[IS COMPLETE] Case {self.case_id} completeness check: {completeness}")
        return completeness



    # def is_finished(self):
    #     return

    def update_time(self, T: timedelta):
        print(f"[UPDATE TIME] Checking expiration for Case {self.case_id} at time {T}")
        if isinstance(T, str):
            T = datetime.strptime(T, "%Y-%m-%d %H:%M:%S")

        max_duration = timedelta(days= 395)
        self.t_since_first_event = T - self.t_1st_event
        print(f"[UPDATE TIME] Time since first event for Case {self.case_id}: {self.t_since_first_event}")

        if (self.t_since_first_event > max_duration) & (not self.finished):
            self.expired = True
            print(f"[UPDATE TIME] Case {self.case_id} marked as expired.")










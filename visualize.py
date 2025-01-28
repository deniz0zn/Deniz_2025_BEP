import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from collections import Counter
from config import cases_output_path, delta_output_path, focus_deltas


class VisualizationManager:
    def __init__(self, delta_stats_path, case_output_path, focus_deltas = []):
        self.delta_stats = pd.read_csv(delta_stats_path)
        self.case_stats = pd.read_csv(case_output_path)

        if focus_deltas:
            self.delta_stats = self.delta_stats[self.delta_stats["delta_file_name"].isin(focus_deltas)]
            self.delta_stats.reset_index(drop=True, inplace=True)

        self.complete_cases = self.case_stats[self.case_stats['final_status'] == "COMPLETE"]
        self.cancelled_cases = self.case_stats[self.case_stats['cancelled']]
        self.incomplete_cases = self.case_stats[self.case_stats['final_status'] == "INCOMPLETE"]
        self.ongoing_cases = self.case_stats[self.case_stats['final_status'] == "ONGOING"]

    def plot_event_counts_line_chart(self):
        """
        Plot a line chart showing the event counts for each delta file.
        """
        self.delta_stats["delta_file_name"] = self.delta_stats["delta_file_name"].astype(str)
        event_counts_df = self.delta_stats[["delta_file_name", "event_counts"]]

        # Transform event counts into a structured DataFrame
        event_counts_expanded = pd.json_normalize(event_counts_df["event_counts"].apply(eval))
        event_counts_expanded["delta_file_name"] = event_counts_df["delta_file_name"]

        # Melt the DataFrame for Plotly
        melted_event_counts = event_counts_expanded.melt(id_vars=["delta_file_name"], var_name="Event",
                                                         value_name="Count")
        melted_event_counts["Count"].fillna(0, inplace=True)
        # Plot the line chart
        fig = px.line(
            melted_event_counts,
            x="delta_file_name",
            y="Count",
            color="Event",
            title="Event Counts Across Delta Logs",
            labels={"delta_file_name": "Delta File", "Count": "Event Count"}
        )
        fig.update_layout(
            hovermode="x unified",
            xaxis_tickangle=45,
            font_size=16
        )
        fig.show()

    def plot_case_status_pie_chart(self):
        """
        Plot a pie chart showing the proportion of cancelled, complete, and incomplete cases.
        """
        pie_data = pd.DataFrame({
            "Status": ["Complete Traces", "Incomplete Traces", "Ongoing Traces"],
            "Count": [len(self.complete_cases), len(self.incomplete_cases), len(self.ongoing_cases)]
        })

        fig = px.pie(
            pie_data,
            values="Count",
            names="Status",
            title="Trace Classification Distribution",
            hole=0.3
        )
        fig.update_traces(textinfo="percent+label")
        fig.update_layout(font_size=20, width=800, height=600)
        fig.show()

    def plot_incompleteness_reasons(self):
        """
        Incompleteness Reasons
        """
        # Map original reasons to customized labels
        reason_mapping = {
            'Missing events': "Missing Essential Events(2)",
            'Trace is not finalised': "No Logical Final State(1)",
            'No updates received': "No updates received(1&2)"
        }

        # Apply mapping to issues
        reasons = self.incomplete_cases['issues'].apply(
            lambda x: 'Missing events' if x.startswith('Missing events:') else x
        ).map(reason_mapping)

        reason_counts = reasons.value_counts()
        reason_df = pd.DataFrame({"Reason": reason_counts.index, "Count": reason_counts.values})

        # Create pie chart with customized labels
        fig = px.pie(
            reason_df,
            values="Count",
            names="Reason",
            title="Sources of Incompleteness",
            hole=0.3
        )
        fig.update_traces(textinfo="percent+label")
        fig.update_layout(font_size=18, width=1000, height=800)
        fig.show()

    def plot_missing_events(self):
        """
        Most common missing events in incomplete cases.
        """
        missing_events_cases = self.incomplete_cases[self.incomplete_cases['issues'].str.startswith('Missing events:')]
        all_missing_events = missing_events_cases['missing_events'].apply(
            lambda x: eval(x) if isinstance(x, str) else set())
        counter = Counter()
        for events in all_missing_events:
            counter.update(events)

        missing_event_counts = pd.DataFrame(counter.items(), columns=["Event", "Count"]).sort_values(by="Count",
                                                                                                         ascending=False)

        fig = px.bar(
            missing_event_counts,
            x="Event",
            y="Count",
            title="Most Common Missing Events in Incomplete Traces",
            labels={"Count": "Frequency", "Event": "Event Name"}
        )
        fig.update_layout(
            xaxis_tickangle=45,
            font_size=20,
            width=1000,
            height=600
        )
        fig.show()

    def plot_complete_cases_pie_chart(self):
        """
        Pie chart of Billed, Cancelled, and Unbillable complete cases.
        """
        billed = len(self.complete_cases[self.complete_cases['isBilled']])
        unbillable = len(self.complete_cases[(self.complete_cases['isUnbillable']) & ~(self.complete_cases['cancelled'])])
        cancelled = len(self.complete_cases[self.complete_cases['cancelled']])

        pie_data = pd.DataFrame({
            "Type": ["Billed", "Unbillable", "Cancelled"],
            "Count": [billed, unbillable, cancelled]
        })

        fig = px.pie(
            pie_data,
            values="Count",
            names="Type",
            title="Complete Cases Breakdown",
            hole=0.3
        )
        fig.update_traces(textinfo="percent+label")
        fig.update_layout(font_size=20, width=800, height=600)
        fig.show()

    def plot_incomplete_trace_last_states(self):
        """
        Create subplots for the frequency of last states and last events for incomplete traces.
        One set of subplots is for cases with the issue "missing events",
        and the other is for cases with the issue "Trace is not finalised".
        """

        missing_events_cases = self.incomplete_cases[
            self.incomplete_cases["issues"].str.contains("Missing events", na=False)]
        not_finalised_cases = self.incomplete_cases[self.incomplete_cases["issues"] == "Trace is not finalised"]

        missing_events_last_states = missing_events_cases["last_state"].value_counts()
        not_finalised_last_states = not_finalised_cases["last_state"].value_counts()

        missing_events_last_events = missing_events_cases["last_event"].value_counts()
        not_finalised_last_events = not_finalised_cases["last_event"].value_counts()

        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=(
                "Last States (Missing Events)", "Last States (Trace is Not Finalised)",
                "Last Events (Missing Events)", "Last Events (Trace is Not Finalised)"
            )
        )

        fig.add_trace(
            go.Bar(
                x=missing_events_last_states.index,
                y=missing_events_last_states.values,
                name="Missing Events - Last States",
                text=missing_events_last_states.values,
                textposition="outside"
            ),
            row=1, col=1
        )
        fig.add_trace(
            go.Bar(
                x=not_finalised_last_states.index,
                y=not_finalised_last_states.values,
                name="Trace Not Finalised - Last States",
                text=not_finalised_last_states.values,
                textposition="outside"
            ),
            row=1, col=2
        )

        # Add bar charts for last events
        fig.add_trace(
            go.Bar(
                x=missing_events_last_events.index,
                y=missing_events_last_events.values,
                name="Missing Events - Last Events",
                text=missing_events_last_events.values,
                textposition="outside"
            ),
            row=2, col=1
        )
        fig.add_trace(
            go.Bar(
                x=not_finalised_last_events.index,
                y=not_finalised_last_events.values,
                name="Trace Not Finalised - Last Events",
                text=not_finalised_last_events.values,
                textposition="outside"  # Show values outside the bars
            ),
            row=2, col=2
        )

        # Update layout
        fig.update_layout(
            title="Last States and Events of Incomplete Traces",
            # xaxis_title="State/Event",
            # yaxis_title="Frequency",
            showlegend=False,
            font_size=18,
            width=1250,
            height=1250,
            template="plotly_white"
        )

        # Adjust tick labels for readability
        fig.update_xaxes(tickangle=45)

        fig.show()

    def plot_trace_classifications_across_deltas(self):
        """
        Plot a stacked bar chart showing the counts of traces classified as COMPLETE, INCOMPLETE, CANCELLED,
        and ONGOING across deltas.
        """
        delta_trace_counts = self.delta_stats[
            ["delta_file_name", "complete_count", "incomplete_count", "ongoing_count"]]
        melted_delta_trace_counts = delta_trace_counts.melt(
            id_vars="delta_file_name",
            var_name="Trace Status",
            value_name="Count"
        )

        trace_status_mapping = {
            "complete_count": "Complete Traces",
            "incomplete_count": "Incomplete Traces",
            "ongoing_count": "Ongoing (Unclassified) Traces"
        }
        melted_delta_trace_counts["Trace Status"] = melted_delta_trace_counts["Trace Status"].map(trace_status_mapping)

        category_order = ["Ongoing (Unclassified) Traces", "Complete Traces", "Incomplete Traces"]

        fig = px.bar(
            melted_delta_trace_counts,
            x="delta_file_name",
            y="Count",
            color="Trace Status",
            title="Trace Classifications Across Deltas",
            labels={"delta_file_name": "Delta", "Count": "Number of Traces"},
            barmode="stack",
            category_orders={"Trace Status": category_order}  # Enforce the custom stack order
        )

        fig.update_layout(
            xaxis_tickangle=45,
            font_size=16,
            hovermode="x unified",
            legend_title="Trace Classifications"
        )

        fig.show()


########################################################################################################################
viz_manager = VisualizationManager(delta_output_path, cases_output_path, focus_deltas)


print("Generating Event Counts Line Chart...")
viz_manager.plot_event_counts_line_chart()

print("Generating Trace Classifications Across Delta...s")
viz_manager.plot_trace_classifications_across_deltas()

print("Generating Case Status Donut Chart...")
viz_manager.plot_case_status_pie_chart()

print("Generating Reasons for Incompleteness Donut Chart...")
viz_manager.plot_incompleteness_reasons()

print("Generating Most Common Missing Events Bar Chart...")
viz_manager.plot_missing_events()

print("Generating Complete Cases Breakdown Donut Chart...")
viz_manager.plot_complete_cases_pie_chart()

print("Generating Last States and Events for Incomplete Traces Subplots...")
viz_manager.plot_incomplete_trace_last_states()

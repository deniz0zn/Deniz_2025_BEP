import plotly.express as px
import plotly.graph_objects as go
import pandas as pd


class VisualizationManager:
    def __init__(self, delta_stats_path, case_output_path):
        self.delta_stats = pd.read_csv(delta_stats_path)
        self.case_stats = pd.read_csv(case_output_path)

        self.complete_cases = self.case_stats[self.case_stats['isComplete']]
        self.cancelled_cases = self.case_stats[self.case_stats['cancelled']]


    def plot_event_counts_line_chart(self):
        """
        Plot a line chart showing the event counts for each delta file.
        """
        # Extract and preprocess event counts

        self.delta_stats = self.delta_stats.drop(index=0)
        print(self.delta_stats.head())
        self.delta_stats["delta_file_name"] = self.delta_stats["delta_file_name"].astype(str)
        event_counts_df = self.delta_stats[["delta_file_name", "event_counts"]]

        # Transform event counts into a structured DataFrame
        event_counts_expanded = pd.json_normalize(event_counts_df["event_counts"].apply(eval))
        event_counts_expanded["delta_file_name"] = event_counts_df["delta_file_name"]

        # Melt the DataFrame for Plotly
        melted_event_counts = event_counts_expanded.melt(id_vars=["delta_file_name"], var_name="Event",
                                                         value_name="Count")

        # Plot the line chart
        fig = px.line(
            melted_event_counts,
            x="delta_file_name",
            y="Count",
            color="Event",
            title="Event Counts Across Delta Files",
            labels={"delta_file_name": "Delta File", "Count": "Event Count"}
        )
        fig.update_layout(hovermode="x unified")
        fig.show()

    def plot_case_status_pie_chart(self):
        """
        Plot a pie chart showing the proportion of cancelled, complete, and incomplete cases.
        """
        # Aggregate data
        cancelled_cases = self.case_stats[self.case_stats["cancelled"]]
        complete_cases = self.case_stats[self.case_stats["isComplete"]]
        ongoing_cases = self.case_stats[self.case_stats["ongoing"]]
        incomplete_cases = self.case_stats[(self.case_stats["cancelled"] == False) & (self.case_stats["isComplete"] ==False) & (self.case_stats["ongoing"] == False)]

        # Prepare data for the pie chart
        pie_data = pd.DataFrame({
            "Status": ["Cancelled Cases", "Complete Cases", "Incomplete Cases", "Ongoing Cases"],
            "Count": [len(cancelled_cases), len(complete_cases), len(incomplete_cases), len(ongoing_cases)]
        })

        # Plot the pie chart
        fig = px.pie(
            pie_data,
            values="Count",
            names="Status",
            title="Case Status Distribution",
            hole=0.3
        )
        fig.update_traces(textinfo="percent+label")
        fig.show()




delta_stats_path = "Dataset/Hospital Billing Delta Logs/Delta Stats/delta_stats_Hospital Billing - Event Log_weekly_(8).csv"
case_output_path = "Dataset/Hospital Billing Delta Logs/cases_output/cases_output_Hospital Billing - Event Log_weekly_(8).csv"

# Initialize Visualization Manager
viz_manager = VisualizationManager(delta_stats_path, case_output_path)

# Generate Visualizations
print("Generating Event Counts Line Chart...")
viz_manager.plot_event_counts_line_chart()

print("Generating Case Status Pie Chart...")
viz_manager.plot_case_status_pie_chart()



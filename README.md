# Trace Completeness Evaluation Framework

## Description
This project provides a robust framework for processing and analyzing event logs by dividing them into delta logs and tracking trace completeness across multiple criteria. The framework processes large datasets efficiently, visualizes results interactively, and provides detailed metrics for evaluation.

---

## Key Features
- **Event Log Splitting**: Converts event logs into delta logs.
- **Trace Classification**: Classifies traces into `Complete`, `Incomplete`, or `Ongoing`.
- **Delta Analysis**: Extracts statistics and metrics for each delta file.
- **Visualization**: Provides a range of interactive plots for understanding trace and delta behaviors.
- **Evaluation**: Enables trace sampling and evaluation for manual review and accuracy checks.

---

## Modules Used
- `pandas`: Data manipulation and processing.
- `plotly`: Interactive visualizations.
  - [Plotly](https://plotly.com/) documentation.
- `os`: Path and directory operations.
- `json`: Handling nested data structures.
- `collections.Counter`: Simplified frequency counting.

---

## Configuration
The project uses a configuration file (`config.py`) for setting key parameters and paths:

```python
# Event log file path
event_log_path = 'Dataset/csv/Hospital Billing - Event Log.csv'

# Splitting frequency for delta logs
frequency = 'weekly'  # Options: 'daily', 'weekly', 'monthly'

# Initial time frame for splitting (in months)
initial_months = 1

# Delta log output directories
delta_log_dir = f'Dataset/Hospital Billing Delta Logs/{filename}_{frequency}_({initial_months})'
cases_output_path = f"Dataset/Hospital Billing Delta Logs/cases_output/cases_output_{frequency}_({initial_months}).csv"
delta_output_path = f"Dataset/Hospital Billing Delta Logs/Delta Stats/delta_stats_{frequency}_({initial_months}).csv"
evaluation_output_path = f"Dataset/Hospital Billing Delta Logs/evaluation/eval_{frequency}_({initial_months}).csv"

# Trace processing parameters
max_days = 190
test_eval = False  # If True, skips processing and uses existing outputs for evaluaiton (when evaluaiton.py is run)

# Visualization filters
focus_deltas = []  # Specify deltas to include in visualizations, e.g., ["2013_w46", "2013_w47"]
```
- **`event_log_path`** in the configuration points to a specific CSV file within this folder.
- **`cases_output_path`** specifies the location for saving case output CSV files.
- **`delta_output_path`** points to the file storing delta statistics.
- **`evaluation_output_path`** is configured for saving evaluation results.

  
## Directory Structure
```bash
├── case.py                   # Core case object definition and status handling
├── config.py                 # Configuration file for paths and parameters
├── delta.py                  # Delta object handling for trace updates
├── delta_log_formation.py    # Logic for splitting event logs into delta logs
├── evaluation.py             # Evaluation
├── main.py                   # Entry point for the entire project pipeline
├── process.py                # Core processing logic for events and traces
├── test_processing_time.py   # Script for benchmarking processing time
├── visualize.py              # Visualization manager for interactive plots
├── requirements.txt          # Python dependencies for the project
├── Dataset/                  # Dataset directory
│   ├── csv/                  # Contains input CSV event logs
│   ├── Hospital Billing Delta Logs/
│       ├── run_time_results.csv     # Runtime performance results
│       ├── cases_output/            # Outputs for processed cases
│       ├── Delta Stats/             # Delta statistics from logs
│       ├── evaluation/              # Evaluation results
│       └── Hospital Billing - Event Log_daily_(1)/  # Example delta log directory
```
### Key Directories
- **`Dataset/`**: Contains all input data and processed outputs.
  - **`csv/`**: Houses raw CSV event logs used as input.  
  - **`Hospital Billing Delta Logs/`**: Stores all delta log outputs and related data.  
    - **`delta_log_dir`** is set to this folder for storing delta files.  
    - **`cases_output/`**: Processed case-level outputs.  
    - **`Delta Stats/`**: Metrics and statistics derived from delta logs.  
    - **`evaluation/`**: Manual review and evaluation results.  
    - **`run_time_results.csv`**: Runtime performance data for delta processing.  
    - Subfolders for each processed delta (e.g., `Hospital Billing - Event Log_daily_(1)/`).  

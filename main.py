# from analyse import VisualizationManager
from process import ProcessManager
from config import initial_months, frequency, output_dir

if __name__ == "__main__":
    process_manager = ProcessManager(initial_months, frequency, output_dir)
    process_manager.run()


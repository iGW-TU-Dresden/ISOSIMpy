import matplotlib.pyplot as plt
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QFileDialog, QMessageBox, QPushButton, QVBoxLayout, QWidget


class SimulationTab(QWidget):
    simulate_requested = pyqtSignal()
    calibrate_requested = pyqtSignal()
    report_requested = pyqtSignal(str)  # carries the file path

    def __init__(self, state, parent=None):
        super().__init__(parent)
        self.state = state

        lay = QVBoxLayout(self)

        # Simulation button
        b_sim = QPushButton("Run Simulation")
        b_sim.clicked.connect(self.simulate_requested)

        # Calibration button
        b_cal = QPushButton("Run Calibration")
        b_cal.clicked.connect(self.calibrate_requested)

        # Plot button
        b_plot = QPushButton("Plot Results")
        b_plot.clicked.connect(self._plot)

        # Report button
        b_report = QPushButton("Write Report")
        b_report.clicked.connect(self._choose_report_file)

        # Add widgets
        lay.addWidget(b_sim)
        lay.addWidget(b_cal)
        lay.addStretch(1)
        lay.addWidget(b_plot)
        lay.addStretch(1)
        lay.addWidget(b_report)

    def _choose_report_file(self):
        """Open save dialog and emit signal with chosen filename."""
        fname, _ = QFileDialog.getSaveFileName(
            self,
            "Save Report",
            "report.txt",  # default filename
            "Text Files (*.txt);;All Files (*)",  # filters
        )
        if fname:  # user clicked OK
            self.report_requested.emit(fname)

    def show_results(self, sim):
        # keep last sim in state; plotting button uses it
        self.state.last_simulation = sim

    def show_status(self, msg):
        QMessageBox.information(self, "Status", msg)

    def _plot(self):
        if self.state.last_simulation is None or self.state.input_series is None:
            QMessageBox.information(self, "Plot", "Nothing to plot yet.")
            return
        times = self.state.input_series[0]
        obs = self.state.target_series[1] if self.state.target_series else None
        fig, ax = plt.subplots(figsize=(8, 4))
        if obs is not None:
            ax.scatter(times, obs, label="Observations", marker="x", zorder=100)
        ax.plot(times, self.state.last_simulation, label="Simulation", c="k")
        ax.set_yscale("log")
        ax.legend()
        fig.tight_layout()
        plt.show()

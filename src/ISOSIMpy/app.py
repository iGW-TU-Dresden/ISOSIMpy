import sys
from datetime import datetime

import matplotlib.pyplot as plt
import numpy as np
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QApplication,
    QButtonGroup,
    QCheckBox,
    QFileDialog,
    QGridLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QRadioButton,
    QScrollArea,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from . import model as mm

### Information
#
# This is the main application window for the ISOSIMpy GUI.
# It is split into different window tabs for different parts of the workflow:
#   1. Input Files / Data
#   2. Model Design
#   3. Parameters
#   4. Simulation /  Calibration
#
# The app does not automatically include all functionality of
# ISOSIMpy.model.

# define default values for all units
DEFAULTS = {
    "EPM": {
        "class": mm.EPMUnit,
        "name": "EPM",
        "param_names": ["Mean Transit Time", "Eta"],
        "default_values": [120.0, 1.1],
        "bounds": [(0.0, 1000.0), (1.0, 2.0)],
    },
    "PM": {
        "class": mm.PMUnit,
        "name": "PM",
        "param_names": ["Mean Transit Time"],
        "default_values": [240.0],
        "bounds": [(0.0, 2000.0)],
    },
    "EM": {
        "class": mm.EMUnit,
        "name": "EM",
        "param_names": ["Mean Transit Time"],
        "default_values": [240.0],
        "bounds": [(0.0, 2000.0)],
    },
}


# the main application window
class CalibrationApp(QWidget):
    """
    The main application window class.

    Attributes
    ----------
    units_selected : dict
        Dictionary of selected units.
    unit_objects : list
        List of unit objects.
    param_entries : list
        List of parameter values.
    unit_fractions_entries : list
        List of unit fractions entry widgets.
    fixed_checkboxes : list
        List of fixed checkbox widgets.
    lower_bounds : list
        List of lower bound values for all parameters.
    upper_bounds : list
        List of upper bound values for all parameters.
    input_series : tuple
        Input time series as a tuple of arrays of time steps / dates and
        values.
    target_series : tuple
        Input time series as a tuple of arrays of time steps / dates and
        values.
    is_monthly : bool
        Whether the input time series is monthly or yearly.
    tracer : str
        The tracer type. Currently ISOSIMpy supports Tritium and Carbon-14.
    steady_state_input : float
        Steady-state input as a single float.
    n_warmup_half_lives : int
        The number of half-lives to use for warmup.
    """

    def __init__(self):
        """
        The main application window class initialization.

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        super().__init__()
        self.setWindowTitle("ISOSIMpy App v2")
        self.units_selected = {}
        self.unit_objects = []
        self.param_entries = []
        self.unit_fractions_entries = []
        self.fixed_checkboxes = []
        self.lower_bounds = []
        self.upper_bounds = []
        self.input_series = None
        self.target_series = None
        self.is_monthly = True
        self.tracer = "Tritium"
        self.steady_state_input = None
        self.n_warmup_half_lives = None

        self.initUI()

    def initUI(self):
        """
        Iintialize the user interface.

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        layout = QVBoxLayout(self)

        self.tabs = QTabWidget()
        self.file_input_tab = QWidget()
        self.model_design_tab = QWidget()
        self.parameters_tab = QWidget()
        self.calibration_tab = QWidget()

        self.tabs.addTab(self.file_input_tab, "[1] Input")
        self.tabs.addTab(self.model_design_tab, "[2] Model Design")
        self.tabs.addTab(self.parameters_tab, "[3] Parameters")
        self.tabs.addTab(self.calibration_tab, "[4] Simulation")

        self.init_file_input_tab()
        self.init_model_design_tab()
        self.init_parameters_tab()
        self.init_calibration_tab()

        self.setFixedSize(800, 600)
        layout.addWidget(self.tabs)
        self.setLayout(layout)

    #
    ##
    ### TAB 1: File Input ###
    ##
    #
    def init_file_input_tab(self):
        """
        Initialize the file input tab.

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        layout = QVBoxLayout()

        # Radio buttons for frequency selection
        freq_label = QLabel("Select time series frequency:")
        self.monthly_radio = QRadioButton("Monthly")
        self.yearly_radio = QRadioButton("Yearly")
        self.monthly_radio.setChecked(True)

        self.freq_group = QButtonGroup()
        self.freq_group.addButton(self.monthly_radio)
        self.freq_group.addButton(self.yearly_radio)
        self.monthly_radio.toggled.connect(self.update_frequency)

        # Radio buttons for tracer selection
        tracer_label = QLabel("Select tracer:")
        self.tritium_radio = QRadioButton("Tritium")
        self.carbon_radio = QRadioButton("Carbon-14")
        self.tritium_radio.setChecked(True)

        self.tracer_group = QButtonGroup()
        self.tracer_group.addButton(self.tritium_radio)
        self.tracer_group.addButton(self.carbon_radio)
        self.tritium_radio.toggled.connect(self.update_tracer)

        self.input_file_label = QLabel("No input series file selected")
        self.target_file_label = QLabel("No target series file selected")

        select_input_btn = QPushButton("Select Input Series CSV")
        select_input_btn.clicked.connect(self.load_input_series)

        select_target_btn = QPushButton("Select Target Series CSV")
        select_target_btn.clicked.connect(self.load_target_series)

        layout.addWidget(freq_label)
        layout.addWidget(self.monthly_radio)
        layout.addWidget(self.yearly_radio)
        layout.addSpacing(20)
        layout.addWidget(tracer_label)
        layout.addWidget(self.tritium_radio)
        layout.addWidget(self.carbon_radio)
        layout.addSpacing(20)
        layout.addWidget(select_input_btn)
        layout.addWidget(self.input_file_label)
        layout.addSpacing(10)
        layout.addWidget(select_target_btn)
        layout.addWidget(self.target_file_label)

        self.file_input_tab.setLayout(layout)

    def update_frequency(self):
        """
        Update the model frequency (monthly or yearly).

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        self.is_monthly = self.monthly_radio.isChecked()

    def update_tracer(self):
        """
        Update the tracer type (Tritium or Carbon-14).

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        if self.tritium_radio.isChecked():
            self.tracer = "Tritium"
        elif self.carbon_radio.isChecked():
            self.tracer = "Carbon-14"

    def load_input_series(self):
        """
        Load input time series from a CSV file.

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        file_name, _ = QFileDialog.getOpenFileName(
            self, "Open Input Series CSV", "", "CSV Files (*.csv)"
        )
        if file_name:
            try:
                data = np.genfromtxt(
                    file_name, delimiter=",", dtype=["<U7", float], encoding="utf-8", skip_header=1
                )

                if self.is_monthly:
                    timestamps = np.array([datetime.strptime(row[0], r"%Y-%m") for row in data])
                else:
                    timestamps = np.array([datetime.strptime(row[0], r"%Y") for row in data])
                values = np.array([float(row[1]) for row in data])
                self.input_series = (timestamps, values)
                self.input_file_label.setText(f"Loaded: {file_name}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load input file:\n{str(e)}")

    def load_target_series(self):
        """
        Load target time series from a CSV file.

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        file_name, _ = QFileDialog.getOpenFileName(
            self, "Open Target Series CSV", "", "CSV Files (*.csv)"
        )
        if file_name:
            try:
                data = np.genfromtxt(
                    file_name, delimiter=",", dtype=["<U7", float], encoding="utf-8", skip_header=1
                )

                if self.is_monthly:
                    timestamps = np.array([datetime.strptime(row[0], "%Y-%m") for row in data])
                else:
                    timestamps = np.array([datetime.strptime(row[0], "%Y") for row in data])
                values = np.array([float(row[1]) for row in data])
                self.target_series = (timestamps, values)
                self.target_file_label.setText(f"Loaded: {file_name}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load target file:\n{str(e)}")

    #
    ##
    ### TAB 2: Model Design ###
    ##
    #
    def init_model_design_tab(self):
        """
        Initialize the model design tab.

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        layout = QVBoxLayout()

        self.epm_box = QCheckBox("Include EPM Unit")
        self.pm_box = QCheckBox("Include PM Unit")
        self.em_box = QCheckBox("Include EM Unit")
        self.epm_box.setChecked(True)
        self.pm_box.setChecked(True)
        self.em_box.setChecked(True)

        layout.addWidget(QLabel("Select which units to include in the model:"))
        layout.addWidget(self.epm_box)
        layout.addWidget(self.pm_box)
        layout.addWidget(self.em_box)

        update_btn = QPushButton("Update Parameters")
        update_btn.clicked.connect(self.update_parameters_tab)
        layout.addWidget(update_btn)

        self.model_design_tab.setLayout(layout)

    #
    ##
    ### TAB 3: Parameter Assignment ###
    ##
    #
    def init_parameters_tab(self):
        """
        Initialize the parameter assignment tab.

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        self.param_layout = QGridLayout()

        self.param_container = QWidget()
        self.param_container.setLayout(self.param_layout)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self.param_container)

        layout = QVBoxLayout()
        layout.addWidget(scroll)

        self.parameters_tab.setLayout(layout)

    def update_parameters_tab(self):
        """
        Update the parameter assignment tab.

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        # Clear layout and storage
        for i in reversed(range(self.param_layout.count())):
            widget = self.param_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)

        self.param_entries.clear()
        self.fixed_checkboxes.clear()
        self.unit_fractions_entries.clear()
        self.lower_bounds.clear()
        self.upper_bounds.clear()
        self.unit_objects.clear()

        # Add column headers
        header_labels = ["Parameter", "Lower Bound", "Initial Value", "Upper Bound", "Fixed?"]
        for col, text in enumerate(header_labels):
            header = QLabel(f"<b>{text}</b>")
            header.setStyleSheet("background-color: #e0e0e0; padding: 5px;")
            header.setAlignment(Qt.AlignCenter)
            header.setFixedHeight(30)
            self.param_layout.addWidget(header, 0, col)

        row = 1

        n_units = sum([self.epm_box.isChecked(), self.pm_box.isChecked(), self.em_box.isChecked()])

        for unit_key in ["EPM", "PM", "EM"]:
            if (
                (unit_key == "EPM" and self.epm_box.isChecked())
                or (unit_key == "PM" and self.pm_box.isChecked())
                or (unit_key == "EM" and self.em_box.isChecked())
            ):

                info = DEFAULTS[unit_key]
                param_names = info["param_names"]
                defaults = info["default_values"]
                bounds = info["bounds"]

                for j, pname in enumerate(param_names):
                    label = QLabel(f"{info['name']} - {pname}")
                    lb_entry = QLineEdit(str(bounds[j][0]))
                    val_entry = QLineEdit(str(defaults[j]))
                    ub_entry = QLineEdit(str(bounds[j][1]))
                    fixed = QCheckBox("Fixed")

                    self.param_layout.addWidget(label, row, 0)
                    self.param_layout.addWidget(lb_entry, row, 1)
                    self.param_layout.addWidget(val_entry, row, 2)
                    self.param_layout.addWidget(ub_entry, row, 3)
                    self.param_layout.addWidget(fixed, row, 4)

                    self.lower_bounds.append(lb_entry)
                    self.param_entries.append(val_entry)
                    self.upper_bounds.append(ub_entry)
                    self.fixed_checkboxes.append(fixed)
                    row += 1

                # Mix param (no bounds/fixed)
                mix_label = QLabel(f"{info['name']} - Mix")
                mix_entry = QLineEdit("{:.1f}".format(1 / n_units))
                self.param_layout.addWidget(mix_label, row, 0)
                self.param_layout.addWidget(mix_entry, row, 2)  # center column
                self.param_layout.addWidget(QWidget(), row, 1)  # filler
                self.param_layout.addWidget(QWidget(), row, 3)  # filler
                self.param_layout.addWidget(QWidget(), row, 4)  # no checkbox

                self.unit_fractions_entries.append(mix_entry)
                row += 1

        # steady state param (no bounds/fixed)
        ss_label = QLabel("Steady State Input")
        ss_entry = QLineEdit("0.0")
        self.steady_state_input = ss_entry
        self.param_layout.addWidget(ss_label, row, 0)
        self.param_layout.addWidget(ss_entry, row, 2)  # center column
        self.param_layout.addWidget(QWidget(), row, 1)  # filler
        self.param_layout.addWidget(QWidget(), row, 3)  # filler
        self.param_layout.addWidget(QWidget(), row, 4)  # no checkbox

        # warmup
        warmup_label = QLabel("Warmup, No. of Half Lives")
        warmup_entry = QLineEdit("2")
        self.n_warmup_half_lives = warmup_entry
        self.param_layout.addWidget(warmup_label, row + 1, 0)
        self.param_layout.addWidget(warmup_entry, row + 1, 2)  # center column
        self.param_layout.addWidget(QWidget(), row + 1, 1)  # filler
        self.param_layout.addWidget(QWidget(), row + 1, 3)  # filler
        self.param_layout.addWidget(QWidget(), row + 1, 4)  # no checkbox

    #
    ##
    ### TAB 4: Calibration ###
    ##
    #
    def init_calibration_tab(self):
        """
        Initialize the calibration tab.

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        layout = QVBoxLayout()

        # Initialize calibration status
        self.model_is_calibrated = False

        # Simulation button
        run_button = QPushButton("Run Simulation")
        run_button.clicked.connect(lambda: self.run_calibration(False))
        layout.addWidget(run_button)

        # Calibration button
        run_button = QPushButton("Run Calibration")
        run_button.clicked.connect(lambda: self.run_calibration(True))
        layout.addWidget(run_button)

        # Add space
        layout.addStretch(1)

        # Plot button
        plot_button = QPushButton("Plot Results")
        plot_button.clicked.connect(lambda: self.plotting())
        layout.addWidget(plot_button)

        # Report button
        report_button = QPushButton("Write Report")
        report_button.clicked.connect(
            lambda: self.write_report(self.model_is_calibrated)  # pass calibration status
        )
        layout.addWidget(report_button)

        self.calibration_tab.setLayout(layout)

    def run_calibration(self, calibrate):
        """
        Run the calibration.

        Parameters
        ----------
        calibrate : bool
            Whether to run the calibration (True) or simple forward
            simulation (False).

        Returns
        -------
        None
        """
        # Check time series
        if not np.all(self.input_series[0] == self.target_series[0]):
            QMessageBox.critical(
                self, "Error", "Input and target series must have the same timestamps"
            )
        try:
            # Define time step
            if self.is_monthly:
                dt = 1.0
                # Define lambda
                if self.tracer == "Tritium":
                    lambda_ = 0.693 / (12.33 * 12.0)
                elif self.tracer == "Carbon-14":
                    lambda_ = 0.693 / (5700.0 * 12.0)
            else:
                dt = 12.0
                # Define lambda
                if self.tracer == "Tritium":
                    lambda_ = 0.693 / (12.33)
                elif self.tracer == "Carbon-14":
                    lambda_ = 0.693 / (5700.0)

            # Get time series and time stamps
            times = self.input_series[0]
            input_series = self.input_series[1]
            target_series = self.target_series[1]

            ### Set up model
            # Get parameter values and fixed parameters from widgets
            params = [float(e.text()) for e in self.param_entries]
            fixed = [cb.isChecked() for cb in self.fixed_checkboxes]

            # Reconstruct selected units
            # At the moment, this is a bit unflexible as we only allow
            # for one unit of each type and parallel units.
            selected_keys = []
            if self.epm_box.isChecked():
                selected_keys.append("EPM")
            if self.pm_box.isChecked():
                selected_keys.append("PM")
            if self.em_box.isChecked():
                selected_keys.append("EM")

            # Initialize model
            ml = mm.Model(
                dt,
                lambda_,
                input_series,
                target_series,
                steady_state_input=float(self.steady_state_input.text()),
                n_warmup_half_lives=int(self.n_warmup_half_lives.text()),
            )

            # Initialize bound list (bounds of all units and parameters)
            # and iterate over selected units. Add units, bounds etc. to the
            # model.
            bounds_list = []
            param_counter = 0
            for num, unit_key in enumerate(selected_keys):
                n_params = len(DEFAULTS[unit_key]["param_names"])
                unit_bounds = []
                unit_params = []
                unit_fixed = []
                for _ in range(n_params):
                    # Get bounds and initial value
                    lb = float(self.lower_bounds[param_counter].text())
                    ub = float(self.upper_bounds[param_counter].text())
                    init_val = params[param_counter]
                    fixed_param = fixed[param_counter]
                    # Append to lists
                    unit_params.append(init_val)
                    unit_bounds.append((lb, ub))
                    unit_fixed.append(fixed_param)
                    # Increment counter
                    param_counter += 1

                # Add unit to model
                if unit_key == "EPM":
                    new_unit = mm.EPMUnit(mtt=unit_params[0], eta=unit_params[1])
                    ml.add_unit(
                        unit=new_unit,
                        fraction=float(self.unit_fractions_entries[num].text()),
                        prefix="epm",
                        bounds=unit_bounds,
                    )
                    ml.set_fixed("epm.mtt", unit_fixed[0])
                    ml.set_fixed("epm.eta", unit_fixed[1])
                elif unit_key == "PM":
                    new_unit = mm.PMUnit(mtt=unit_params[0])
                    ml.add_unit(
                        unit=new_unit,
                        fraction=float(self.unit_fractions_entries[num].text()),
                        prefix="pm",
                        bounds=unit_bounds,
                    )
                    ml.set_fixed("pm.mtt", unit_fixed[0])
                elif unit_key == "EM":
                    new_unit = mm.EMUnit(mtt=unit_params[0])
                    ml.add_unit(
                        unit=new_unit,
                        fraction=float(self.unit_fractions_entries[num].text()),
                        prefix="em",
                        bounds=unit_bounds,
                    )
                    ml.set_fixed("em.mtt", unit_fixed[0])

                # Add bounds to global list
                bounds_list.append(unit_bounds)

            # Add solver to the model
            solver = mm.Solver(model=ml)

            # Calibrate the model or just simulate with current parameters.
            if calibrate:
                opt_params, opt_sim = solver.solve()
                QMessageBox.information(self, "Status", "Calibration finished.")
                self.model_is_calibrated = True
            else:
                opt_sim = ml.simulate()
                QMessageBox.information(self, "Status", "Simulation finished.")

            # Store data for plotting
            self.plot_sim = opt_sim
            self.plot_times = times
            self.plot_target = target_series
            self.model = ml

        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def plotting(self):
        """
        Plot output series and observations.
        """

        # Plotting
        fig, ax = plt.subplots(figsize=(8, 4))
        # ax.plot(times, input_series, label="Input")
        ax.plot(
            self.plot_times, self.plot_target, label="Observations", c="r", marker="x", zorder=10
        )
        ax.plot(self.plot_times, self.plot_sim, label="Simulation", c="k", lw=3)
        ax.set_yscale("log")
        # ax.set_ylim(0.1, 12)
        ax.legend()
        plt.tight_layout()
        plt.show()

    def write_report(self, calibrate):
        # write to txt file
        if not calibrate:
            if self.model.target_series is None:
                QMessageBox.information(
                    self, "Status", "The model has no target series, cannot create report."
                )
            else:
                QMessageBox.information(self, "Status", "The model has not been calibrated yet.")

        if self.is_monthly:
            frequency = "1 month"
        else:
            frequency = "1 year"

        _ = self.model.write_report(
            filepath="report.txt",
            frequency=frequency,
            sim=self.plot_sim,
            title="Model Report",
            include_initials=True,
            include_bounds=True,
        )


# if __name__ == "__main__":
#     import sys
#     import numpy as np
#     import matplotlib.pyplot as plt
#     from datetime import datetime

#     import scipy
#     from scipy.optimize import differential_evolution

#     from PyQt5.QtWidgets import (
#         QApplication, QWidget, QTabWidget, QVBoxLayout, QHBoxLayout,
#         QLabel, QCheckBox, QPushButton, QLineEdit, QGridLayout, QMessageBox,
#         QScrollArea
#     )
#     from PyQt5.QtCore import Qt

#     import model as mm

#     app = QApplication(sys.argv)
#     window = CalibrationApp()
#     window.show()
#     sys.exit(app.exec_())


def main():
    app = QApplication(sys.argv)
    window = CalibrationApp()
    window.show()
    sys.exit(app.exec_())

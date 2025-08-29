from PyQt5.QtWidgets import QMessageBox, QTabWidget, QVBoxLayout, QWidget

from ..model.registry import UNIT_REGISTRY
from .controller import Controller
from .state import AppState
from .tabs.file_input import FileInputTab
from .tabs.model_design import ModelDesignTab
from .tabs.parameters import ParametersTab
from .tabs.simulation import SimulationTab


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ISOSIMpy")
        self.state = AppState()
        self.ctrl = Controller(self.state)

        tabs = QTabWidget()
        t1 = FileInputTab(self.state)
        t2 = ModelDesignTab(self.state, UNIT_REGISTRY)
        t3 = ParametersTab(self.state, UNIT_REGISTRY)
        t4 = SimulationTab(self.state)

        tabs.addTab(t1, "[1] Input")
        tabs.addTab(t2, "[2] Model")
        tabs.addTab(t3, "[3] Parameters")
        tabs.addTab(t4, "[4] Simulation")

        lay = QVBoxLayout(self)
        lay.addWidget(tabs)

        # wiring
        t1.changed.connect(t3.refresh)
        t2.selection_changed.connect(t3.refresh)
        t4.simulate_requested.connect(lambda: (t3.commit(), self.ctrl.simulate()))
        t4.calibrate_requested.connect(lambda: (t3.commit(), self.ctrl.calibrate()))
        t4.report_requested.connect(lambda fname: (t3.commit(), self.ctrl.write_report(fname)))

        self.ctrl.simulated.connect(t4.show_results)
        self.ctrl.calibrated.connect(t4.show_results)
        self.ctrl.status.connect(t4.show_status)
        self.ctrl.error.connect(lambda m: QMessageBox.critical(self, "Error", m))

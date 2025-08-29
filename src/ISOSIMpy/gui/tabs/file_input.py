from datetime import datetime

import numpy as np
from PyQt5.QtCore import QSize, pyqtSignal
from PyQt5.QtWidgets import (
    QButtonGroup,
    QFileDialog,
    QLabel,
    QPushButton,
    QRadioButton,
    QVBoxLayout,
    QWidget,
)


class FileInputTab(QWidget):
    changed = pyqtSignal()

    def __init__(self, state, parent=None):
        super().__init__(parent)
        self.state = state
        lay = QVBoxLayout(self)

        ### Temporal reolution selection radio buttons
        self.monthly = QRadioButton("Monthly")
        self.monthly.setChecked(True)
        self.yearly = QRadioButton("Yearly")
        g1 = QButtonGroup(self)
        g1.addButton(self.monthly)
        g1.addButton(self.yearly)
        # Set title, add widgets
        lbl = QLabel("Frequency")
        lbl.setStyleSheet("font-weight: 600;")
        lay.addWidget(lbl)
        lay.addWidget(self.monthly)
        lay.addWidget(self.yearly)

        ### Tracer Selection radio buttons
        self.t_h3 = QRadioButton("Tritium")
        self.t_h3.setChecked(True)
        self.t_c14 = QRadioButton("Carbon-14")
        g2 = QButtonGroup(self)
        g2.addButton(self.t_h3)
        g2.addButton(self.t_c14)
        # Set title, add widgets
        lbl = QLabel("Tracer")
        lbl.setStyleSheet("font-weight: 600;")
        lay.addWidget(lbl)
        lay.addWidget(self.t_h3)
        lay.addWidget(self.t_c14)

        ### Input and target series selection buttons
        self.lbl_in = QLabel("No input series selected")
        self.lbl_tg = QLabel("No observation series selected")
        b_in = QPushButton("Select Input CSV")
        b_in.setFixedSize(QSize(200, 40))
        b_in.clicked.connect(self._open_input)
        b_tg = QPushButton("Select Observation CSV")
        b_tg.setFixedSize(QSize(200, 40))
        b_tg.clicked.connect(self._open_target)
        # Set title, add widgets
        lbl = QLabel("Input and Observation Series")
        lbl.setStyleSheet("font-weight: 600;")
        lay.addWidget(lbl)
        lay.addWidget(b_in)
        lay.addWidget(self.lbl_in)
        lay.addWidget(b_tg)
        lay.addWidget(self.lbl_tg)

        # Signal connections
        self.monthly.toggled.connect(self._freq_changed)
        self.t_h3.toggled.connect(self._tracer_changed)

    def _freq_changed(self, checked):
        self.state.is_monthly = checked
        self.changed.emit()

    def _tracer_changed(self, checked):
        self.state.tracer = "Tritium" if checked else "Carbon-14"
        self.changed.emit()

    def _read_csv(self, path, monthly=True):
        data = np.genfromtxt(
            path, delimiter=",", dtype=["<U7", float], encoding="utf-8", skip_header=1
        )
        fmt = "%Y-%m" if monthly else "%Y"
        ts = np.array([datetime.strptime(row[0], fmt) for row in data])
        vals = np.array([float(row[1]) for row in data])
        return ts, vals

    def _open_input(self):
        file, _ = QFileDialog.getOpenFileName(
            self, "Open Input Series CSV", "", "CSV Files (*.csv)"
        )
        if file:
            self.state.input_series = self._read_csv(file, self.state.is_monthly)
            self.lbl_in.setText(f"Loaded: {file}")
            self.changed.emit()

    def _open_target(self):
        file, _ = QFileDialog.getOpenFileName(
            self, "Open Observation Series CSV", "", "CSV Files (*.csv)"
        )
        if file:
            self.state.target_series = self._read_csv(file, self.state.is_monthly)
            self.lbl_tg.setText(f"Loaded: {file}")
            self.changed.emit()

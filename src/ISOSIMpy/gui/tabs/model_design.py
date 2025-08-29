from functools import partial

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QDoubleValidator, QFont
from PyQt5.QtWidgets import (
    QCheckBox,
    QGridLayout,
    QLabel,
    QLineEdit,
    QSizePolicy,
    QSpacerItem,
    QVBoxLayout,
    QWidget,
)
from PyQt5.QtWidgets import (
    QSizePolicy as SP,
)


class ModelDesignTab(QWidget):
    selection_changed = pyqtSignal()

    def __init__(self, state, registry, parent=None):
        super().__init__(parent)
        self.state = state
        self.registry = registry
        self.boxes = {}
        self.fracs = {}

        # ensure attributes exist on state
        if not hasattr(self.state, "unit_fractions"):
            self.state.unit_fractions = {}
        if not hasattr(self.state, "steady_state_input"):
            self.state.steady_state_input = 0.0
        if not hasattr(self.state, "steady_state_enabled"):
            self.state.steady_state_enabled = False
        if not hasattr(self.state, "n_warmup_half_lives"):
            self.state.n_warmup_half_lives = 0.0

        outer = QVBoxLayout(self)
        outer.setContentsMargins(12, 12, 12, 12)
        outer.setSpacing(8)

        # Title
        title = QLabel("Include units and set fractions:")
        title_font = QFont(title.font())
        title_font.setBold(True)
        title.setFont(title_font)
        outer.addWidget(title)

        # Main grid
        grid = QGridLayout()
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(6)
        outer.addLayout(grid)

        ### Unit section headers
        hdr_unit = QLabel("Unit")
        hdr_frac = QLabel("Fraction")
        hdr_unit.setStyleSheet("font-weight: 600;")
        hdr_frac.setStyleSheet("font-weight: 600;")
        grid.addWidget(hdr_unit, 0, 0, alignment=Qt.AlignLeft | Qt.AlignVCenter)
        grid.addWidget(hdr_frac, 0, 1, alignment=Qt.AlignLeft | Qt.AlignVCenter)

        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 0)

        # Float validator
        validator = QDoubleValidator(self)
        validator.setNotation(QDoubleValidator.StandardNotation)
        validator.setDecimals(6)

        # Width probe
        probe = QLineEdit()
        fm = probe.fontMetrics()
        frac_width = fm.horizontalAdvance(" -0.0000 ") + 18

        ### Unit rows
        row = 1
        for name, cls in self.registry.items():
            cb = QCheckBox(name, self)
            cb.setChecked(False)
            self.boxes[name] = cb

            fx = QLineEdit(self)
            fx.setText("0.0000")
            fx.setAlignment(Qt.AlignRight)
            fx.setValidator(validator)
            fx.setMaximumWidth(frac_width)
            fx.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
            fx.setEnabled(False)
            self.fracs[cls.PREFIX] = fx

            grid.addWidget(cb, row, 0, alignment=Qt.AlignLeft | Qt.AlignVCenter)
            grid.addWidget(fx, row, 1, alignment=Qt.AlignLeft | Qt.AlignVCenter)

            cb.toggled.connect(partial(self._on_toggle, prefix=cls.PREFIX))
            fx.textChanged.connect(self._update)

            row += 1

        # spacer between sections
        grid.addItem(QSpacerItem(0, 10, SP.Minimum, SP.Minimum), row, 0)
        row += 1

        ### Steady-state section headers
        hdr_ss = QLabel("Steady-State Input")
        hdr_val = QLabel("Value")
        hdr_ss.setStyleSheet("font-weight: 600;")
        hdr_val.setStyleSheet("font-weight: 600;")
        grid.addWidget(hdr_ss, row, 0, alignment=Qt.AlignLeft | Qt.AlignVCenter)
        grid.addWidget(hdr_val, row, 1, alignment=Qt.AlignLeft | Qt.AlignVCenter)
        row += 1

        # Steady-state controls
        self.ss_checkbox = QCheckBox("", self)
        self.ss_checkbox.setChecked(bool(self.state.steady_state_enabled))

        self.ss_value = QLineEdit(self)
        self.ss_value.setText(f"{float(self.state.steady_state_input):.4f}")
        self.ss_value.setAlignment(Qt.AlignRight)
        self.ss_value.setValidator(validator)
        self.ss_value.setMaximumWidth(frac_width)
        self.ss_value.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.ss_value.setEnabled(self.ss_checkbox.isChecked())

        grid.addWidget(self.ss_checkbox, row, 0, alignment=Qt.AlignLeft | Qt.AlignVCenter)
        grid.addWidget(self.ss_value, row, 1, alignment=Qt.AlignLeft | Qt.AlignVCenter)

        self.ss_checkbox.toggled.connect(self._on_ss_toggle)
        self.ss_value.textChanged.connect(self._update)
        row += 1

        # spacer
        grid.addItem(QSpacerItem(0, 10, SP.Minimum, SP.Minimum), row, 0)
        row += 1

        ### Warmup half lives header
        hdr_warm = QLabel("Warmup half lives")
        hdr_warm.setStyleSheet("font-weight: 600;")
        grid.addWidget(hdr_warm, row, 0, alignment=Qt.AlignLeft | Qt.AlignVCenter)
        row += 1

        # Warmup field (no checkbox, always enabled)
        self.warmup_value = QLineEdit(self)
        self.warmup_value.setText(f"{int(self.state.n_warmup_half_lives)}")
        self.warmup_value.setAlignment(Qt.AlignRight)
        self.warmup_value.setValidator(validator)
        self.warmup_value.setMaximumWidth(frac_width)
        self.warmup_value.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        grid.addWidget(self.warmup_value, row, 0, alignment=Qt.AlignLeft | Qt.AlignVCenter)
        self.warmup_value.textChanged.connect(self._update)

        self._update()

    # Enable/disable unit fraction field
    def _on_toggle(self, checked: bool, prefix: str):
        fx = self.fracs.get(prefix)
        if fx is not None:
            fx.setEnabled(checked)
        self._update()

    def _on_ss_toggle(self, checked: bool):
        self.ss_value.setEnabled(checked)
        self.state.steady_state_enabled = bool(checked)
        self._update()

    def _update(self):
        # Selected units
        self.state.selected_units = [n for n, cb in self.boxes.items() if cb.isChecked()]

        # Fractions
        for prefix, w in self.fracs.items():
            if not w.isEnabled():
                self.state.unit_fractions[prefix] = 0.0
                continue
            try:
                self.state.unit_fractions[prefix] = float(w.text()) if w.text() else 0.0
            except ValueError:
                pass

        # Steady-state
        if self.ss_checkbox.isChecked():
            try:
                self.state.steady_state_input = (
                    float(self.ss_value.text()) if self.ss_value.text() else 0.0
                )
            except ValueError:
                pass

        # Warmup half lives
        try:
            self.state.n_warmup_half_lives = (
                int(self.warmup_value.text()) if self.warmup_value.text() else 0.0
            )
        except ValueError:
            pass

        self.selection_changed.emit()

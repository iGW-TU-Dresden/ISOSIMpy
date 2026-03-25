"""Tab to design the model layout: unit types, fractions, warmup."""

from functools import partial

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QDoubleValidator, QFont
from PyQt5.QtWidgets import (
    QCheckBox,
    QComboBox,
    QGridLayout,
    QHBoxLayout,
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
    """Tab to select unit types, assign fractions, and set warmup options.

    Emits ``selection_changed`` whenever unit selection, fractions, or
    warmup settings change. Updates fields in :class:`AppState` used by the
    parameters tab and controller.
    """

    # Define signals that this tab can emit
    selection_changed = pyqtSignal()

    def __init__(self, state, registry, parent=None):
        super().__init__(parent)
        self.state = state
        self.registry = registry
        # rows of (combobox, fraction editor)
        self.rows = []

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
        title = QLabel("Select up to 4 units and set fractions:")
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
        self.float_validator = validator

        # Width probe
        probe = QLineEdit()
        fm = probe.fontMetrics()
        frac_width = fm.horizontalAdvance(" -0.0000 ") + 18
        self.value_field_width = frac_width

        ### Unit rows (up to 4 selections)
        row = 1
        unit_names = list(self.registry.keys())
        placeholder = "— Select —"
        for i in range(4):
            combo = QComboBox(self)
            combo.addItem(placeholder, userData=None)
            for nm in unit_names:
                combo.addItem(nm, userData=nm)

            fx = QLineEdit(self)
            fx.setText("0.00")
            fx.setAlignment(Qt.AlignRight)
            fx.setValidator(validator)
            fx.setMaximumWidth(frac_width)
            fx.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
            fx.setEnabled(False)

            grid.addWidget(combo, row, 0, alignment=Qt.AlignLeft | Qt.AlignVCenter)
            grid.addWidget(fx, row, 1, alignment=Qt.AlignLeft | Qt.AlignVCenter)

            combo.currentIndexChanged.connect(
                partial(self._on_combo_changed, combo=combo, frac_edit=fx)
            )
            fx.textChanged.connect(self._update)

            self.rows.append({"combo": combo, "frac": fx})
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

        # Steady-state unit notification header
        hdr_note = QLabel(
            "Steady-state input units must match units of tracer input and"
            + " observations (e.g., [TU])!"
        )
        hdr_note.setStyleSheet("color: #C42136;")
        grid.addWidget(hdr_note, row, 0, alignment=Qt.AlignLeft | Qt.AlignVCenter)
        row += 1

        # Steady-state controls
        self.ss_checkbox = QCheckBox("", self)
        self.ss_checkbox.setChecked(bool(self.state.steady_state_enabled))

        self.ss_container = QWidget(self)
        self.ss_container_layout = QVBoxLayout(self.ss_container)
        self.ss_container_layout.setContentsMargins(0, 0, 0, 0)
        self.ss_container_layout.setSpacing(4)
        self.ss_inputs: list[QLineEdit] = []

        grid.addWidget(self.ss_checkbox, row, 0, alignment=Qt.AlignLeft | Qt.AlignVCenter)
        grid.addWidget(self.ss_container, row, 1, alignment=Qt.AlignLeft | Qt.AlignVCenter)

        self.ss_checkbox.toggled.connect(self._on_ss_toggle)
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

        # Try to restore previous design if present
        if hasattr(self.state, "design_units") and self.state.design_units:
            for (name, frac), r in zip(self.state.design_units, self.rows):
                # set combo selection
                idx = r["combo"].findData(name)
                r["combo"].setCurrentIndex(idx if idx != -1 else 0)
                # set fraction and enable
                r["frac"].setText(f"{float(frac):.4f}")
                r["frac"].setEnabled(idx != -1 and idx != 0)

        self.refresh_tracer_inputs()
        self._update()

    def _on_combo_changed(self, index: int, combo: QComboBox, frac_edit: QLineEdit):
        # Enable fraction only when a real unit is selected
        selected = combo.currentData()
        frac_edit.setEnabled(selected is not None)
        self._update()

    def _on_ss_toggle(self, checked: bool):
        self._set_ss_inputs_enabled(checked)
        self.state.steady_state_enabled = bool(checked)
        self._update()

    def _set_ss_inputs_enabled(self, enabled: bool):
        for edit in self.ss_inputs:
            edit.setEnabled(enabled)

    def refresh_tracer_inputs(self):
        self._rebuild_steady_state_inputs()
        # Keep state in sync with possibly new widgets
        self._update()

    def _rebuild_steady_state_inputs(self):
        while self.ss_container_layout.count():
            item = self.ss_container_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        self.ss_inputs = []

        tracer_names = [getattr(self.state, "tracer1", None)]
        tracer2 = getattr(self.state, "tracer2", None)
        if tracer2 and str(tracer2).lower() not in {"none", ""}:
            tracer_names.append(tracer2)

        raw_values = getattr(self.state, "steady_state_input", 0.0)
        if isinstance(raw_values, (list, tuple)):
            values = [float(v) for v in raw_values]
        elif raw_values is None:
            values = []
        else:
            values = [float(raw_values)]

        for idx, name in enumerate(tracer_names):
            row_widget = QWidget(self)
            row_layout = QHBoxLayout(row_widget)
            row_layout.setContentsMargins(0, 0, 0, 0)
            row_layout.setSpacing(6)

            label_text = f"Tracer {idx + 1}"
            if name:
                label_text += f" ({name})"
            label = QLabel(label_text, self)

            edit = QLineEdit(self)
            edit.setAlignment(Qt.AlignRight)
            edit.setValidator(self.float_validator)
            edit.setMaximumWidth(self.value_field_width)
            edit.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
            if idx < len(values):
                val = values[idx]
            elif idx == 0 and values:
                val = values[0]
            else:
                val = 0.0
            edit.setText(f"{float(val):.2f}")
            edit.textChanged.connect(self._update)

            row_layout.addWidget(label)
            row_layout.addWidget(edit)
            self.ss_container_layout.addWidget(row_widget)
            self.ss_inputs.append(edit)

        self.ss_container_layout.addStretch(1)
        self._set_ss_inputs_enabled(self.ss_checkbox.isChecked())

    def _update(self):
        # Gather selected units (up to 4) and their fractions
        design_units = []  # list of (unit_name, fraction)
        for r in self.rows:
            name = r["combo"].currentData()
            if name is None:
                continue
            try:
                frac = float(r["frac"].text()) if r["frac"].text() else 0.0
            except ValueError:
                frac = 0.0
            design_units.append((name, frac))

        # Persist basic list
        self.state.design_units = design_units

        # Build per-instance descriptors with unique prefixes (e.g., pm1, pm2, ...)
        # We have to do this and not just rely on design_units because there
        # could be multiple instances of the same unit type
        counts: dict[str, int] = {}
        instances = []
        for name, frac in design_units:
            counts[name] = counts.get(name, 0) + 1
            cls = self.registry[name]
            base = getattr(cls, "PREFIX", name.lower())
            inst_prefix = f"{base}{counts[name]}"
            instances.append({"name": name, "prefix": inst_prefix, "fraction": float(frac)})
        self.state.design_instances = instances

        # Maintain selected_units for any legacy consumers (unique types)
        seen = set()
        unique_units = []
        for name, _ in design_units:
            if name not in seen:
                seen.add(name)
                unique_units.append(name)
        self.state.selected_units = unique_units

        # Fractions per instance prefix for controller
        self.state.unit_fractions = {inst["prefix"]: inst["fraction"] for inst in instances}

        # Steady-state
        vals = []
        for edit in self.ss_inputs:
            text = edit.text()
            try:
                vals.append(float(text) if text else 0.0)
            except ValueError:
                vals.append(0.0)

        if len(vals) <= 1:
            self.state.steady_state_input = vals[0] if vals else 0.0
        else:
            self.state.steady_state_input = vals

        # Warmup half lives
        try:
            self.state.n_warmup_half_lives = (
                int(self.warmup_value.text()) if self.warmup_value.text() else 0.0
            )
        except ValueError:
            pass

        self.selection_changed.emit()

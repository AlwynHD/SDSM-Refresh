# src/modules/qqplot.py

import os
from datetime import timedelta
import numpy as np

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QFileDialog, QLabel, QCheckBox,
    QComboBox, QDateEdit, QSpinBox, QRadioButton,
    QButtonGroup, QMessageBox
)
from PyQt5.QtCore import Qt, QDate
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure

class QQPlotPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.observed_path = None
        self.modelled_path = None
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        # — File selectors —
        file_layout = QHBoxLayout()
        self.obs_btn = QPushButton("Select Observed")
        self.obs_lbl = QLabel("None")
        self.mod_btn = QPushButton("Select Modelled")
        self.mod_lbl = QLabel("None")
        for w in (self.obs_btn, self.obs_lbl, self.mod_btn, self.mod_lbl):
            file_layout.addWidget(w)
        layout.addLayout(file_layout)

        # — Date range —
        date_layout = QHBoxLayout()
        date_layout.addWidget(QLabel("Start:"))
        self.start_date = QDateEdit(QDate.currentDate().addYears(-10))
        self.start_date.setCalendarPopup(True)
        date_layout.addWidget(self.start_date)
        date_layout.addWidget(QLabel("End:"))
        self.end_date = QDateEdit(QDate.currentDate())
        self.end_date.setCalendarPopup(True)
        date_layout.addWidget(self.end_date)
        layout.addLayout(date_layout)

        # — Period filter —
        period_layout = QHBoxLayout()
        period_layout.addWidget(QLabel("Period:"))
        self.period_combo = QComboBox()
        self.period_combo.addItems([
            "All Data","Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep",
            "Oct","Nov","Dec","DJF","MAM","JJA","SON"
        ])
        period_layout.addWidget(self.period_combo)
        layout.addLayout(period_layout)

        # — Threshold —
        thresh_layout = QHBoxLayout()
        self.apply_thresh = QCheckBox("Apply threshold?")
        self.thresh_spin   = QSpinBox()
        self.thresh_spin.setRange(0, 1_000_000)
        self.thresh_spin.setValue(0)
        for w in (self.apply_thresh, QLabel("Thresh:"), self.thresh_spin):
            thresh_layout.addWidget(w)
        layout.addLayout(thresh_layout)

        # — Ensemble options —
        ens_layout = QHBoxLayout()
        ens_layout.addWidget(QLabel("Ensemble:"))
        self.ens_group = QButtonGroup(self)
        for idx, label in enumerate(("All","Mean","Member","All+Mean")):
            rb = QRadioButton(label)
            self.ens_group.addButton(rb, idx)
            ens_layout.addWidget(rb)
        self.ens_group.button(0).setChecked(True)
        ens_layout.addWidget(QLabel("Member #"))
        self.ens_spin = QSpinBox()
        self.ens_spin.setRange(1,200)
        ens_layout.addWidget(self.ens_spin)
        layout.addLayout(ens_layout)

        # — Draw button —
        self.draw_btn = QPushButton("Draw Q-Q Plot")
        layout.addWidget(self.draw_btn)

        # — Matplotlib canvas —
        self.figure = Figure(figsize=(6,5))
        self.canvas = FigureCanvasQTAgg(self.figure)
        layout.addWidget(self.canvas)

        # — Signals —
        self.obs_btn.clicked.connect(self._pick_observed)
        self.mod_btn.clicked.connect(self._pick_modelled)
        self.draw_btn.clicked.connect(self._on_draw)

    def _pick_observed(self):
        p, _ = QFileDialog.getOpenFileName(self, "Select Observed Data")
        if p:
            self.observed_path = p
            self.obs_lbl.setText(os.path.basename(p))

    def _pick_modelled(self):
        p, _ = QFileDialog.getOpenFileName(self, "Select Modelled Data")
        if p:
            self.modelled_path = p
            self.mod_lbl.setText(os.path.basename(p))

    def _on_draw(self):
        # 1) validate
        if not self.observed_path or not self.modelled_path:
            QMessageBox.critical(self, "Error", "Please select both files.")
            return
        sd = self.start_date.date().toPyDate()
        ed = self.end_date.date().toPyDate()
        if sd >= ed:
            QMessageBox.critical(self, "Error", "Start date must be before end date.")
            return

        # 2) read + filter
        obs = self._read_series(self.observed_path, sd, ed, is_model=False)
        mod = self._read_series(self.modelled_path,   sd, ed, is_model=True)

        # 3) ensemble logic
        mode = self.ens_group.checkedId()
        if   mode == 1:  mod = mod.mean(axis=1, keepdims=True)
        elif mode == 2:
            idx = self.ens_spin.value() - 1
            mod = mod[:, [idx]]
        elif mode == 3:
            mean_col = mod.mean(axis=1, keepdims=True)
            mod = np.hstack([mod, mean_col])

        # 4) must have ≥100 points per series
        if obs.shape[0] < 100 or any(
            np.count_nonzero(~np.isnan(mod[:,c])) < 100
            for c in range(mod.shape[1])
        ):
            QMessageBox.critical(self, "Error", "Insufficient data (<100) to plot.")
            return

        # 5) draw
        self._plot_qq(obs, mod)

    def _read_series(self, path, start_date, end_date, is_model):
        """
        Read daily values, apply period and threshold, drop ALL negatives
        (so any sentinel <0 is removed), return an (N×E) array.
        """
        total_days = (end_date - start_date).days + 1
        dates = [start_date + timedelta(days=i) for i in range(total_days)]
        lines = open(path).read().splitlines()
        if len(lines) < total_days:
            raise IOError("Data file shorter than selected date range.")

        # detect number of 14-char slices in model-file (VB6’s Mid$(…,14))
        ens_count = 1
        if is_model:
            ln = lines[0]
            ens_count = len(ln) // 14 if len(ln) > 15 else 1

        thr = self.thresh_spin.value() if self.apply_thresh.isChecked() else None
        data = []

        for i, dt in enumerate(dates):
            if not self._in_period(dt):
                continue
            raw = lines[i].ljust(14*ens_count)
            row = []
            for e in range(ens_count):
                seg = raw[e*14:(e+1)*14].strip() or "0"
                v   = float(seg)
                # VB6 skips only missing & below‐threshold, but precip <0 never occurs
                if v < 0:            # <0 = sentinel or error
                    row.append(np.nan)
                elif (thr is not None and v < thr):
                    row.append(np.nan)
                else:
                    row.append(v)
            data.append(row)

        arr = np.array(data, dtype=float)
        # drop days where *all* columns are nan
        mask = ~np.all(np.isnan(arr), axis=1)
        return arr[mask, :]

    def _in_period(self, dt):
        idx = self.period_combo.currentIndex()
        m   = dt.month
        if idx == 0:   return True
        if 1 <= idx <= 12:
            return m == idx
        if idx == 13:  return m in (12,1,2)   # DJF
        if idx == 14:  return m in (3,4,5)    # MAM
        if idx == 15:  return m in (6,7,8)    # JJA
        if idx == 16:  return m in (9,10,11)  # SON
        return False

    def _qq_quantiles(self, arr):
        """VB6‐style 1–99% via linear interpolation."""
        s = np.sort(arr)
        n = len(s)
        qs = []
        for p in range(1, 100):
            pos = 1 + p * (n - 1) / 100
            lo  = int(np.floor(pos)) - 1
            hi  = int(np.ceil(pos))  - 1
            frac = pos - np.floor(pos)
            qs.append(s[lo] + (s[hi] - s[lo]) * frac)
        return np.array(qs)

    def _plot_qq(self, obs, mod):
        self.figure.clear()
        ax = self.figure.add_subplot(111)

        # observed quantiles
        obs_q = self._qq_quantiles(obs[:, 0])

        # scatter each ensemble’s quantiles
        for c in range(mod.shape[1]):
            col = mod[:, c]
            col = col[~np.isnan(col)]
            mq  = self._qq_quantiles(col)
            ax.scatter(mq, obs_q, s=10, c='k')

        # 1:1 line
        M = max(obs_q.max(), *(self._qq_quantiles(mod[:, c]).max()
                               for c in range(mod.shape[1])))
        ax.plot([0, M], [0, M], c='b', lw=2)

        ax.set_title("Quantile-Quantile Plot")
        ax.set_xlabel(os.path.basename(self.modelled_path))
        ax.set_ylabel(os.path.basename(self.observed_path))
        ax.grid(True)
        self.canvas.draw()

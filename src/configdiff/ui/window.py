from pathlib import Path

from PySide6.QtCore import QEvent, QObject, Qt, QTimer
from PySide6.QtGui import QCloseEvent, QKeyEvent, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from configdiff.domain.errors import ConfigError, ErrorCode
from configdiff.domain.limits import DEFAULT_LIMITS, Limits
from configdiff.domain.paths import render_path
from configdiff.domain.results import Category, Format, SanitizedEntry, SanitizedReportDTO
from configdiff.services.exporting import export_report
from configdiff.services.files import detect_format
from configdiff.services.reports import LABELS, filter_entries
from configdiff.settings.preferences import Preferences, PreferenceStore
from configdiff.ui.model import DiffTableModel
from configdiff.workers.comparing import Compared, ComparisonJob
from configdiff.workers.protocol import Failure


def plain_label(text: str) -> QLabel:
    label = QLabel(text)
    label.setTextFormat(Qt.TextFormat.PlainText)
    label.setWordWrap(True)
    return label


class MainWindow(QMainWindow):
    def __init__(
        self, store: PreferenceStore | None = None, limits: Limits = DEFAULT_LIMITS
    ) -> None:
        super().__init__()
        self.store = store if store is not None else PreferenceStore()
        preferences = self.store.load()
        self.limits = limits
        self.paths: list[Path | None] = [None, None]
        self.job: ComparisonJob | None = None
        self.compared: Compared | None = None
        self.state = "empty"
        self.setWindowTitle("ConfigDiff Desktop")
        self.resize(preferences.width, preferences.height)
        self.setMinimumSize(480, 320)
        panel = QWidget()
        layout = QVBoxLayout(panel)
        title = plain_label("Compare configurações locais")
        title.setStyleSheet("font-weight: bold; font-size: 18pt")
        layout.addWidget(title)
        layout.addWidget(
            plain_label("JSON, YAML e .env • Sem envio à internet • Valores ocultos por padrão")
        )
        selectors = QGridLayout()
        self.file_buttons: list[QPushButton] = []
        self.file_labels: list[QLabel] = []
        self.formats: list[QComboBox] = []
        for side in range(2):
            name = "A" if side == 0 else "B"
            button = QPushButton(f"Selecionar {name}…")
            button.setAccessibleName(f"Selecionar arquivo {name}")
            button.clicked.connect(lambda checked=False, side=side: self.choose_file(side))
            label = plain_label("Nenhum arquivo selecionado")
            combo = QComboBox()
            combo.addItem("Escolha o formato", "auto")
            for format in Format:
                combo.addItem(format.value.upper(), format.value)
            combo.setCurrentIndex(max(0, combo.findData(preferences.format)))
            combo.setAccessibleName(f"Formato do arquivo {name}")
            combo.currentIndexChanged.connect(self.format_changed)
            selectors.addWidget(button, side, 0)
            selectors.addWidget(label, side, 1)
            selectors.addWidget(combo, side, 2)
            self.file_buttons.append(button)
            self.file_labels.append(label)
            self.formats.append(combo)
        selectors.setColumnStretch(1, 1)
        layout.addLayout(selectors)
        self.details_button = QPushButton("Mostrar caminhos completos")
        self.details_button.setCheckable(True)
        self.details = plain_label("")
        self.details.hide()
        self.details_button.toggled.connect(self.toggle_details)
        layout.addWidget(self.details_button)
        layout.addWidget(self.details)
        actions = QHBoxLayout()
        self.compare_button = QPushButton("Comparar")
        self.compare_button.clicked.connect(self.start)
        self.cancel_button = QPushButton("Cancelar")
        self.cancel_button.clicked.connect(self.cancel)
        self.clear_button = QPushButton("Limpar")
        self.clear_button.clicked.connect(self.clear)
        self.export_button = QPushButton("Exportar Markdown…")
        self.export_button.clicked.connect(self.choose_export)
        self.theme = QComboBox()
        for theme_label, value in (
            ("Tema do sistema", "system"),
            ("Claro", "light"),
            ("Escuro", "dark"),
        ):
            self.theme.addItem(theme_label, value)
        self.theme.setCurrentIndex(self.theme.findData(preferences.theme))
        self.theme.setAccessibleName("Tema")
        self.theme.currentIndexChanged.connect(self.apply_theme)
        for widget in (
            self.compare_button,
            self.cancel_button,
            self.clear_button,
            self.export_button,
            self.theme,
        ):
            actions.addWidget(widget)
        layout.addLayout(actions)
        self.search = QLineEdit()
        self.search.setPlaceholderText("Buscar no caminho — nunca nos valores (Ctrl+F)")
        self.search.setAccessibleName("Buscar por caminho")
        self.search.textChanged.connect(self.refresh_view)
        layout.addWidget(self.search)
        filters = QHBoxLayout()
        self.categories: dict[Category, QCheckBox] = {}
        for category in Category:
            check = QCheckBox(LABELS[category])
            check.setChecked(category != Category.EQUAL)
            check.toggled.connect(self.refresh_view)
            self.categories[category] = check
            filters.addWidget(check)
        layout.addLayout(filters)
        self.counts = plain_label("Nenhum resultado")
        layout.addWidget(self.counts)
        self.model = DiffTableModel(self)
        self.table = QTableView()
        self.table.setModel(self.model)
        self.table.setAccessibleName("Diferenças de configuração")
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectItems)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSortingEnabled(True)
        self.table.sortByColumn(0, Qt.SortOrder.AscendingOrder)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.table.setColumnWidth(0, 280)
        self.table.setColumnWidth(1, 150)
        self.table.setAlternatingRowColors(True)
        self.table.installEventFilter(self)
        self.table.viewport().installEventFilter(self)
        self.table.selectionModel().currentChanged.connect(lambda *_: self.model.hide_values())
        layout.addWidget(self.table, 1)
        reveal_actions = QHBoxLayout()
        self.reveal_button = QPushButton("Revelar célula por 15 s (Alt+R)")
        self.reveal_button.clicked.connect(self.reveal_selected)
        self.copy_button = QPushButton("Copiar caminho")
        self.copy_button.clicked.connect(self.copy_path)
        reveal_actions.addWidget(self.reveal_button)
        reveal_actions.addWidget(self.copy_button)
        layout.addLayout(reveal_actions)
        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        self.progress.hide()
        layout.addWidget(self.progress)
        self.status = plain_label("Selecione os arquivos A e B para começar.")
        layout.addWidget(self.status)
        panel.setMinimumSize(620, 580)
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(panel)
        self.setCentralWidget(self.scroll_area)
        self.timer = QTimer(self)
        self.timer.setInterval(25)
        self.timer.timeout.connect(self.poll)
        for keys, callback in (
            ("Ctrl+O", lambda: self.choose_file(0)),
            ("Ctrl+Shift+O", lambda: self.choose_file(1)),
            ("Ctrl+Return", self.start),
            ("Ctrl+Enter", self.start),
            ("Ctrl+F", self.search.setFocus),
            ("Ctrl+E", self.choose_export),
            ("Escape", self.escape),
            ("Alt+R", self.reveal_selected),
        ):
            QShortcut(QKeySequence(keys), self, callback)
        self.apply_theme()
        self.update_actions()

    def apply_theme(self) -> None:
        theme = self.theme.currentData()
        base = "QPushButton:focus, QComboBox:focus, QLineEdit:focus, QCheckBox:focus { border: 2px solid #4488dd; }"
        if theme == "dark":
            base += "QWidget { background: #20242b; color: #eff2f6; } QLineEdit, QTableView, QComboBox { background: #15191f; alternate-background-color: #292f38; selection-background-color: #315c89; } QPushButton { padding: 6px; }"
        elif theme == "light":
            base += "QWidget { background: #f6f7f9; color: #17202a; } QLineEdit, QTableView, QComboBox { background: white; alternate-background-color: #eef2f6; selection-background-color: #c8def5; } QPushButton { padding: 6px; }"
        self.setStyleSheet(base)

    def update_actions(self) -> None:
        busy = self.job is not None
        self.compare_button.setEnabled(not busy and all(self.paths))
        self.cancel_button.setEnabled(busy)
        self.export_button.setEnabled(not busy and self.compared is not None)
        self.reveal_button.setEnabled(not busy and bool(self.model.entries))
        self.copy_button.setEnabled(not busy and bool(self.model.entries))

    def invalidate(self) -> None:
        self.cancel()
        self.compared = None
        self.model.set_entries(())
        self.counts.setText("Nenhum resultado")
        self.update_actions()

    def format_changed(self) -> None:
        if not hasattr(self, "model"):
            return
        self.invalidate()
        self.state = "selected" if any(self.paths) else "empty"
        self.status.setText("Formato alterado; compare novamente.")

    def choose_file(self, side: int) -> None:
        self.model.hide_values()
        name, _ = QFileDialog.getOpenFileName(
            self,
            f"Selecionar arquivo {'A' if side == 0 else 'B'}",
            "",
            "Configurações (*.json *.yaml *.yml *.env);;Todos os arquivos (*)",
        )
        if name:
            self.set_file(side, Path(name))

    def set_file(self, side: int, path: Path) -> None:
        self.invalidate()
        self.paths[side] = path.absolute()
        detected = detect_format(path)
        self.formats[side].blockSignals(True)
        self.formats[side].setCurrentIndex(
            self.formats[side].findData(detected.value if detected else "auto")
        )
        self.formats[side].blockSignals(False)
        try:
            size = path.stat().st_size
            summary = f"{path.name} • {size} bytes"
        except OSError:
            summary = f"{path.name} • tamanho indisponível"
        self.file_labels[side].setText(summary)
        self.state = "selected"
        self.status.setText("Arquivos selecionados. Escolha o mesmo formato e compare.")
        self.toggle_details(self.details_button.isChecked())
        self.update_actions()

    def toggle_details(self, checked: bool) -> None:
        self.model.hide_values()
        self.details.setText(
            "\n".join(
                f"{'A' if index == 0 else 'B'}: {path}"
                for index, path in enumerate(self.paths)
                if path
            )
        )
        self.details.setVisible(checked)
        self.details_button.setText(
            "Ocultar caminhos completos" if checked else "Mostrar caminhos completos"
        )

    def start(self) -> None:
        if self.job is not None:
            return
        self.invalidate()
        first, second = self.paths
        if first is None or second is None:
            self.status.setText("Selecione os dois arquivos.")
            return
        a, b = (combo.currentData() for combo in self.formats)
        if a == "auto" or b == "auto":
            self.status.setText("Escolha explicitamente o formato de cada arquivo.")
            return
        try:
            self.job = ComparisonJob(first, second, Format(a), Format(b), self.limits)
        except ConfigError as error:
            self.state = "error"
            self.status.setText(error.message)
            self.update_actions()
            return
        self.state = "processing"
        self.status.setText("Processando; os valores permanecerão ocultos.")
        self.progress.show()
        self.timer.start()
        self.update_actions()

    def poll(self) -> None:
        if self.job is None or (reply := self.job.poll()) is None:
            return
        self.job = None
        self.timer.stop()
        self.progress.hide()
        if isinstance(reply, Failure):
            self.compared = None
            self.state = "error"
            self.status.setText(reply.exception().message)
        else:
            self.compared = reply
            self.state = "done"
            self.refresh_view()
            self.status.setText(
                "Concluído. Valores ocultos; selecione uma célula Valor A/B para revelar."
            )
        self.update_actions()

    def selected_categories(self) -> frozenset[Category]:
        return frozenset(
            category for category, check in self.categories.items() if check.isChecked()
        )

    def refresh_view(self) -> None:
        if self.compared is None:
            self.model.hide_values()
            return
        entries = filter_entries(
            self.compared.result.entries,
            query=self.search.text(),
            categories=self.selected_categories(),
        )
        self.model.set_entries(entries)
        self.model.sort(
            self.table.horizontalHeader().sortIndicatorSection(),
            self.table.horizontalHeader().sortIndicatorOrder(),
        )
        counts = {
            category: sum(entry.category == category for entry in entries) for category in Category
        }
        self.counts.setText(
            f"Visão: {len(entries)} de {len(self.compared.result.entries)} entradas • "
            + " • ".join(f"{LABELS[category]}: {counts[category]}" for category in Category)
        )
        self.update_actions()

    def reveal_selected(self) -> None:
        index = self.table.currentIndex()
        self.table.setFocus()
        if self.model.reveal(index):
            self.status.setText("Célula revelada por até 15 segundos; Esc oculta imediatamente.")
        else:
            self.status.setText("Selecione uma célula nas colunas Valor A ou Valor B.")

    def copy_path(self) -> None:
        self.model.hide_values()
        index = self.table.currentIndex()
        if index.isValid() and index.row() < len(self.model.entries):
            QApplication.clipboard().setText(render_path(self.model.entries[index.row()].path))
            self.status.setText("Caminho copiado. Nenhum valor foi copiado.")

    def choose_export(self) -> None:
        self.model.hide_values()
        if self.compared is None or self.job is not None:
            return
        name, _ = QFileDialog.getSaveFileName(
            self,
            "Exportar para arquivo novo",
            "relatorio-configdiff.md",
            "Markdown (*.md)",
            options=QFileDialog.Option.DontConfirmOverwrite,
        )
        if name:
            self.export_to(Path(name))

    def export_to(self, destination: Path) -> bool:
        self.model.hide_values()
        if self.compared is None:
            return False
        report = SanitizedReportDTO(
            self.compared.result.format,
            tuple(
                SanitizedEntry(render_path(entry.path), entry.category, entry.kind_a, entry.kind_b)
                for entry in self.model.entries
            ),
        )
        try:
            export_report(report, destination, self.compared.sources)
        except ConfigError as error:
            self.status.setText(error.message)
            return False
        self.status.setText(
            f"Relatório sanitizado exportado: {len(report.entries)} entradas. Valores omitidos."
        )
        return True

    def cancel(self) -> None:
        if not hasattr(self, "model"):
            return
        self.model.hide_values()
        if self.job is not None:
            self.job.cancel(ErrorCode.CANCELLED)
            self.job = None
            self.timer.stop()
            self.progress.hide()
            self.compared = None
            self.model.set_entries(())
            self.state = "cancelled"
            self.status.setText("Comparação cancelada.")
        self.update_actions()

    def clear(self) -> None:
        self.invalidate()
        self.paths = [None, None]
        for label in self.file_labels:
            label.setText("Nenhum arquivo selecionado")
        self.search.clear()
        self.details_button.setChecked(False)
        self.details.setText("")
        self.state = "empty"
        self.status.setText("Dados removidos da sessão. Selecione os arquivos A e B.")
        self.update_actions()

    def escape(self) -> None:
        self.cancel()
        self.model.hide_values()

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        if (
            event.type() == QEvent.Type.KeyPress
            and isinstance(event, QKeyEvent)
            and event.matches(QKeySequence.StandardKey.Copy)
        ):
            self.model.hide_values()
            self.status.setText("Use Copiar caminho; valores não são copiados.")
            return True
        if event.type() in (QEvent.Type.FocusOut, QEvent.Type.WindowDeactivate):
            self.model.hide_values()
        return super().eventFilter(watched, event)

    def changeEvent(self, event: QEvent) -> None:
        if (
            event.type() == QEvent.Type.ActivationChange
            and hasattr(self, "model")
            and not self.isActiveWindow()
        ):
            self.model.hide_values()
        super().changeEvent(event)

    def closeEvent(self, event: QCloseEvent) -> None:
        self.invalidate()
        preferences = Preferences(
            theme=self.theme.currentData(),
            width=self.width(),
            height=self.height(),
            format=self.formats[0].currentData(),
        )
        self.store.save(preferences)
        self.paths = [None, None]
        self.details.clear()
        event.accept()

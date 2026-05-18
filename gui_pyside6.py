"""
VideOCRplus - PySide6/Qt GUI Design
====================================

Modern GUI implementation using PySide6 (Qt for Python).
This module provides a dark-themed, professional interface for video OCR processing.

Design Goals:
- Maintain the same dark theme color scheme from the original PySimpleGUI version
- Use Qt's native widgets for better performance and appearance
- Modular architecture with separate components
- Responsive layout that adapts to window resizing
- Cross-platform compatibility (Windows, macOS, Linux)

Architecture:
- MainWindow: Main application window with tab-based navigation
- VideoPreviewWidget: Custom widget for video frame display with crop support
- MediaControlsWidget: Playback controls (seek, time display)
- ProcessingPanel: Run/pause/cancel controls with progress tracking
- SidebarWidget: Video info, task status, and quick actions
- SettingsPanel: OCR and LLM Vision configuration
- AboutPanel: Application information and links

Color Palette (Dark Theme):
- Background: #151922
- Panel: #1b202a
- Preview: #05070a
- Input: #0f131a
- Text: #e7ecf3
- Muted: #9ba8b7
- Accent: #69b7ff
- Danger: #b85a5a
- Button: #2f4055
- Scroll: #2c3442

Usage:
    from gui_pyside6 import VideOCRApplication
    app = VideOCRApplication()
    app.run()
"""

from __future__ import annotations

import sys
from typing import Optional

from PySide6.QtCore import (
    Qt, QSize, QThread, Signal, Slot, QTimer, QSettings, QStandardPaths
)
from PySide6.QtGui import (
    QFont, QColor, QPalette, QIcon, QPixmap, QImage, QAction, QMouseEvent, QPaintEvent
)
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QTabWidget, QGroupBox, QLabel, QPushButton, QLineEdit, QComboBox, QCheckBox,
    QSlider, QProgressBar, QTextEdit, QScrollArea, QSplitter, QFrame,
    QFileDialog, QMessageBox, QSizePolicy, QGraphicsView, QGraphicsScene,
    QGraphicsPixmapItem, QGraphicsRectItem, QSpinBox, QDoubleSpinBox,
    QToolButton, QStatusBar, QMenuBar, QMenu
)


# ============================================================================
# Color Constants
# ============================================================================

COLOR_BACKGROUND = '#151922'
COLOR_PANEL = '#1b202a'
COLOR_PREVIEW = '#05070a'
COLOR_INPUT = '#0f131a'
COLOR_TEXT = '#e7ecf3'
COLOR_MUTED = '#9ba8b7'
COLOR_ACCENT = '#69b7ff'
COLOR_DANGER = '#b85a5a'
COLOR_BUTTON = '#2f4055'
COLOR_SCROLL = '#2c3442'


# ============================================================================
# Font Configuration
# ============================================================================

def get_font(size: int, bold: bool = False, family: str = "Segoe UI") -> QFont:
    """Create a configured QFont object."""
    font = QFont(family, size)
    if bold:
        font.setBold(True)
    return font


FONT_TITLE = get_font(16, bold=True)
FONT_SECTION = get_font(10, bold=True)
FONT_PRIMARY = get_font(11, bold=True)
FONT_MONO = QFont("Consolas", 9)
FONT_DEFAULT = get_font(9)


# ============================================================================
# Stylesheet Templates
# ============================================================================

STYLESHEET = f"""
QMainWindow {{
    background-color: {COLOR_BACKGROUND};
}}

QWidget {{
    background-color: {COLOR_BACKGROUND};
    color: {COLOR_TEXT};
    font-family: "Segoe UI";
    font-size: 9pt;
}}

QTabWidget::pane {{
    border: 1px solid {COLOR_PANEL};
    background-color: {COLOR_BACKGROUND};
}}

QTabBar::tab {{
    background-color: {COLOR_PANEL};
    color: {COLOR_MUTED};
    padding: 8px 16px;
    margin-right: 2px;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
}}

QTabBar::tab:selected {{
    background-color: {COLOR_BACKGROUND};
    color: {COLOR_TEXT};
}}

QGroupBox {{
    background-color: {COLOR_PANEL};
    border: 1px solid {COLOR_PANEL};
    border-radius: 6px;
    margin-top: 12px;
    padding-top: 16px;
    font-weight: bold;
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 6px;
    color: {COLOR_TEXT};
}}

QLabel {{
    color: {COLOR_MUTED};
    background-color: transparent;
}}

QLabel[class="title"] {{
    color: {COLOR_TEXT};
    font-size: 16pt;
    font-weight: bold;
}}

QLabel[class="accent"] {{
    color: {COLOR_ACCENT};
}}

QPushButton {{
    background-color: {COLOR_BUTTON};
    color: {COLOR_TEXT};
    border: none;
    border-radius: 4px;
    padding: 6px 16px;
    min-width: 80px;
}}

QPushButton:hover {{
    background-color: #3a5070;
}}

QPushButton:pressed {{
    background-color: #1a2a3a;
}}

QPushButton:disabled {{
    background-color: {COLOR_PANEL};
    color: {COLOR_MUTED};
}}

QPushButton[class="primary"] {{
    background-color: {COLOR_ACCENT};
    color: #07131f;
    font-weight: bold;
}}

QPushButton[class="primary"]:hover {{
    background-color: #7ec3ff;
}}

QPushButton[class="danger"] {{
    background-color: {COLOR_DANGER};
    color: white;
}}

QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox {{
    background-color: {COLOR_INPUT};
    color: {COLOR_TEXT};
    border: 1px solid {COLOR_PANEL};
    border-radius: 4px;
    padding: 4px 8px;
}}

QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus {{
    border-color: {COLOR_ACCENT};
}}

QComboBox::drop-down {{
    border: none;
    width: 20px;
}}

QComboBox::down-arrow {{
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 6px solid {COLOR_MUTED};
    margin-right: 6px;
}}

QComboBox QAbstractItemView {{
    background-color: {COLOR_INPUT};
    color: {COLOR_TEXT};
    selection-background-color: {COLOR_ACCENT};
    selection-color: #07131f;
}}

QSlider::groove:horizontal {{
    background-color: {COLOR_PANEL};
    height: 6px;
    border-radius: 3px;
}}

QSlider::handle:horizontal {{
    background-color: {COLOR_ACCENT};
    width: 16px;
    height: 16px;
    margin: -5px 0;
    border-radius: 8px;
}}

QSlider::sub-page:horizontal {{
    background-color: {COLOR_ACCENT};
    border-radius: 3px;
}}

QProgressBar {{
    background-color: {COLOR_PANEL};
    border: none;
    border-radius: 4px;
    text-align: center;
    height: 18px;
}}

QProgressBar::chunk {{
    background-color: {COLOR_ACCENT};
    border-radius: 4px;
}}

QTextEdit {{
    background-color: {COLOR_INPUT};
    color: {COLOR_TEXT};
    border: 1px solid {COLOR_PANEL};
    border-radius: 4px;
    font-family: "Consolas";
    font-size: 9pt;
}}

QScrollArea {{
    border: none;
    background-color: {COLOR_BACKGROUND};
}}

QScrollBar:vertical {{
    background-color: {COLOR_BACKGROUND};
    width: 12px;
    margin: 0;
}}

QScrollBar::handle:vertical {{
    background-color: {COLOR_SCROLL};
    min-height: 20px;
    border-radius: 6px;
    margin: 2px;
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}

QScrollBar:horizontal {{
    background-color: {COLOR_BACKGROUND};
    height: 12px;
    margin: 0;
}}

QScrollBar::handle:horizontal {{
    background-color: {COLOR_SCROLL};
    min-width: 20px;
    border-radius: 6px;
    margin: 2px;
}}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0;
}}

QStatusBar {{
    background-color: {COLOR_PANEL};
    color: {COLOR_MUTED};
    border-top: 1px solid {COLOR_PANEL};
}}

QMenuBar {{
    background-color: {COLOR_PANEL};
    color: {COLOR_TEXT};
    border-bottom: 1px solid {COLOR_PANEL};
}}

QMenuBar::item:selected {{
    background-color: {COLOR_ACCENT};
    color: #07131f;
}}

QMenu {{
    background-color: {COLOR_INPUT};
    color: {COLOR_TEXT};
    border: 1px solid {COLOR_PANEL};
}}

QMenu::item:selected {{
    background-color: {COLOR_ACCENT};
    color: #07131f;
}}

QSplitter::handle {{
    background-color: {COLOR_PANEL};
}}
"""


# ============================================================================
# Custom Widgets
# ============================================================================

class VideoPreviewWidget(QGraphicsView):
    """Custom widget for displaying video frames with crop box support."""

    crop_changed = Signal(tuple)  # Emits (x1, y1, x2, y2) normalized coordinates

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)

        self.pixmap_item: Optional[QGraphicsPixmapItem] = None
        self.crop_rect: Optional[QGraphicsRectItem] = None
        self.drawing = False
        self.start_pos = None
        self.end_pos = None

        self.setMinimumSize(640, 360)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setRenderHint(QPainter.Antialiasing)
        self.setRenderHint(QPainter.SmoothPixmapTransform)
        self.setStyleSheet(f"background-color: {COLOR_PREVIEW};")

    def set_frame(self, image: QImage) -> None:
        """Display a new video frame."""
        if self.pixmap_item:
            self.scene.removeItem(self.pixmap_item)

        pixmap = QPixmap.fromImage(image)
        self.pixmap_item = QGraphicsPixmapItem(pixmap)
        self.scene.addItem(self.pixmap_item)
        self.fitInView(self.pixmap_item, Qt.KeepAspectRatio)

    def clear_crop(self) -> None:
        """Remove the current crop rectangle."""
        if self.crop_rect:
            self.scene.removeItem(self.crop_rect)
            self.crop_rect = None
        self.crop_changed.emit((0, 0, 0, 0))

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.LeftButton:
            self.drawing = True
            self.start_pos = self.mapToScene(event.pos())
            self.end_pos = self.start_pos
            self.update_crop_rect()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self.drawing:
            self.end_pos = self.mapToScene(event.pos())
            self.update_crop_rect()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.LeftButton and self.drawing:
            self.drawing = False
            self.end_pos = self.mapToScene(event.pos())
            self.update_crop_rect()
            self.emit_crop_coords()

    def update_crop_rect(self) -> None:
        """Update the visual crop rectangle."""
        if self.crop_rect:
            self.scene.removeItem(self.crop_rect)

        if self.start_pos and self.end_pos:
            from PySide6.QtCore import QPointF
            from PySide6.QtGui import QPen

            rect = QRectF(self.start_pos, self.end_pos).normalized()
            pen = QPen(QColor(COLOR_DANGER), 2, Qt.DashLine)
            self.crop_rect = self.scene.addRect(rect, pen)

    def emit_crop_coords(self) -> None:
        """Emit normalized crop coordinates."""
        if self.pixmap_item and self.start_pos and self.end_pos:
            pixmap_rect = self.pixmap_item.boundingRect()
            x1 = (self.start_pos.x() - pixmap_rect.x()) / pixmap_rect.width()
            y1 = (self.start_pos.y() - pixmap_rect.y()) / pixmap_rect.height()
            x2 = (self.end_pos.x() - pixmap_rect.x()) / pixmap_rect.width()
            y2 = (self.end_pos.y() - pixmap_rect.y()) / pixmap_rect.height()

            # Clamp to [0, 1]
            x1, x2 = max(0, min(1, x1)), max(0, min(1, x2))
            y1, y2 = max(0, min(1, y1)), max(0, min(1, y2))

            self.crop_changed.emit((x1, y1, x2, y2))


class MediaControlsWidget(QWidget):
    """Media playback controls with seek slider and time display."""

    seek_requested = Signal(float)  # Emits position in seconds

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 4, 0, 4)

        # Seek label
        self.seek_label = QLabel("Seek:")
        layout.addWidget(self.seek_label)

        # Seek slider
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(0, 0)
        self.slider.setEnabled(False)
        self.slider.valueChanged.connect(self.on_slider_changed)
        layout.addWidget(self.slider, stretch=1)

        # Time display
        self.time_label = QLabel("Time: -/-")
        self.time_label.setMinimumWidth(150)
        layout.addWidget(self.time_label)

    def on_slider_changed(self, value: int) -> None:
        """Handle slider value change."""
        self.seek_requested.emit(value / 1000.0)  # Convert ms to seconds

    def set_duration(self, duration_ms: int) -> None:
        """Set the slider range based on video duration."""
        self.slider.setRange(0, duration_ms)
        self.slider.setEnabled(True)

    def set_position(self, position_ms: int, duration_ms: int) -> None:
        """Update the current position display."""
        self.slider.blockSignals(True)
        self.slider.setValue(position_ms)
        self.slider.blockSignals(False)

        current = self.format_time(position_ms)
        total = self.format_time(duration_ms)
        self.time_label.setText(f"Time: {current}/{total}")

    def format_time(self, ms: int) -> str:
        """Format milliseconds to HH:MM:SS."""
        seconds = ms // 1000
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"


class ProcessingPanel(QWidget):
    """Processing controls with progress tracking."""

    run_clicked = Signal()
    pause_clicked = Signal()
    cancel_clicked = Signal()

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 4, 0, 4)

        # Action buttons row
        button_layout = QHBoxLayout()

        self.run_button = QPushButton("  Run  ")
        self.run_button.setProperty("class", "primary")
        self.run_button.setFont(FONT_PRIMARY)
        self.run_button.clicked.connect(self.run_clicked.emit)
        button_layout.addWidget(self.run_button)

        self.pause_button = QPushButton("Pause")
        self.pause_button.setEnabled(False)
        self.pause_button.setVisible(False)
        self.pause_button.clicked.connect(self.pause_clicked.emit)
        button_layout.addWidget(self.pause_button)

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setProperty("class", "danger")
        self.cancel_button.setEnabled(False)
        self.cancel_button.setVisible(False)
        self.cancel_button.clicked.connect(self.cancel_clicked.emit)
        button_layout.addWidget(self.cancel_button)

        button_layout.addStretch()

        # Status and ETA
        self.status_label = QLabel("")
        self.status_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        button_layout.addWidget(self.status_label)

        self.eta_label = QLabel("")
        self.eta_label.setMinimumWidth(150)
        self.eta_label.setAlignment(Qt.AlignRight)
        button_layout.addWidget(self.eta_label)

        layout.addLayout(button_layout)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

    def set_running(self, running: bool) -> None:
        """Update UI state for running/stopped."""
        self.run_button.setEnabled(not running)
        self.run_button.setVisible(not running)
        self.pause_button.setEnabled(running)
        self.pause_button.setVisible(running)
        self.cancel_button.setEnabled(running)
        self.cancel_button.setVisible(running)

    def set_progress(self, value: int, status: str = "", eta: str = "") -> None:
        """Update progress bar and status text."""
        self.progress_bar.setValue(value)
        if status:
            self.status_label.setText(status)
        if eta:
            self.eta_label.setText(eta)


class SidebarWidget(QWidget):
    """Right sidebar with video info, task status, and quick actions."""

    open_output_clicked = Signal()

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 0, 0, 0)

        # Video Info group
        video_info_group = QGroupBox("Video Info")
        video_info_layout = QGridLayout(video_info_group)

        video_info_layout.addWidget(QLabel("Res:"), 0, 0)
        self.res_label = QLabel("--")
        video_info_layout.addWidget(self.res_label, 0, 1)

        video_info_layout.addWidget(QLabel("Dur:"), 1, 0)
        self.dur_label = QLabel("--")
        video_info_layout.addWidget(self.dur_label, 1, 1)

        video_info_layout.addWidget(QLabel("FPS:"), 2, 0)
        self.fps_label = QLabel("--")
        video_info_layout.addWidget(self.fps_label, 2, 1)

        video_info_layout.addWidget(QLabel("Size:"), 3, 0)
        self.size_label = QLabel("--")
        video_info_layout.addWidget(self.size_label, 3, 1)

        layout.addWidget(video_info_group)

        # Task Status group
        task_status_group = QGroupBox("Task Status")
        task_status_layout = QGridLayout(task_status_group)

        task_status_layout.addWidget(QLabel("Engine:"), 0, 0)
        self.engine_label = QLabel("--")
        task_status_layout.addWidget(self.engine_label, 0, 1)

        task_status_layout.addWidget(QLabel("Status:"), 1, 0)
        self.status_label = QLabel("Idle")
        self.status_label.setProperty("class", "accent")
        task_status_layout.addWidget(self.status_label, 1, 1)

        task_status_layout.addWidget(QLabel("GPU:"), 2, 0)
        self.gpu_label = QLabel("--")
        task_status_layout.addWidget(self.gpu_label, 2, 1)

        layout.addWidget(task_status_group)

        # Quick Actions group
        quick_actions_group = QGroupBox("Quick Actions")
        quick_actions_layout = QVBoxLayout(quick_actions_group)

        self.open_output_button = QPushButton("Open Output")
        self.open_output_button.setEnabled(False)
        self.open_output_button.clicked.connect(self.open_output_clicked.emit)
        quick_actions_layout.addWidget(self.open_output_button)

        layout.addWidget(quick_actions_group)

        layout.addStretch()

    def update_video_info(self, resolution: str, duration: str, fps: str, size: str) -> None:
        """Update video information display."""
        self.res_label.setText(resolution)
        self.dur_label.setText(duration)
        self.fps_label.setText(fps)
        self.size_label.setText(size)

    def update_task_status(self, engine: str, status: str, gpu: str) -> None:
        """Update task status display."""
        self.engine_label.setText(engine)
        self.status_label.setText(status)
        self.gpu_label.setText(gpu)


class LogWidget(QWidget):
    """Collapsible log output widget."""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.expanded = False
        self.setup_ui()

    def setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 4, 0, 0)

        # Header with toggle button
        header_layout = QHBoxLayout()
        header_layout.addWidget(QLabel("Log:"))
        header_layout.addStretch()

        self.toggle_button = QPushButton("Expand")
        self.toggle_button.clicked.connect(self.toggle_log)
        header_layout.addWidget(self.toggle_button)

        layout.addLayout(header_layout)

        # Log text area
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(100)  # Collapsed by default
        self.log_text.setVisible(False)
        layout.addWidget(self.log_text)

    def toggle_log(self) -> None:
        """Toggle log visibility."""
        self.expanded = not self.expanded
        self.log_text.setVisible(self.expanded)
        self.toggle_button.setText("Collapse" if self.expanded else "Expand")
        if self.expanded:
            self.log_text.setMaximumHeight(200)

    def append_log(self, message: str) -> None:
        """Append a message to the log."""
        self.log_text.append(message)


# ============================================================================
# Main Window
# ============================================================================

class MainWindow(QMainWindow):
    """Main application window with tab-based navigation."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("VideOCRplus")
        self.setMinimumSize(1024, 768)
        self.setup_ui()
        self.setup_menubar()
        self.setup_statusbar()

    def setup_ui(self) -> None:
        """Initialize the main UI layout."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Tab widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabPosition(QTabWidget.North)

        # Tab 1: Process Video
        self.tab1 = self.create_process_tab()
        self.tab_widget.addTab(self.tab1, "Process Video")

        # Tab 2: Advanced Settings
        self.tab2 = self.create_settings_tab()
        self.tab_widget.addTab(self.tab2, "Advanced Settings")

        # Tab 3: About
        self.tab3 = self.create_about_tab()
        self.tab_widget.addTab(self.tab3, "About")

        main_layout.addWidget(self.tab_widget)

    def create_process_tab(self) -> QWidget:
        """Create the Process Video tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(14, 12, 14, 12)

        # Header row
        header_layout = QHBoxLayout()
        title_label = QLabel("VideOCRplus")
        title_label.setProperty("class", "title")
        title_label.setFont(FONT_TITLE)
        header_layout.addWidget(title_label)

        header_layout.addStretch()

        header_layout.addWidget(QLabel("When ready:"))
        self.post_action_combo = QComboBox()
        self.post_action_combo.setFixedWidth(150)
        header_layout.addWidget(self.post_action_combo)

        layout.addLayout(header_layout)

        # File + Engine Controls
        file_engine_group = QGroupBox()
        file_engine_layout = QVBoxLayout(file_engine_group)

        # Row 1: Open File/Folder + Source
        row1 = QHBoxLayout()
        self.open_file_button = QPushButton("Open File")
        self.open_file_button.setProperty("class", "primary")
        row1.addWidget(self.open_file_button)

        self.open_folder_button = QPushButton("Open Folder")
        row1.addWidget(self.open_folder_button)

        row1.addWidget(QLabel("Source:"))
        self.video_list_combo = QComboBox()
        self.video_list_combo.setEnabled(False)
        row1.addWidget(self.video_list_combo, stretch=1)

        file_engine_layout.addLayout(row1)

        # Row 2: Output
        row2 = QHBoxLayout()
        row2.addWidget(QLabel("Output:"))
        self.output_input = QLineEdit()
        self.output_input.setReadOnly(True)
        self.output_input.setEnabled(False)
        row2.addWidget(self.output_input, stretch=1)

        self.save_as_button = QPushButton("Save As")
        self.save_as_button.setEnabled(False)
        row2.addWidget(self.save_as_button)

        file_engine_layout.addLayout(row2)

        # Row 3: Engine + Language + Position + Help
        row3 = QHBoxLayout()
        row3.addWidget(QLabel("Engine:"))
        self.engine_combo = QComboBox()
        self.engine_combo.setFixedWidth(200)
        row3.addWidget(self.engine_combo)

        self.engine_info_button = QPushButton("Info")
        self.engine_info_button.setFixedWidth(50)
        row3.addWidget(self.engine_info_button)

        row3.addWidget(QLabel("Lang:"))
        self.lang_combo = QComboBox()
        self.lang_combo.setFixedWidth(150)
        row3.addWidget(self.lang_combo)

        row3.addWidget(QLabel("Pos:"))
        self.pos_combo = QComboBox()
        self.pos_combo.setFixedWidth(100)
        row3.addWidget(self.pos_combo)

        row3.addStretch()

        self.help_button = QPushButton("Help")
        row3.addWidget(self.help_button)

        file_engine_layout.addLayout(row3)

        layout.addWidget(file_engine_group)

        # Main workspace: Preview + Sidebar
        workspace_layout = QHBoxLayout()

        # Left side: Preview + Controls
        left_panel = QVBoxLayout()

        # Video preview
        self.video_preview = VideoPreviewWidget()
        left_panel.addWidget(self.video_preview, stretch=1)

        # Media controls
        self.media_controls = MediaControlsWidget()
        left_panel.addWidget(self.media_controls)

        # Crop info
        crop_layout = QHBoxLayout()
        crop_layout.addWidget(QLabel("Crop:"))
        self.crop_label = QLabel("Not Set")
        crop_layout.addWidget(self.crop_label, stretch=1)

        self.clear_crop_button = QPushButton("Clear Crop")
        self.clear_crop_button.setEnabled(False)
        crop_layout.addWidget(self.clear_crop_button)

        left_panel.addLayout(crop_layout)

        # Processing controls
        self.processing_panel = ProcessingPanel()
        left_panel.addWidget(self.processing_panel)

        # Log widget
        self.log_widget = LogWidget()
        left_panel.addWidget(self.log_widget)

        workspace_layout.addLayout(left_panel, stretch=3)

        # Right sidebar
        self.sidebar = SidebarWidget()
        workspace_layout.addWidget(self.sidebar, stretch=1)

        layout.addLayout(workspace_layout, stretch=1)

        return tab

    def create_settings_tab(self) -> QWidget:
        """Create the Advanced Settings tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(14, 12, 14, 12)

        # Header
        header_layout = QHBoxLayout()
        title_label = QLabel("Advanced Settings")
        title_label.setProperty("class", "title")
        title_label.setFont(FONT_TITLE)
        header_layout.addWidget(title_label)

        header_layout.addStretch()

        subtitle_label = QLabel("Tune recognition, integrations, components, and app behavior.")
        header_layout.addWidget(subtitle_label)

        layout.addLayout(header_layout)

        # Settings content in two columns
        settings_layout = QHBoxLayout()

        # Left column: OCR Settings
        ocr_group = QGroupBox("OCR Settings")
        ocr_layout = QVBoxLayout(ocr_group)

        # Frame Range section
        ocr_layout.addWidget(QLabel("Frame Range"))
        ocr_layout.addWidget(self.create_labeled_input("Start Time (e.g., 0:00 or 1:23:45):", "0:00"))
        ocr_layout.addWidget(self.create_labeled_input("End Time (e.g., 0:10 or 2:34:56):", ""))

        # Separator
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        ocr_layout.addWidget(line)

        # OCR Filtering section
        ocr_layout.addWidget(QLabel("OCR Filtering"))
        ocr_layout.addWidget(self.create_labeled_input("Confidence Threshold (0-100):", "60"))
        ocr_layout.addWidget(self.create_labeled_input("Similarity Threshold (0-100):", "70"))
        ocr_layout.addWidget(self.create_labeled_input("Max Merge Gap (seconds):", "0.1"))
        ocr_layout.addWidget(self.create_labeled_input("Brightness Threshold (0-255):", ""))
        ocr_layout.addWidget(self.create_labeled_input("SSIM Threshold (0-100):", "80"))
        ocr_layout.addWidget(self.create_labeled_input("Max OCR Image Width (pixel):", "1920"))
        ocr_layout.addWidget(self.create_labeled_input("Frames to Skip:", "0"))
        ocr_layout.addWidget(self.create_labeled_input("Minimum Subtitle Duration (seconds):", "0.1"))

        settings_layout.addWidget(ocr_group)

        # Right column: LLM Vision Settings
        llm_group = QGroupBox("LLM Vision Settings")
        llm_layout = QVBoxLayout(llm_group)

        # Header with test button
        llm_header = QHBoxLayout()
        llm_header.addWidget(QLabel("External Vision OCR"))
        llm_header.addStretch()

        self.llm_test_button = QPushButton("Test Connection")
        self.llm_test_button.setProperty("class", "primary")
        llm_header.addWidget(self.llm_test_button)

        llm_layout.addLayout(llm_header)

        # LLM settings inputs
        llm_layout.addWidget(self.create_labeled_input("API Key:", "", password=True))
        llm_layout.addWidget(self.create_labeled_input("API Base URL:", ""))
        llm_layout.addWidget(self.create_labeled_input("Model Name:", ""))
        llm_layout.addWidget(self.create_labeled_input("Concurrency (1-32):", "4"))

        # Checkboxes
        self.llm_disable_inference = QCheckBox("Disable Inference Mode (reasoning/thinking)")
        llm_layout.addWidget(self.llm_disable_inference)

        llm_layout.addWidget(self.create_labeled_input("Image Quality (50-100):", "75"))

        settings_layout.addWidget(llm_group)

        layout.addLayout(settings_layout, stretch=1)

        return tab

    def create_about_tab(self) -> QWidget:
        """Create the About tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(14, 12, 14, 12)

        # Title
        title_label = QLabel("About VideOCRplus")
        title_label.setProperty("class", "title")
        title_label.setFont(FONT_TITLE)
        layout.addWidget(title_label)

        # Version info
        version_group = QGroupBox("Version Information")
        version_layout = QVBoxLayout(version_group)

        self.version_label = QLabel("Version: --")
        version_layout.addWidget(self.version_label)

        self.update_status_label = QLabel("Update Status: Checking...")
        version_layout.addWidget(self.update_status_label)

        check_update_button = QPushButton("Check for Updates")
        check_update_button.clicked.connect(self.check_for_updates)
        version_layout.addWidget(check_update_button)

        layout.addWidget(version_group)

        # Links
        links_group = QGroupBox("Links")
        links_layout = QVBoxLayout(links_group)

        github_link = QLabel('<a href="https://github.com/kiriya55/VideOCRplus">GitHub Repository</a>')
        github_link.setOpenExternalLinks(True)
        links_layout.addWidget(github_link)

        issues_link = QLabel('<a href="https://github.com/kiriya55/VideOCRplus/issues">Report Issues</a>')
        issues_link.setOpenExternalLinks(True)
        links_layout.addWidget(issues_link)

        layout.addWidget(links_group)

        # Notes
        notes_group = QGroupBox("Notes")
        notes_layout = QVBoxLayout(notes_group)

        notes_layout.addWidget(QLabel("For first-run setup, open Advanced Settings and refresh Component Status."))
        notes_layout.addWidget(QLabel("LLM Vision uses your configured OpenAI-compatible or Anthropic-compatible API endpoint."))

        layout.addWidget(notes_group)

        layout.addStretch()

        return tab

    def create_labeled_input(self, label_text: str, default_value: str, password: bool = False) -> QWidget:
        """Helper to create a labeled input field."""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 4, 0, 4)

        label = QLabel(label_text)
        label.setFixedWidth(250)
        layout.addWidget(label)

        input_field = QLineEdit(default_value)
        if password:
            input_field.setEchoMode(QLineEdit.Password)
        layout.addWidget(input_field, stretch=1)

        return widget

    def setup_menubar(self) -> None:
        """Setup the menu bar."""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("File")

        open_action = QAction("Open File", self)
        open_action.setShortcut("Ctrl+O")
        file_menu.addAction(open_action)

        open_folder_action = QAction("Open Folder", self)
        open_folder_action.setShortcut("Ctrl+Shift+O")
        file_menu.addAction(open_folder_action)

        file_menu.addSeparator()

        exit_action = QAction("Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Settings menu
        settings_menu = menubar.addMenu("Settings")

        preferences_action = QAction("Preferences", self)
        preferences_action.setShortcut("Ctrl+,")
        settings_menu.addAction(preferences_action)

        # Help menu
        help_menu = menubar.addMenu("Help")

        about_action = QAction("About", self)
        help_menu.addAction(about_action)

        check_updates_action = QAction("Check for Updates", self)
        help_menu.addAction(check_updates_action)

    def setup_statusbar(self) -> None:
        """Setup the status bar."""
        self.statusBar().showMessage("Ready")

    def check_for_updates(self) -> None:
        """Placeholder for update checking functionality."""
        QMessageBox.information(self, "Check for Updates", "Update checking is not yet implemented.")


# ============================================================================
# Application Class
# ============================================================================

class VideOCRApplication:
    """Main application class."""

    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setStyle("Fusion")  # Use Fusion style for consistent cross-platform appearance

        # Apply dark theme palette
        self.apply_dark_palette()

        # Apply stylesheet
        self.app.setStyleSheet(STYLESHEET)

        # Create main window
        self.window = MainWindow()

    def apply_dark_palette(self) -> None:
        """Apply dark color palette to the application."""
        palette = QPalette()

        # Base colors
        palette.setColor(QPalette.Window, QColor(COLOR_BACKGROUND))
        palette.setColor(QPalette.WindowText, QColor(COLOR_TEXT))
        palette.setColor(QPalette.Base, QColor(COLOR_INPUT))
        palette.setColor(QPalette.AlternateBase, QColor(COLOR_PANEL))
        palette.setColor(QPalette.ToolTipBase, QColor(COLOR_INPUT))
        palette.setColor(QPalette.ToolTipText, QColor(COLOR_TEXT))
        palette.setColor(QPalette.Text, QColor(COLOR_TEXT))
        palette.setColor(QPalette.Button, QColor(COLOR_BUTTON))
        palette.setColor(QPalette.ButtonText, QColor(COLOR_TEXT))
        palette.setColor(QPalette.BrightText, QColor(COLOR_ACCENT))
        palette.setColor(QPalette.Link, QColor(COLOR_ACCENT))
        palette.setColor(QPalette.Highlight, QColor(COLOR_ACCENT))
        palette.setColor(QPalette.HighlightedText, QColor("#07131f"))

        # Disabled colors
        palette.setColor(QPalette.Disabled, QPalette.WindowText, QColor(COLOR_MUTED))
        palette.setColor(QPalette.Disabled, QPalette.Text, QColor(COLOR_MUTED))
        palette.setColor(QPalette.Disabled, QPalette.ButtonText, QColor(COLOR_MUTED))

        self.app.setPalette(palette)

    def run(self) -> int:
        """Run the application."""
        self.window.show()
        return self.app.exec()


# ============================================================================
# Entry Point
# ============================================================================

if __name__ == "__main__":
    app = VideOCRApplication()
    sys.exit(app.run())

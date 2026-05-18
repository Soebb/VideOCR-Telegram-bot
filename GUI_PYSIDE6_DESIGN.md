# VideOCRplus - PySide6 GUI Design

## Overview

This document describes the PySide6/Qt GUI design for VideOCRplus, a modern video OCR application. The new GUI replaces the original PySimpleGUI implementation with a more professional, maintainable, and performant Qt-based interface.

## Design Goals

1. **Modern Appearance**: Dark theme with professional color scheme
2. **Better Performance**: Qt's native widgets for smoother interactions
3. **Modular Architecture**: Separate components for easy maintenance
4. **Cross-Platform**: Consistent behavior on Windows, macOS, and Linux
5. **Responsive Layout**: Adapts to different window sizes and screen resolutions

## Color Palette

The dark theme uses the following color palette:

| Role | Hex Code | Description |
|------|----------|-------------|
| Background | `#151922` | Main window background |
| Panel | `#1b202a` | Group boxes, sidebars |
| Preview | `#05070a` | Video preview area |
| Input | `#0f131a` | Text inputs, dropdowns |
| Text | `#e7ecf3` | Primary text color |
| Muted | `#9ba8b7` | Secondary text, labels |
| Accent | `#69b7ff` | Highlights, primary buttons |
| Danger | `#b85a5a` | Error states, cancel buttons |
| Button | `#2f4055` | Default button background |
| Scroll | `#2c3442` | Scrollbar tracks |

## Architecture

### Main Components

```
MainWindow (QMainWindow)
├── TabWidget
│   ├── Tab 1: Process Video
│   │   ├── Header (Title + Post-Action combo)
│   │   ├── File/Engine Controls (GroupBox)
│   │   ├── Workspace (Splitter)
│   │   │   ├── Left Panel
│   │   │   │   ├── VideoPreviewWidget (QGraphicsView)
│   │   │   │   ├── MediaControlsWidget (Slider + Time)
│   │   │   │   ├── Crop Info
│   │   │   │   ├── ProcessingPanel (Run/Cancel/Progress)
│   │   │   │   └── LogWidget (Collapsible)
│   │   │   └── Right Sidebar (SidebarWidget)
│   │   │       ├── Video Info Group
│   │   │       ├── Task Status Group
│   │   │       └── Quick Actions Group
│   ├── Tab 2: Advanced Settings
│   │   ├── OCR Settings (GroupBox)
│   │   └── LLM Vision Settings (GroupBox)
│   └── Tab 3: About
│       ├── Version Information
│       ├── Links
│       └── Notes
├── MenuBar
└── StatusBar
```

### Custom Widgets

#### VideoPreviewWidget
- Inherits from `QGraphicsView`
- Displays video frames using `QGraphicsScene`
- Supports interactive crop box drawing
- Emits `crop_changed` signal with normalized coordinates

#### MediaControlsWidget
- Seek slider with time display
- Supports seeking via `seek_requested` signal
- Updates current position and duration

#### ProcessingPanel
- Run/Pause/Cancel buttons
- Progress bar with percentage
- Status and ETA display

#### SidebarWidget
- Video information (resolution, duration, FPS, size)
- Task status (engine, status, GPU)
- Quick actions (open output folder)

#### LogWidget
- Collapsible log output area
- Auto-scrolling text display

## Usage

### Installation

1. Install PySide6:
   ```bash
   pip install -r requirements_pyside6.txt
   ```

2. Run the GUI:
   ```bash
   python gui_pyside6.py
   ```

### Integration with Existing Code

The PySide6 GUI is designed to work alongside the existing PySimpleGUI version. To migrate:

1. Keep the existing `gui.py` for reference
2. Update imports to use the new PySide6 widgets
3. Connect signals to existing processing functions
4. Test thoroughly on all platforms

## Signal/Slot Connections

The GUI uses Qt's signal/slot mechanism for event handling:

```python
# Video preview crop changes
video_preview.crop_changed.connect(on_crop_changed)

# Media control seeking
media_controls.seek_requested.connect(on_seek_requested)

# Processing buttons
processing_panel.run_clicked.connect(on_run)
processing_panel.pause_clicked.connect(on_pause)
processing_panel.cancel_clicked.connect(on_cancel)

# Sidebar actions
sidebar.open_output_clicked.connect(on_open_output)
```

## Styling

The application uses a combination of:

1. **QPalette**: Base color scheme for Qt widgets
2. **QSS Stylesheet**: Fine-grained styling for specific widgets
3. **Property-based styling**: Using `setProperty("class", "primary")` for special buttons

### Custom Button Styles

```python
# Primary button (accent color)
button.setProperty("class", "primary")

# Danger button (red)
button.setProperty("class", "danger")
```

## Future Enhancements

1. **Animation**: Add smooth transitions for tab switches and panel expansions
2. **Themes**: Support for light theme and custom theme loading
3. **Drag & Drop**: Support for dragging video files onto the preview
4. **Keyboard Shortcuts**: Additional shortcuts for common actions
5. **Plugin UI**: Dynamic UI generation for OCR plugins
6. **Localization**: Full i18n support with Qt's translation system

## Migration Guide

### From PySimpleGUI to PySide6

| PySimpleGUI | PySide6 Equivalent |
|-------------|-------------------|
| `sg.Window` | `QMainWindow` |
| `sg.Tab` | `QTabWidget.addTab()` |
| `sg.Frame` | `QGroupBox` |
| `sg.Column` | `QWidget` + `QVBoxLayout` |
| `sg.Text` | `QLabel` |
| `sg.Input` | `QLineEdit` |
| `sg.Combo` | `QComboBox` |
| `sg.Button` | `QPushButton` |
| `sg.Slider` | `QSlider` |
| `sg.ProgressBar` | `QProgressBar` |
| `sg.Multiline` | `QTextEdit` |
| `sg.Graph` | `QGraphicsView` |
| `sg.Checkbox` | `QCheckBox` |

### Event Handling

```python
# PySimpleGUI
event, values = window.read()
if event == "-BTN-RUN-":
    handle_run()

# PySide6
button.clicked.connect(handle_run)
```

## Testing

To test the PySide6 GUI:

1. Run the standalone demo:
   ```bash
   python gui_pyside6.py
   ```

2. Verify all widgets render correctly
3. Test resize behavior
4. Check dark theme consistency
5. Verify signal/slot connections

## Conclusion

The PySide6 GUI provides a modern, maintainable foundation for VideOCRplus. Its modular architecture makes it easy to extend and customize, while Qt's native widgets ensure excellent performance and cross-platform compatibility.

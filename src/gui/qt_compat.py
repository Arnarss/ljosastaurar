"""
Qt compatibility layer supporting either PySide6 or PyQt6 seamlessly.
"""

try:
    from PySide6 import QtCore, QtGui, QtWidgets
    from PySide6.QtCore import QThread, Signal, Slot, QTimer, Qt, QPoint
    from PySide6.QtGui import QImage, QPixmap, QColor, QFont, QPainter, QPen
    from PySide6.QtWidgets import (
        QApplication, QMainWindow, QWidget, QLabel, QPushButton,
        QVBoxLayout, QHBoxLayout, QGridLayout, QTableWidget, QTableWidgetItem,
        QHeaderView, QGroupBox, QComboBox, QFileDialog, QMessageBox, QFrame,
        QSplitter, QInputDialog
    )
    QT_BINDING = "PySide6"
except ImportError:
    try:
        from PyQt6 import QtCore, QtGui, QtWidgets
        from PyQt6.QtCore import QThread, pyqtSignal as Signal, pyqtSlot as Slot, QTimer, Qt, QPoint
        from PyQt6.QtGui import QImage, QPixmap, QColor, QFont, QPainter, QPen
        from PyQt6.QtWidgets import (
            QApplication, QMainWindow, QWidget, QLabel, QPushButton,
            QVBoxLayout, QHBoxLayout, QGridLayout, QTableWidget, QTableWidgetItem,
            QHeaderView, QGroupBox, QComboBox, QFileDialog, QMessageBox, QFrame,
            QSplitter, QInputDialog
        )
        QT_BINDING = "PyQt6"
    except ImportError as e:
        raise ImportError(
            "Neither PySide6 nor PyQt6 is installed. Please install one with:\n"
            "pip install PySide6  OR  pip install PyQt6"
        ) from e

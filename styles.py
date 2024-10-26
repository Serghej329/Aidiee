# styles.py
STYLE_SHEET = """
QMainWindow {
    background-color: #2D2D2D;
    color: white;
}

QLabel {
    color: white;
}

QLineEdit {
    background-color: #3D3D3D;
    color: white;
    border: 1px solid #505050;
    padding: 5px;
    border-radius: 3px;
}

QPushButton {
    background-color: #3D3D3D;
    color: white;
    border: none;
    padding: 10px;
    text-align: left;
    border-radius: 3px;
}

QPushButton:hover {
    background-color: #505050;
}

QTreeWidget {
    background-color: #2D2D2D;
    color: white;
    border: none;
}

QTreeWidget::item {
    padding: 5px;
}

QTreeWidget::item:selected {
    background-color: #505050;
}

.action-button {
    padding: 15px;
    margin: 5px 0;
}

.action-button QLabel {
    color: #D8DEE9;
}

.action-description {
    color: #808080;
    font-size: 11px;
}

.icon-button {
    padding: 10px;
    margin: 2px;
}
"""
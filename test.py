import sys
from PyQt5.QtWidgets import QApplication
from simple_ide import SimpleIDE

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = SimpleIDE()
    window.showMaximized()  # Imposta la finestra a full size di default
    sys.exit(app.exec_())
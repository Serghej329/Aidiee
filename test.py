import sys
from PyQt5.QtWidgets import QApplication
from simple_ide import SimpleIDE
from welcome_window import WelcomeWindow


if __name__ == "__main__":
    app = QApplication(sys.argv)
    welcome_window = WelcomeWindow()
    welcome_window.show()
    sys.exit(app.exec_())
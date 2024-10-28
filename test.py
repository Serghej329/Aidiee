import sys
from PyQt5.QtWidgets import QApplication
from simple_ide import SimpleIDE
from welcome_window import WelcomeWindow
if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    window = WelcomeWindow()
    # window2 = SimpleIDE()
    window.show()  # Seconda finestra in dimensione normale

    sys.exit(app.exec_())
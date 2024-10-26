import sys
from PyQt5.QtWidgets import QApplication
from simple_ide import SimpleIDE
from provas import VSCodeClone
if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    window = VSCodeClone()
    # window2 = SimpleIDE()
    window.show()  # Seconda finestra in dimensione normale

    sys.exit(app.exec_())
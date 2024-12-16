import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from Aidee import SimpleIDE
from welcome_window import WelcomeWindow        
if __name__ == '__main__':
    # Enable DPI scale
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)
    
    app = QApplication(sys.argv)
    app.setAttribute(Qt.AA_DontCreateNativeWidgetSiblings)
    
    window = WelcomeWindow()
    window.resize(800, 600)
    window.show()
    # can you create a pygame program with the bash command to run it
    sys.exit(app.exec_())
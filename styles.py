class DarkThemeStyles:
    @staticmethod
    def get_dark_palette():
        return {
            'background': '#2b2b2b',
            'foreground': '#ffffff',
            'accent': '#3d3d3d',
            'highlight': '#323232',
            'button_hover': '#404040'
        }

    @staticmethod
    def get_main_style_sheet(colors):
        return f"""
            /* Main Window */
            QMainWindow {{
                background-color: {colors['background']};
                color: {colors['foreground']};
            }}
            
            /* Text Edit */
            QTextEdit {{
                background-color: {colors['background']};
                color: {colors['foreground']};
                border: none;
                font-size: 15px;
            }}
            
            /* Status Bar */
            QStatusBar {{
                background-color: {colors['background']};
                color: {colors['foreground']};
            }}
            
            /* Dialog */
            QDialog {{
                background-color: {colors['background']};
                color: {colors['foreground']};
            }}
            
            QDialog QLabel {{
                color: {colors['foreground']};
                font-size: 15px;
            }}
        """
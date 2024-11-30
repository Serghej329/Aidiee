from tree_sitter import Language, Parser
import tree_sitter_python as tspython
from bs4 import BeautifulSoup
from html import escape
from PyQt5.QtGui import QTextCharFormat, QColor, QFont
class SyntaxThemes:
    def __init__(self):
        # Tokyo Night theme definition
        #
        self.tokyo_night = {
            'theme_name': 'Tokyo Night',
            'highlight' : '#545c7e',
            'background': '#1f2335',
            'foreground': '#a9b1d6',
            'self': '#b4f9f8',
            'error': '#ff0000',
            'decorator': '#ff007c',
            'import': '#bb9af7',
            'as': '#bb9af7',
            'from': '#bb9af7',
            'dotted_name': '#7aa2f7',
            'attribute': '#A6A6C1',
            'class_definition': '#D8C285',
            'class': '#C87B93',
            'function_definition': '#7aa2f7',
            'def': '#bb9af7',
            'parameters': '#e0af68',
            'default_parameter': '#e0af68',
            'lambda_parameters': '#e0af68',
            'if': '#bb9af7',
            'else': '#bb9af7',
            'elif': '#bb9af7',
            'while': '#bb9af7',
            'for': '#bb9af7',
            'in': '#bb9af7',
            'break': '#bb9af7',
            'lambda': '#bb9af7',
            'call': '#7aa2f7',
            'argument_list': '#C87B93',
            'keyword_argument': '#e0af68',
            '=': '#89ddff',
            '==': '#89ddff',
            'not': '#bb9af7',
            'and': '#bb9af7',
            'is': '#bb9af7',
            'is not': '#bb9af7',
            '-': '#89ddff',
            '+': '#89ddff',
            '|': '#89ddff',
            '*': '#89ddff',
            'string': '#9ece6a',
            'string_start': '#9ece6a',
            'string_content': '#9ece6a',
            'string_end': '#9ece6a',
            'integer': '#ff9e64',
            'float': '#ff9e64',
            'list': '#7aa2f7',
            'true': '#ff9e64',
            'false': '#ff9e64',
            'none': '#bb9af7',
            'list_comprehension': '#7aa2f7',
            'subscript': '#7aa2f7',
            'block': '#c0caf5',
            '[': '#ffc777',
            ']': '#ffc777',
            '(': '#ffc777',
            ')': '#ffc777',
            ',': '#89ddff',
            '.': '#89ddff',
            ':': '#89ddff',
            '{': '#89ddff',
            '}': '#89ddff',
            'comment': '#565f89',
            'builtin_function': '#89ddff',
        }

        self.themes = {
            'Tokyo Night': self.tokyo_night,
            # Add more themes here
        }



class SyntaxFormatter:
    def __init__(self, editor, theme_colors):
        self.editor = editor
        self.colors = theme_colors
        self.parser = Parser(Language(tspython.language()))
        self.editor.textChanged.connect(lambda: self.format_code())
        self.builtin_functions = {
            'print', 'len', 'range', 'str', 'int', 'float', 'list', 'dict', 'set',
            'tuple', 'sum', 'min', 'max', 'abs', 'round', 'sorted', 'enumerate',
            'zip', 'filter', 'map', 'any', 'all', 'open', 'isinstance', 'type', '__init__'
        }
        
        self.keyword_statements = {
            'import_from_statement', 'import_statement', 'as', 'for_statement',
            'for_in_clause', 'and', 'or', 'if_statement', 'while_statement', 'expression_statement'
        }
        
        self.keyword_operators = {
            'boolean_operator', 'assignment', 'binary_operator'
        }

    def apply_format(self, start_byte, end_byte, color, bold=False, underline=False):
        cursor = self.editor.textCursor()
        original_position = cursor.position()
        
        cursor.setPosition(start_byte)
        cursor.setPosition(end_byte, cursor.KeepAnchor)
        fmt = QTextCharFormat()
        fmt.setForeground(QColor(color))
        if bold:
            fmt.setFontWeight(QFont.Bold)
        if underline:
            fmt.setUnderlineStyle(QTextCharFormat.WaveUnderline)
        cursor.setCharFormat(fmt)
        
        cursor.setPosition(original_position)
        self.editor.setTextCursor(cursor)

    def get_node_text(self, node):
        return node.text.decode('utf-8')

    def handle_special_cases(self, node, parent):
        if node.type == 'identifier' and self.get_node_text(node) == 'self':
            self.apply_format(node.start_byte, node.end_byte, self.colors['self'], bold=True)
            return True
        if node.type == 'ERROR':
            self.apply_format(node.start_byte, node.end_byte, self.colors['error'], underline=True)
            return True
        return False

    def handle_identifier(self, node, parent):
        node_text = self.get_node_text(node)
        
        if parent:
            if parent.type == 'call' and node == parent.children[0]:
                if node_text in self.builtin_functions:
                    self.apply_format(node.start_byte, node.end_byte, self.colors['builtin_function'])
                else:
                    self.apply_format(node.start_byte, node.end_byte, self.colors['call'])
            elif parent.type in self.keyword_operators:
                self.apply_format(node.start_byte, node.end_byte, self.colors['attribute'])
            elif parent.type == 'function_definition':
                self.apply_format(node.start_byte, node.end_byte, self.colors['function_definition'])
            elif parent.type in {'import_statement', 'import_from_statement', 'aliased_import'}:
                self.handle_import_identifier(node, parent, node_text)
            elif parent.type == 'argument_list':
                self.apply_format(node.start_byte, node.end_byte, self.colors['attribute'])
        else:
            self.apply_format(node.start_byte, node.end_byte, self.colors['attribute'])

    def handle_import_identifier(self, node, parent, node_text):
        if parent.type == 'import_statement':
            self.apply_format(node.start_byte, node.end_byte, self.colors['dotted_name'])
        elif parent.type == 'import_from_statement':
            if node.prev_sibling and node.prev_sibling.type == 'from':
                self.apply_format(node.start_byte, node.end_byte, self.colors['dotted_name'])
            else:
                self.apply_format(node.start_byte, node.end_byte, self.colors['dotted_name'])
        elif parent.type == 'aliased_import':
            if node.prev_sibling and node.prev_sibling.type == 'as':
                self.apply_format(node.start_byte, node.end_byte, self.colors['dotted_name'])
            else:
                self.apply_format(node.start_byte, node.end_byte, self.colors['dotted_name'])

    def handle_attribute(self, node, parent):
        if parent and parent.type == 'call':
            i = 0
            for child in node.children:
                if child.type == 'identifier' and i == len(node.children)-1:
                    self.apply_format(child.start_byte, child.end_byte, self.colors['call'])
                else:
                    self.apply_format(child.start_byte, child.end_byte, self.colors['attribute'])
                i += 1
        else:
            self.apply_format(node.start_byte, node.end_byte, self.colors['attribute'])
            for child in node.children:
                if child.type == 'identifier':
                    self.apply_format(child.start_byte, child.end_byte, self.colors['attribute'])

    def format_code(self):
        try:
            self.editor.blockSignals(True)
            
            # Reset formatting
            cursor = self.editor.textCursor()
            original_position = cursor.position()
            cursor.select(cursor.Document)
            fmt = QTextCharFormat()
            cursor.setCharFormat(fmt)
            cursor.setPosition(original_position)
            self.editor.setTextCursor(cursor)

            # Parse and format code
            code = self.editor.toPlainText().encode('utf-8')
            tree = self.parser.parse(code)

            def traverse(node, parent=None):
                if not self.handle_special_cases(node, parent):
                    if node.type == 'identifier':
                        self.handle_identifier(node, parent)
                    elif node.type == 'attribute':
                        self.handle_attribute(node, parent)
                    elif node.type in self.colors and node.type not in {'call', 'argument_list'}:
                        self.apply_format(node.start_byte, node.end_byte, self.colors[node.type])
                for child in node.children:
                    traverse(child, node)

            traverse(tree.root_node)
            
        finally:
            self.editor.blockSignals(False)
            
    def highlight_to_html(self, text):
        """
        Highlights a given text and returns it as an HTML string.
        """
        from html import escape

        # Parse the text with Tree-sitter
        code = text.encode('utf-8')
        tree = self.parser.parse(code)
        
        # Generate HTML with highlighting
        highlighted_html = []
        
        def apply_format(start_byte, end_byte, color, bold=False, underline=False):
            snippet = escape(text[start_byte:end_byte])
            styles = [f"color: {color}"]
            if bold:
                styles.append("font-weight: bold")
            if underline:
                styles.append("text-decoration: underline")
            highlighted_html.append(f"<span style='{' '.join(styles)}'>{snippet}</span>")
        
        def traverse(node, parent=None):
            if not self.handle_special_cases_html(node, parent, apply_format):
                if node.type == 'identifier':
                    self.handle_identifier_html(node, parent, apply_format)
                elif node.type == 'attribute':
                    self.handle_attribute_html(node, parent, apply_format)
                elif node.type in self.colors and node.type not in {'call', 'argument_list'}:
                    apply_format(node.start_byte, node.end_byte, self.colors[node.type])
            for child in node.children:
                traverse(child, node)
        
        traverse(tree.root_node)
        return ''.join(highlighted_html)

    def handle_special_cases_html(self, node, parent, apply_format):
        if node.type == 'identifier' and self.get_node_text(node) == 'self':
            apply_format(node.start_byte, node.end_byte, self.colors['self'], bold=True)
            return True
        if node.type == 'ERROR':
            apply_format(node.start_byte, node.end_byte, self.colors['error'], underline=True)
            return True
        return False

    def handle_identifier_html(self, node, parent, apply_format):
        node_text = self.get_node_text(node)
        if parent:
            if parent.type == 'call' and node == parent.children[0]:
                if node_text in self.builtin_functions:
                    apply_format(node.start_byte, node.end_byte, self.colors['builtin_function'])
                else:
                    apply_format(node.start_byte, node.end_byte, self.colors['call'])
            elif parent.type in self.keyword_operators:
                apply_format(node.start_byte, node.end_byte, self.colors['attribute'])
            elif parent.type == 'function_definition':
                apply_format(node.start_byte, node.end_byte, self.colors['function_definition'])
            elif parent.type in {'import_statement', 'import_from_statement', 'aliased_import'}:
                self.handle_import_identifier_html(node, parent, node_text, apply_format)
            elif parent.type == 'argument_list':
                apply_format(node.start_byte, node.end_byte, self.colors['attribute'])
        else:
            apply_format(node.start_byte, node.end_byte, self.colors['attribute'])

    def handle_attribute_html(self, node, parent, apply_format):
        if parent and parent.type == 'call':
            for child in node.children:
                if child.type == 'identifier':
                    apply_format(child.start_byte, child.end_byte, self.colors['attribute'])
        else:
            apply_format(node.start_byte, node.end_byte, self.colors['attribute'])

    def handle_import_identifier_html(self, node, parent, node_text, apply_format):
        if parent.type == 'import_statement':
            apply_format(node.start_byte, node.end_byte, self.colors['dotted_name'])
        elif parent.type == 'import_from_statement':
            if node.prev_sibling and node.prev_sibling.type == 'from':
                apply_format(node.start_byte, node.end_byte, self.colors['dotted_name'])
            else:
                apply_format(node.start_byte, node.end_byte, self.colors['dotted_name'])
        elif parent.type == 'aliased_import':
            if node.prev_sibling and node.prev_sibling.type == 'as':
                apply_format(node.start_byte, node.end_byte, self.colors['dotted_name'])
            else:
                apply_format(node.start_byte, node.end_byte, self.colors['dotted_name'])
    
    def highlight_html_input(self, html_input):
        """
        Highlights a given HTML input and returns it as syntax-highlighted HTML,
        preserving newlines and indentation.
        """
        # Parse the input HTML to extract plain text while preserving whitespace
        soup = BeautifulSoup(html_input, 'html.parser')
        text = soup.get_text(separator='\0')  # Use null character as separator to preserve whitespace
        
        # Replace null characters back with newlines
        text = text.replace('\0', '\n')
        
        # Parse the text with Tree-sitter
        code = text.encode('utf-8')
        tree = self.parser.parse(code)

        # Generate highlighted HTML
        highlighted_html = []
        last_end = 0
        
        def apply_format(start_byte, end_byte, color, bold=False, underline=False):
            nonlocal last_end
            
            # Preserve any whitespace before this token
            if start_byte > last_end:
                whitespace = text[last_end:start_byte]
                highlighted_html.append(escape(whitespace))
            
            # Add the highlighted token
            snippet = escape(text[start_byte:end_byte])
            styles = [f"color: {color}"]
            if bold:
                styles.append("font-weight: bold")
            if underline:
                styles.append("text-decoration: underline")
            highlighted_html.append(f"<span style='{' '.join(styles)}'>{snippet}</span>")
            
            last_end = end_byte

        def traverse(node, parent=None):
            if not self.handle_special_cases_html(node, parent, apply_format):
                if node.type == 'identifier':
                    self.handle_identifier_html(node, parent, apply_format)
                elif node.type == 'attribute':
                    self.handle_attribute_html(node, parent, apply_format)
                elif node.type in self.colors and node.type not in {'call', 'argument_list'}:
                    apply_format(node.start_byte, node.end_byte, self.colors[node.type])
            for child in node.children:
                traverse(child, node)

        traverse(tree.root_node)
        
        # Add any remaining whitespace after the last token
        if last_end < len(text):
            highlighted_html.append(escape(text[last_end:]))

        # Wrap the result in a pre tag to preserve formatting
        highlighted_text = ''.join(highlighted_html)
        return f'<div style="padding: 10;border-radius:5px;background-color:{self.colors['background']};"><pre style="">{highlighted_text}</pre></div>'#padding: 10; background-color:{self.colors['background']};border-radius:5px;margin: 0
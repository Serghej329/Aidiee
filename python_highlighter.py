from tree_sitter import Language, Parser, Tree, TreeCursor
import tree_sitter_python as tspython
from bs4 import BeautifulSoup
from html import escape
from PyQt5.QtGui import QTextCharFormat, QColor, QFont, QSyntaxHighlighter
from PyQt5.QtCore import QTimer
from typing import Dict, List, Tuple, Optional
import weakref

class SyntaxThemes:
    def __init__(self):
        # Tokyo Night theme definition
        self.tokyo_night = {
            'theme_name': 'Tokyo Night',
            #UI Theme:
            'main_background' : '#1a1b26',
            'main_foreground' : '#c0caf5',
            'description_background' : '#24283b',
            'description_foreground' : '#7982a9',
            #Highlighter Theme:
            'highlight' : '#545c7e',
            'background': '#1f2335',
            'foreground': '#a9b1d6',
            'self': '#b4f9f8',
            'error': '#c53b53',
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
            '+='
            '|': '#89ddff',
            '*': '#89ddff',
            'operator':'#89ddff',
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



class TreeCache:
    def __init__(self, max_size: int = 100):
        self.max_size = max_size
        self._cache: Dict[str, Tuple[Tree, float]] = {}
        self._access_count = 0
        
    def get(self, text: str) -> Optional[Tree]:
        if text in self._cache:
            tree, _ = self._cache[text]
            self._cache[text] = (tree, self._access_count)
            self._access_count += 1
            return tree
        return None
    
    def put(self, text: str, tree: Tree):
        if len(self._cache) >= self.max_size:
            # Remove least recently used item
            lru_key = min(self._cache.items(), key=lambda x: x[1][1])[0]
            del self._cache[lru_key]
        self._cache[text] = (tree, self._access_count)
        self._access_count += 1

class BatchFormatter:
    def __init__(self):
        self.formats: List[Tuple[int, int, QTextCharFormat]] = []
        
    def add_format(self, start: int, length: int, fmt: QTextCharFormat):
        self.formats.append((start, length, fmt))
    
    def apply_formats(self, highlighter: QSyntaxHighlighter):
        # Sort formats by start position for efficient application
        self.formats.sort(key=lambda x: x[0])
        
        # Merge adjacent formats with the same formatting
        merged_formats = []
        if self.formats:
            current_start, current_length, current_fmt = self.formats[0]
            
            for start, length, fmt in self.formats[1:]:
                if (start == current_start + current_length and 
                    fmt.foreground() == current_fmt.foreground() and
                    fmt.fontWeight() == current_fmt.fontWeight()):
                    current_length += length
                else:
                    merged_formats.append((current_start, current_length, current_fmt))
                    current_start, current_length, current_fmt = start, length, fmt
            
            merged_formats.append((current_start, current_length, current_fmt))
        
        # Apply merged formats
        for start, length, fmt in merged_formats:
            highlighter.setFormat(start, length, fmt)
        
        self.formats.clear()
class SyntaxFormatter(QSyntaxHighlighter):
    def __init__(self, parent, theme_colors):
        super().__init__(parent)
        self.colors = theme_colors
        self.parser = Parser(Language(tspython.language()))
        self.editor = weakref.proxy(parent)
        
        # Caches
        self.tree_cache = TreeCache()
        self.format_cache: Dict[Tuple[str, bool, bool], QTextCharFormat] = {}
        self.byte_to_char_cache = {}  # Cache for byte-to-char maps
        
        # Batch formatter
        self.batch_formatter = BatchFormatter()
        
        # Debounce timer
        self._rehighlight_timer = QTimer()
        self._rehighlight_timer.setSingleShot(True)
        self._rehighlight_timer.timeout.connect(self.rehighlight_now)
        
        # Connect to document's contentsChanged signal
        self.document().contentsChanged.connect(self.on_contents_changed)
        
        self.initialize_attributes()

    def initialize_attributes(self):
        self.builtin_functions = {
            'print', 'len', 'range', 'str', 'int', 'float', 'list', 'dict', 'set',
            'tuple', 'sum', 'min', 'max', 'abs', 'round', 'sorted', 'enumerate',
            'zip', 'filter', 'map', 'any', 'all', 'open', 'isinstance', 'type', '__init__'
        }
        
        self.keyword_statements = {
            'import_from_statement', 'import_statement', 'as', 'for_statement',
            'for_in_clause', 'and', 'or', 'if_statement', 'while_statement', 
            'expression_statement'
        }
        
        self.keyword_operators = {
            'boolean_operator', 'assignment', 'binary_operator'
        }

    def build_byte_to_char_map(self, text):
        """
        Efficiently builds a byte-to-char position mapping using array operations.
        
        Args:
            text: Input string to map
            
        Returns:
            Dict mapping byte positions to character positions
        """
        # Check cache first
        text_hash = hash(text)
        if text_hash in self.byte_to_char_cache:
            return self.byte_to_char_cache[text_hash]
        
        # Pre-calculate encoded lengths
        char_lengths = [len(char.encode('utf-8')) for char in text]
        
        # Pre-allocate arrays for better performance
        byte_positions = []
        char_positions = []
        
        current_byte = 0
        for char_pos, byte_len in enumerate(char_lengths):
            # Map each byte position to its corresponding character position
            for i in range(byte_len):
                byte_positions.append(current_byte + i)
                char_positions.append(char_pos)
            current_byte += byte_len
    
        # Add final position
        byte_positions.append(current_byte)
        char_positions.append(len(text))
    
        # Create mapping dict in one operation
        mapping = dict(zip(byte_positions, char_positions))
        
        # Cache the result
        if len(self.byte_to_char_cache) > 100:  # Limit cache size
            self.byte_to_char_cache.clear()
        self.byte_to_char_cache[text_hash] = mapping
        return mapping
        

    def get_char_position(self, byte_pos: int, mapping: dict) -> int:
        """
        Fast character position lookup.
        
        Args:
            byte_pos: Byte position to convert
            mapping: Byte-to-char mapping dictionary
            
        Returns:
            Character position
        """
        return mapping.get(byte_pos, byte_pos)  # Fallback to byte_pos for single-byte chars

    def adjust_node_range(self,node, byte_to_char_map):
        """
        Converts a node's byte range to character range.
        
        Args:
                node: The tree-sitter node
                byte_to_char_map (dict): Mapping from byte positions to character positions
                
        Returns:
                tuple: (start_char, end_char) positions, or None if invalid
        """
        start_char = byte_to_char_map.get(node.start_byte)
        end_char = byte_to_char_map.get(node.end_byte)
    
        if start_char is None or end_char is None:
                print(f"Warning: Invalid byte range for node {node.type} ({node.start_byte}, {node.end_byte})")
                return None
        
        return start_char, end_char

    def create_format(self, color: str, bold: bool = False, underline: bool = False) -> QTextCharFormat:
        key = (color, bold, underline)
        
        if key in self.format_cache:
            return self.format_cache[key]
        
        fmt = QTextCharFormat()
        fmt.setForeground(QColor(color))
        if bold:
            fmt.setFontWeight(QFont.Bold)
        if underline:
            fmt.setUnderlineStyle(QTextCharFormat.SingleUnderline)
        
        self.format_cache[key] = fmt
        return fmt
    
    def get_node_text(self, node, text, byte_map=None):
        """Optimized node text extraction"""
        if byte_map is None or not byte_map:
            return text[node.start_byte:node.end_byte]
        
        start_char = self.get_char_position(node.start_byte, byte_map)
        end_char = self.get_char_position(node.end_byte, byte_map)
        return text[start_char:end_char]
    
    def handle_special_cases(self, node, text, formats):
        node_text = self.get_node_text(node, text)
        if node.type == 'identifier' and node_text == 'self':
            fmt = self.create_format(self.colors['self'], bold=True)
            formats.append((node.start_byte, node.end_byte - node.start_byte, fmt))
            return True
        if node.type == 'ERROR':
            fmt = self.create_format(self.colors['error'], underline=True)
            formats.append((node.start_byte, node.end_byte - node.start_byte, fmt))
            return True
        return False

    def handle_identifier(self, node, parent, text, formats):
        node_text = self.get_node_text(node, text)
        
        if parent:
            if parent.type == 'call' and node == parent.children[0]:
                color = self.colors['builtin_function'] if node_text in self.builtin_functions else self.colors['call']
                fmt = self.create_format(color)
                formats.append((node.start_byte, node.end_byte - node.start_byte, fmt))
            elif parent.type in self.keyword_operators:
                fmt = self.create_format(self.colors['attribute'])
                formats.append((node.start_byte, node.end_byte - node.start_byte, fmt))
            elif parent.type == 'function_definition':
                fmt = self.create_format(self.colors['function_definition'])
                formats.append((node.start_byte, node.end_byte - node.start_byte, fmt))
            elif parent.type in {'import_statement', 'import_from_statement', 'aliased_import'}:
                self.handle_import_identifier(node, parent, formats)
            elif parent.type == 'argument_list':
                fmt = self.create_format(self.colors['attribute'])
                formats.append((node.start_byte, node.end_byte - node.start_byte, fmt))
        else:
            fmt = self.create_format(self.colors['attribute'])
            formats.append((node.start_byte, node.end_byte - node.start_byte, fmt))


    def handle_import_identifier(self, node, parent, formats):
        fmt = self.create_format(self.colors['dotted_name'])
        formats.append((node.start_byte, node.end_byte - node.start_byte, fmt))

    def give_attribute_format(self, node, parent, text):
        """
        Handle 'attribute' nodes and apply appropriate formatting using batch formatter.
        
        Args:
                node: The current Tree-sitter node to process
                parent: The parent node, used to determine context
                text: The full text being processed
        """
        if parent and parent.type == 'call':
                # For function calls, process the attribute chain
                children = [child for child in node.children]
                
                for i, child in enumerate(children):
                        if child.type == 'identifier':
                                # If this is the last identifier in the chain, it's the function name
                                if i == len(children) - 1:
                                        fmt = self.create_format(self.colors['call'])
                                else:
                                        fmt = self.create_format(self.colors['attribute'])
                                
                                self.batch_formatter.add_format(
                                child.start_byte,
                                child.end_byte - child.start_byte,
                                fmt
                                )
                        elif child.type == '.':
                                # Format the dots consistently with attributes
                                fmt = self.create_format(self.colors['attribute'])
                                self.batch_formatter.add_format(
                                child.start_byte,
                                child.end_byte - child.start_byte,
                                fmt
                                )
        else:
                # Handle regular attribute access (non-call context)
                # Format the entire attribute node
                fmt = self.create_format(self.colors['attribute'])
                self.batch_formatter.add_format(
                node.start_byte,
                node.end_byte - node.start_byte,
                fmt
                )
                
                # Additionally format each identifier in the chain
                for child in node.children:
                        if child.type == 'identifier':
                                fmt = self.create_format(self.colors['attribute'])
                                self.batch_formatter.add_format(
                                child.start_byte,
                                child.end_byte - child.start_byte,
                                fmt
                                )



    def highlightBlock(self, text: str):
        block = self.currentBlock()
        doc = self.document()
        
        # Check if block is visible
        if self.should_skip_block(block, doc):
            return
            
        # Get document text and parse
        full_text = doc.toPlainText()
        tree = self.get_or_parse_tree(full_text)
        
        # Build byte-to-char map once for the entire text
        byte_map = self.build_byte_to_char_map(full_text)
        
        # Calculate block positions
        block_pos = block.position()
        block_length = len(text)
        block_end = block_pos + block_length
        
        # Create cursor for efficient tree traversal
        cursor = tree.walk()
        
        # Process nodes using cursor with the byte map
        self.process_visible_nodes(cursor, block_pos, block_end, full_text, byte_map)
        
        # Apply batched formats
        self.batch_formatter.apply_formats(self)

    def should_skip_block(self, block, doc) -> bool:
        if hasattr(doc, 'documentLayout'):
            layout = doc.documentLayout()
            if hasattr(layout, 'documentRect'):
                visible_rect = layout.documentRect()
                block_rect = layout.blockBoundingRect(block)
                return (block_rect.bottom() < visible_rect.top() or 
                        block_rect.top() > visible_rect.bottom())
        return False

    def get_or_parse_tree(self, text: str) -> Tree:
        tree = self.tree_cache.get(text)
        if tree is None:
            tree = self.parser.parse(text.encode('utf-8'))
            self.tree_cache.put(text, tree)
        return tree

    def process_visible_nodes(self, cursor, block_start, block_end, text, byte_map):
        while True:
            node = cursor.node
            
            # Fast position conversion
            node_start = self.get_char_position(node.start_byte, byte_map)
            node_end = self.get_char_position(node.end_byte, byte_map)
            
            if node_end < block_start:
                if not cursor.goto_next_sibling():
                    if not cursor.goto_parent() or not cursor.goto_next_sibling():
                        break
                continue
            
            if node_start > block_end:
                break
            
            # Process node if it's in view
            if node_start <= block_end and node_end >= block_start:
                self.process_node(node, node.parent, text, block_start, byte_map)
            
            if cursor.goto_first_child():
                continue
                
            if cursor.goto_next_sibling():
                continue
                
            while True:
                if not cursor.goto_parent():
                    return
                if cursor.goto_next_sibling():
                    break


    def process_node(self, node, parent_node, text, block_start, byte_map):
        node_start = self.get_char_position(node.start_byte, byte_map)
        node_end = self.get_char_position(node.end_byte, byte_map)
        
        rel_start = node_start - block_start
        length = node_end - node_start
        
        # Fast node text extraction
        node_text = text[node_start:node_end]
        
        # Quick format lookup and application
        fmt = None
        if node.type == 'ERROR':
                fmt = self.create_format(self.colors['error'], underline=True)

        elif node.type == 'identifier':
            if node_text == 'self':
                fmt = self.create_format(self.colors['self'], bold=True)
            else:
                fmt = self.get_identifier_format(node, parent_node, node_text)

        elif node.type == 'attribute':
            self.give_attribute_format(node, parent_node, node_text)

        elif node.type in self.colors:
            fmt = self.create_format(self.colors[node.type])
        
        if fmt is not None:
            self.batch_formatter.add_format(rel_start, length, fmt)

    def get_identifier_format(self, node, parent_node, node_text: str) -> QTextCharFormat:
        current = node
        while parent_node:
                if parent_node.type == 'attribute':
                        return None
                current = parent_node
                parent_node = current.parent
                
        if parent_node:
            if parent_node.type == 'call' and node == parent_node.children[0]:
                color = (self.colors['builtin_function'] if node_text in self.builtin_functions 
                        else self.colors['call'])
            elif parent_node.type in self.keyword_operators:
                color = self.colors['attribute']
            elif parent_node.type == 'function_definition':
                color = self.colors['function_definition']
            elif parent_node.type in {'import_statement', 'import_from_statement', 'aliased_import'}:
                color = self.colors['dotted_name']
            else:
                color = self.colors['attribute']
        else:
            color = self.colors['attribute']
            
        return self.create_format(color)
    
    def rehighlight(self):
        """Debounced rehighlight to avoid excessive updates"""
        if self._rehighlight_timer.isActive():
            self._rehighlight_timer.stop()
        self._rehighlight_timer.start(500)  # 500ms debounce

    def on_contents_changed(self):
        if self._rehighlight_timer.isActive():
            self._rehighlight_timer.stop()
        self._rehighlight_timer.start(500)  # 500ms debounce
    
    def rehighlight_now(self):
        super().rehighlight()

    def highlight_to_html(self, text):
        """
        Highlights text and returns HTML with proper character position handling
        """
        code = text.encode('utf-8')
        tree = self.parser.parse(code)
        
        # Build character mappings
        byte_to_char_map, char_to_byte_map = self.build_byte_to_char_map(text)
        highlighted_html = []
        
        def apply_format(start_byte, end_byte, color, bold=False, underline=False):
            char_range = self.adjust_node_range(
                type('Node', (), {'start_byte': start_byte, 'end_byte': end_byte}),
                byte_to_char_map
            )
            if char_range is None:
                return
                
            start_char, end_char = char_range
            snippet = escape(text[start_char:end_char])
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

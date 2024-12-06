import subprocess
import threading
import queue
import time
import sys
import os
from enum import Enum, auto
from output_types import OutputType


class OutputMessage:
    def __init__(self, type: OutputType, content: str, timestamp=None):
        self.type = type
        self.content = content
        self.timestamp = timestamp or time.time()

class TerminalHandler:
    def __init__(self, terminal_type="cmd", initial_cwd=None):
        self.terminal_type = terminal_type
        self.process = None
        self.stop_event = threading.Event()
        self.command_thread = None
        self.newline = "\n" if terminal_type == "cmd" else "`n"
        self.command_queue = queue.Queue()
        self.output_queue = queue.Queue()
        self.current_process = None
        self.commands_pending = 0
        self.commands_lock = threading.Lock()
        self.current_cwd = initial_cwd or os.getcwd()
        self.filtered_messages = [
            "Microsoft Windows [Version",
            "(c) Microsoft Corporation. All rights reserved.",
            "(c) Microsoft Corporation. Tutti i diritti sono riservati."
        ]

    def _start_terminal(self):
        """Start the terminal process with appropriate settings."""
        if self.terminal_type == "cmd":
            command = ["cmd.exe", "/q"]
        elif self.terminal_type == "powershell":
            command = ["powershell.exe"]
        else:
            raise ValueError("Unsupported terminal type")
        
        try:
            self.process = subprocess.Popen(
                command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=0,
                universal_newlines=True,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0,
                cwd=self.current_cwd  # Set initial working directory
            )
        except Exception as e:
            self._emit_error(f"Failed to start terminal: {e}")
            raise
        
        threading.Thread(target=self._read_process_output, 
                        args=(self.process.stdout, OutputType.STDOUT),
                        daemon=True).start()
        threading.Thread(target=self._read_process_output, 
                        args=(self.process.stderr, OutputType.STDERR),
                        daemon=True).start()

    def _update_cwd(self, new_cwd):
        """Update the current working directory."""
        self.current_cwd = new_cwd
        self._emit_output(OutputType.CWD, new_cwd)

    def _execute_python_script(self, script_name):
        """Execute a Python script with unbuffered output."""
        python_executable = "pythonw.exe" if os.name == 'nt' else "python"
        
        try:
            self.current_process = subprocess.Popen(
                [python_executable, "-u", script_name],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=0,
                universal_newlines=True,
                cwd=self.current_cwd  # Use current working directory
            )
            
            out_thread = threading.Thread(target=self._read_process_output, 
                                        args=(self.current_process.stdout, OutputType.STDOUT),
                                        daemon=True)
            err_thread = threading.Thread(target=self._read_process_output, 
                                        args=(self.current_process.stderr, OutputType.STDERR),
                                        daemon=True)
            out_thread.start()
            err_thread.start()
            
            self.current_process.wait()
            
            out_thread.join()
            err_thread.join()
            self.current_process = None
            
        except Exception as e:
            self._emit_error(f"Error executing Python script {script_name}: {e}")
            raise

    def _execute_terminal_command(self, command):
        """Execute a command directly in the terminal."""
        try:
            # Handle CD commands specially to track directory changes
            if command.lower().startswith('cd '):
                new_path = command[3:].strip().strip('"').strip("'")
                if new_path:
                    try:
                        # Handle relative or absolute paths
                        if os.path.isabs(new_path):
                            new_cwd = new_path
                        else:
                            new_cwd = os.path.abspath(os.path.join(self.current_cwd, new_path))
                        
                        if os.path.exists(new_cwd):
                            self._update_cwd(new_cwd)
                        else:
                            self._emit_error(f"Directory not found: {new_path}")
                    except Exception as e:
                        self._emit_error(f"Error changing directory: {e}")

            command_with_newline = command + self.newline
            self.process.stdin.write(command_with_newline)
            self.process.stdin.flush()
            
            time.sleep(0.1)
        except Exception as e:
            self._emit_error(f"Error executing command '{command}': {e}")
            raise

    def _read_process_output(self, stream, output_type: OutputType):
        """Read output from a process stream and put it in the output queue."""
        try:
            while True:
                line = stream.readline()
                if not line:
                    break
                if line.strip():  # Only process non-empty lines
                    self._emit_output(output_type, line.strip())
        except (ValueError, IOError) as e:
            self._emit_error(f"Error reading from {output_type.name}: {e}")

    def _emit_output(self, type: OutputType, content: str):
        """Put an output message in the queue, filtering out unwanted messages."""
        if not self._should_filter_message(content):
            self.output_queue.put(OutputMessage(type, content))

    def _emit_error(self, message: str):
        """Emit an error message."""
        self._emit_output(OutputType.ERROR, message)

    def _emit_info(self, message: str):
        """Emit an informational message."""
        self._emit_output(OutputType.INFO, message)

    def _emit_command(self, message: str):
        """Emit a command execution message."""
        self._emit_output(OutputType.COMMAND, message)

    def _should_filter_message(self, content: str) -> bool:
        """Check if a message should be filtered out."""
        return any(filtered in content for filtered in self.filtered_messages)
    
    def _command_worker(self):
        """Worker thread that processes commands from the command queue."""
        while not self.stop_event.is_set():
            try:
                command = self.command_queue.get(timeout=0.1)
                if command is None:
                    break
                
                try:
                    # Special handling for Python scripts
                    if command.startswith("python "):
                        script_name = command.split()[1]
                        self._execute_python_script(script_name)
                    else:
                        # Regular command execution
                        self._execute_terminal_command(command)
                        
                except Exception as e:
                    self._emit_error(f"Command execution failed: {e}")
                
                self.command_queue.task_done()
                with self.commands_lock:
                    self.commands_pending -= 1
                    
            except queue.Empty:
                continue

    def start(self):
        """Start the terminal and command processing thread."""
        if self.process is not None:
            self.stop()
        
        self.stop_event.clear()
        self._start_terminal()
        
        # Start command processing thread
        self.command_thread = threading.Thread(
            target=self._command_worker,
            daemon=True
        )
        self.command_thread.start()

    def stop(self):
        """Stop the terminal and clean up resources."""
        self.stop_event.set()
        self.command_queue.put(None)
        
        # Stop current Python process if running
        if self.current_process:
            try:
                self.current_process.terminate()
                self.current_process.wait(timeout=1)
            except Exception as e:
                self._emit_error(f"Error stopping current process: {e}")
        
        if self.process:
            try:
                # Send exit command to CMD
                self.process.stdin.write("exit" + self.newline)
                self.process.stdin.flush()
                
                try:
                    self.process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    if os.name == 'nt':
                        self.process.send_signal(subprocess.CTRL_BREAK_EVENT)
                    else:
                        self.process.terminate()
                    self.process.wait(timeout=1)
                    
                    if self.process.poll() is None:
                        self.process.kill()
                        self.process.wait()
            
            except Exception as e:
                self._emit_error(f"Error stopping terminal: {e}")
            
            finally:
                self.process = None
                #self._emit_info("Terminal stopped")

        # Wait for command thread to finish
        if self.command_thread and self.command_thread.is_alive():
            self.command_thread.join(timeout=1)

    def execute_command(self, command):
        """Queue a command for execution in the terminal."""
        if not self.process or self.process.poll() is not None:
            raise RuntimeError("Terminal is not running")
        
        with self.commands_lock:
            self.commands_pending += 1
        self.command_queue.put(command)
        return True

    def has_pending_commands(self):
        """Check if there are any pending commands."""
        with self.commands_lock:
            return self.commands_pending > 0

    def get_output(self, timeout=0.1):
        """Get output from the output queue. Returns OutputMessage object
        or None if queue is empty."""
        try:
            return self.output_queue.get(timeout=timeout)
        except queue.Empty:
            return None

def run_test():
    # Create and start terminal handler
    terminal = TerminalHandler()
    terminal.start()
    
    try:
        # Execute test commands
        commands = [
            "echo Running Python program...",
            "python loop_program.py",
            "cd .."
        ]
        
        # Queue all commands
        for command in commands:
            terminal.execute_command(command)
            time.sleep(0.2)
        
        # Process output while commands are running
        while terminal.has_pending_commands():
            message = terminal.get_output()
            if message:
                # Example of handling different output types
                if message.type == OutputType.ERROR:
                    print(f"\033[91m[ERROR] {message.content}\033[0m")  # Red text
                elif message.type == OutputType.STDERR:
                    print(f"\033[93m[STDERR] {message.content}\033[0m")  # Yellow text
                elif message.type == OutputType.COMMAND:
                    print(f"\033[94m[CMD] {message.content}\033[0m")    # Blue text
                elif message.type == OutputType.INFO:
                    print(f"\033[92m[INFO] {message.content}\033[0m")   # Green text
                elif message.type == OutputType.CWD:
                        print(f"\033[95m[CWD] {message.content}\033[0m")
                else:
                    print(f"[STDOUT] {message.content}")
            time.sleep(0.1)
            
        # Process any remaining output
        while True:
            message = terminal.get_output(timeout=0.5)
            if not message:
                break
            # Same output handling as above
            if message.type == OutputType.ERROR:
                print(f"\033[91m[ERROR] {message.content}\033[0m")
            elif message.type == OutputType.STDERR:
                print(f"\033[93m[STDERR] {message.content}\033[0m")
            elif message.type == OutputType.COMMAND:
                print(f"\033[94m[CMD] {message.content}\033[0m")
            elif message.type == OutputType.INFO:
                print(f"\033[92m[INFO] {message.content}\033[0m")
            elif message.type == OutputType.CWD:
                print(f"\033[95m[CWD] {message.content}\033[0m")
            else:
                print(f"[STDOUT] {message.content}")
            
        print("\nAll commands completed. Exiting...")
    
    except KeyboardInterrupt:
        print("\nReceived keyboard interrupt, stopping...")
    
    finally:
        terminal.stop()

if __name__ == "__main__":
    run_test()
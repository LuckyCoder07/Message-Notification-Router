import os
import sys
import shlex
try:
    import readline  # Enables up/down arrow history on Unix automatically
except ImportError:
    pass

class Colors:
    """ANSI color codes for terminal output."""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

class CLI:
    """
    A modular, reusable terminal framework.
    Supports command registration, parsing, history, and colored output.
    """
    def __init__(self, prompt: str = "cli> ", welcome_message: str = "Welcome to the CLI."):
        self.prompt = f"{Colors.OKCYAN}{prompt}{Colors.ENDC}"
        self.welcome_message = welcome_message
        self.commands = {}
        self.history = []
        
        # Register built-in commands
        self.register("help", self._cmd_help, "List all available commands")
        self.register("clear", self._cmd_clear, "Clear the terminal screen")
        self.register("exit", self._cmd_exit, "Exit the CLI")
        self.register("history", self._cmd_history, "Show command history")

    def register(self, name: str, handler, description: str = "No description provided.") -> None:
        """
        Registers a new command in the CLI.
        
        Args:
            name: The command string the user types.
            handler: A callable that accepts a list of string arguments.
            description: Help text for the command.
        """
        self.commands[name] = {
            "handler": handler,
            "description": description
        }

    def _cmd_help(self, args: list) -> None:
        print(f"\n{Colors.BOLD}Available Commands:{Colors.ENDC}")
        for name, cmd in sorted(self.commands.items()):
            print(f"  {Colors.OKGREEN}{name:<15}{Colors.ENDC} {cmd['description']}")
        print()

    def _cmd_clear(self, args: list) -> None:
        os.system('cls' if os.name == 'nt' else 'clear')

    def _cmd_exit(self, args: list) -> None:
        print(f"{Colors.OKBLUE}Goodbye!{Colors.ENDC}")
        sys.exit(0)

    def _cmd_history(self, args: list) -> None:
        print(f"\n{Colors.BOLD}Command History:{Colors.ENDC}")
        for i, cmd in enumerate(self.history, 1):
            print(f"  {i:>3}. {cmd}")
        print()

    def parse_and_execute(self, raw_input: str) -> None:
        """Parses the raw input string and executes the corresponding command."""
        raw_input = raw_input.strip()
        if not raw_input:
            return
            
        self.history.append(raw_input)
        
        try:
            # Use shlex to properly handle quotes in arguments
            parts = shlex.split(raw_input)
        except ValueError as e:
            print(f"{Colors.FAIL}Parse error: {e}{Colors.ENDC}")
            return
            
        cmd_name = parts[0]
        args = parts[1:]
        
        if cmd_name in self.commands:
            try:
                self.commands[cmd_name]["handler"](args)
            except Exception as e:
                print(f"{Colors.FAIL}Error executing '{cmd_name}': {e}{Colors.ENDC}")
        else:
            print(f"{Colors.WARNING}Unknown command: '{cmd_name}'. Type 'help' for a list of commands.{Colors.ENDC}")

    def run(self) -> None:
        """Starts the interactive CLI loop."""
        print(f"{Colors.HEADER}{self.welcome_message}{Colors.ENDC}")
        print(f"Type {Colors.OKGREEN}'help'{Colors.ENDC} to see available commands.")
        
        while True:
            try:
                user_input = input(self.prompt)
                self.parse_and_execute(user_input)
            except KeyboardInterrupt:
                # Handle Ctrl+C gracefully
                print("\nType 'exit' to quit.")
            except EOFError:
                # Handle Ctrl+D gracefully
                self._cmd_exit([])

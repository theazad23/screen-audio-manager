#!/usr/bin/env python3
"""
Utilities for running shell commands and processing their output.
"""
import subprocess
from typing import Optional, Union, List
from dataclasses import dataclass

@dataclass
class CommandResult:
    """Stores the result of a command execution."""
    returncode: int
    stdout: str
    stderr: str
    
    @property
    def success(self) -> bool:
        """Returns True if the command executed successfully."""
        return self.returncode == 0

def run_command(command: Union[str, List[str]], 
                timeout: Optional[int] = 30,
                shell: bool = True) -> CommandResult:
    """
    Run a shell command and return its output.
    
    Args:
        command: Command to run as string or list of arguments
        timeout: Timeout in seconds (None for no timeout)
        shell: Whether to run the command through the shell
        
    Returns:
        CommandResult object with return code, stdout, and stderr
    """
    try:
        process = subprocess.run(
            command,
            shell=shell,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        
        return CommandResult(
            returncode=process.returncode,
            stdout=process.stdout.strip(),
            stderr=process.stderr.strip()
        )
    except subprocess.TimeoutExpired:
        return CommandResult(
            returncode=124,  # Standard timeout exit code
            stdout="",
            stderr=f"Command timed out after {timeout} seconds"
        )
    except Exception as e:
        return CommandResult(
            returncode=1,
            stdout="",
            stderr=f"Error executing command: {str(e)}"
        )

def check_command_exists(command: str) -> bool:
    """
    Check if a command exists in the system.
    
    Args:
        command: Command name to check
        
    Returns:
        True if command exists, False otherwise
    """
    result = run_command(f"which {command}")
    return result.success

def check_dependency(command: str, package: str) -> bool:
    """
    Check if a dependency exists and suggest installation if not.
    
    Args:
        command: Command to check
        package: Package name that provides the command
        
    Returns:
        True if dependency exists, False otherwise
    """
    if check_command_exists(command):
        return True
    
    print(f"Required dependency '{command}' not found.")
    print(f"Please install it with: sudo pacman -S {package}")
    return False

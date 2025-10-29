# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from rich.console import Console


class ExtendedConsole(Console):
    def error(self, message: str):
        self.print(f"💥 [red]ERROR[/red]: {message}")

    def warning(self, message: str):
        self.print(f"❗ [yellow]WARNING[/yellow]: {message}")

    def hint(self, message: str):
        self.print(f"💡 [bright_cyan]HINT[/bright_cyan]: {message}")

    def success(self, message: str):
        self.print(f"✅ [green]SUCCESS[/green]: {message}")

    def info(self, message: str):
        self.print(f"📝 INFO: {message}")


err_console = ExtendedConsole(stderr=True)
console = ExtendedConsole()

import io
from contextlib import redirect_stdout
from pathlib import Path

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Button, Checkbox, ContentSwitcher, Footer, Header, Input, Label, Log, Select, Static

from .commands import print_ip_table, sync, time_sync

PACKAGE_LISTS_DIR = Path(__file__).parent / "package_lists"


def _package_list_options():
    files = sorted(PACKAGE_LISTS_DIR.glob("*.yaml"))
    return [(f.stem, str(f)) for f in files]


class RoverApp(App):
    TITLE = "Rover TUI"
    BINDINGS = [
        Binding("1", "show_ip_table", "IP table", priority=True),
        Binding("2", "show_time_sync", "Time sync", priority=True),
        Binding("3", "show_sync", "Sync", priority=True),
        Binding("q", "exit", "Exit", priority=True),
    ]
    CSS = """
    Screen { align: center middle; }
    #main { width: 96%; height: 94%; }
    #workspace { height: 1fr; }
    #command-rail { width: 24; padding: 1; border: round $panel; }
    #command-rail Button { width: 100%; margin-bottom: 1; }
    #command-rail Button.-selected { background: $accent; color: $text; }
    #content { width: 1fr; padding-left: 1; }
    .command-panel { height: auto; padding: 1; border: round $accent; }
    .command-panel Input { margin: 0 1; }
    #log { height: 1fr; border: round $panel; padding: 1; }
    """

    def compose(self) -> ComposeResult:
        yield Header()
        with Container(id="main"):
            yield Static("Rover operations", id="heading")
            with Horizontal(id="workspace"):
                with Vertical(id="command-rail"):
                    yield Button("1  IP table", id="select-ip")
                    yield Button("2  Time sync", id="select-time")
                    yield Button("3  Sync", id="select-sync")
                    yield Button("Exit", id="exit", variant="error")
                with Vertical(id="content"):
                    with ContentSwitcher(initial="ip-panel", id="command-content"):
                        yield Static("", id="ip-panel")
                        with Vertical(classes="command-panel", id="sync-panel"):
                            yield Label("Sync workspace")
                            yield Input("RoverFlake2", placeholder="Source root", id="src-root")
                            yield Input("RoverFlake2", placeholder="Destination root", id="dst-root")
                            yield Input("rv@192.168.1.4", placeholder="Remote host", id="remote-host")
                            yield Select(
                                _package_list_options(),
                                prompt="Package list (optional)",
                                id="package-list",
                            )
                            yield Input(placeholder="Extra packages (space separated)", id="extra-packages")
                            yield Checkbox("Build after sync", value=True, id="build")
                            yield Checkbox("Include external packages", value=True, id="external-pkgs")
                            yield Button("Run sync", id="run-sync", variant="success")
                        with Vertical(classes="command-panel", id="time-panel"):
                            yield Label("Time sync")
                            yield Input(placeholder="Remote host for time sync", id="time-host")
                            yield Input(placeholder="sudo password", password=True, id="time-password")
                            yield Button("Run time sync", id="run-time-sync", variant="primary")
                    yield Log(id="log", highlight=True)
        yield Footer()

    def on_mount(self) -> None:
        for button in self.query(Button):
            button.can_focus = False
        heading = self.query_one("#heading", Static)
        heading.can_focus = True
        heading.focus()
        self._write_output(print_ip_table)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "select-ip":
            self.action_show_ip_table()
        elif event.button.id == "select-time":
            self.action_show_time_sync()
        elif event.button.id == "select-sync":
            self.action_show_sync()
        elif event.button.id == "exit":
            self.exit()
        elif event.button.id == "run-time-sync":
            self._write_output(
                time_sync,
                remote_host=self.query_one("#time-host", Input).value or "rover",
                password=self.query_one("#time-password", Input).value,
            )
        elif event.button.id == "run-sync":
            self._run_sync()

    def action_show_ip_table(self) -> None:
        self._select_command("ip-panel")
        self._write_output(print_ip_table)

    def action_show_time_sync(self) -> None:
        self._select_command("time-panel")

    def action_show_sync(self) -> None:
        self._select_command("sync-panel")

    def _select_command(self, panel_id) -> None:
        self.query_one("#log", Log).clear()
        self.query_one("#command-content", ContentSwitcher).current = panel_id
        selected_button = {
            "ip-panel": "#select-ip",
            "time-panel": "#select-time",
            "sync-panel": "#select-sync",
        }[panel_id]
        for button in self.query("#command-rail Button"):
            button.remove_class("-selected")
        self.query_one(selected_button, Button).add_class("-selected")

    def action_exit(self) -> None:
        self.exit()

    def _write_output(self, function, *args, **kwargs):
        output = io.StringIO()
        try:
            with redirect_stdout(output):
                function(*args, **kwargs)
        except Exception as error:
            output.write(f"Error: {error}\n")
        self.query_one("#log", Log).write(output.getvalue())

    def _run_sync(self):
        package_list = self.query_one("#package-list", Select).value
        extra_packages = self.query_one("#extra-packages", Input).value.split()
        self._write_output(
            sync,
            self.query_one("#src-root", Input).value,
            self.query_one("#dst-root", Input).value,
            remote_host=self.query_one("#remote-host", Input).value,
            packages=extra_packages or None,
            build=self.query_one("#build", Checkbox).value,
            external_pkgs=self.query_one("#external-pkgs", Checkbox).value,
            package_list=package_list if package_list != Select.BLANK else None,
        )


def run_tui():
    RoverApp().run()
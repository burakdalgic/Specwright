"""Specwright CLI: project scaffolding, code generation, validation, and docs."""

from __future__ import annotations

import importlib.resources
import importlib.util
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import click
import jinja2
from rich.console import Console
from rich.table import Table

from . import __version__
from .decorators import SpecMetadata
from .state_machine import StateMachine, TransitionMeta
from .testing import TestRequirements

console = Console()
err_console = Console(stderr=True)


# ---------------------------------------------------------------------------
# Template helpers
# ---------------------------------------------------------------------------


def _get_template_env() -> jinja2.Environment:
    """Create a Jinja2 environment reading from specwright/templates/."""
    templates_ref = importlib.resources.files("specwright.templates")
    return jinja2.Environment(
        loader=jinja2.FileSystemLoader(str(templates_ref)),
        keep_trailing_newline=True,
    )


def _render_template(template_name: str, **context: Any) -> str:
    """Render a Jinja2 template by name and return the result."""
    env = _get_template_env()
    template = env.get_template(template_name)
    return template.render(**context)


def _write_file(path: Path, content: str) -> None:
    """Write content to a file, creating parent directories as needed."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


def _to_class_name(name: str) -> str:
    """Convert a snake_case name to PascalCase."""
    return "".join(part.capitalize() for part in name.split("_"))


# ---------------------------------------------------------------------------
# Import scanning for validate / docs
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ScannedFunction:
    """A @spec or @requires_tests decorated function found during scanning."""

    name: str
    qualname: str
    module: str
    spec_meta: SpecMetadata | None = None
    test_reqs: TestRequirements | None = None


@dataclass(frozen=True)
class ScannedStateMachine:
    """A StateMachine subclass found during scanning."""

    class_name: str
    module: str
    states: list[str] = field(default_factory=list)
    initial_state: str = ""
    transitions: list[tuple[str, str, str]] = field(default_factory=list)


def _scan_project(
    path: Path,
) -> tuple[list[ScannedFunction], list[ScannedStateMachine], list[str]]:
    """Import .py files under *path* and collect decorated objects.

    Returns ``(functions, state_machines, errors)``.
    """
    functions: list[ScannedFunction] = []
    machines: list[ScannedStateMachine] = []
    errors: list[str] = []

    py_files = sorted(path.rglob("*.py"))
    # Exclude test files from scanning
    py_files = [
        f
        for f in py_files
        if not f.name.startswith("test_") and not f.name.endswith("_test.py")
    ]

    original_path = list(sys.path)
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

    for py_file in py_files:
        mod_name = (
            str(py_file.relative_to(path))
            .replace("/", ".")
            .replace("\\", ".")
            .removesuffix(".py")
        )
        try:
            spec = importlib.util.spec_from_file_location(mod_name, py_file)
            if spec is None or spec.loader is None:
                continue
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
        except Exception as exc:
            errors.append(f"{py_file}: {exc}")
            continue

        for attr_name in dir(module):
            obj = getattr(module, attr_name, None)
            if obj is None:
                continue

            # Check for @spec / @requires_tests
            spec_meta = getattr(obj, "__spec__", None)
            test_reqs = getattr(obj, "__test_requirements__", None)
            if isinstance(spec_meta, SpecMetadata) or isinstance(
                test_reqs, TestRequirements
            ):
                functions.append(
                    ScannedFunction(
                        name=attr_name,
                        qualname=getattr(obj, "__qualname__", attr_name),
                        module=mod_name,
                        spec_meta=(
                            spec_meta if isinstance(spec_meta, SpecMetadata) else None
                        ),
                        test_reqs=(
                            test_reqs
                            if isinstance(test_reqs, TestRequirements)
                            else None
                        ),
                    )
                )

            # Check for StateMachine subclasses
            if (
                isinstance(obj, type)
                and issubclass(obj, StateMachine)
                and obj is not StateMachine
            ):
                transitions: list[tuple[str, str, str]] = []
                for method_name in dir(obj):
                    method = getattr(obj, method_name, None)
                    tmeta = getattr(method, "__transition__", None)
                    if isinstance(tmeta, TransitionMeta):
                        from_str = ", ".join(sorted(tmeta.from_states))
                        transitions.append((from_str, method_name, tmeta.to_state))
                machines.append(
                    ScannedStateMachine(
                        class_name=attr_name,
                        module=mod_name,
                        states=list(getattr(obj, "states", [])),
                        initial_state=getattr(obj, "initial_state", ""),
                        transitions=transitions,
                    )
                )

    sys.path[:] = original_path
    return functions, machines, errors


# ---------------------------------------------------------------------------
# CLI group
# ---------------------------------------------------------------------------


@click.group()
@click.version_option(version=__version__, prog_name="specwright")
def main() -> None:
    """Specwright: specification-first development tools."""


# ---------------------------------------------------------------------------
# specwright init
# ---------------------------------------------------------------------------


@main.command()
@click.argument("project_name", default="my_specwright_project")
def init(project_name: str) -> None:
    """Scaffold a new specwright project."""
    root = Path(project_name)
    if root.exists():
        err_console.print(f"[red]Error:[/red] '{project_name}' already exists.")
        raise SystemExit(1)

    # Create directories
    (root / project_name / "__init__.py").parent.mkdir(parents=True)
    (root / "tests").mkdir()
    (root / "examples").mkdir()

    # Render templates
    _write_file(
        root / "pyproject.toml",
        _render_template("init_pyproject.toml.j2", project_name=project_name),
    )
    _write_file(
        root / project_name / "__init__.py",
        _render_template("init_module.py.j2", project_name=project_name),
    )
    _write_file(root / "tests" / "__init__.py", "")
    _write_file(root / "README.md", f"# {project_name}\n")
    _write_file(
        root / ".specwright.toml",
        (
            "[specwright]\n"
            'test_enforcement = "strict"\n'
            'test_pattern = "test_*.py"\n'
        ),
    )

    console.print(f"[green]Created project '{project_name}':[/green]")
    console.print(f"  {project_name}/")
    console.print("    pyproject.toml")
    console.print("    .specwright.toml")
    console.print("    README.md")
    console.print(f"    {project_name}/")
    console.print("      __init__.py")
    console.print("    tests/")
    console.print("      __init__.py")
    console.print("    examples/")
    console.print()
    console.print("[bold]Next steps:[/bold]")
    console.print(f"  cd {project_name}")
    console.print("  specwright new function my_function")
    console.print("  specwright new statemachine my_workflow")


# ---------------------------------------------------------------------------
# specwright new
# ---------------------------------------------------------------------------


@main.group("new")
def new_group() -> None:
    """Generate new specwright components."""


@new_group.command("function")
@click.argument("name")
@click.option(
    "--params",
    default=None,
    help="Parameter list, e.g. 'x: int, y: str'. Prompted if omitted.",
)
@click.option(
    "--returns",
    "return_type",
    default=None,
    help="Return type, e.g. 'int'. Prompted if omitted.",
)
@click.option("--tests/--no-tests", default=True, help="Generate test file.")
@click.option("--output-dir", default=".", type=click.Path(), help="Output directory.")
def new_function(
    name: str,
    params: str | None,
    return_type: str | None,
    tests: bool,
    output_dir: str,
) -> None:
    """Generate a @spec-decorated function with test file."""
    if not name.isidentifier():
        err_console.print(
            f"[red]Error:[/red] '{name}' is not a valid Python identifier."
        )
        raise SystemExit(1)

    out = Path(output_dir)
    target = out / f"{name}.py"
    if target.exists():
        err_console.print(f"[red]Error:[/red] '{target}' already exists.")
        raise SystemExit(1)

    # Prompt if not provided
    if params is None:
        params = click.prompt("Parameters (e.g. 'x: int, y: str')", default="x: int")
    if return_type is None:
        return_type = click.prompt("Return type", default="int")

    # Build template context
    edge_cases: list[str] = []
    error_cases: list[str] = []

    content = _render_template(
        "function.py.j2",
        name=name,
        params=params,
        return_type=return_type,
        description=f"Module containing the {name} function.",
        docstring=f"TODO: Describe what {name} does.",
        edge_cases=edge_cases,
        error_cases=error_cases,
    )
    _write_file(target, content)
    console.print(f"[green]Created[/green] {target}")

    if tests:
        # Parse example args from params for test stub
        example_args = ", ".join(
            _default_value(p.split(":")[-1].strip()) if ":" in p else "None"
            for p in params.split(",")
        )
        test_target = out / f"test_{name}.py"
        # If a tests/ dir exists at output_dir level, put there instead
        tests_dir = out / "tests"
        if tests_dir.is_dir():
            test_target = tests_dir / f"test_{name}.py"

        test_content = _render_template(
            "function_test.py.j2",
            name=name,
            class_name=_to_class_name(name),
            module_path=name,
            example_args=example_args,
            edge_cases=edge_cases,
            error_cases=error_cases,
        )
        _write_file(test_target, test_content)
        console.print(f"[green]Created[/green] {test_target}")


def _default_value(type_str: str) -> str:
    """Return a sensible default literal for a type string."""
    type_str = type_str.strip()
    defaults: dict[str, str] = {
        "int": "0",
        "float": "0.0",
        "str": '""',
        "bool": "True",
        "list": "[]",
        "dict": "{}",
    }
    return defaults.get(type_str, "None")


# ---------------------------------------------------------------------------
# specwright new statemachine
# ---------------------------------------------------------------------------


@new_group.command("statemachine")
@click.argument("name")
@click.option(
    "--states",
    default=None,
    help="Comma-separated states, e.g. 'idle,running,done'. Prompted if omitted.",
)
@click.option(
    "--initial",
    default=None,
    help="Initial state (defaults to first state).",
)
@click.option("--tests/--no-tests", default=True, help="Generate test file.")
@click.option("--output-dir", default=".", type=click.Path(), help="Output directory.")
def new_statemachine(
    name: str,
    states: str | None,
    initial: str | None,
    tests: bool,
    output_dir: str,
) -> None:
    """Generate a StateMachine subclass with test file."""
    if not name.isidentifier():
        err_console.print(
            f"[red]Error:[/red] '{name}' is not a valid Python identifier."
        )
        raise SystemExit(1)

    out = Path(output_dir)
    target = out / f"{name}.py"
    if target.exists():
        err_console.print(f"[red]Error:[/red] '{target}' already exists.")
        raise SystemExit(1)

    # Prompt if not provided
    if states is None:
        states = click.prompt("States (comma-separated)", default="idle,running,done")
    state_list = [s.strip() for s in states.split(",") if s.strip()]

    if not state_list:
        err_console.print("[red]Error:[/red] At least one state is required.")
        raise SystemExit(1)

    if initial is None:
        initial = state_list[0]

    if initial not in state_list:
        err_console.print(
            f"[red]Error:[/red] Initial state '{initial}' not in states: {state_list}"
        )
        raise SystemExit(1)

    class_name = _to_class_name(name)

    # Auto-generate sequential transitions
    transitions = []
    for i in range(len(state_list) - 1):
        transitions.append(
            {
                "from_state": state_list[i],
                "to_state": state_list[i + 1],
                "method": f"go_{state_list[i + 1]}",
            }
        )

    content = _render_template(
        "statemachine.py.j2",
        class_name=class_name,
        states=state_list,
        initial_state=initial,
        transitions=transitions,
        description=f"State machine: {class_name}.",
        docstring=f"TODO: Describe the {class_name} state machine.",
    )
    _write_file(target, content)
    console.print(f"[green]Created[/green] {target}")

    if tests:
        test_target = out / f"test_{name}.py"
        tests_dir = out / "tests"
        if tests_dir.is_dir():
            test_target = tests_dir / f"test_{name}.py"

        test_content = _render_template(
            "statemachine_test.py.j2",
            class_name=class_name,
            module_path=name,
            initial_state=initial,
            transitions=transitions,
        )
        _write_file(test_target, test_content)
        console.print(f"[green]Created[/green] {test_target}")


# ---------------------------------------------------------------------------
# specwright validate
# ---------------------------------------------------------------------------


@main.command()
@click.option("--path", default=".", type=click.Path(exists=True), help="Project root.")
def validate(path: str) -> None:
    """Validate specs, test coverage, and state machine definitions."""
    project = Path(path)
    functions, machines, scan_errors = _scan_project(project)

    issues: list[str] = []
    passed = 0

    # Report import errors
    for err in scan_errors:
        issues.append(f"Import error: {err}")

    # Check spec'd functions have corresponding tests
    test_files = list(project.rglob("test_*.py")) + list(project.rglob("*_test.py"))
    test_names: set[str] = set()
    for tf in test_files:
        content = tf.read_text()
        test_names.update(re.findall(r"def (test_\w+)", content))

    for fn in functions:
        expected_name = f"test_{fn.name}"
        matching = [t for t in test_names if t.startswith(expected_name)]
        if matching:
            passed += 1
        else:
            issues.append(f"No tests found for '{fn.name}' (expected test_{fn.name}_*)")

        # Check @requires_tests coverage
        if fn.test_reqs is not None:
            for expected in fn.test_reqs.expected_test_names:
                if expected in test_names:
                    passed += 1
                else:
                    issues.append(f"Missing required test: {expected}")

    # Validate state machines — check reachability
    for sm in machines:
        reachable = {sm.initial_state}
        changed = True
        while changed:
            changed = False
            for from_states, _, to_state in sm.transitions:
                for fs in from_states.split(", "):
                    if fs in reachable and to_state not in reachable:
                        reachable.add(to_state)
                        changed = True
        unreachable = set(sm.states) - reachable
        if unreachable:
            issues.append(
                f"State machine '{sm.class_name}': unreachable states: "
                f"{sorted(unreachable)}"
            )
        else:
            passed += 1

    # Report
    if not functions and not machines:
        console.print("[yellow]No spec'd functions or state machines found.[/yellow]")
        return

    table = Table(title="Validation Results")
    table.add_column("Check", style="cyan")
    table.add_column("Status")

    for fn in functions:
        expected_name = f"test_{fn.name}"
        matching = [t for t in test_names if t.startswith(expected_name)]
        status = "[green]pass[/green]" if matching else "[red]FAIL[/red]"
        table.add_row(f"Tests for {fn.name}", status)

    for sm in machines:
        reachable = {sm.initial_state}
        changed = True
        while changed:
            changed = False
            for from_states, _, to_state in sm.transitions:
                for fs in from_states.split(", "):
                    if fs in reachable and to_state not in reachable:
                        reachable.add(to_state)
                        changed = True
        unreachable = set(sm.states) - reachable
        status = "[green]pass[/green]" if not unreachable else "[red]FAIL[/red]"
        table.add_row(f"SM {sm.class_name} reachability", status)

    console.print(table)
    console.print()

    if issues:
        console.print(f"[red]{len(issues)} issue(s) found:[/red]")
        for issue in issues:
            console.print(f"  [red]x[/red] {issue}")
        raise SystemExit(1)
    else:
        console.print(f"[green]All {passed} check(s) passed.[/green]")


# ---------------------------------------------------------------------------
# specwright docs
# ---------------------------------------------------------------------------


@main.command()
@click.option("--path", default=".", type=click.Path(exists=True), help="Project root.")
@click.option("--output", default=None, type=click.Path(), help="Output file.")
@click.option(
    "--diagram/--no-diagram",
    default=False,
    help="Generate state diagrams (requires graphviz).",
)
def docs(path: str, output: str | None, diagram: bool) -> None:
    """Generate API documentation from @spec metadata."""
    project = Path(path)
    functions, machines, scan_errors = _scan_project(project)

    lines: list[str] = [
        "# API Documentation",
        "",
        f"Generated by specwright v{__version__}",
        "",
    ]

    # Group functions by module
    by_module: dict[str, list[ScannedFunction]] = {}
    for fn in functions:
        by_module.setdefault(fn.module, []).append(fn)

    for mod_name, fns in sorted(by_module.items()):
        lines.append(f"## {mod_name}")
        lines.append("")

        for fn in fns:
            lines.append(f"### {fn.name}")
            lines.append("")

            if fn.spec_meta:
                lines.append(fn.spec_meta.docstring)
                lines.append("")

                if fn.spec_meta.parameters:
                    lines.append("| Parameter | Type |")
                    lines.append("|-----------|------|")
                    for pname, ptype in fn.spec_meta.parameters.items():
                        lines.append(f"| {pname} | `{ptype}` |")
                    lines.append("")

                lines.append(f"**Returns:** `{fn.spec_meta.return_type}`")
                lines.append("")

            if fn.test_reqs:
                lines.append("**Required tests:**")
                for tname in fn.test_reqs.expected_test_names:
                    lines.append(f"- `{tname}`")
                lines.append("")

            lines.append("---")
            lines.append("")

    # State machines
    for sm in machines:
        lines.append(f"## {sm.class_name} (State Machine)")
        lines.append("")
        lines.append(f"**States:** {', '.join(sm.states)}")
        lines.append(f"**Initial state:** {sm.initial_state}")
        lines.append("")

        if sm.transitions:
            lines.append("| From | Method | To |")
            lines.append("|------|--------|----|")
            for from_states, method, to_state in sm.transitions:
                lines.append(f"| {from_states} | {method} | {to_state} |")
            lines.append("")

        # Optional graphviz diagram
        if diagram:
            dot_lines = _generate_dot(sm)
            if dot_lines:
                lines.append("**State diagram:**")
                lines.append("")
                lines.append("```dot")
                lines.extend(dot_lines)
                lines.append("```")
                lines.append("")

        lines.append("---")
        lines.append("")

    result = "\n".join(lines)

    if output:
        Path(output).write_text(result)
        console.print(f"[green]Documentation written to {output}[/green]")
    else:
        click.echo(result)


def _generate_dot(sm: ScannedStateMachine) -> list[str]:
    """Generate DOT graph lines for a state machine."""
    lines = [f"digraph {sm.class_name} {{", "  rankdir=LR;"]
    lines.append("  node [shape=circle];")
    lines.append(f'  "{sm.initial_state}" [shape=doublecircle];')
    for from_states, method, to_state in sm.transitions:
        for fs in from_states.split(", "):
            lines.append(f'  "{fs}" -> "{to_state}" [label="{method}"];')
    lines.append("}")
    return lines

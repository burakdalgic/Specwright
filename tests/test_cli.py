"""Tests for the specwright CLI."""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from click.testing import CliRunner

from specwright.cli import main


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


# ---------------------------------------------------------------------------
# specwright --version / --help
# ---------------------------------------------------------------------------


class TestTopLevel:
    def test_version_flag(self, runner: CliRunner) -> None:
        result = runner.invoke(main, ["--version"])
        assert result.exit_code == 0
        assert "specwright" in result.output
        assert "0.1.0" in result.output

    def test_help(self, runner: CliRunner) -> None:
        result = runner.invoke(main, ["--help"])
        assert result.exit_code == 0
        assert "init" in result.output
        assert "new" in result.output
        assert "validate" in result.output
        assert "docs" in result.output

    def test_new_help(self, runner: CliRunner) -> None:
        result = runner.invoke(main, ["new", "--help"])
        assert result.exit_code == 0
        assert "function" in result.output
        assert "statemachine" in result.output


# ---------------------------------------------------------------------------
# specwright init
# ---------------------------------------------------------------------------


class TestInit:
    def test_creates_project_structure(self, runner: CliRunner) -> None:
        with runner.isolated_filesystem():
            result = runner.invoke(main, ["init", "myproject"])
            assert result.exit_code == 0
            assert Path("myproject/pyproject.toml").exists()
            assert Path("myproject/myproject/__init__.py").exists()
            assert Path("myproject/tests/__init__.py").exists()
            assert Path("myproject/README.md").exists()
            assert Path("myproject/.specwright.toml").exists()
            assert Path("myproject/examples").is_dir()

    def test_default_project_name(self, runner: CliRunner) -> None:
        with runner.isolated_filesystem():
            result = runner.invoke(main, ["init"])
            assert result.exit_code == 0
            assert Path("my_specwright_project").is_dir()

    def test_existing_directory_aborts(self, runner: CliRunner) -> None:
        with runner.isolated_filesystem():
            os.makedirs("myproject")
            result = runner.invoke(main, ["init", "myproject"])
            assert result.exit_code != 0

    def test_pyproject_contains_specwright_dep(self, runner: CliRunner) -> None:
        with runner.isolated_filesystem():
            runner.invoke(main, ["init", "myproject"])
            content = Path("myproject/pyproject.toml").read_text()
            assert "specwright" in content

    def test_init_module_has_spec_decorator(self, runner: CliRunner) -> None:
        with runner.isolated_filesystem():
            runner.invoke(main, ["init", "myproject"])
            content = Path("myproject/myproject/__init__.py").read_text()
            assert "@spec" in content
            assert "from specwright" in content

    def test_specwright_config_created(self, runner: CliRunner) -> None:
        with runner.isolated_filesystem():
            runner.invoke(main, ["init", "myproject"])
            content = Path("myproject/.specwright.toml").read_text()
            assert "test_enforcement" in content

    def test_output_shows_next_steps(self, runner: CliRunner) -> None:
        with runner.isolated_filesystem():
            result = runner.invoke(main, ["init", "myproject"])
            assert "Next steps" in result.output
            assert "cd myproject" in result.output


# ---------------------------------------------------------------------------
# specwright new function
# ---------------------------------------------------------------------------


class TestNewFunction:
    def test_generates_function_file(self, runner: CliRunner) -> None:
        with runner.isolated_filesystem():
            result = runner.invoke(
                main,
                [
                    "new",
                    "function",
                    "calculate",
                    "--params",
                    "x: int",
                    "--returns",
                    "int",
                ],
            )
            assert result.exit_code == 0
            assert Path("calculate.py").exists()
            content = Path("calculate.py").read_text()
            assert "@spec" in content
            assert "def calculate" in content

    def test_generates_test_file(self, runner: CliRunner) -> None:
        with runner.isolated_filesystem():
            result = runner.invoke(
                main,
                [
                    "new",
                    "function",
                    "calculate",
                    "--params",
                    "x: int",
                    "--returns",
                    "int",
                ],
            )
            assert result.exit_code == 0
            assert Path("test_calculate.py").exists()
            content = Path("test_calculate.py").read_text()
            assert "test_calculate_happy_path" in content

    def test_custom_params_and_return(self, runner: CliRunner) -> None:
        with runner.isolated_filesystem():
            result = runner.invoke(
                main,
                [
                    "new",
                    "function",
                    "greet",
                    "--params",
                    "name: str, excited: bool",
                    "--returns",
                    "str",
                ],
            )
            assert result.exit_code == 0
            content = Path("greet.py").read_text()
            assert "name: str" in content
            assert "-> str" in content

    def test_no_tests_flag(self, runner: CliRunner) -> None:
        with runner.isolated_filesystem():
            result = runner.invoke(
                main,
                [
                    "new",
                    "function",
                    "calc",
                    "--params",
                    "x: int",
                    "--returns",
                    "int",
                    "--no-tests",
                ],
            )
            assert result.exit_code == 0
            assert Path("calc.py").exists()
            assert not Path("test_calc.py").exists()

    def test_invalid_name_rejected(self, runner: CliRunner) -> None:
        with runner.isolated_filesystem():
            result = runner.invoke(main, ["new", "function", "123bad"])
            assert result.exit_code != 0

    def test_existing_file_aborts(self, runner: CliRunner) -> None:
        with runner.isolated_filesystem():
            Path("calculate.py").write_text("# existing")
            result = runner.invoke(
                main,
                [
                    "new",
                    "function",
                    "calculate",
                    "--params",
                    "x: int",
                    "--returns",
                    "int",
                ],
            )
            assert result.exit_code != 0

    def test_prompts_when_no_flags(self, runner: CliRunner) -> None:
        with runner.isolated_filesystem():
            result = runner.invoke(
                main,
                ["new", "function", "myfunc"],
                input="a: int, b: int\nint\n",
            )
            assert result.exit_code == 0
            content = Path("myfunc.py").read_text()
            assert "a: int, b: int" in content
            assert "-> int" in content

    def test_test_in_tests_dir_if_exists(self, runner: CliRunner) -> None:
        with runner.isolated_filesystem():
            os.makedirs("tests")
            result = runner.invoke(
                main,
                ["new", "function", "calc", "--params", "x: int", "--returns", "int"],
            )
            assert result.exit_code == 0
            assert Path("tests/test_calc.py").exists()
            assert not Path("test_calc.py").exists()


# ---------------------------------------------------------------------------
# specwright new statemachine
# ---------------------------------------------------------------------------


class TestNewStateMachine:
    def test_generates_statemachine_file(self, runner: CliRunner) -> None:
        with runner.isolated_filesystem():
            result = runner.invoke(
                main,
                [
                    "new",
                    "statemachine",
                    "order_processor",
                    "--states",
                    "pending,paid,shipped",
                ],
            )
            assert result.exit_code == 0
            assert Path("order_processor.py").exists()
            content = Path("order_processor.py").read_text()
            assert "StateMachine" in content
            assert "class OrderProcessor" in content

    def test_custom_states(self, runner: CliRunner) -> None:
        with runner.isolated_filesystem():
            result = runner.invoke(
                main,
                ["new", "statemachine", "traffic", "--states", "red,yellow,green"],
            )
            assert result.exit_code == 0
            content = Path("traffic.py").read_text()
            assert '"red"' in content
            assert '"yellow"' in content
            assert '"green"' in content

    def test_custom_initial_state(self, runner: CliRunner) -> None:
        with runner.isolated_filesystem():
            result = runner.invoke(
                main,
                [
                    "new",
                    "statemachine",
                    "machine",
                    "--states",
                    "off,on",
                    "--initial",
                    "off",
                ],
            )
            assert result.exit_code == 0
            content = Path("machine.py").read_text()
            assert 'initial_state = "off"' in content

    def test_generates_test_file(self, runner: CliRunner) -> None:
        with runner.isolated_filesystem():
            result = runner.invoke(
                main,
                ["new", "statemachine", "workflow", "--states", "a,b,c"],
            )
            assert result.exit_code == 0
            assert Path("test_workflow.py").exists()
            content = Path("test_workflow.py").read_text()
            assert "TestWorkflow" in content

    def test_no_tests_flag(self, runner: CliRunner) -> None:
        with runner.isolated_filesystem():
            result = runner.invoke(
                main,
                ["new", "statemachine", "sm", "--states", "a,b", "--no-tests"],
            )
            assert result.exit_code == 0
            assert not Path("test_sm.py").exists()

    def test_invalid_initial_state(self, runner: CliRunner) -> None:
        with runner.isolated_filesystem():
            result = runner.invoke(
                main,
                ["new", "statemachine", "machine", "--states", "a,b", "--initial", "z"],
            )
            assert result.exit_code != 0

    def test_invalid_name_rejected(self, runner: CliRunner) -> None:
        with runner.isolated_filesystem():
            result = runner.invoke(main, ["new", "statemachine", "123bad"])
            assert result.exit_code != 0

    def test_sequential_transitions_generated(self, runner: CliRunner) -> None:
        with runner.isolated_filesystem():
            result = runner.invoke(
                main,
                ["new", "statemachine", "pipeline", "--states", "start,middle,end"],
            )
            assert result.exit_code == 0
            content = Path("pipeline.py").read_text()
            assert "go_middle" in content
            assert "go_end" in content

    def test_prompts_when_no_states_flag(self, runner: CliRunner) -> None:
        with runner.isolated_filesystem():
            result = runner.invoke(
                main,
                ["new", "statemachine", "mymachine"],
                input="x,y,z\n",
            )
            assert result.exit_code == 0
            content = Path("mymachine.py").read_text()
            assert '"x"' in content


# ---------------------------------------------------------------------------
# specwright validate
# ---------------------------------------------------------------------------


class TestValidate:
    def test_validate_clean_project(self, runner: CliRunner) -> None:
        with runner.isolated_filesystem():
            os.makedirs("mymod")
            Path("mymod/__init__.py").write_text("")
            Path("mymod/core.py").write_text(
                "from specwright import spec\n\n"
                "@spec\n"
                "def add(x: int, y: int) -> int:\n"
                '    """Add two numbers."""\n'
                "    return x + y\n"
            )
            os.makedirs("tests")
            Path("tests/__init__.py").write_text("")
            Path("tests/test_core.py").write_text(
                "from mymod.core import add\n\n"
                "def test_add_happy_path() -> None:\n"
                "    assert add(1, 2) == 3\n"
            )
            result = runner.invoke(main, ["validate", "--path", "."])
            assert result.exit_code == 0

    def test_validate_missing_tests(self, runner: CliRunner) -> None:
        with runner.isolated_filesystem():
            os.makedirs("mymod")
            Path("mymod/__init__.py").write_text("")
            Path("mymod/core.py").write_text(
                "from specwright import spec\n\n"
                "@spec\n"
                "def add(x: int, y: int) -> int:\n"
                '    """Add two numbers."""\n'
                "    return x + y\n"
            )
            result = runner.invoke(main, ["validate", "--path", "."])
            assert result.exit_code != 0

    def test_validate_no_specs_found(self, runner: CliRunner) -> None:
        with runner.isolated_filesystem():
            os.makedirs("mymod")
            Path("mymod/__init__.py").write_text("")
            Path("mymod/core.py").write_text("x = 1\n")
            result = runner.invoke(main, ["validate", "--path", "."])
            assert result.exit_code == 0
            assert "No spec'd functions" in result.output


# ---------------------------------------------------------------------------
# specwright docs
# ---------------------------------------------------------------------------


class TestDocs:
    def test_docs_stdout(self, runner: CliRunner) -> None:
        with runner.isolated_filesystem():
            os.makedirs("mymod")
            Path("mymod/__init__.py").write_text("")
            Path("mymod/core.py").write_text(
                "from specwright import spec\n\n"
                "@spec\n"
                "def add(x: int, y: int) -> int:\n"
                '    """Add two numbers."""\n'
                "    return x + y\n"
            )
            result = runner.invoke(main, ["docs", "--path", "."])
            assert result.exit_code == 0
            assert "add" in result.output
            assert "int" in result.output

    def test_docs_output_file(self, runner: CliRunner) -> None:
        with runner.isolated_filesystem():
            os.makedirs("mymod")
            Path("mymod/__init__.py").write_text("")
            Path("mymod/core.py").write_text(
                "from specwright import spec\n\n"
                "@spec\n"
                "def add(x: int, y: int) -> int:\n"
                '    """Add two numbers."""\n'
                "    return x + y\n"
            )
            result = runner.invoke(main, ["docs", "--path", ".", "--output", "API.md"])
            assert result.exit_code == 0
            assert Path("API.md").exists()
            assert "add" in Path("API.md").read_text()

    def test_docs_includes_param_table(self, runner: CliRunner) -> None:
        with runner.isolated_filesystem():
            os.makedirs("mymod")
            Path("mymod/__init__.py").write_text("")
            Path("mymod/core.py").write_text(
                "from specwright import spec\n\n"
                "@spec\n"
                "def greet(name: str) -> str:\n"
                '    """Greet someone."""\n'
                '    return f"Hello, {name}!"\n'
            )
            result = runner.invoke(main, ["docs", "--path", "."])
            assert result.exit_code == 0
            assert "Parameter" in result.output
            assert "name" in result.output

    def test_docs_empty_project(self, runner: CliRunner) -> None:
        with runner.isolated_filesystem():
            os.makedirs("mymod")
            Path("mymod/__init__.py").write_text("")
            Path("mymod/core.py").write_text("x = 1\n")
            result = runner.invoke(main, ["docs", "--path", "."])
            assert result.exit_code == 0
            assert "API Documentation" in result.output

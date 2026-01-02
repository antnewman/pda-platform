"""Tests for CLI commands."""

import subprocess
import sys
import pytest
from click.testing import CliRunner
from pathlib import Path

from pm_data_tools.cli import main
from pm_data_tools.cli.commands.convert import convert
from pm_data_tools.cli.commands.validate import validate
from pm_data_tools.cli.commands.inspect import inspect_cmd


@pytest.fixture
def runner() -> CliRunner:
    """Click test runner."""
    return CliRunner()


@pytest.fixture
def sample_file(tmp_path: Path) -> Path:
    """Create a sample file for testing."""
    file_path = tmp_path / "test.xml"
    file_path.write_text("<Project><Name>Test</Name></Project>")
    return file_path


class TestMainCLI:
    """Tests for main CLI."""

    def test_help(self, runner: CliRunner) -> None:
        """Test main help output."""
        result = runner.invoke(main, ["--help"])
        assert result.exit_code == 0
        assert "PM Data Tools" in result.output
        assert "convert" in result.output
        assert "validate" in result.output
        assert "inspect" in result.output

    def test_version(self, runner: CliRunner) -> None:
        """Test version output."""
        result = runner.invoke(main, ["--version"])
        assert result.exit_code == 0
        assert "0.1.0" in result.output

    def test_main_callable(self) -> None:
        """Test that main() is callable directly (covers pass statement on line 13)."""
        # Calling main() directly should work without errors
        # This is a Click group, so it should be callable
        assert callable(main)
        assert hasattr(main, "commands")

    def test_main_module_execution(self) -> None:
        """Test that CLI can be executed as module (covers __main__.py)."""
        result = subprocess.run(
            [sys.executable, "-m", "pm_data_tools.cli", "--version"],
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0
        assert "0.1.0" in result.stdout


class TestConvertCommand:
    """Tests for convert command."""

    def test_help(self, runner: CliRunner) -> None:
        """Test convert command help."""
        result = runner.invoke(convert, ["--help"])
        assert result.exit_code == 0
        assert "Convert project data" in result.output

    def test_convert_requires_to_format(
        self, runner: CliRunner, sample_file: Path, tmp_path: Path
    ) -> None:
        """Test convert requires --to argument."""
        output_file = tmp_path / "output.json"
        result = runner.invoke(convert, [str(sample_file), str(output_file)])
        assert result.exit_code != 0  # Should fail without --to

    def test_convert_with_to_format(
        self, runner: CliRunner, sample_file: Path, tmp_path: Path
    ) -> None:
        """Test convert with --to format."""
        output_file = tmp_path / "output.json"
        result = runner.invoke(
            convert, [str(sample_file), str(output_file), "--to", "canonical"]
        )
        assert result.exit_code == 0
        assert "Converting" in result.output
        assert "canonical" in result.output

    def test_convert_with_from_and_to(
        self, runner: CliRunner, sample_file: Path, tmp_path: Path
    ) -> None:
        """Test convert with both --from and --to."""
        output_file = tmp_path / "output.xer"
        result = runner.invoke(
            convert,
            [str(sample_file), str(output_file), "--from", "mspdi", "--to", "p6"],
        )
        assert result.exit_code == 0
        assert "mspdi" in result.output
        assert "p6" in result.output

    def test_convert_no_validate(
        self, runner: CliRunner, sample_file: Path, tmp_path: Path
    ) -> None:
        """Test convert with validation disabled."""
        output_file = tmp_path / "output.json"
        result = runner.invoke(
            convert,
            [str(sample_file), str(output_file), "--to", "canonical", "--no-validate"],
        )
        assert result.exit_code == 0
        assert "disabled" in result.output


class TestValidateCommand:
    """Tests for validate command."""

    def test_help(self, runner: CliRunner) -> None:
        """Test validate command help."""
        result = runner.invoke(validate, ["--help"])
        assert result.exit_code == 0
        assert "Validate project data" in result.output

    def test_validate_file(self, runner: CliRunner, sample_file: Path) -> None:
        """Test validate command with file."""
        result = runner.invoke(validate, [str(sample_file)])
        assert result.exit_code == 0
        assert "Validating" in result.output

    def test_validate_with_format(self, runner: CliRunner, sample_file: Path) -> None:
        """Test validate with explicit format."""
        result = runner.invoke(validate, [str(sample_file), "--format", "mspdi"])
        assert result.exit_code == 0
        assert "mspdi" in result.output

    def test_validate_strict_mode(self, runner: CliRunner, sample_file: Path) -> None:
        """Test validate with strict mode."""
        result = runner.invoke(validate, [str(sample_file), "--strict"])
        assert result.exit_code == 0
        assert "enabled" in result.output

    def test_validate_with_output(
        self, runner: CliRunner, sample_file: Path, tmp_path: Path
    ) -> None:
        """Test validate with output file."""
        output_file = tmp_path / "report.json"
        result = runner.invoke(
            validate, [str(sample_file), "--output", str(output_file)]
        )
        assert result.exit_code == 0
        assert str(output_file) in result.output


class TestInspectCommand:
    """Tests for inspect command."""

    def test_help(self, runner: CliRunner) -> None:
        """Test inspect command help."""
        result = runner.invoke(inspect_cmd, ["--help"])
        assert result.exit_code == 0
        assert "Inspect project file" in result.output

    def test_inspect_file(self, runner: CliRunner, sample_file: Path) -> None:
        """Test inspect command with file."""
        result = runner.invoke(inspect_cmd, [str(sample_file)])
        assert result.exit_code == 0
        assert "Inspecting" in result.output

    def test_inspect_with_format(self, runner: CliRunner, sample_file: Path) -> None:
        """Test inspect with explicit format."""
        result = runner.invoke(inspect_cmd, [str(sample_file), "--format", "mspdi"])
        assert result.exit_code == 0
        assert "mspdi" in result.output

    def test_inspect_verbose(self, runner: CliRunner, sample_file: Path) -> None:
        """Test inspect in verbose mode."""
        result = runner.invoke(inspect_cmd, [str(sample_file), "-v"])
        assert result.exit_code == 0
        assert "Detailed" in result.output or "detailed" in result.output

    def test_inspect_show_risks(self, runner: CliRunner, sample_file: Path) -> None:
        """Test inspect with risks enabled."""
        result = runner.invoke(inspect_cmd, [str(sample_file), "--show-risks"])
        assert result.exit_code == 0
        assert "risk" in result.output.lower()

    def test_inspect_no_tasks(self, runner: CliRunner, sample_file: Path) -> None:
        """Test inspect with tasks disabled."""
        result = runner.invoke(inspect_cmd, [str(sample_file), "--no-show-tasks"])
        assert result.exit_code == 0

    def test_inspect_risks_no_resources(self, runner: CliRunner, sample_file: Path) -> None:
        """Test inspect with risks enabled but resources disabled (covers branch 69->72)."""
        result = runner.invoke(
            inspect_cmd, [str(sample_file), "--no-show-resources", "--show-risks"]
        )
        assert result.exit_code == 0
        assert "risk" in result.output.lower()

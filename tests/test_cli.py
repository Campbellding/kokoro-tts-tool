"""CLI tests for voice blending support."""

from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from kokoro_tts_tool.commands.infinite_commands import infinite
from kokoro_tts_tool.commands.synthesize_commands import synthesize


def test_synthesize_cli_with_voice_blend() -> None:
    """Test CLI synthesize command with voice blend syntax."""
    runner = CliRunner()

    with patch("kokoro_tts_tool.commands.synthesize_commands.synthesize_and_play") as mock_play:
        mock_play.return_value = 5
        result = runner.invoke(
            synthesize,
            ["Hello", "--voice", "af_heart:0.7,af_bella:0.3"],
        )

        assert result.exit_code == 0
        mock_play.assert_called_once()
        args, _ = mock_play.call_args
        assert args[0] == "Hello"
        assert args[1] == "af_heart:0.7,af_bella:0.3"


def test_synthesize_cli_with_invalid_blend() -> None:
    """Test CLI synthesize command with an invalid voice blend."""
    runner = CliRunner()

    result = runner.invoke(
        synthesize,
        ["Hello", "--voice", "unknown_voice:0.7,af_bella:0.3"],
    )

    assert result.exit_code == 1
    assert "Unknown voice: unknown_voice" in result.output


def test_infinite_cli_with_voice_blend(tmp_path: MagicMock) -> None:
    """Test CLI infinite command with voice blend syntax."""
    runner = CliRunner()
    test_file = tmp_path / "test.md"
    test_file.write_text("# Chapter 1\nHello from chapter 1.")

    with patch("kokoro_tts_tool.commands.infinite_commands._play_to_speaker") as mock_speaker:
        result = runner.invoke(
            infinite,
            ["--input", str(test_file), "--voice", "af_heart:0.7,af_bella:0.3"],
        )

        assert result.exit_code == 0
        mock_speaker.assert_called_once()
        _, voice_arg, _, _ = mock_speaker.call_args[0]
        assert voice_arg == "af_heart:0.7,af_bella:0.3"

"""Tests for kokoro_tts_tool.engine module, including voice blending."""

from unittest.mock import MagicMock

import numpy as np

from kokoro_tts_tool.engine import KokoroEngine


def test_resolve_voice_single() -> None:
    """Test resolving a single voice returns the voice string without engine lookup."""
    engine = KokoroEngine()
    result = engine._resolve_voice("af_heart")
    assert result == "af_heart"


def test_resolve_voice_single_with_weight() -> None:
    """Test resolving a single voice with weight 1.0 returns the voice string."""
    engine = KokoroEngine()
    result = engine._resolve_voice("af_heart:1.0")
    assert result == "af_heart"


def test_resolve_voice_blend() -> None:
    """Test resolving a voice blend computes the weighted style array."""
    engine = KokoroEngine()
    mock_kokoro = MagicMock()

    style_heart = np.ones((510, 1, 256), dtype=np.float32) * 1.0
    style_bella = np.ones((510, 1, 256), dtype=np.float32) * 2.0

    def mock_get_voice_style(name: str) -> np.ndarray:
        if name == "af_heart":
            return style_heart
        elif name == "af_bella":
            return style_bella
        raise ValueError(f"Unknown voice {name}")

    mock_kokoro.get_voice_style.side_effect = mock_get_voice_style
    engine._engine = mock_kokoro

    result = engine._resolve_voice("af_heart:0.7,af_bella:0.3")

    assert isinstance(result, np.ndarray)
    assert result.shape == (510, 1, 256)
    assert result.dtype == np.float32
    # 0.7 * 1.0 + 0.3 * 2.0 = 0.7 + 0.6 = 1.3
    np.testing.assert_allclose(result, 1.3, rtol=1e-5)


def test_resolve_voice_blend_caching() -> None:
    """Test that resolved blended styles are cached."""
    engine = KokoroEngine()
    mock_kokoro = MagicMock()

    style_heart = np.ones((510, 1, 256), dtype=np.float32)
    style_bella = np.ones((510, 1, 256), dtype=np.float32) * 2.0

    mock_kokoro.get_voice_style.side_effect = lambda name: (
        style_heart if name == "af_heart" else style_bella
    )
    engine._engine = mock_kokoro

    blend_spec = "af_heart:0.7,af_bella:0.3"
    result1 = engine._resolve_voice(blend_spec)
    assert mock_kokoro.get_voice_style.call_count == 2

    # Second call should use cache
    result2 = engine._resolve_voice(blend_spec)
    assert mock_kokoro.get_voice_style.call_count == 2
    assert result1 is result2


def test_generate_with_blend() -> None:
    """Test generate method passes blended voice array to underlying create."""
    engine = KokoroEngine()
    mock_kokoro = MagicMock()

    style_heart = np.ones((510, 1, 256), dtype=np.float32)
    style_bella = np.ones((510, 1, 256), dtype=np.float32) * 2.0
    mock_kokoro.get_voice_style.side_effect = lambda name: (
        style_heart if name == "af_heart" else style_bella
    )

    fake_samples = np.zeros(24000, dtype=np.float32)
    mock_kokoro.create.return_value = (fake_samples, 24000)

    engine._engine = mock_kokoro

    samples, sample_rate = engine.generate("Hello world", voice="af_heart:0.7,af_bella:0.3")

    assert sample_rate == 24000
    assert len(samples) == 24000
    mock_kokoro.create.assert_called_once()
    call_kwargs = mock_kokoro.create.call_args.kwargs
    assert call_kwargs["text"] == "Hello world"
    assert isinstance(call_kwargs["voice"], np.ndarray)
    assert call_kwargs["lang"] == "en-us"

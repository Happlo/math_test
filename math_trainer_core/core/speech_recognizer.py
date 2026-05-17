from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Protocol


_DEFAULT_MODEL_DIRNAME = "vosk-model-small-sv-rhasspy-0.15"


class SpeechRecognitionError(RuntimeError):
    pass


class SpeechRecognizer(Protocol):
    def transcribe(self, pcm_bytes: bytes, sample_rate: int) -> str:
        ...


class VoskSpeechRecognizer:
    def __init__(self, model_path: Path | None = None):
        self._model_path = model_path
        self._model = None

    def transcribe(self, pcm_bytes: bytes, sample_rate: int) -> str:
        if not pcm_bytes:
            return ""

        try:
            from vosk import KaldiRecognizer, Model
        except ImportError as exc:
            raise SpeechRecognitionError(
                "Vosk is not installed. Install it with: python3 -m pip install vosk"
            ) from exc

        if self._model is None:
            model_path = self._model_path or _find_default_model_path()
            if model_path is None:
                raise SpeechRecognitionError(
                    "Vosk Swedish model not found. Set VOSK_MODEL_PATH or place "
                    f"{_DEFAULT_MODEL_DIRNAME} under ./models."
                )
            self._model = Model(str(model_path))

        recognizer = KaldiRecognizer(self._model, sample_rate)
        recognizer.AcceptWaveform(pcm_bytes)
        result = json.loads(recognizer.FinalResult())
        return str(result.get("text", "")).strip()


def create_default_speech_recognizer() -> SpeechRecognizer:
    return VoskSpeechRecognizer()


def _find_default_model_path() -> Path | None:
    env_path = os.environ.get("VOSK_MODEL_PATH")
    candidates: list[Path] = []
    if env_path:
        candidates.append(Path(env_path))

    repo_root = Path(__file__).resolve().parents[2]
    candidates.extend(
        [
            Path.cwd() / "models" / _DEFAULT_MODEL_DIRNAME,
            repo_root / "models" / _DEFAULT_MODEL_DIRNAME,
        ]
    )

    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None

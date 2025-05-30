"""Translate with HF models."""

from typing import List

import torch
from transformers import pipeline


_KEY_TEXT = "translation_text"

SUPPORTED_LANGS = ("de", "en", "es", "fr", "zh")

SUPPORTED_PAIRS = {
    (src, target): f"Helsinki-NLP/opus-mt-{src}-{target}"
    for src in SUPPORTED_LANGS
    for target in SUPPORTED_LANGS
    if src != target
}


class Translator:
    """Translator with HF models."""

    def __init__(self, src_lang: str, target_lang: str):
        model_key = (src_lang, target_lang)
        if model_key not in SUPPORTED_PAIRS:
            raise ValueError(f"No translation model for {src_lang} → {target_lang}")

        model_name = SUPPORTED_PAIRS[model_key]
        try:
            self.translator = pipeline(
                "translation",
                model=model_name,
                device=0 if torch.cuda.is_available() else -1,
            )
        except OSError as e:
            raise RuntimeError(f"Model {model_name} could not be loaded: {str(e)}")

    def translate(self, texts: List[str]) -> List[str]:
        """Translate with HF models."""
        results = self.translator(list(texts))
        return [r[_KEY_TEXT] for r in results]

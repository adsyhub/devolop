"""Shared language metadata and backward-compatible manifest text helpers."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class LanguageProfile:
    code: str
    locale: str
    english_name: str
    chinese_name: str
    native_name: str
    input_placeholder: str
    uses_spaces: bool
    continuation_endings: tuple[str, ...]


LANGUAGES: dict[str, LanguageProfile] = {
    "ja": LanguageProfile("ja", "ja-JP", "Japanese", "日语", "日本語", "ここに入力してください…", False, ("、", ",", "，", "､")),
    "en": LanguageProfile("en", "en-US", "English", "英语", "English", "Type what you hear…", True, (",", ";", ":")),
    "fr": LanguageProfile("fr", "fr-FR", "French", "法语", "Français", "Écrivez ce que vous entendez…", True, (",", ";", ":")),
    "ko": LanguageProfile("ko", "ko-KR", "Korean", "韩语", "한국어", "들은 내용을 입력하세요…", True, (",", "，")),
    "es": LanguageProfile("es", "es-ES", "Spanish", "西班牙语", "Español", "Escribe lo que escuchas…", True, (",", ";", ":")),
    "de": LanguageProfile("de", "de-DE", "German", "德语", "Deutsch", "Gib ein, was du hörst…", True, (",", ";", ":")),
    "it": LanguageProfile("it", "it-IT", "Italian", "意大利语", "Italiano", "Scrivi ciò che senti…", True, (",", ";", ":")),
    "pt": LanguageProfile("pt", "pt-BR", "Portuguese", "葡萄牙语", "Português", "Digite o que você ouve…", True, (",", ";", ":")),
    "zh": LanguageProfile("zh", "zh-CN", "Chinese", "中文", "中文", "请输入你听到的内容…", False, ("、", ",", "，")),
}

SUPPORTED_LANGUAGE_CODES = tuple(LANGUAGES)


def normalize_language_code(value: Any, *, default: str = "ja") -> str:
    """Normalize a Whisper/BCP-47 language value to a supported base code."""
    text = str(value or "").strip().lower().replace("_", "-")
    if not text:
        text = default
    aliases = {"jp": "ja", "kr": "ko", "cn": "zh", "zh-cn": "zh", "zh-tw": "zh"}
    code = aliases.get(text, text.split("-", 1)[0])
    if code not in LANGUAGES:
        supported = ", ".join(SUPPORTED_LANGUAGE_CODES)
        raise ValueError(f"Unsupported source language {value!r}. Supported codes: {supported}.")
    return code


def language_profile(value: Any, *, default: str = "ja") -> LanguageProfile:
    return LANGUAGES[normalize_language_code(value, default=default)]


def manifest_language_code(manifest: dict[str, Any]) -> str:
    if manifest.get("sourceLanguage"):
        return normalize_language_code(manifest["sourceLanguage"])
    language = manifest.get("language")
    if isinstance(language, dict) and language.get("code"):
        return normalize_language_code(language["code"])
    locales = manifest.get("locales")
    if isinstance(locales, dict) and locales.get("source"):
        return normalize_language_code(locales["source"])
    metadata = manifest.get("buildMetadata")
    if isinstance(metadata, dict):
        config = metadata.get("transcriptionConfig")
        if isinstance(config, dict) and config.get("language") not in (None, "auto"):
            return normalize_language_code(config["language"])
    return "ja"


def source_text(sentence: dict[str, Any], language: Any = "ja") -> str:
    code = normalize_language_code(language)
    # jaText was the original public field. Prefer it for Japanese so edits made
    # by older review tools remain authoritative after migration.
    if code == "ja" and str(sentence.get("jaText") or "").strip():
        return str(sentence.get("jaText") or "").strip()
    return str(sentence.get("sourceText") or sentence.get("jaText") or "").strip()


def set_source_text(sentence: dict[str, Any], value: Any, language: Any) -> None:
    code = normalize_language_code(language)
    text = str(value or "").strip()
    sentence["sourceText"] = text
    if code == "ja":
        sentence["jaText"] = text
    elif "jaText" in sentence:
        sentence.pop("jaText", None)


def translation_text(sentence: dict[str, Any]) -> str:
    # zhTranslation is the v1 editing surface; prefer it when present so older
    # human-review tools can still correct an already-migrated manifest.
    return str(sentence.get("zhTranslation") or sentence.get("translationText") or "").strip()


def set_translation_text(sentence: dict[str, Any], value: Any) -> None:
    text = str(value or "").strip()
    sentence["translationText"] = text
    # Keep the v1 field for older players and correction tools.
    sentence["zhTranslation"] = text


def transcript_text(sentences: list[Any], language: Any) -> str:
    profile = language_profile(language)
    values = [source_text(item, profile.code) for item in sentences if isinstance(item, dict)]
    return (" " if profile.uses_spaces else "").join(value for value in values if value)


def upgrade_manifest_language(manifest: dict[str, Any], language: Any | None = None) -> str:
    """Add canonical multilingual fields in-place and return the language code."""
    code = normalize_language_code(language) if language is not None else manifest_language_code(manifest)
    profile = language_profile(code)
    manifest["sourceLanguage"] = code
    manifest["language"] = {
        "code": profile.code,
        "locale": profile.locale,
        "name": profile.english_name,
        "displayName": profile.chinese_name,
        "nativeName": profile.native_name,
    }
    locales = manifest.setdefault("locales", {})
    if not isinstance(locales, dict):
        locales = {}
        manifest["locales"] = locales
    locales["source"] = profile.locale
    locales.setdefault("translation", "zh-Hans-CN")
    locales.setdefault("interface", "zh-Hans-CN")

    sentences = manifest.get("sentences")
    if isinstance(sentences, list):
        for sentence in sentences:
            if not isinstance(sentence, dict):
                continue
            set_source_text(sentence, source_text(sentence, code), code)
            if "translationText" in sentence or "zhTranslation" in sentence:
                set_translation_text(sentence, translation_text(sentence))
        manifest["transcriptText"] = transcript_text(sentences, code)
    return code


def language_metadata(value: Any) -> dict[str, Any]:
    """Return serializable profile metadata for diagnostics and API users."""
    return asdict(language_profile(value))

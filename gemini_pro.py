"""Generate full comic narration/dialogue using Gemini Pro.

Uses ``models/gemini-2.5-pro`` when ``GEMINI_API_KEY`` is set, otherwise
returns a deterministic local story so the app works offline.
"""
import os

from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
PRO_MODEL = os.getenv("GEMINI_PRO_MODEL", "models/gemini-2.5-pro")

_model = None
if GEMINI_API_KEY:
    try:
        import google.generativeai as genai

        genai.configure(api_key=GEMINI_API_KEY)
        _model = genai.GenerativeModel(PRO_MODEL)
    except Exception as exc:  # pragma: no cover
        print(f"[gemini_pro] Gemini init failed, using fallback: {exc}")
        _model = None


def _fallback_story(outline: list) -> str:
    """Deterministic panel-by-panel story (offline/demo mode)."""
    parts = []
    for i, item in enumerate(outline, start=1):
        if isinstance(item, dict):
            title = item.get("title", f"Panel {i}")
            scene = item.get("scene_description", "")
        else:
            title = f"Panel {i}"
            scene = str(item)
        parts.append(
            f"**Panel {i}: {title}**\n"
            f"**CAPTION:** {scene}\n"
            f"**NARRATION:** Our hero pushes forward, heart pounding with "
            f"determination in '{title}'.\n"
            f'Hero: "I won\'t give up — this is my story to finish!"\n'
        )
    return "\n".join(parts)


def generate_story(outline: list) -> str:
    """Generate a detailed comic story with narration and character dialogue.

    Args:
        outline (list): A list of strings or dicts representing each panel.

    Returns:
        str: The generated comic story text or an error message.
    """
    if not outline:
        return "Error generating story: empty outline."

    if _model is None:
        print("[gemini_pro] No API key -> using local fallback story.")
        return _fallback_story(outline)

    # Format the panel outline as a numbered list for clarity
    def _fmt(i, item):
        if isinstance(item, dict):
            t = item.get("title", "")
            s = item.get("scene_description", "")
            return f"{i + 1}. {t} — {s}"
        return f"{i + 1}. {item}"

    formatted_outline = "\n".join(_fmt(i, item) for i, item in enumerate(outline))

    # Construct the prompt
    prompt = f"""You're a comic book writer.

Given the following panel breakdown, write a comic-style story with engaging narration and character dialogues for each panel.

Panel Outline:
{formatted_outline}

Guidelines:
- Use a fun and engaging tone, like an actual comic book.
- Include narration and clearly marked character lines.
- Keep each panel self-contained but part of a cohesive story.
- Start EVERY panel with a heading exactly like: **Panel N: Title**
- Inside each panel include lines starting with **CAPTION:** and **NARRATION:**.
"""

    try:
        response = _model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error generating story: {str(e)}"

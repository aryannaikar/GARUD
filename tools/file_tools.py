import os
import re
import difflib
import subprocess
from pathlib import Path

FILE_CACHE = []
CACHE_BUILT = False


def build_file_cache():
    global FILE_CACHE, CACHE_BUILT

    if CACHE_BUILT:
        return

    print("Building file cache...")

    home = Path.home()
    search_paths = []

    for folder in ["Desktop", "Documents", "Downloads"]:
        path = home / folder

        if path.exists():
            search_paths.append(path)

        onedrive = home / "OneDrive" / folder

        if onedrive.exists():
            search_paths.append(onedrive)

    for base in search_paths:
        for root, dirs, files in os.walk(base):

            dirs[:] = [
                d for d in dirs
                if d not in {
                    "node_modules",
                    ".git",
                    "__pycache__",
                    ".venv",
                    "venv",
                    ".idea"
                }
            ]

            for file in files:
                FILE_CACHE.append(
                    os.path.join(root, file)
                )

    CACHE_BUILT = True

    print(f"Cached {len(FILE_CACHE)} files.")


def create_folder(folder_name):
    try:
        Path(folder_name).mkdir(exist_ok=True)

        return f"Folder '{folder_name}' created successfully."

    except Exception as e:
        return f"Error creating folder: {e}"


def open_downloads():
    try:
        downloads = Path.home() / "Downloads"

        if not downloads.exists():
            downloads = Path.home() / "OneDrive" / "Downloads"

        subprocess.Popen(f'explorer "{downloads}"')

        return "Opening Downloads..."

    except Exception as e:
        return f"Error: {e}"


def open_desktop():
    try:
        desktop = Path.home() / "Desktop"

        if not desktop.exists():
            desktop = Path.home() / "OneDrive" / "Desktop"

        subprocess.Popen(f'explorer "{desktop}"')

        return "Opening Desktop..."

    except Exception as e:
        return f"Error: {e}"


def create_file_on_desktop(file_name, content=None):
    try:
        desktop = Path.home() / "Desktop"

        if not desktop.exists():
            desktop = Path.home() / "OneDrive" / "Desktop"

        if "." not in file_name:
            file_name += ".txt"

        file_path = desktop / file_name

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content if content else "Created by Garud AI Assistant")

        return f"File '{file_name}' created on Desktop."

    except Exception as e:
        return f"Error: {e}"


def write_content_to_file(file_name, content):
    """Find an existing file by name and overwrite it with content."""
    try:
        build_file_cache()

        # First look on Desktop
        desktop = Path.home() / "Desktop"
        if not desktop.exists():
            desktop = Path.home() / "OneDrive" / "Desktop"

        if "." not in file_name:
            file_name += ".txt"

        desktop_path = desktop / file_name
        if desktop_path.exists():
            with open(desktop_path, "w", encoding="utf-8") as f:
                f.write(content)
            return f"Content saved to '{file_name}'."

        # Search cache for the file
        for path in FILE_CACHE:
            if os.path.basename(path).lower() == file_name.lower():
                with open(path, "w", encoding="utf-8") as f:
                    f.write(content)
                return f"Content saved to '{file_name}'."

        # File not found — create it on Desktop
        return create_file_on_desktop(file_name, content=content)

    except Exception as e:
        return f"Error writing file: {e}"





# Document types that should be preferred over code/binary files
PREFERRED_EXTENSIONS = {".pdf", ".docx", ".doc", ".xlsx", ".xls", ".pptx", ".ppt", ".txt", ".odt"}


def _rank_matches(matches):
    """Sort matches so preferred document types come first."""
    def priority(path):
        ext = os.path.splitext(path)[1].lower()
        return 0 if ext in PREFERRED_EXTENSIONS else 1
    return sorted(matches, key=priority)


def _normalize(text):
    """Strip separators so 'aryannaikar' matches 'Aryan_Naikar_Resume'."""
    return re.sub(r"[\s_\-\.\(\)]+", "", text).lower()


def semantic_file_search(query):
    build_file_cache()

    query = query.lower().replace("open", "").strip()

    # ── Tier 1: Exact filename match (with or without extension) ──────────
    matches = []
    for path in FILE_CACHE:
        filename = os.path.basename(path).lower()
        name_no_ext = os.path.splitext(filename)[0]
        if query == filename or query == name_no_ext:
            matches.append(path)
    if matches:
        return _rank_matches(matches)[0]

    # ── Tier 2: Full query substring inside filename ───────────────────────
    matches = []
    for path in FILE_CACHE:
        filename = os.path.basename(path).lower()
        if query in filename:
            matches.append(path)
    if matches:
        return _rank_matches(matches)[0]

    # ── Tier 3: Normalized match (ignores _ - . spaces) ───────────────────
    # Handles "aryannaikar resume" matching "Aryan_Naikar_Resume_2025.pdf"
    norm_query = _normalize(query)
    query_words_norm = norm_query.split() if " " in query else [norm_query]
    matches = []
    for path in FILE_CACHE:
        filename = os.path.basename(path).lower()
        norm_file = _normalize(filename)
        if all(w in norm_file for w in query_words_norm):
            matches.append(path)
    if matches:
        return _rank_matches(matches)[0]

    # ── Tier 4: All words present anywhere in filename ────────────────────
    query_words = query.split()
    matches = []
    for path in FILE_CACHE:
        filename = os.path.basename(path).lower()
        if all(word in filename for word in query_words):
            matches.append(path)
    if matches:
        return _rank_matches(matches)[0]

    # ── Tier 5: Fuzzy word-level match (catches typos like "rresume") ─────
    # Each query word must fuzzy-match either a filename token OR a slice
    # of the normalized (joined) filename — handles "aryannaikar" → "aryan_naikar"
    query_words = query.split()
    matches = []
    for path in FILE_CACHE:
        filename = os.path.basename(path).lower()
        name_no_ext = os.path.splitext(filename)[0]
        file_tokens = [t for t in re.split(r"[\s_\-\.\(\)]+", name_no_ext) if t]
        norm_file = _normalize(name_no_ext)  # fully joined: "aryannaikarresume2025"

        def word_matches(qw):
            # 1. fuzzy match against individual tokens
            if any(difflib.SequenceMatcher(None, qw, ft).ratio() >= 0.75 for ft in file_tokens):
                return True
            # 2. fuzzy match against normalized full filename (for compound words)
            if difflib.SequenceMatcher(None, qw, norm_file).ratio() >= 0.6:
                return True
            # 3. substring of normalized filename
            if qw in norm_file:
                return True
            return False

        if all(word_matches(qw) for qw in query_words):
            score = sum(
                max(difflib.SequenceMatcher(None, qw, ft).ratio() for ft in file_tokens)
                for qw in query_words
            )
            matches.append((score, path))
    if matches:
        matches.sort(key=lambda x: x[0], reverse=True)
        top = [p for _, p in matches[:10]]
        return _rank_matches(top)[0]

    # ── Tier 6: Any single word match (broad fallback) ────────────────────
    matches = []
    for path in FILE_CACHE:
        filename = os.path.basename(path).lower()
        if any(word in filename for word in query_words):
            matches.append(path)
    if matches:
        return _rank_matches(matches)[0]

    return None





def open_best_match(query):
    try:
        path = semantic_file_search(query)

        if not path:
            return "No matching file found."

        os.startfile(path)

        return f"Opening: {os.path.basename(path)}"

    except Exception as e:
        return f"Error: {e}"


def refresh_file_cache():
    global FILE_CACHE, CACHE_BUILT

    FILE_CACHE = []
    CACHE_BUILT = False

    build_file_cache()

    return f"Cache refreshed. {len(FILE_CACHE)} files indexed."
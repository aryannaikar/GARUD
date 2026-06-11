from pathlib import Path


def get_search_paths():
    paths = []

    home = Path.home()

    folders = [
        "Desktop",
        "Documents",
        "Downloads"
    ]

    for folder in folders:
        path = home / folder

        if path.exists():
            paths.append(path)

        onedrive_path = home / "OneDrive" / folder

        if onedrive_path.exists():
            paths.append(onedrive_path)

    return paths
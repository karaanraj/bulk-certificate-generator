from pathlib import Path

GENERATED_DIR = Path("storage/generated")


def ensure_storage_dirs() -> None:
    GENERATED_DIR.mkdir(parents=True, exist_ok=True)


def certificate_path(file_name: str) -> Path:
    return GENERATED_DIR / file_name

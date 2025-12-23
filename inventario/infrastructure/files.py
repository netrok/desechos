from django.core.files.storage import default_storage

def delete_file_if_exists(path: str | None) -> None:
    if path and default_storage.exists(path):
        default_storage.delete(path)

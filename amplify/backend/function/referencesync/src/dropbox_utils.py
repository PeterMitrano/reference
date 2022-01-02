import pathlib

from dropbox.exceptions import HttpError
from dropbox.files import FileMetadata
from tqdm import tqdm


def download_from_dropbox(dbx, path):
    try:
        md, res = dbx.files_download('/' + path)
    except HttpError as err:
        print('*** HTTP error', err)
        return None
    data = res.content
    return data


def get_pdf_files(dbx):
    res = dbx.files_list_folder('')

    for i, file in enumerate(res.entries):
        print(f"{i}/{len(res.entries)}")
        path = pathlib.Path(file.name)
        file_path: str = file.path_display
        if isinstance(file, FileMetadata):
            if path.suffix == '.pdf':
                yield file, file_path
            else:
                print(f"Skipping non-PDF file {file_path}")
        else:
            print(f"Skipping non-file {path}")
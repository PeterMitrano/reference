import pathlib

from dropbox.exceptions import HttpError
from dropbox.files import FileMetadata

from logging_utils import get_logger

logger = get_logger(__file__)


def download_from_dropbox(dbx, path):
    try:
        md, res = dbx.files_download('/' + path)
    except HttpError as err:
        logger.error('*** HTTP error', err)
        return None
    data = res.content
    return data


def get_pdf_files(dbx):
    res = dbx.files_list_folder('')

    for i, file in enumerate(res.entries):
        logger.debug(f"{i}/{len(res.entries)}")
        path = pathlib.Path(file.name)
        file_path: str = file.path_display
        if isinstance(file, FileMetadata):
            if path.suffix == '.pdf':
                yield file, file_path
            else:
                logger.debug(f"Skipping non-PDF file {file_path}")
        else:
            logger.debug(f"Skipping non-file {path}")

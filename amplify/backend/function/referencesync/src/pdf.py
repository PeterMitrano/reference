import io
from dataclasses import dataclass

from pdfminer.high_level import extract_text
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfparser import PDFParser

from dropbox_utils import download_from_dropbox

TITLE_GUESS_MAX_LENGTH = 256


@dataclass
class TitleAuthor:
    title: str
    author: str


def extract_standardized_metadata(dbx, file):
    file_data = download_from_dropbox(dbx, file.name)
    io_fp = io.BytesIO(file_data)
    parser = PDFParser(io_fp)
    doc = PDFDocument(parser)
    metadata = doc.info[0]

    full_text = extract_text(io_fp, maxpages=1)
    # use an ML model to extract title and author information from full text? train it on S2ORC?

    if 'Title' in metadata and 'Author' in metadata:
        title = metadata['Title'].decode("utf-8", errors='ignore')
        authors = metadata['Author'].decode("utf-8", errors='ignore')
        return TitleAuthor(title, authors)
    elif 'Title' in metadata:
        title = metadata['Title'].decode("utf-8", errors='ignore')
        return TitleAuthor(title, '')
    else:
        title_guess_from_text = full_text.split('\n')[0]
        title_guess_from_text = title_guess_from_text[:TITLE_GUESS_MAX_LENGTH]
        return TitleAuthor(title_guess_from_text, '')

import pathlib
import numpy as np
from random import shuffle

import pyperclip
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfparser import PDFParser

from citation_search import make_gpt_prompt


def main():
    dataset_dir = pathlib.Path("dataset")
    dataset = []
    rng = np.random.RandomState(0)
    filenames = np.array(list(dataset_dir.glob("*.pdf")))
    rng.shuffle(filenames)
    for filename in filenames:
        with filename.open("rb") as pdf_fp:
            inputs = make_gpt_prompt(pdf_fp)
            print(inputs)
            parser = PDFParser(pdf_fp)
            doc = PDFDocument(parser)
            pdf_metadata = doc.info[0]
            title = pdf_metadata['Title'].decode("utf-8", errors='ignore')  # FIXME: utf-8 is totally unacceptable
            dataset.append([inputs, title])


if __name__ == '__main__':
    main()

from dropbox import Dropbox

from citation_search import extract_citation_info
from dropbox_utils import get_pdf_files


def main():
    test_idx = 0
    dropbox_oauth_token = "TiA1HlRcg2oAAAAAAAAAAe42lvAY77xyzbJoobhxFm3JtezXpZHrDmJIS2ODkYxm"
    with Dropbox(oauth2_access_token=dropbox_oauth_token) as dbx:
        file, file_path = list(get_pdf_files(dbx))[test_idx]
    citation_info = extract_citation_info(dbx, file)
    print(citation_info)


if __name__ == '__main__':
    main()

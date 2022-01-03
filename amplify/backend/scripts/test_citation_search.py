from dropbox import Dropbox

from citation_search import extract_citation_info
from dropbox_utils import get_pdf_files


def main():
    test_idx = 4
    # test_name = "/https%2Fscience-sciencemag-org.proxy.lib.umich.edu%2Fcontent%2Fsci%2F369%2F6506.pdf"
    dropbox_oauth_token = "TiA1HlRcg2oAAAAAAAAAAe42lvAY77xyzbJoobhxFm3JtezXpZHrDmJIS2ODkYxm"
    with Dropbox(oauth2_access_token=dropbox_oauth_token) as dbx:
        files_and_paths = list(get_pdf_files(dbx))
        # for file, file_path in files_and_paths:
        #     if file_path == test_name:
        #         break
        file, file_path = files_and_paths[test_idx]
    citation_info = extract_citation_info(dbx, file)
    print(citation_info)


if __name__ == '__main__':
    main()

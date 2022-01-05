from time import perf_counter
import numpy as np

from dropbox import Dropbox

from citation_search import CitationGA, extract_citation
from dropbox_utils import get_pdf_files


class TestCitationGA(CitationGA):

    def __init__(self, test_init):
        super().__init__(population_size=100, pdf_fp=None, filename=None)
        self.test_init = test_init

    def initialize(self):
        population = [
            self.test_init
        ]

        population = self.rng.choice(population, self.population_size)
        return population


def main():
    np.set_printoptions(linewidth=200, precision=1, suppress=True)
    test_idx = 0
    # test_name = "/https%2Fscience-sciencemag-org.proxy.lib.umich.edu%2Fcontent%2Fsci%2F369%2F6506.pdf"
    rng = np.random.RandomState(0)
    dropbox_oauth_token = "TiA1HlRcg2oAAAAAAAAAAe42lvAY77xyzbJoobhxFm3JtezXpZHrDmJIS2ODkYxm"
    with Dropbox(oauth2_access_token=dropbox_oauth_token) as dbx:
        files_and_paths = list(get_pdf_files(dbx))
    file, _ = files_and_paths[test_idx]
    print(extract_citation(dbx, file))

    # rng.shuffle(files_and_paths)
    # for file, file_path in files_and_paths:
    #     t0 = perf_counter()
    #     print(extract_citation(dbx, file))
    #     dt = perf_counter() - t0
    #     print('dt', dt)

    # test_init = Citation(
    #     title="Embracing Change",
    #     authors=["Hadsell, R"],
    #     venue="Trends in",
    #     year=2030,
    #     confidence=0)
    #
    # ga = TestCitationGA(test_init)
    # t0 = perf_counter()
    # citation = ga.opt(generations=4)
    # dt = perf_counter() - t0
    # print(f'dt {dt:.2f}')
    # print(citation)


if __name__ == '__main__':
    main()

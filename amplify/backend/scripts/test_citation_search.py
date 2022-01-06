import numpy as np

from citation_search import CitationGA, standardize_venue


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

    test_venues = [
        "Machine Learning",
        "ICML '09",
        "Proceedings 35th Annual Symposium on Foundations of Computer Science",
        "2021 International Conference on Instrumentation, Control, and Automation (ICA)",
        "2014 IEEE Global Conference on Signal and Information Processing (GlobalSIP)",
        "2016 IEEE/RSJ International Conference on Intelligent Robots and Systems (IROS)",
        "2020 IEEE International Conference on Robotics and Automation (ICRA)",
        "2021 IEEE International Conference on Robotics and Automation (ICRA)",
        "ArXiv",
        "CoRL",
        "EPJ Data Science",
        "Ethics and Information Technology",
        "ICLR",
        "ICML",
        "IEEE transactions on pattern analysis and machine intelligence",
        "J. Mach. Learn. Res.",
        "KDD",
        "Robotics: Science and Systems",
        "Technology in Society",
        "Trends in Cognitive Sciences",
        "UAI",
    ]
    for test_venue in test_venues:
        print(f"{test_venue} -> {standardize_venue(test_venue)}")
    # for a in c.authors:
    #     print(standardize_author(a))

        # test_idx = 0
    # # test_name = "/https%2Fscience-sciencemag-org.proxy.lib.umich.edu%2Fcontent%2Fsci%2F369%2F6506.pdf"
    # rng = np.random.RandomState(0)
    # dropbox_oauth_token = "TiA1HlRcg2oAAAAAAAAAAe42lvAY77xyzbJoobhxFm3JtezXpZHrDmJIS2ODkYxm"
    # with Dropbox(oauth2_access_token=dropbox_oauth_token) as dbx:
    #     files_and_paths = list(get_pdf_files(dbx))
    # file, _ = files_and_paths[test_idx]
    # print(extract_citation(dbx, file))
    #
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

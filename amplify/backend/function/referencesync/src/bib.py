import numpy as np

from database import list_papers_for_token_with_confidence
from logging_utils import get_logger

logger = get_logger(__file__)


def generate_bib(dropbox_oauth_token):
    papers = list_papers_for_token_with_confidence(dropbox_oauth_token)
    if papers is None:
        logger.error("Listing papers for the user failed")
        return None

    logger.debug(f"Found {len(papers)} papers")

    entries = []

    titles = [p['title'] for p in papers]
    cite_names = choose_cite_names(titles)

    for paper, cite_name in zip(papers, cite_names):
        authors = paper['authors']
        venue = paper['venue']
        year = str(paper['year'])
        title = paper['title']
        entry_str = format_bibtex_entry(title, authors, venue, year, cite_name)
        entries.append(entry_str)

    full_bib_str = '\n'.join(entries)

    return full_bib_str


def softmax(x):
    """
    Compute softmax values for each sets of scores in x
    taken from https://stackoverflow.com/questions/34968722/how-to-implement-the-softmax-function-in-python/38250088
    """
    e_x = np.exp(x - np.max(x))
    return e_x / e_x.sum()


def choose_cite_names(titles):
    rng = np.random.RandomState(0)
    j = 0
    while True:
        sampled_cite_names = []
        for title in titles:
            cite_names, scores = scored_cite_names(title)
            probabilities = softmax(scores)
            cumulative_probabilities = np.cumsum(probabilities)
            sampled_idx = np.where(rng.rand() < cumulative_probabilities)[0][0]
            sampled_cite_name = cite_names[sampled_idx]
            sampled_cite_names.append(sampled_cite_name)

        all_unique = (len(set(sampled_cite_names)) == len(sampled_cite_names))
        j += 1
        if all_unique:
            logger.info(f"Finding unique cite names took {j} tries")
            return sampled_cite_names


def scored_cite_names(title):
    split_by_colon = title.split(":")
    pre_colon_words = []
    if len(split_by_colon) == 2:
        pre_colon = split_by_colon[0]
        pre_colon_words = pre_colon.split(" ")

    uncleaned_words = title.split(" ")
    chars_to_replace = [':', '/', ',', '-']
    cleaned_words = []
    for w in uncleaned_words:
        cleaned_word = w
        for c in chars_to_replace:
            cleaned_word = cleaned_word.replace(c, '')
        cleaned_words.append(cleaned_word)

    cleaned_words = list(filter(lambda w: w not in ['', ' '], cleaned_words))
    with open("1-1000.txt", 'r') as f:
        common_words = [l.strip("\n") for l in f.readlines()]

    scores = []
    for i, word_in_title in enumerate(cleaned_words):
        word_in_title = word_in_title.lower()
        score = 0
        if word_in_title not in common_words:
            score += 100
        score += len(word_in_title) / 3
        if word_in_title in pre_colon_words:
            score += 100
        score += int(5 / (i + 1))
        scores.append(score)

    return np.array(cleaned_words), np.array(scores)


def split_name(author):
    if author == '':
        return author, ''
    parts = author.split(" ")
    return parts[0], " ".join(parts[1:])


def make_last_comma_first(author):
    first, last = split_name(author)
    return f"{last}, {first}"


def format_bibtex_entry(title, authors, venue, year, cite_name):
    last_firsts = [make_last_comma_first(author) for author in authors]
    first_author = authors[0]
    _, first_author_last_name = split_name(first_author)
    authors_string = " and ".join(last_firsts)
    bibtex_parts = [
        "@article {",
        f"{cite_name}{first_author_last_name}{year},",
        f"title={{{title}}},",
        f"author={{{authors_string}}},",
        f"journal={{{venue}}},",
        f"year={{{year}}},",
        "}\n",
    ]
    bibtex_str = '\n'.join(bibtex_parts)
    return bibtex_str

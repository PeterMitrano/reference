from database import list_papers_for_token


def generate_bib(dropbox_oauth_token):
    papers = list_papers_for_token(dropbox_oauth_token)
    if papers is None:
        print("Listing papers for the user failed")
    print(f"Found {len(papers)} papers")

    entries = []
    for paper in papers:
        authors = paper['authors']
        venue = paper['venue']
        year = str(paper['year'])
        title = paper['title']
        entry_str = format_bibtex_entry(title, authors, venue, year)
        entries.append(entry_str)

    full_bib_str = '\n'.join(entries)
    print(full_bib_str)

    return full_bib_str


def make_cite_name(title, authors, venue, year):
    # FIXME: use a something clever here
    first_significant_word = title.split(" ")[0]
    return f"{first_significant_word}{year}"


def split_name(author):
    if author == '':
        return author, ''
    parts = author.split(" ")
    return parts[0], " ".join(parts[1:])


def make_last_comma_first(author):
    first, last = split_name(author)
    return f"{last}, {first}"


def format_bibtex_entry(title, authors, venue, year):
    cite_name = make_cite_name(title, authors, venue, year)
    last_firsts = [make_last_comma_first(author) for author in authors]
    authors_string = " and ".join(last_firsts)
    bibtex_parts = [
        "@article {",
        f"{cite_name},",
        f"title={{{title}}},",
        f"author={{{authors_string}}},",
        f"journal={{{venue}}},",
        f"year={{{year}}},",
        "}\n",
    ]
    bibtex_str = '\n'.join(bibtex_parts)
    return bibtex_str

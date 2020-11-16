#!/usr/bin/python

"""Script to manage papers."""

from pathlib import Path

from slugify import slugify


def safe_prompt(prompt: str):
    """Prompt for text allowing user to can el."""


def rename_paper(inf: Path) -> Path:
    while True:
        author = input("Enter Principal Author ")
        print("A descriptive title is something one might look the paper up under.")
        print("This is probably the subtitle.")
        title = input("Enter descriptive title ")
        yn = input("Continue? [Yn]")
        if "n" not in yn.upper:
            break
    author = slugify(author, separator="_")
    title = slugify(title, separator="_")
    return inf.rename(inf.with_name(f"{title}-{author}.pdf"))


def dejstorify(paper: Path) -> Path:
    """Try to remove jstor page from pdf."""
    raise NotImplementedError("Not yet implemented, but easy enough! do so now!")


# pdfcrop --margins [] --clip
# pdfbook cropped-tmp (use python tmpdir)
# return tmpbooklet file


if __name__ == "__main__":

    from argparse import ArgumentParser

    parser = ArgumentParser()

    parser.add_argument("INPUT", help="Input pdf to process")
    parser.add_argument(
        "-d",
        "--de-jstorify",
        help="De-Jstorify the pdf, i.e. delete cover pages and banners.",
    )
    parser.add_argument("--skip-rename", help="Skip rename.", action="store_true")

    args = parser.parse_args()

    inf = Path(args.INPUT)

    if not args.skip_rename:
        inf = rename_paper(inf)

    if args.de_jstorify:
        dejstorify(inf)

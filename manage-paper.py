#!/usr/bin/python

"""Script to manage papers."""

import readline
from json import loads
from pathlib import Path
from subprocess import run
from tempfile import TemporaryDirectory

from PyPDF2 import PdfFileReader, PdfFileWriter
from slugify import slugify


def input_with_prefill(prompt, text):
    """
    Input with prefill by abusing readline hook.

    Copied from https://stackoverflow.com/questions/8505163/is-it-possible-to-prefill-a-input-in-python-3s-command-line-interface
    """

    def hook():
        readline.insert_text(text)
        readline.redisplay()

    readline.set_pre_input_hook(hook)
    result = input(prompt)
    readline.set_pre_input_hook()
    return result


def open_paper(inf: Path):
    """Open paper in most appropriate way, either on another monitor or on this one."""

    cmd = ["i3-msg", "-t", "get_workspaces"]
    workspaces = run(cmd, capture_output=True, encoding="utf8")
    workspaces = loads(workspaces.stdout)
    if len(workspaces) > 1:  # we have multiple monitors
        for workspace in workspaces:
            if not workspace["focused"]:
                other = workspace["name"]
            else:
                current = workspace["name"]

        cmd = [
            "i3-msg",
            "workspace",
            f"{other};",
            f'exec "zathura \\"{inf.resolve()}\\""',
            ";",
            "workspace",
            current,
        ]
        print(" ".join(cmd))
        run(cmd)
    else:
        cmd = ["i3-msg", "exec", "zathura", inf.resolve()]
        run(cmd)


def rename_paper(inf: Path) -> Path:
    pdf = PdfFileReader(inf.open("rb"))
    pdf.documentInfo.author
    while True:
        author = input_with_prefill("Enter Principal Author: ", pdf.documentInfo.author)
        print("A descriptive title is something one might look the paper up under.")
        print("This is probably the subtitle.")
        title = input_with_prefill("Enter descriptive title: ", pdf.documentInfo.title)
        yn = input("Continue? [Yn] ")
        if "n" not in yn.upper():
            break
    author = slugify(author, separator="_")
    title = slugify(title, separator="_")
    cmd = ["pkill", "-f", f"zathura {inf.resolve()}"]
    run(cmd)
    return inf.rename(inf.with_name(f"{author}-{title}.pdf"))


def dejstorify(paper: Path) -> Path:
    """Try to remove jstor page from pdf."""

    with TemporaryDirectory(dir="./") as tmpdir:
        pdf = PdfFileReader(paper.open("rb"))
        max_size = pdf.getPage(0).mediaBox
        larger_pages = []
        writer = PdfFileWriter()
        for pgno, page in enumerate(pdf.pages):
            cropbox = page.cropBox
            mediabox = page.mediaBox
            max_size = max(mediabox, max_size)

            if cropbox > max_size or mediabox < max_size:
                writer.addPage(page)
            else:
                larger_pages.append(pgno)

        if len(larger_pages) > 1:
            raise NotImplementedError(
                "Unable to handle multiple pages of differing sizes\
                ---implement here now you've found a source."
            )
        elif len(larger_pages) == 0:
            print("No jstor page found, skipping")
            pre_crop = paper

        pre_crop = Path(f"{tmpdir}/{paper.name}")
        writer.write(pre_crop.open("wb"))

        # implement banner removal here

        post_crop = pre_crop

        return post_crop.replace(paper)


# paper = Path("/home/john/hutter-pdfs/project_muse_636205.pdf")
# dejstorify(paper)


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
        action="store_true",
        help="De-Jstorify the pdf, i.e. delete cover pages and banners.",
    )
    parser.add_argument("--skip-rename", help="Skip rename.", action="store_true")

    args = parser.parse_args()

    inf = Path(args.INPUT)
    open_paper(inf)

    if not args.skip_rename:
        inf = rename_paper(inf)

    if args.de_jstorify:
        dejstorify(inf)

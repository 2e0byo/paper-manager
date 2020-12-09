#!/usr/bin/python

"""Script to manage papers."""

import readline
from json import loads
from os import chdir, getcwd
from pathlib import Path
from subprocess import run
from tempfile import TemporaryDirectory

from PyPDF2 import PdfFileReader, PdfFileWriter
from PyPDF2.pdf import PageObject
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


def get_significant_discrepancy(pdf):
    """Get significant discrepancy, if there is one."""

    # work out a significant difference
    max_media_size = max([page.mediaBox for page in pdf.pages])
    min_media_size = min([page.mediaBox for page in pdf.pages])
    if (
        abs(max_media_size.getWidth() - min_media_size.getWidth()) < 10
        and abs(max_media_size.getHeight() - min_media_size.getHeight()) < 10
    ):
        media_size_discrepancy = None
    else:
        media_size_discrepancy = {
            "height": abs(max_media_size.getHeight() - min_media_size.getHeight()),
            "width": abs(max_media_size.getWidth() - min_media_size.getWidth()),
            "min": min_media_size,
            "max": max_media_size,
        }

    max_crop_size = max([page.cropBox for page in pdf.pages])
    min_crop_size = min([page.cropBox for page in pdf.pages])
    if (
        abs(max_crop_size.getWidth() - min_crop_size.getWidth()) < 10
        and abs(max_crop_size.getHeight() - min_crop_size.getHeight()) < 10
    ):
        crop_size_discrepancy = None
    else:
        crop_size_discrepancy = {
            "height": abs(max_crop_size.getHeight() - min_crop_size.getHeight()),
            "width": abs(max_crop_size.getWidth() - min_crop_size.getWidth()),
            "max": min_crop_size,  # this is not an error
            "min": max_crop_size,  # largest cropbox = smallest page
        }

    return media_size_discrepancy, crop_size_discrepancy


def is_large(page, media_size_discrepancy, crop_size_discrepancy):
    """Test if page is larger than the minimum by seeing if a significant dimension is
    more than half the distance between the maximum and minimum dimensions above the
    minimum."""

    cropbox = page.cropBox
    mediabox = page.mediaBox

    if media_size_discrepancy:
        if any(
            [
                mediabox.getHeight() - media_size_discrepancy["min"].getHeight()
                > media_size_discrepancy["height"] / 2,
                mediabox.getWidth() - media_size_discrepancy["min"].getWidth()
                > media_size_discrepancy["width"] / 2,
            ]
        ):
            return True

    if crop_size_discrepancy:
        if any(
            [
                cropbox.getHeight() - crop_size_discrepancy["min"].getHeight()
                > crop_size_discrepancy["height"] / 2,
                cropbox.getWidth() - crop_size_discrepancy["min"].getWidth()
                > crop_size_discrepancy["width"] / 2,
            ]
        ):
            return True
        else:
            print(
                cropbox.getHeight(),
                cropbox.getWidth(),
                crop_size_discrepancy["min"].getHeight(),
                crop_size_discrepancy["min"].getWidth(),
            )

    return False


def test_footer(page: PageObject):
    """Test whether a pdf contains a 'this content downloaded...' footer."""
    if "This content downloaded from" in page.extractText():
        return "jstor"
    else:
        return None


def dejstorify(paper: Path) -> Path:
    """Try to remove jstor page from pdf."""

    with TemporaryDirectory(dir="./") as tmpdir:
        pdf = PdfFileReader(paper.open("rb"))

        media_size_discrepancy, crop_size_discrepancy = get_significant_discrepancy(pdf)

        larger_pages = []
        writer = PdfFileWriter()
        smaller = 0
        for pgno, page in enumerate(pdf.pages):
            if is_large(page, media_size_discrepancy, crop_size_discrepancy):
                larger_pages.append(pgno)
            else:
                smaller += 1
                footer = test_footer(page)
                if footer == "jstor":
                    crop = (0, 25)
                    print("Cropping out jstor footer.")
                    page.cropBox.setLowerLeft(
                        tuple(map(sum, zip(page.cropBox.getLowerLeft(), crop)))
                    )
                writer.addPage(page)

        if len(larger_pages) > 1:
            print(len(larger_pages))
            raise NotImplementedError(
                "Unable to handle multiple pages of differing sizes\
                ---implement here now you've found a source."
            )
        elif len(larger_pages) == 0:
            print(smaller)
            print("No jstor page found, skipping")
            pre_crop = paper

        pre_crop = Path(f"{tmpdir}/{paper.name}")
        writer.write(pre_crop.open("wb"))

        post_crop = pre_crop

        return post_crop.replace(paper)


def test_for_text(inf: Path) -> bool:
    """Test whether or no a file appears to contain text."""
    pdf = PdfFileReader(inf.open("rb"))
    if pdf.getNumPages() > 1:
        page = pdf.getPage(1)
    else:
        page = pdf.getPage(0)
    return True if page.extractText().strip() else False


def ocr(inf: Path, lang):
    inf = inf.resolve()

    pwd = getcwd()
    with TemporaryDirectory(
        dir=".",
    ) as tmpdir:
        chdir(tmpdir)
        # burst input into pages
        cmd = [
            "pdftk",
            inf.resolve(),
            "burst",
            "output",
            inf.stem + "_%04d.pdf",
        ]
        run(cmd)

        print("Converting to images")
        # can we use pdfimages?
        pdfimages = True

        cmd = ["pdfimages", "-list"]
        for pdf in Path("./").glob("*.pdf"):
            images = run(cmd + [pdf], encoding="utf8", capture_output=True).stdout
            if len(images.strip().split("\n")) > 3:
                pdfimages = False
                break

        if not pdfimages:
            print("Using Imagemagick")
            cmd = (
                "find . -name '*.pdf' | parallel "
                + " --bar --max-args 1 env MAGICK_THREAD_LIMIT=1 convert -density 300 {} {}.png \\;"
            )
            run(cmd, shell=True)

        else:
            print("Using pdfimages")
            cmd = (
                "find . -name '*.pdf' | parallel --bar --max-args 1 "
                "pdfimages -j -png {} {}-img \\;"
            )
            run(cmd, shell=True)

        print("Running Tesseract")
        cmd = (
            'find . -maxdepth 1 -name "*.tif" -o -name "*.png" -o -name "*.jpeg" |'
            "parallel --bar --maxargs 1 "
            "-i{} env OMP_THREAD_LIMIT=1 tesseract {} {}-ocr -l " + lang + " pdf \\;"
        )
        run(cmd, shell=True)

        bak = inf.rename(inf.with_name(inf.name + ".bak"))

        cmd = f'pdftk *-ocr.pdf output "{inf.resolve()}"'
        run(cmd, shell=True, check=True)
        chdir(pwd)


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
    parser.add_argument("--ocr", help="Ocr if appropriate", action="store_true")
    parser.add_argument(
        "--ocr-langs", help="Ocr languages for tesseract", default="eng+fra+lat+grc"
    )

    args = parser.parse_args()

    inf = Path(args.INPUT)

    if not args.skip_rename:
        open_paper(inf)
        inf = rename_paper(inf)

    if args.de_jstorify:
        dejstorify(inf)

    if args.ocr:
        if not test_for_text(inf):
            print("Applying OCR")
            ocr(inf, args.ocr_langs)
        else:
            print("No need to OCR")

# Paper Management Script

This is a very personalised paper management script which I use all the time. It
might be useful for you to build on, but it won't even run unless you happen to
be running i3/sway and have zathura installed.

Operation:

- open paper (on other monitor if possible)
- prompt for author (prefilling if possible)
- prompt for title (prefilling if possible)
- if told to do so, strip cover pages and copyright margins (makes printing booklets possible, otherwise the text is too small)
- if told to do so, and the pdf does not contain a text layer, ocr it
- save resultant file under programmatic name.

Then I move the file manually to the correct dir.

## Installation

```bash
python3 -m pip install -r requirements.txt
ln -rs ./paper_manager.py ~/bin/
```

## Use

```bash
manage_paper.py --help
```

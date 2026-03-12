# Personal web site

This is the source repo for my personal website. It's a simple static HTML generator whipped up in python with the help of Claude. Article sources live in the `articles` folder, HTML or markdown is supported. Build the static site from sources with
```
pip install -r requirements.txt && python build.py
```
The build site is placed in `dist/`. The actual site is at www.rolandnilsson.net

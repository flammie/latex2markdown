#!/usr/bin/env python3
"""Simple converter from latex papers to github pages markdowns."""

import sys
import re

from argparse import ArgumentParser, FileType


def main():
    """CLI for latex to markdown conversion."""
    ap = ArgumentParser()
    ap.add_argument("-i", "--input", metavar="INFILE", type=open,
                    dest="infile", help="read vislcg3 data from INFILE")
    ap.add_argument("-o", "--output", metavar="OUTFILE", type=FileType("w"),
                    dest="outfile", help="write UD to OUTFILE")
    ap.add_argument("-v", "--verbose", action="store_true", default=False,
                    help="print verbosely while processing")
    opts = ap.parse_args()
    if not opts.infile:
        opts.infile = sys.stdin
        print("reading from <stdin>")
    if not opts.outfile:
        opts.outfile = sys.stdout
    latex = ""
    # comments
    for line in opts.infile.readlines():
        if "%" in line:
            line = line.replace("\\%", "§PERCENT§")
            line = line.split("%")[0].replace("§PERCENT§", "%")
        latex = latex + line
    documentclassre = re.compile(r"\\documentclass(\[[^]]*\])?({[^}]*})")
    documentclasses = documentclassre.findall(latex)
    if len(documentclasses) == 0:
        print("Coildn't find documentclass maybe not latex")
        sys.exit(1)
    elif len(documentclasses) > 1:
        print("Found too many documentclasses")
        sys.exit(1)
    # headings
    documentclass = documentclasses[0][1]
    dcoptions = documentclass[0][0]
    latex = documentclassre.sub("", latex)
    usepackagere = re.compile(r"\\usepackage(\[[^]*]\])?({[^}]*})")
    usepackages = usepackagere.findall(latex)
    usedpackages = []
    for usepackage in usepackages:
        usedpackages.append(usepackage[1])
    latex = usepackagere.sub("", latex)
    # contents
    # need some tracking for labels and refs
    # then cites and bibstuff
    # small local things first
    textttre = re.compile(r"\\texttt{([^}]*)}", re.MULTILINE)
    latex = textttre.sub(r"`\1`", latex)
    textbfre = re.compile(r"\\textbf{([^}]*)}", re.MULTILINE)
    latex = textbfre.sub(r"**\1**", latex)
    textitre = re.compile(r"\\textit{([^}]*)}", re.MULTILINE)
    latex = textitre.sub(r"*\1*", latex)
    urlre = re.compile(r"\\url{([^}]*)}", re.MULTILINE)
    latex = urlre.sub(r"<\1>", latex)
    footnotere = re.compile(r"\\footnote{([^}]*)}", re.MULTILINE)
    latex = footnotere.sub(r" (footnote: \1)", latex)
    # even more simple stuffs
    latex = latex.replace("\\begin{document}", "<!-- begin document -->")
    latex = latex.replace("\\maketitle", "<!-- make title -->")
    latex = latex.replace("\\begin{abstract}", "*Abstract:*")
    latex = latex.replace("\\end{abstract}", "<!-- end abstract -->")
    latex = latex.replace("\\begin{figure}", "*Figure:*")
    latex = latex.replace("\\begin{figure*}", "*Figure:*")
    latex = latex.replace("\\end{figure}", "<!-- end figure -->")
    latex = latex.replace("\\end{figure*}", "<!-- end figure* -->")
    latex = latex.replace("\\begin{table}", "*Table:*")
    latex = latex.replace("\\begin{table*}", "*Table:*")
    latex = latex.replace("\\end{table}", "<!-- end table -->")
    latex = latex.replace("\\end{table*}", "<!-- end table* -->")
    latex = latex.replace("\\and", "and")
    latex = latex.replace("\\\\", " ")  # should be linebreak but but
    # stuffs
    sectionre = re.compile(r"\\section{([^}]*)}", re.MULTILINE)
    latex = sectionre.sub(r"## \1", latex)
    subsectionre = re.compile(r"\\subsection{([^}]*)}", re.MULTILINE)
    latex = subsectionre.sub(r"### \1", latex)
    subsubsectionre = re.compile(r"\\subsubsection{([^}]*)}", re.MULTILINE)
    latex = subsubsectionre.sub(r"#### \1", latex)
    # more contentful stuffs agan
    titlere = re.compile(r"\\title{([^}]*)}", re.MULTILINE)
    titles = titlere.findall(latex)
    if len(titles) == 0:
        print("Couldn't find title maybe not document")
        sys.exit(1)
    elif len(titles) > 1:
        print("Too many titles?")
        sys.exit(1)
    title = titles[0].replace("\n", " ")
    latex = titlere.sub(r"# §§§TITLE§§§", latex)
    latex = latex.replace("§§§TITLE§§§", title)
    authorre = re.compile(r"\\author{([^}]*)}", re.MULTILINE)
    latex = authorre.sub(r"Authors: \1", latex)
    markdown = latex
    print(markdown, file=opts.outfile)


if __name__ == "__main__":
    main()

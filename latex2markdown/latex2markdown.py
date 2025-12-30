#!/usr/bin/env python3
"""Simple converter from latex papers to github pages markdowns."""

import os
import re
import sys
from argparse import ArgumentParser, FileType


def readbib(relpath: str, bibfile: str):
    """Read bibfile into a map of maps."""
    with open(os.path.join(relpath, bibfile + ".bib")) as f:
        curkey = None
        bib = {}
        for line in f:
            line = line.strip()
            if line.startswith("@"):
                bracket = line.find("{")
                comma = line.find(",")
                curkey = line[bracket+1:comma]
                bib[curkey] = {}
            elif line.startswith("}"):
                curkey = None
            elif "=" in line:
                if curkey is None:
                    print(f"error parsing {bibfile} data before key",
                          file=sys.stderr)
                    continue
                fields = line.split("=")
                thing = fields[0].strip()
                stuff = fields[1].strip()
                if stuff.startswith("{") and "}" not in line:
                    line = next(f)
                    while "}" not in line:
                        stuff = stuff + line.strip()
                        line = next(f)
                if stuff.startswith("{") or stuff.startswith("\""):
                    stuff = stuff[1:]
                if stuff.endswith("}") or stuff.endswith("\""):
                    stuff = stuff[:-1]
                elif stuff.endswith("},") or stuff.endswith("\","):
                    stuff = stuff[:-2]
                bib[curkey][thing] = stuff.replace("\\", "\\\\")
            else:
                pass
    return bib


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
    relpath = os.getcwd()
    if not opts.infile:
        opts.infile = sys.stdin
        print("reading from <stdin>")
    else:
        relpath = os.path.dirname(os.path.realpath(opts.infile.name))
    if not opts.outfile:
        opts.outfile = sys.stdout
    latex = ""
    # read in and remvoe comments
    for line in opts.infile.readlines():
        if "%" in line:
            line = line.replace("\\%", "§PERCENT§")
            line = line.split("%")[0].replace("§PERCENT§", "%")
        latex = latex + line
    # get rid of html / markdown problems
    latex = latex.replace("<", "&lt;")
    latex = latex.replace(">", "&gt;")
    # document class
    documentclassre = re.compile(r"\\documentclass(\[[^]]*\])?({[^}]*})")
    documentclasses = documentclassre.findall(latex)
    if len(documentclasses) == 0:
        print("Coildn't find documentclass maybe not latex", file=sys.stderr)
        sys.exit(1)
    elif len(documentclasses) > 1:
        print("Found too many documentclasses", file=sys.stderr)
        sys.exit(1)
    # headings
    documentclass = documentclasses[0][1]
    dcoptions = documentclass[0][0]
    latex = documentclassre.sub("", latex)
    usepackagere = re.compile(r"\\usepackage(\[[^]]*\])?{([^}]*)}")
    usepackages = usepackagere.findall(latex)
    usedpackages = []
    for usepackage in usepackages:
        usedpackages.append(usepackage[1])
    latex = usepackagere.sub("", latex)
    # no programming and macros
    newcommandre = re.compile(r"\\newcommand\\([^{]*){.*}")
    latex = newcommandre.sub(r"<!-- new command \1 -->", latex)
    # contents
    # need some tracking for labels and refs
    # then cites and bibstuff
    labelre = re.compile(r"\\label{([^}]*)}")
    labels = labelre.findall(latex)
    labelmap = {}
    labelcount = 1
    for label in labels:
        if label in labelmap:
            print(f"Duplicate label {label}! References may fail",
                  file=sys.stderr)
        else:
            labelmap[label] = "LABEL " + label
            labelcount = labelcount + 1
    latex = labelre.sub("<a id=\"\\1\">(¶ \\1)</a>", latex)
    refre = re.compile(r"\\ref{([^}]*)}")
    refs = refre.findall(latex)
    for ref in refs:
        if ref not in labelmap:
            print(f"ref to missing label {ref}, generating borken links",
                  file=sys.stderr)
    latex = refre.sub("[(see: \\1)](#\\1)", latex)
    # bibliographies... absolute first fist
    bibliographyre = re.compile(r"\\bibliography{([^}]*)}")
    bibs = bibliographyre.findall(latex)
    bibmap = {}
    for bib in bibs:
        bibmap.update(readbib(relpath, bib))
    citere = re.compile(r"\\cite{([^}]*)}")
    cites = citere.findall(latex)
    usedbibs = {}
    for citestr in cites:
        for cite in citestr.split(","):
            if cite in bibmap:
                usedbibs[cite] = bibmap[cite]
            else:
                print(f"bib data for {cite} missing, generating broken "
                      "citation", file=sys.stderr)
                usedbibs[cite] = {"error": "missing from bibliography"}
    latex = citere.sub("[(cites: \\1)](#\\1)", latex)
    bibcontent = "# References\n\n"
    # no support for bibliography styles, we just dump all available data
    bibliographystylere = re.compile(r"\\bibliographystyle{([^}]*)}")
    latex = bibliographystylere.sub(r"<!-- bib style: \1 -->", latex)
    for key, bib in usedbibs.items():
        bibcontent += f"* <a id=\"{key}\">**{key}**</a>:\n"
        for k, v in bib.items():
            if len(v) > 60:
                v = v[:60] + "..."
            bibcontent += f"    * {k}: {v}\n"
    latex = bibliographyre.sub(bibcontent, latex)
    # smallest local things first: chars and codes
    latex = latex.replace("\\\\",
                          "<!-- LINEBREAK -->")  # should be linebreak but but
    latex = latex.replace("``", "“")
    latex = latex.replace("''", "”")
    latex = latex.replace("`", "‘")
    latex = latex.replace("'", "’")
    latex = latex.replace("~", " ")
    latex = latex.replace("\\ ", " ")   # FIXME: other space?
    latex = latex.replace("\\\"{o}", "ö")
    latex = latex.replace("\\\"{a}", "ä")
    latex = latex.replace("\\ng", "ŋ")
    # tabulars...
    tabularre = re.compile(r" *\\begin{tabular}.*?\\end{tabular}",
                           re.MULTILINE | re.DOTALL)
    tabulars = tabularre.findall(latex)
    tablecontent = ""
    for tabular in tabulars:
        tablecontent = tabular
        tablecontent = tablecontent.lstrip()
        tablecontent = tablecontent.replace(r"\begin{tabular}", "")
        tablecontent = tablecontent.replace(r"\end{tabular}", "")
        if tablecontent.startswith("["):
            tablecontent = tablecontent[tablecontent.find("]", 1)+1:]
        columns = 0
        if tablecontent.startswith("{"):
            columnstr = tablecontent[1:tablecontent.find("}", 1)]
            columns = columns + columnstr.count("l")
            columns = columns + columnstr.count("r")
            columns = columns + columnstr.count("c")
            columns = columns + columnstr.count("p")
            tablecontent = tablecontent[tablecontent.find("}", 1)+1:]
        linerule = "|"
        linerule = linerule + (" ---- |" * columns)
        tablefinal = ""
        for line in tablecontent.split("\n"):
            line = line.lstrip()
            if "&" in line:
                line = "| " + line.replace("&", " | ")
            if "<!-- LINEBREAK -->" in line:
                line = line.replace("<!-- LINEBREAK -->", "|")
            line = line.replace("\\toprule", "")
            if "\\midrule" in line:
                line = line.replace("\\midrule", linerule)
                linerule = ""
            line = line.replace("\\bottomrule", "")
            if "\\hline" in line:
                line = line.replace("\\hline", linerule)
                linerule = ""
            if line.strip() == "":
                continue
            else:
                tablefinal += line + "\n"
        latex = latex.replace(tabular, "\n\n" + tablefinal)

    # small local things first
    mathre = re.compile(r"\$([^$]*)\$")
    latex = mathre.sub(r"<span class='math'>\1</span>", latex)
    textttre = re.compile(r"\\texttt{([^}]*)}", re.MULTILINE)
    latex = textttre.sub(r"`\1`", latex)
    textbfre = re.compile(r"\\textbf{([^}]*)}", re.MULTILINE)
    latex = textbfre.sub(r"**\1**", latex)
    textitre = re.compile(r"\\textit{([^}]*)}", re.MULTILINE)
    latex = textitre.sub(r"*\1*", latex)
    textscre = re.compile(r"\\textsc{([^}]*)}", re.MULTILINE)
    latex = textscre.sub(r"<span style='font-variant: small-caps'>\1</span>",
                         latex)
    urlre = re.compile(r"\\url{([^}]*)}", re.MULTILINE)
    latex = urlre.sub(r"<\1>", latex)
    footnotere = re.compile(r"\\footnote{([^}]*)}", re.MULTILINE)
    latex = footnotere.sub(r" (footnote: \1)", latex)
    textcolorre = re.compile(r"\\textcolor{([^}]*)}{([^}]*)}", re.MULTILINE)
    latex = textcolorre.sub(r"<span style='color: \1'>\2</span>", latex)
    latex = latex.replace("\\appendix", "* * *\n\n# Appendix\n")
    captionre = re.compile(r"\\caption{([^}]*)}", re.MULTILINE)
    latex = captionre.sub(r" (Caption: \1)", latex)
    definecolorre = re.compile(r"\\definecolor{([^}]*)}{([^}]*)}{([^}]*)}")
    latex = definecolorre.sub(r"<!-- definecolor \1 \2 \3 -->", latex)
    # flammie specific
    aappdre = re.compile(r"\\aclanthologypostprintdoi{([^}]*)}")
    latex = aappdre.sub("Publisher’s version available at [ACL Anthology "
                        r"identifier: \1](https://aclanthology.org/\1). "
                        "All modern "
                        "ACL conferences are open access usually CC BY",
                        latex)
    springerre = re.compile(r"\\springerpostprintdoi{([^}]*)}")
    latex = springerre.sub("Publisher’s version available at [Springer via "
                           r"doi: \1](https://dx.doi.org/\1). For more "
                           "information, see [Springers self archiving "
                           "policy]"
                           "(http://www.springer.com/gp/open-access/"
                           "authors-rights/self-archiving-policy/2124).",
                           latex)
    fnprre = re.compile(r"\\footnotepubrights{([^}]*)}", re.MULTILINE)
    latex = fnprre.sub("¹\n§TITLEFOOTNOTE§"
                       "<span style='font-size:8pt'>(¹ Authors' archival "
                       r"version: \1)</span>", latex)
    # also my stuff
    gecfail = re.compile(r"\\gecfail{([^}]*)}")
    latex = gecfail.sub(r"<span style='text-decoration-line: "
                        r"grammar-error'>\1</span>",
                        latex)
    spellfail = re.compile(r"\\mispelt{([^}]*)}")
    latex = spellfail.sub(r"<span style='text-decoration-line: "
                          r"spelling-error'>\1</span>",
                          latex)
    # includegraphics...
    # \includegraphics[width=.5\textwidth]{syntaxflow.png}
    includegraphicsre = re.compile(r"\\includegraphics(\[[^]]*\])?{([^}]*)}")
    latex = includegraphicsre.sub(r"![\2](\2)", latex)
    # Linguistics
    latex = latex.replace("\\ex.", "**Linguistic examples:**\n\n")
    latex = latex.replace("\\exg.", "**Linguistic example group:**\n\n")
    latex = latex.replace("\\ag.", "a. ")
    latex = latex.replace("\\b.", "b. ")
    # tcolorbox
    tcolorboxre = re.compile(r"\\begin{tcolorbox}"
                             r"\s*\[([^]]*)\](.*?)"
                             r"\\end{tcolorbox}", re.MULTILINE | re.DOTALL)
    latex = tcolorboxre.sub(r"<div style='border: black solid 5px;"
                            r" background-color: gray'>\2</div>", latex)
    # even more simple stuffs
    latex = latex.replace("\\begin{document}", "<!-- begin document -->")
    latex = latex.replace("\\end{document}", "<!-- end document -->")
    latex = latex.replace("\\maketitle", "<!-- make title -->")
    latex = latex.replace("\\begin{abstract}", "\n**Abstract:**")
    latex = latex.replace("\\end{abstract}", "<!-- end abstract -->")
    latex = latex.replace("\\begin{figure}", "\n**Figure:**")
    latex = latex.replace("\\begin{figure*}", "\n**Figure:**")
    latex = latex.replace("\\end{figure}", "<!-- end figure -->")
    latex = latex.replace("\\end{figure*}", "<!-- end figure* -->")
    latex = latex.replace("\\begin{table}", "\n**Table:**")
    latex = latex.replace("\\begin{table*}", "\n**Table:**")
    latex = latex.replace("\\end{table}", "<!-- end table -->")
    latex = latex.replace("\\end{table*}", "<!-- end table* -->")
    latex = latex.replace("\\begin{verbatim}", "\n```\n")
    latex = latex.replace("\\end{verbatim}", "\n```\n")
    latex = latex.replace("\\centering", "<!-- centering -->")
    latex = latex.replace("\\and", "\nand\n\n")
    # things that cannot be handled properly
    latex = latex.replace("\\small", "<!-- small -->")
    latex = latex.replace("\\scriptsize", "<!-- scriptsize -->")
    latex = latex.replace("\\bf", "<!-- bf -->")
    # lists
    itemizere = re.compile(r"\\begin{itemize}.*?\\end{itemize}",
                           re.MULTILINE | re.DOTALL)
    itemizes = itemizere.findall(latex)
    itemizecontent = ""
    for itemize in itemizes:
        itemizecontent = itemize
        itemizecontent = itemizecontent.replace(r"\begin{itemize}", "")
        itemizecontent = itemizecontent.replace(r"\end{itemize}", "")
        itemizecontent = itemizecontent.replace(r"\item ", "* ")
        latex = latex.replace(itemize, itemizecontent)
    enumeratere = re.compile(r"\\begin{enumerate}.*?\\end{enumerate}",
                             re.MULTILINE | re.DOTALL)
    enumerates = enumeratere.findall(latex)
    enumeratecontent = ""
    for enumrate in enumerates:
        enumeratecontent = enumrate
        enumeratecontent = enumeratecontent.replace(r"\begin{enumerate}", "")
        enumeratecontent = enumeratecontent.replace(r"\end{enumerate}", "")
        enumeratecontent = enumeratecontent.replace(r"\item ", "1. ")
        latex = latex.replace(enumrate, enumeratecontent)
    enumstarre = re.compile(r"\\begin{enumerate\*}.*?\\end{enumerate\*}",
                            re.MULTILINE | re.DOTALL)
    enumstars = enumstarre.findall(latex)
    enumstarcontent = ""
    for enumstar in enumstars:
        enumstarcontent = enumstar
        enumstarcontent = enumstarcontent.replace(r"\begin{enumerate*}", "")
        enumstarcontent = enumstarcontent.replace(r"\end{enumerate*}", "")
        enumstarcontent = enumstarcontent.replace(r"\item ", " ")
        latex = latex.replace(enumstar, enumstarcontent)
    # stuffs
    sectionre = re.compile(r"\\section{([^}]*)}", re.MULTILINE)
    latex = sectionre.sub(r"## \1", latex)
    subsectionre = re.compile(r"\\subsection{([^}]*)}", re.MULTILINE)
    latex = subsectionre.sub(r"### \1", latex)
    subsubsectionre = re.compile(r"\\subsubsection{([^}]*)}", re.MULTILINE)
    latex = subsubsectionre.sub(r"#### \1", latex)
    sectionre = re.compile(r"\\section\*{([^}]*)}", re.MULTILINE)
    latex = sectionre.sub(r"## \1", latex)
    subsectionre = re.compile(r"\\subsection\*{([^}]*)}", re.MULTILINE)
    latex = subsectionre.sub(r"### \1", latex)
    subsubsectionre = re.compile(r"\\subsubsection\*{([^}]*)}", re.MULTILINE)
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
    latex = latex.replace("§TITLEFOOTNOTE§", "\n\n")
    authorre = re.compile(r"\\author{([^}]*)}", re.MULTILINE)
    latex = authorre.sub(r"**Authors:** \1", latex)
    # final fixes
    # I don't use the indent as codeblock markup so de-indenting most stuff
    # will fix those problems (retain nested lists maybe?)
    chompre = re.compile(r"^[ \t]*(\*\*|<!--|\(Caption|\w|!\[)",
                         re.MULTILINE)
    latex = chompre.sub(r"\1", latex)
    latex = latex.replace(".\\@", ".")   # inter sent spacing
    latex = latex.replace(".\\", ".")   # inter sent spacing
    latex = latex.replace("<!-- LINEBREAK -->", "\n")
    latex = latex.replace("\\textbackslash", "\\")
    latex = latex.replace("{}", "")  # I use empty {} as command terminator
    markdown = latex
    markdown = markdown + "\n* * *\n\n" + \
        "<span style='font-size: 8pt'>Converted with [Flammie’s " + \
        "latex2markdown](https://github.com/flammie/latex2markdown) v." + \
        "0.1.0</span>\n"  # FIXME: get version somewhere
    print(markdown, file=opts.outfile)


if __name__ == "__main__":
    main()

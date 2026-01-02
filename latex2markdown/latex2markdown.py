#!/usr/bin/env python3
"""Simple converter from latex papers to github pages markdowns."""

import os
import re
import sys
from argparse import ArgumentParser, FileType
from datetime import datetime


def readbibs(relpath: str, bibfiles: str) -> dict():
    """Read multiple bibfiels."""
    bibmap = {}
    for bibfile in bibfiles.split(","):
        bibmap.update(readbib(relpath, bibfile))
    return bibmap

def readbib(relpath: str, bibfile: str) -> dict():
    """Read bibfile into a map of maps."""
    with open(os.path.join(relpath, bibfile + ".bib")) as f:
        curkey = None
        bib = {}
        for line in f:
            line = line.strip()
            # early fix
            line = line.replace(r"\=u", "ū")
            line = line.replace(r"\= u", "ū")
            line = line.replace(r"\=e", "ē")
            line = line.replace(r"\= e", "ē")
            line = line.replace(r"\=\i", "ī")
            line = line.replace(r"\= \i", "ī")
            line = line.replace(r"\=", "¯")
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
                # fix escapes here already, there's more crap in bib than tex
                forcecapsre = re.compile(r"{([A-Z]{1,6})}")
                stuff = forcecapsre.sub(r"\1", stuff)
                stuff = stuff.replace(r"{\'a}", "á")
                stuff = stuff.replace(r"{\'c}", "ć")
                stuff = stuff.replace(r"{\'e}", "é")
                stuff = stuff.replace(r"{\'\i}", "í")
                stuff = stuff.replace(r"{\'o}", "ó")
                stuff = stuff.replace(r"{\'s}", "ś")
                stuff = stuff.replace(r"{\'u}", "ú")
                stuff = stuff.replace(r"{\'y}", "ý")
                stuff = stuff.replace(r"{\`a}", "à")
                stuff = stuff.replace(r"{\`e}", "è")
                stuff = stuff.replace(r"{\`o}", "ò")
                stuff = stuff.replace(r"{\"a}", "ä")
                stuff = stuff.replace(r"{\"{\i}}", "ï")
                stuff = stuff.replace(r"\"{o}", "ö")
                stuff = stuff.replace(r"{\"o}", "ö")
                stuff = stuff.replace(r"{\"O}", "Ö")
                stuff = stuff.replace(r"{\"u}", "ü")
                stuff = stuff.replace(r"{\: u}", "ü")
                stuff = stuff.replace(r"{\o}", "ø")
                stuff = stuff.replace(r"{\ae}", "æ")
                stuff = stuff.replace(r"{\aa}", "å")
                stuff = stuff.replace(r"\&", "&")
                stuff = stuff.replace(r"{\ss}", "ß")
                stuff = stuff.replace(r"{\ug}", "ǧ")
                stuff = stuff.replace(r"{\vr}", "ř")
                stuff = stuff.replace(r"{\vs}", "š")
                stuff = stuff.replace(r"{\v Z}", "Ž")
                stuff = stuff.replace(r"{\v c}", "č")
                stuff = stuff.replace(r"{\v s}", "š")
                stuff = stuff.replace(r"\v{s}", "š")
                stuff = stuff.replace(r"{\=u}", "ū")
                stuff = stuff.replace(r"{\i}", "ı")
                stuff = stuff.replace(r"{\.e}", "ė")
                stuff = stuff.replace(r"{\l}", "ł")
                stuff = stuff.replace(r"{\cC}", "Ç")
                stuff = stuff.replace(r"{\cc}", "ç")
                stuff = stuff.replace(r"{\~a}", "ã")
                stuff = stuff.replace(r"{\~n}", "ñ")
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
    latex = usepackagere.sub(r"<!-- usepackage \2 \1 -->", latex)
    requirepackagere = re.compile(r"\\RequirePackage(\[[^]]*\])?{([^}]*)}")
    requirepackages = requirepackagere.findall(latex)
    for requirepackage in requirepackages:
        usedpackages.append(requirepackage[1])
    latex = requirepackagere.sub(r"<!-- RequirePackage \1 -->", latex)
    usetikzlibraryre = re.compile(r"\\usetikzlibrary(\[[^]]*\])?{([^}]*)}")
    latex = usetikzlibraryre.sub(r"<!-- usetikzlibrary \2 \1 -->", latex)
    # no programming and macros
    newcommandre = re.compile(r"\\newcommand\\([^{]*){.*}")
    latex = newcommandre.sub(r"<!-- new command \1 -->", latex)
    newcommandre = re.compile(r"\\newcommand{([^{]*)}{.*}")
    latex = newcommandre.sub(r"<!-- new command \1 -->", latex)
    renewcommandre = re.compile(r"\\renewcommand\*{([^]}]*)}{([^}]*)}")
    latex = renewcommandre.sub(r"<!-- renew command \1 \2 -->", latex)
    newifre = re.compile(r"\\newif\\(\w*)")
    latex = newifre.sub(r"<!-- new if \1 -->", latex)
    ifsomethingre = re.compile(r"\\if(\w*)")
    latex = ifsomethingre.sub(r"<!-- if \1 -->", latex)
    latex = latex.replace("\\fi", "<!-- fi -->")
    latex = latex.replace("\\makeatletter", "<!-- makeatletter -->")
    latex = latex.replace("\\makeatother", "<!-- makeatother -->")
    setlengthre = re.compile(r"\\setlength{([^{]*)}{([^}]*)}")
    latex = setlengthre.sub(r"<!-- set length \1 \2 -->", latex)
    setlengthstarre = re.compile(r"\\setlength\*{([^{]*)}{([^}]*)}")
    latex = setlengthstarre.sub(r"<!-- set length * \1 \2 -->", latex)
    setcounterre = re.compile(r"\\setcounter{([^{]*)}{([^}]*)}")
    latex = setcounterre.sub(r"<!-- set counter \1 \2 -->", latex)
    setmainlanguagere = re.compile(r"\\setmainlanguage(\[[^]]*\])?{([^}]*)}")
    latex = setmainlanguagere.sub(r"<!-- set main language \2 \1 -->", latex)
    setotherlanguagesre = re.compile(r"\\setotherlanguages{([^}]*)}")
    latex = setotherlanguagesre.sub(r"<!-- set main language \1 -->", latex)
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
        bibmap.update(readbibs(relpath, bib))
    citere = re.compile(r"\\cite[tp]?(\[[^]]*\])?{([^}]*)}")
    cites = citere.findall(latex)
    usedbibs = {}
    for citegroup in cites:
        for cite in citegroup[1].split(","):
            if cite in bibmap:
                usedbibs[cite] = bibmap[cite]
            else:
                print(f"bib data for {cite} missing, generating broken "
                      "citation", file=sys.stderr)
                usedbibs[cite] = {"error": "<strong style=\"color: red\">"
                                           "missing from bibs"
                                           "</strong>"}
    latex = citere.sub("[(cites: \\2\\1)](#\\2)", latex)
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
    latex = bibliographyre.sub(bibcontent.replace("\\", "\\\\"), latex)
    # hand-written bibs eww
    latex = latex.replace(r"\begin{thebibliography}", "# References")
    latex = latex.replace(r"\bibitem", "* ")
    # smallest local things first: chars and codes
    latex = latex.replace("\\\\",
                          "<!-- LINEBREAK -->")  # should be linebreak but but
    latex = latex.replace("``", "“")
    latex = latex.replace("''", "”")
    latex = latex.replace("`", "‘")
    latex = latex.replace("'", "’")
    latex = latex.replace("~", " ")
    latex = latex.replace("\\ ", " ")   # FIXME: other space?
    latex = latex.replace("\\qquad", " ")   # FIXME: other space?
    latex = latex.replace("\\\"{u}", "ü")
    latex = latex.replace("{\\\"u}", "ü")
    latex = latex.replace("\\\"{o}", "ö")
    latex = latex.replace("\\\"{a}", "ä")
    latex = latex.replace("\\\v{s}", "š")
    latex = latex.replace("\\ng", "ŋ")
    latex = latex.replace("\\ldots", "...")
    latex = latex.replace("\\textyen", "¥")
    latex = latex.replace("\\textless", "<")
    latex = latex.replace("\\textgreater", ">")
    latex = latex.replace("\\star", "★")
    latex = latex.replace("\\dag", "†")
    latex = latex.replace("\\ddag", "‡")
    latex = latex.replace("\\natural", "♮")
    latex = latex.replace("\\TeX", "TeX")
    # theoretically only math symbols but I see no harm in replace everything
    latex = latex.replace("\\cdot", "⋅")
    latex = latex.replace("\\emptyset", "∅")
    latex = latex.replace("\\Rightarrow", "→")
    latex = latex.replace("\\rightarrow", "⇒")
    latex = latex.replace("\\Leftarrow", "←")
    latex = latex.replace("\\leftarrow", "⇐")
    # Alpha (Α, ), Beta (Β, ), Gamma (, ), Delta (Δ, ), Epsilon (Ε, ), Zeta (Ζ, ζ), Eta (Η, η), Theta (Θ, θ), Iota (Ι, ι), Kappa (Κ, κ), Lambda (Λ, λ), Mu (Μ, μ), Nu (Ν, ν), Xi (Ξ, ξ), Omicron (Ο, ο), Pi (Π, π), Rho (Ρ, ), Sigma (, σ, ς), Tau (Τ, τ), Upsilon (Υ, υ), Phi (Φ, φ), Chi (Χ, χ), Psi (Ψ, ψ), and Omega (Ω, ω)
    latex = latex.replace("\\alpha", "α")
    latex = latex.replace("\\beta", "β")
    latex = latex.replace("\\gamma", "γ")
    latex = latex.replace("\\Gamma", "Γ")
    latex = latex.replace("\\delta", "δ")
    latex = latex.replace("\\epsilon", "ε")   # FIXME
    latex = latex.replace("\\varepsilon", "ε")   # FIXME
    latex = latex.replace("\\rho", "ρ")
    latex = latex.replace("\\Sigma", "Σ")
    # math symbs
    latex = latex.replace("\\times", "×")
    latex = latex.replace("\\prime", "′")
    latex = latex.replace("\\circ", "•")
    latex = latex.replace("\\diamond", "♢")
    latex = latex.replace("\\sim", "∽")
    latex = latex.replace("\\bigcup", "⋃")
    latex = latex.replace("\\cup ", "∪")
    latex = latex.replace("\\cap ", "∩")
    latex = latex.replace("\\bigcap", "⋂")
    latex = latex.replace("\\in ", "∈ ")
    latex = latex.replace("\\notin", "∉")
    latex = latex.replace("\\subseteq", "⊆")
    latex = latex.replace("\\subset", "⊂")
    latex = latex.replace("\\mathcal{L}", "𝓛")
    latex = latex.replace("\\mathcal{R}", "𝓡")
    latex = latex.replace("\\mathcal{M}", "𝓜")
    latex = latex.replace("\\mathcal{F}", "𝓕")
    latex = latex.replace("_{x}", "ₓ")
    # tabulars...
    multicolre = re.compile(r"\\multicolumn{([^}]*)}{([^}]*)}")
    latex = multicolre.sub(r"| <!-- FIXME: multicolumn \1 \2 -->", latex)
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
            line = line.replace("\\hrule", "")
            if line.strip() == "":
                continue
            else:
                tablefinal += line + "\n"
        latex = latex.replace(tabular, "\n\n" + tablefinal)
    tabularxre = re.compile(r" *\\begin{tabularx}.*?\\end{tabularx}",
                            re.MULTILINE | re.DOTALL)
    tabularxs = tabularxre.findall(latex)
    tablecontent = ""
    for tabularx in tabularxs:
        tablecontent = tabularx
        tablecontent = tablecontent.lstrip()
        tablecontent = tablecontent.replace(r"\begin{tabularx}", "")
        tablecontent = tablecontent.replace(r"\end{tabularx}", "")
        if tablecontent.startswith("{"):
            tablecontent = tablecontent[tablecontent.find("}", 1)+1:]
        columns = 0
        if tablecontent.startswith("{"):
            columnstr = tablecontent[1:tablecontent.find("}", 1)]
            columns = columns + columnstr.count("l")
            columns = columns + columnstr.count("r")
            columns = columns + columnstr.count("c")
            columns = columns + columnstr.count("p")
            columns = columns + columnstr.count("X")
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
        latex = latex.replace(tabularx, "\n\n" + tablefinal)
    # all items that are "outside" environments just turn into list items
    latex = latex.replace("\\item", "* ")
    # small local things first
    mathre = re.compile(r"\$([^$]*)\$")
    latex = mathre.sub(r"<span class='math'>\1</span>", latex)
    latex = latex.replace(r"\(", "<span class='math'>")
    latex = latex.replace(r"\)", "</span>")
    latex = latex.replace(r"\[", "<div class='math'>")
    latex = latex.replace(r"\]", "</div>")
    verbpipere = re.compile(r"\\verb\|([^|]*)\|")
    latex = verbpipere.sub(r"`\1`", latex)
    urlre = re.compile(r"\\url{([^}]*)}", re.MULTILINE)
    latex = urlre.sub(r"<\1>", latex)
    hrefre = re.compile(r"\\href{([^}]*)}{([^}]*)}", re.MULTILINE)
    latex = hrefre.sub(r"[\2](\1)", latex)
    textttre = re.compile(r"\\texttt{([^}]*)}", re.MULTILINE)
    latex = textttre.sub(r"`\1`", latex)
    textbfre = re.compile(r"\\textbf{([^}]*)}", re.MULTILINE)
    latex = textbfre.sub(r"**\1**", latex)
    textitre = re.compile(r"\\textit{([^}]*)}", re.MULTILINE)
    latex = textitre.sub(r"*\1*", latex)
    emphre = re.compile(r"\\emph{([^}]*)}", re.MULTILINE)
    latex = emphre.sub(r"*\1*", latex)
    textscre = re.compile(r"\\textsc{([^}]*)}", re.MULTILINE)
    latex = textscre.sub(r"<span style='font-variant: small-caps'>\1</span>",
                         latex)
    footnotere = re.compile(r"\\footnote{([^}]*)}", re.MULTILINE)
    latex = footnotere.sub(r" (footnote: \1)", latex)
    textcolorre = re.compile(r"\\textcolor{([^}]*)}{([^}]*)}", re.MULTILINE)
    latex = textcolorre.sub(r"<span style='color: \1'>\2</span>", latex)
    latex = latex.replace("\\appendix", "* * *\n\n# Appendix\n")
    captionre = re.compile(r"\\caption{([^}]*)}", re.MULTILINE)
    latex = captionre.sub(r" (Caption: \1)", latex)
    underlinere = re.compile(r"\\underline{([^}]*)}", re.MULTILINE)
    latex = underlinere.sub(r"<span style='text-underline: thin black single'>"
                            r"\1**</span>", latex)
    definecolorre = re.compile(r"\\definecolor{([^}]*)}{([^}]*)}{([^}]*)}")
    latex = definecolorre.sub(r"<!-- definecolor \1 \2 \3 -->", latex)
    hyphenationre = re.compile(r"\\hyphenation{([^}]*)}")
    latex = hyphenationre.sub(r"<!-- hyphenation \1 -->", latex)
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
    spellfail = re.compile(r"\\misspelt{([^}]*)}")
    latex = spellfail.sub(r"<span style='text-decoration-line: "
                          r"spelling-error'>\1</span>",
                          latex)
    # includegraphics...
    # \includegraphics[width=.5\textwidth]{syntaxflow.png}
    includegraphicsre = re.compile(r"\\includegraphics(\[[^]]*\])?{([^}]*)}")
    latex = includegraphicsre.sub(r"![\2](\2)", latex)
    scaleboxre = re.compile(r"\\scalebox{([^}]*)}(\[[^]]*\])?{([^}]*)}")
    latex = scaleboxre.sub(r"<!-- scalebox \1 \2 -->\n\3", latex)
    # Linguistics
    latex = latex.replace("\\ex.", "**Linguistic examples:**\n\n")
    latex = latex.replace("\\exg.", "**Linguistic example group:**\n\n")
    latex = latex.replace("\\ag.", "a. ")
    latex = latex.replace("\\b.", "b. ")
    pexre = re.compile(r"\\pex&lt;([^&]*)&gt;")
    latex = pexre.sub(r"**Linguistic example group \1:**\n\n", latex)
    expexare = re.compile(r"^\\a$", re.MULTILINE)
    latex = expexare.sub("<!-- a -->", latex)
    latex = latex.replace("\\begingl", "<!-- begingl -->")
    latex = latex.replace("\\gla ", "* surface: ")
    latex = latex.replace("\\glb ", "* glosses: ")
    latex = latex.replace("\\glft ", "* free translation: ")
    latex = latex.replace("\\endgl", "<!-- endgl -->")
    latex = latex.replace("\\xe", "<!-- /xe -->")
    # algorithmic
    latex = latex.replace("\\begin{algorithmic}", "<!-- algoritmic -->")
    latex = latex.replace("\\end{algorithmic}", "<!-- /algoritmic -->")
    latex = latex.replace("\\STATE ", "1. ")
    latex = latex.replace("\\FORALL", "1. FOR ∀ { ")
    latex = latex.replace("\\ENDFOR", "1. ENDFOR }")
    latex = latex.replace("\\IF ", "1. IF { ")
    latex = latex.replace("\\ELSE ", "1. } ELSE { ")
    latex = latex.replace("\\ENDIF ", "1. ENDIF } ")
    latex = latex.replace("\\COMMENT", "1. // ")
    # tcolorbox
    tcolorboxre = re.compile(r"\\begin{tcolorbox}"
                             r"\s*\[([^]]*)\](.*?)"
                             r"\\end{tcolorbox}", re.MULTILINE | re.DOTALL)
    latex = tcolorboxre.sub(r"<div style='border: black solid 5px;"
                            r" background-color: lightgray; color: black'>"
                            r"\2</div>", latex)
    # even more simple stuffs
    latex = latex.replace("\\begin{document}", "<!-- begin document -->")
    latex = latex.replace("\\end{document}", "<!-- end document -->")
    latex = latex.replace("\\maketitle", "<!-- make title -->")
    latex = latex.replace("\\begin{abstract}", "\n**Abstract:**")
    latex = latex.replace("\\abstract{", "\n**Abstract:**")
    latex = latex.replace("\\end{abstract}", "<!-- end abstract -->")
    latex = latex.replace("\\begin{algorithm}", "\n**Algorithm:**")
    latex = latex.replace("\\end{algorith}", "<!-- end figure -->")
    latex = latex.replace("\\begin{figure}", "\n**Figure:**")
    latex = latex.replace("\\end{figure}", "<!-- end figure -->")
    latex = latex.replace("\\begin{figure*}", "\n**Figure:**")
    latex = latex.replace("\\end{figure*}", "<!-- end figure* -->")
    latex = latex.replace("\\begin{table}", "\n**Table:**")
    latex = latex.replace("\\begin{table*}", "\n**Table:**")
    latex = latex.replace("\\end{table}", "<!-- end table -->")
    latex = latex.replace("\\end{table*}", "<!-- end table* -->")
    latex = latex.replace("\\begin{verbatim}", "\n```\n")
    latex = latex.replace("\\end{verbatim}", "\n```\n")
    latex = latex.replace("\\begin{Verbatim}", "\n```\n")
    latex = latex.replace("\\end{Verbatim}", "\n```\n")
    latex = latex.replace("\\begin{lstlisting}", "\n```\n")
    latex = latex.replace("\\end{lstlisting}", "\n```\n")
    latex = latex.replace("\\begin{tikzpicture}", "\n```tikz\n")
    latex = latex.replace("\\end{tikzpicture}", "\n```\n")
    latex = latex.replace("\\begin{small}", "<div style='font-size: small'>")
    latex = latex.replace("\\end{small}", "</div>")
    latex = latex.replace("\\begin{tiny}", "<div style='font-size: x-small'>")
    latex = latex.replace("\\end{tiny}", "</div>")
    latex = latex.replace("\\begin{scriptsize}",
                          "<div style='font-size: xx-small'>")
    latex = latex.replace("\\end{scriptsize}", "</div>")
    latex = latex.replace("\\begin{center}",
                          "<div style='text-align: center'>")
    latex = latex.replace("\\end{center}", "</div>")
    latex = latex.replace("\\begin{centering}",
                          "<div style='text-align: center'>")
    latex = latex.replace("\\end{centering}", "</div>")
    latex = latex.replace("\\begin{equation}",
                          "<div class='math'>")
    latex = latex.replace("\\end{equation}", "</div>")
    latex = latex.replace("\\begin{equnarray}",
                          "**Equations:**\n<div class='math'>")
    latex = latex.replace("\\end{eqnarray}", "</div>")
    latex = latex.replace("\\begin{displaymath}",
                          "<div class='math'>")
    latex = latex.replace("\\end{displaymath}", "</div>")
    latex = latex.replace("\\centering", "<!-- centering -->")
    latex = latex.replace("\\and", "\nand\n\n")
    # languages in multilingual docs
    latex = latex.replace("\\begin{english}", "<span xml:lang=\"en\">")
    latex = latex.replace("\\end{english}", "</span>")
    selectlanguagere = re.compile(r"\\selectlanguage{([^}]*)}")
    latex = selectlanguagere.sub(r"<!-- select language \1 -->", latex)
    # things that cannot be handled properly...
    # these are kind of trigger commands that change whole rest of the "block"
    # figuring out where the block ends is a hard problem
    latex = latex.replace("\\smaller", "<!-- smaller -->")
    latex = latex.replace("\\small", "<!-- small -->")
    latex = latex.replace("\\scriptsize", "<!-- scriptsize -->")
    latex = latex.replace("\\footnotesize", "<!-- footnotesize -->")
    latex = latex.replace("\\bfseries ", "<!-- bfseries -->")
    latex = latex.replace("\\bf ", "<!-- bf -->")
    latex = latex.replace("\\it ", "<!-- it -->")
    latex = latex.replace("\\tt ", "<!-- tt -->")
    # layout nonsense
    minipagere = re.compile(r"\\begin{minipage}{([^}]*)}")
    latex = minipagere.sub(r"<!-- minipage \1 -->", latex)
    latex = latex.replace("\\end{minipage}", "<!-- /minipage -->")
    multicolsre = re.compile(r"\\begin{multicols}{([^}]*)}")
    latex = multicolsre.sub(r"<!-- multicols \1 -->", latex)
    latex = latex.replace("\\end{multicols}", "<!-- /multicols -->")
    # useless tweaks (in markdown / html context)
    latex = latex.replace("\\relax", "<!-- relax -->")
    latex = latex.replace("\\noindent", "<!-- no indent -->")
    latex = latex.replace("\\newpage", "<!-- new page -->")
    vspacere = re.compile(r"\\vspace{([^}]*)}")
    latex = vspacere.sub(r"<!-- vspace \1 -->", latex)
    hspacere = re.compile(r"\\hspace{([^}]*)}")
    latex = hspacere.sub(r"<!-- hspace \1 -->", latex)
    pagestylere = re.compile(r"\\pagestyle{([^}]*)}")
    latex = pagestylere.sub(r"<!-- pagestyle \1 -->", latex)
    thispagestylere = re.compile(r"\\thispagestyle{([^}]*)}")
    latex = thispagestylere.sub(r"<!-- thispagestyle \1 -->", latex)
    linespreadre = re.compile(r"\\linespread{([^}]*)}")
    latex = linespreadre.sub(r"<!-- linespread \1 -->", latex)
    defaultfontfeaturesre = re.compile(r"\\defaultfontfeatures{([^}]*)}")
    latex = defaultfontfeaturesre.sub(r"<!-- default font feat \1 -->", latex)
    setmainfontre = re.compile(r"\\setmainfont(\[[^]]*\])?{([^}]*)}")
    latex = setmainfontre.sub(r"<!-- set main font \2 \1 -->", latex)
    setlistre = re.compile(r"\\setlist(\[[^]]*\])?{([^}]*)}")
    latex = setlistre.sub(r"<!-- set list \2 \1 -->", latex)
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
    chapterre = re.compile(r"\\chapter{([^}]*)}", re.MULTILINE)
    latex = chapterre.sub(r"# \1", latex)
    sectionre = re.compile(r"\\section{([^}]*)}", re.MULTILINE)
    latex = sectionre.sub(r"## \1", latex)
    subsectionre = re.compile(r"\\subsection{([^}]*)}", re.MULTILINE)
    latex = subsectionre.sub(r"### \1", latex)
    subsubsectionre = re.compile(r"\\subsubsection{([^}]*)}", re.MULTILINE)
    latex = subsubsectionre.sub(r"#### \1", latex)
    chapterre = re.compile(r"\\chapter\*{([^}]*)}", re.MULTILINE)
    latex = chapterre.sub(r"# \1", latex)
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
        print("Couldn't find title maybe not document:")
        print(latex)
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
    datere = re.compile(r"\\date{([^}]*)}")
    latex = datere.sub(r"**Date:** \1", latex)
    latex = latex.replace(r"\today", "(date of conversion: " +
                          datetime.today().strftime("%Y-%m-%d") + ")")
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
    latex = latex.replace("| ----", "§TR§")
    latex = latex.replace("<!--", "§SGMLCOMMENT§")
    latex = latex.replace("-->", "§/SGMLCOMMENT§")
    latex = latex.replace("---", "—")
    latex = latex.replace("--", "–")
    latex = latex.replace("§SGMLCOMMENT§", "<!--")
    latex = latex.replace("§/SGMLCOMMENT§", "-->")
    latex = latex.replace("§TR§", "| ----")
    latex = latex.replace("{}", "")  # I use empty {} as command terminator
    markdown = latex
    markdown = markdown + "\n* * *\n\n" + \
        "<span style='font-size: 8pt'>Converted with [Flammie’s " + \
        "latex2markdown](https://github.com/flammie/latex2markdown) v." + \
        "0.1.0</span>\n"  # FIXME: get version somewhere
    print(markdown, file=opts.outfile)


if __name__ == "__main__":
    main()

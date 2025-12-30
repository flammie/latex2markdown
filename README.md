# latex2markdown

Hacky scripts to convert latex to markdown for gh pages use. This is like my
no nonsense replacement of [latexml]() which afaics aims to be more of a 100 %
implementation of latex for all uses but especially html conversions. Whereas
latexml is a perl-based functionality complete parser and compiler of latex
stuffs, latex2markdown implements exactly the latex commands I have used in my
texts so far, just abouts well enough to be able to convert them into markdown
and nothing else.

## Rationale

The purpose of this script is for converting [my](https://flammie.github.io)
academic articles in LaTeX format into markdown format for web viewing. The
purpose of this script is to be lightweight, single pass, search and replace
kind of hack to convert files. It is well known that TeX is a Turing complete
programming language that would require a full parser and compiler and infinite
passes to process the TeX file correctly to produce a beautiful document
printed on paper with book style formattings, most of the features here are
actually very irrelevant nowadays, 95 % of reading academic articles happens on
screen and PDF readers with 2+ column formats and numbered references and
footnotes instead of hyperlinks are just ridiculous.

### Goals and non-goals

* produce markdown creates readable github pages version of the article
* actually works in reasonable time
* doesn't totally crash with unrecognised macros, renewed commands and such
* doesn't take million hours to process large bibliographies
* no implementation for counting pages, references, labels, math blocks,
  sections; this is all relevant only for dead tree books
* no implementations for hundreds of pedantic ways of formatting cites and
  bibliographies
* no specialty footnotes, endnotes, side notes, aside notes
* no complicated tables, if it doesn't work as markdown table it'll probably
  linearise horribly
* no graphics programming with tikz and stuff
* no complicated programmatically generated content
* no maths, since markdown has no math support and html really neither, and
  anyone who reads papers in comp.ling. should be able to understand the linear
  TeX math codes just as well
* the resulting markdown code can easily be tweaked to fix remaining bugs and
  issues
* ...

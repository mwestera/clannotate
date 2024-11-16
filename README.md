# Clannotate: Simple command-line annotation tool (`textual` app).

It reads lines from a (.txt or .csv) file or pipe, starts an annotation interface, and finally (upon closing with `ctrl+c`) write pairs of a score (-1, 0 or 1) and a comment to `stdout`. Implements some keyboard shortcuts, and saves progress between different runs.

## Install

```bash
$ pip intall git+https://github.com/mwestera/clannotate
```

## Use

```bash
$ clannotate lines_to_annotate.txt > annotations.csv
```

Press `ctrl+c` when done (you can restart later, it saves progress), and it will write the results to the file. 

# Disclaimer

This repository (`krystophny/gcc-dev`) is a **personal research and
development meta-repository**. It exists to support the author's own
work on GCC's Fortran frontend, libgomp, and libgfortran. It is not
affiliated with, endorsed by, or sponsored by the GCC Steering
Committee, the Free Software Foundation, GNU, the author's employer,
or any other organisation.

## No warranty, no liability

The contents of this repository are provided **AS IS**, without
warranty of any kind, express or implied, including but not limited to
the warranties of merchantability, fitness for a particular purpose,
title, and non-infringement.

To the maximum extent permitted by applicable law, the author shall
not be liable for any direct, indirect, incidental, special,
exemplary, or consequential damages arising in any way out of the use,
inability to use, or reliance on the contents of this repository,
even if advised of the possibility of such damages.

The author makes **no representation or warranty** that any patch,
reproducer, build script, scanner output, provenance observation, or
note in this repository is correct, complete, current, fit for any
particular purpose, legally compliant in any specific jurisdiction,
or free from defects.

## Provenance observations are working notes, not legal conclusions

Files under `.provenance/`, `docs/provenance-research.md`, the
`scripts/provenance/` scanners, the `pr/<N>/` directories, and any
GitHub issue or commit message in this repository that discusses
"provenance", "imports", "attribution", "license", "trail gap",
"chain of custody", or similar terms are the author's **personal
working observations from automated similarity scans and manual
review**, not findings of fact, not legal opinions, and not
allegations of wrongdoing against any individual contributor,
maintainer, project, or organisation.

In particular:

- **Severity tags** like `[CRITICAL]`, `[HIGH]`, `[MEDIUM]`, `[LOW]`
  reflect the author's prioritisation of follow-up work on a scanner
  signal. They are **not** legal severity ratings, are not based on
  any external review, and should not be read as accusations.
- **Phrases** like "silent import", "silently adapted", "stripped
  header", "dropped license", "lacks attribution", "missing
  provenance note", "unattributed copy" describe the **output of a
  string-similarity scan and a partial header inspection**, not a
  finding of copyright infringement, license violation, or any other
  legal wrong. Many scanner hits are false positives (k-gram
  collisions, sibling imports of a common upstream, in-tree LICENSE
  files at a different path, language-standard boilerplate, valid
  FSF copyright assignment, etc.).
- **Author names, commit SHAs, dates, and email addresses** that
  appear in chain-of-custody narratives are drawn from public git
  history, public mailing-list archives, and public Bugzilla pages.
  Naming a contributor as the author of an import does **not** imply
  any allegation against that contributor; the author of the
  contribution has no obligation to ship attribution in any specific
  form, and many "trail gaps" are perfectly valid under the
  copyright-assignment policies that applied at contribution time.
- **The author's reading of upstream license terms** (e.g., "Apache-2.0
  WITH LLVM-exception is GPL-3-compatible") is the author's
  layperson's interpretation, not legal advice. Anyone relying on
  these classifications for distribution, packaging, or compliance
  decisions should obtain independent legal review.

## Bug reports, reproducers, attribution lines

Reproducer files under `pr/<N>/` follow the GCC testsuite convention
of including a `! Contributed by <reporter> <email>` line when a
testcase is derived from a Bugzilla report. Email addresses in those
lines are taken verbatim from the corresponding **public** Bugzilla
comment, where the reporter chose to publish them. Their inclusion
here is for attribution only and implies no endorsement, contact
authorisation, or relationship with the named individual.

If you are named in this repository and wish to be removed,
re-attributed, or have a description corrected, please open an issue
at <https://github.com/krystophny/gcc-dev/issues> or contact the
repository owner. Reasonable requests will be addressed promptly.

## External code and third-party content

This repository tracks only:

- The author's own work (patches, reproducers, notes, scripts, docs).
- Configuration and download/fetch scripts that point at canonical
  upstream sources. External source code itself is fetched into
  gitignored directories (`gcc/`, `corpusbin/`, `third_party/`) and
  is **not** redistributed from this repository.

If you believe any tracked file in this repository redistributes
content for which the author lacks the necessary rights, please
report it via the GitHub issue tracker so it can be removed or
re-licensed.

## License

This repository is licensed under the **GNU General Public License
version 3 or later** (see [`LICENSE`](LICENSE)).

#!/usr/bin/env bash
# Render the Internet-Drafts in this directory to XML, text and HTML.
#
#   ./build.sh                 # all draft-*.md
#   ./build.sh draft-x-00.md   # one
#
# Needs: kramdown-rfc (Ruby >= 3.2; on this Mac the Homebrew ruby at
# /opt/homebrew/opt/ruby, `gem install --user-install kramdown-rfc`) and xml2rfc
# (installed into ietf/.venv-xml2rfc on first run). Output goes to ietf/build/,
# which is git-ignored, as is the .refcache/ that kramdown-rfc writes.
set -euo pipefail
cd "$(dirname "$0")"

RUBY_BIN=/opt/homebrew/opt/ruby/bin
if [ -d "$RUBY_BIN" ]; then
  GEM_BIN="$("$RUBY_BIN/ruby" -e 'puts Gem.user_dir')/bin"
  export PATH="$RUBY_BIN:$GEM_BIN:$PATH"
fi
command -v kramdown-rfc >/dev/null || {
  echo "kramdown-rfc not found: gem install --user-install --no-document kramdown-rfc" >&2; exit 1; }

if ! command -v xml2rfc >/dev/null; then
  [ -x .venv-xml2rfc/bin/xml2rfc ] || { python3 -m venv .venv-xml2rfc && .venv-xml2rfc/bin/pip install -q xml2rfc; }
  export PATH="$PWD/.venv-xml2rfc/bin:$PATH"
fi

mkdir -p build
files=("$@"); [ ${#files[@]} -gt 0 ] || files=(draft-*.md)
status=0
for md in "${files[@]}"; do
  name="${md%.md}"
  echo "== $name"
  kramdown-rfc "$md" > "build/$name.xml"
  # xml2rfc prints warnings to stderr; a non-zero exit is an error.
  xml2rfc --text --html --path build "build/$name.xml" 2>&1 | grep -v 'NotOpenSSLWarning\|warnings.warn' || status=1
done
grep -l "AUTHOR NAME\|AUTHOR@EXAMPLE" build/*.xml >/dev/null 2>&1 && echo "NOTE: AUTHOR placeholders still present — fill the front matter before submitting." >&2
exit $status

#!/bin/bash
set -e

exists() {
  if ! [ -f "$1" ]; then
    echo "Error: Missing ${1}"
    return 1
  fi
}
missing() {
  if [ -f "$1" ]; then
    echo "Error: Found ${1}"
    return 1
  fi
}

tmpdir=$(mktemp -d)
cleanup(){
  rm -rf "$tmpdir"
}
trap cleanup EXIT

python -m toltec \
  --verbose \
  --work-dir "$tmpdir/work" \
  --dist-dir "$tmpdir/dist" \
  --arch-name rmall \
  $(dirname $0)

tree $tmpdir/dist
exists $tmpdir/dist/rmall/foo_0.0.0-1_rmall.ipk
missing $tmpdir/dist/rm1/foo_0.0.0-1_rm1.ipk
missing $tmpdir/dist/rm2/foo_0.0.0-1_rm2.ipk
exists $tmpdir/dist/rmall/bar_0.0.0-1_rmall.ipk
missing $tmpdir/dist/rm1/bar_0.0.0-1_rm1.ipk
missing $tmpdir/dist/rm2/bar_0.0.0-1_rm2.ipk

#!/usr/bin/env bash
# Usage: check_release_ref.sh <ref>
# Prints the commit SHA for a branch, tag or SHA, and fails unless it is on origin/main: production only deploys main.
set -u
ref=$(printf '%s' "${1:?usage: check_release_ref.sh <ref>}" | tr -d '[:space:]')
# the input picks which remote ref is fetched, so refuse anything git could read as an option or a revision expression
[[ $ref =~ ^[A-Za-z0-9][A-Za-z0-9._/-]*$ ]] || { echo "invalid ref: $ref" >&2; exit 1; }
git fetch --no-tags -q origin +refs/heads/main:refs/remotes/origin/main || {
  echo "could not fetch origin/main" >&2; exit 1; }
# the ref is usually already in the checkout (fetch-depth 0); otherwise fetch it by name
sha=$(git rev-parse --verify -q "$ref^{commit}" || true)
if [ -z "$sha" ]; then
  git fetch --no-tags -q origin -- "$ref" 2>/dev/null || { echo "unknown ref: $ref (is it pushed?)" >&2; exit 1; }
  sha=$(git rev-parse --verify -q 'FETCH_HEAD^{commit}') || { echo "unknown ref: $ref (is it pushed?)" >&2; exit 1; }
fi
git merge-base --is-ancestor "$sha" refs/remotes/origin/main || {
  echo "ref is not on main: $sha" >&2; exit 1; }
echo "$sha"

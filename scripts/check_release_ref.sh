#!/usr/bin/env bash
# Usage: check_release_ref.sh <ref> [branch]
# Prints the commit SHA for a branch, tag or SHA, and fails unless it is on origin/<branch> (default main).
set -u
ref=$(printf '%s' "${1:?usage: check_release_ref.sh <ref> [branch]}" | tr -d '[:space:]')
branch=$(printf '%s' "${2:-main}" | tr -d '[:space:]')
# the input picks which remote ref is fetched, so refuse anything git could read as an option or a revision expression
[[ $ref =~ ^[A-Za-z0-9][A-Za-z0-9._/-]*$ ]] || { echo "invalid ref: $ref" >&2; exit 1; }
[[ $branch =~ ^[A-Za-z0-9][A-Za-z0-9._/-]*$ ]] || { echo "invalid branch: $branch" >&2; exit 1; }
git fetch --no-tags -q origin "+refs/heads/$branch:refs/remotes/origin/$branch" || {
  echo "could not fetch origin/$branch" >&2; exit 1; }
# the ref is usually already in the checkout (fetch-depth 0); otherwise fetch it by name
sha=$(git rev-parse --verify -q "$ref^{commit}" || true)
if [ -z "$sha" ]; then
  git fetch --no-tags -q origin -- "$ref" 2>/dev/null || { echo "unknown ref: $ref (is it pushed?)" >&2; exit 1; }
  sha=$(git rev-parse --verify -q 'FETCH_HEAD^{commit}') || { echo "unknown ref: $ref (is it pushed?)" >&2; exit 1; }
fi
git merge-base --is-ancestor "$sha" "refs/remotes/origin/$branch" || {
  echo "ref is not on $branch: $sha" >&2; exit 1; }
echo "$sha"

#!/usr/bin/env python3
"""Markdown-first tickets: check, push to and sync from GitHub Issues. Stdlib only.

Source of truth is plans/tickets/T-NNN.md (see docs/references/ticket-sync.md).
Every command is a dry run unless --apply is given; push --apply is the only
command that writes to GitHub, sync --apply only edits local Markdown.

  tickets.py check  [T-018 ... | --sprint S-001 | --all]
  tickets.py push   [selector] [--apply] [--issues-json FILE]
  tickets.py sync   [selector] [--apply] [--issues-json FILE]
  tickets.py show   T-018            # title, labels, body as JSON (for MCP creation)
  tickets.py record T-018 --issue 34 --url URL   # write Tracking after an MCP create
"""
import argparse
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PLANS = ROOT / "plans"
DECISIONS = ROOT / "docs" / "decisions"

TYPES = {"Bug": "bug", "Feature": "enhancement", "Chore": "chore"}
PRIORITIES = {"Low", "Medium", "High"}
ESTIMATES = {"XS", "S", "M", "L", "TBD"}
PUSH = {"Draft", "Ready"}
PLAN = {"Pending", "Approved"}
KEYS = {"Sprint", "Feature", "Type", "Priority", "Estimate", "Push", "Plan", "Severity", "Areas", "Decisions"}
REQUIRED = ("Type", "Priority", "Push")
ID_RE = re.compile(r"^T-\d{3,}$")
FEATURE_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
DECISION_RE = re.compile(r"^(ADR|DDR)-\d{4}$")
REPO_RE = re.compile(r"^[\w.-]+/[\w.-]+$")
REASON_RE = re.compile(r"^[a-z_ ]+$")
URL_RE = re.compile(r"^https://github\.com/[\w.-]+/[\w.-]+/issues/\d+$")
TRACKING_HEAD = re.compile(r"^## Tracking[ \t]*$", re.M)
PAIR = re.compile(r"\*\*([A-Za-z ]+):\*\*\s*(.*?)(?=\s{2,}\*\*[A-Za-z ]+:\*\*|$)")
TRACK_RE = re.compile(r"^- \*\*([A-Za-z ]+):\*\*\s*(.*)$")
JIRA_RE = re.compile(r"^\[[A-Z][A-Z0-9]+-\d+\]\(https://[\w.-]+\.atlassian\.net/browse/[A-Z][A-Z0-9]+-\d+\)$")
ISSUE_RE = re.compile(r"\[#(\d+)\]\((https://github\.com/[\w.-]+/[\w.-]+/issues/\d+)\)")
MARKER = "<!-- ticket-id: {} -->"
TABLE = re.compile(r"(<!-- tickets:begin.*?-->\n)(.*?)(<!-- tickets:end -->)", re.S)
TRACKING_COMMENT = "<!-- tracking (written by push-tickets / sync-tickets, do not edit) -->"


def now_utc():
    return datetime.now(timezone.utc).replace(microsecond=0)


class Ticket:
    def __init__(self, path):
        self.path = Path(path)
        self.id = self.path.stem
        self.errors = []
        self.fields = {}
        self.tracking = {}
        self.title = ""
        self.body = ""
        self._parse(self.path.read_text())

    def _parse(self, text):
        m = TRACKING_HEAD.search(text)
        head, track = (text[:m.start()], text[m.end():]) if m else (text, "")
        lines = head.split("\n")
        if not ID_RE.match(self.id):
            self.errors.append(f"file name must be T-NNN.md, got {self.path.name}")
        if not lines or not lines[0].startswith("# "):
            self.errors.append("first line must be '# <title>'")
        else:
            self.title = lines[0][2:].strip()
        rest = lines[1:]
        header = []
        for line in rest:
            if line.startswith("## "):
                break
            header.append(line)
        for line in header:
            for key, value in PAIR.findall(line):
                if key not in KEYS:
                    self.errors.append(f"unknown field '{key}'")
                elif key in self.fields:
                    self.errors.append(f"field '{key}' repeated")
                else:
                    self.fields[key] = value.strip()
        self.body = "\n".join(rest).strip()
        for line in track.split("\n"):
            m = TRACK_RE.match(line.strip())
            if m:
                self.tracking[m.group(1)] = m.group(2).strip()
        self._validate()

    def _validate(self):
        f, err = self.fields, self.errors.append
        for key in REQUIRED:
            if key not in f:
                err(f"missing {key}")
        if f.get("Type") and f["Type"] not in TYPES:
            err(f"Type must be one of {sorted(TYPES)}")
        if f.get("Priority") and f["Priority"] not in PRIORITIES:
            err(f"Priority must be one of {sorted(PRIORITIES)}")
        if f.get("Estimate") and f["Estimate"] not in ESTIMATES:
            err(f"Estimate must be one of {sorted(ESTIMATES)}")
        if "Plan" in f and f["Plan"] not in PLAN:
            err(f"Plan must be one of {sorted(PLAN)}")
        if f.get("Plan") == "Approved" and not self._has_plan():
            err("Plan: Approved needs a non-empty '## Plan' (or '## Fix and test') section")
        if f.get("Push") and f["Push"] not in PUSH:
            err(f"Push must be one of {sorted(PUSH)}")
        if f.get("Type") == "Bug" and not re.match(r"S[1-4]\b", f.get("Severity", "")):
            err("a Bug needs Severity starting S1-S4")
        if f.get("Severity") and not re.match(r"S[1-4]\b", f["Severity"]):
            err("Severity must start with S1-S4")
        if f.get("Sprint") and not re.match(r"^S-\d{3}$", f["Sprint"]):
            err("Sprint must look like S-001")
        if not self.title:
            err("empty title")
        if f.get("Feature") and not FEATURE_RE.match(f["Feature"]):
            err("Feature must be a lower-case slug (a-z, 0-9, -)")
        for ref in self.decisions:
            if not DECISION_RE.match(ref):
                err(f"Decisions entry {ref!r} must look like ADR-0001 or DDR-0001")
            elif not list(DECISIONS.glob(f"{ref}-*.md")):
                err(f"decision record {ref} not found in docs/decisions/")
        if "Issue" in self.tracking and not ISSUE_RE.search(self.tracking["Issue"]):
            err("Tracking Issue must look like [#34](url)")
        if "Jira" in self.tracking and not JIRA_RE.match(self.tracking["Jira"]):
            err("Tracking Jira must look like [CLB-2](https://<site>.atlassian.net/browse/CLB-2)")

    def _has_plan(self):
        """True if a '## Plan' (or '## Fix and test') section has text beyond blanks, HTML comments and code fences."""
        body = re.sub(r"<!--.*?-->|```.*?```", "", self.body, flags=re.S)
        return bool(re.search(r"^## (Plan|Fix and test)[ \t]*\n+(?!##)\S", body + "\n", re.M))

    @property
    def decisions(self):
        return [d for d in re.split(r"[,\s]+", self.fields.get("Decisions", "")) if d]

    @property
    def issue(self):
        m = ISSUE_RE.search(self.tracking.get("Issue", ""))
        return (int(m.group(1)), m.group(2)) if m else None

    @property
    def labels(self):
        f = self.fields
        labels = [TYPES.get(f.get("Type"), "")]
        if f.get("Priority"):
            labels.append(f"priority: {f['Priority'].lower()}")
        if f.get("Severity"):
            labels.append(f"severity: {f['Severity'].split()[0]}")
        labels += [f"area: {a.strip()}" for a in f.get("Areas", "").split(",") if a.strip()]
        return [x for x in labels if x]

    @property
    def issue_title(self):
        return f"{self.id}: {self.title}"

    @property
    def issue_body(self):
        body = self.body
        if self.decisions:
            body += "\n\nDecisions: " + ", ".join(
                str(p.relative_to(ROOT)) for d in self.decisions for p in sorted(DECISIONS.glob(f"{d}-*.md"))
            )
        return f"{body}\n\n{MARKER.format(self.id)}"

    def gate(self):
        """Return a reason the ticket may not be pushed yet, or None."""
        sprint = self.fields.get("Sprint")
        if sprint and not (PLANS / "sprints" / f"{sprint}.md").exists():
            return f"sprint file plans/sprints/{sprint}.md not found"
        feature = self.fields.get("Feature")
        if feature:
            fdir = PLANS / "features" / feature
            spec = fdir / "spec.md"
            if not spec.exists() or not re.search(r"\*\*Status:\*\*\s*Approved", spec.read_text()):
                return f"features/{feature}/spec.md is not Approved"
            plan = fdir / "plan.md"
            if plan.exists() and re.search(r"\*\*Status:\*\*\s*Draft", plan.read_text()):
                return f"features/{feature}/plan.md is Draft"
        return None

    def write_tracking(self, issue, url, state, reason=None):
        if not URL_RE.match(url) or (reason and not REASON_RE.match(reason)):
            raise ValueError(f"refusing to write unexpected issue url or reason: {url!r} {reason!r}")
        text = self.path.read_text()
        m = TRACKING_HEAD.search(text)
        head = (text[:m.start()] if m else text).rstrip("\n")
        lines = [f"- **Issue:** [#{issue}]({url})", f"- **State:** {state}"]
        if reason:
            lines.append(f"- **Reason:** {reason}")
        lines.append(f"- **Synced:** {now_utc().isoformat().replace('+00:00', 'Z')}")
        # Jira lines belong to the /jira-tickets skill: keep them across a GitHub rewrite.
        kept = {k: v for k, v in self.tracking.items() if k == "Jira" or k.startswith("Jira ")}
        lines += [f"- **{k}:** {v}" for k, v in kept.items()]
        self.path.write_text(head + "\n\n## Tracking\n" + TRACKING_COMMENT + "\n" + "\n".join(lines) + "\n")
        self.tracking = {"Issue": f"[#{issue}]({url})", "State": state, **kept}
        if reason:
            self.tracking["Reason"] = reason


def load_tickets():
    return [Ticket(p) for p in sorted((PLANS / "tickets").glob("*.md")) if p.name != "README.md"]


def select(tickets, args):
    if args.all:
        return tickets
    if args.sprint:
        return [t for t in tickets if t.fields.get("Sprint") == args.sprint]
    by_id = {t.id: t for t in tickets}
    missing = [i for i in args.ids if i not in by_id]
    if missing:
        sys.exit(f"error: unknown ticket(s): {', '.join(missing)}")
    return [by_id[i] for i in args.ids]


def duplicates(tickets):
    seen, dupes = {}, set()
    for t in tickets:
        if t.issue:
            seen.setdefault(t.issue[0], []).append(t.id)
    for n, ids in seen.items():
        if len(ids) > 1:
            dupes.update(ids)
    return {i: [n for n, ids in seen.items() if i in ids and len(ids) > 1] for i in dupes}


class GitHub:
    """Minimal REST client; tests and --issues-json use the same interface."""

    def __init__(self, repo, token):
        if not REPO_RE.match(repo):
            sys.exit(f"error: bad repo {repo!r}; expected owner/name")
        self.repo, self.token = repo, token
        self._issues = None

    def _req(self, method, path, data=None):
        req = urllib.request.Request(
            f"https://api.github.com/repos/{self.repo}{path}",
            data=json.dumps(data).encode() if data is not None else None,
            method=method,
            headers={"Authorization": f"Bearer {self.token}", "Accept": "application/vnd.github+json"},
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.load(resp)

    def list_issues(self):
        if self._issues is None:
            issues, page = [], 1
            while True:
                batch = self._req("GET", f"/issues?state=all&per_page=100&page={page}")
                issues += [i for i in batch if "pull_request" not in i]
                if len(batch) < 100:
                    break
                page += 1
            self._issues = issues
        return self._issues

    def me(self):
        try:
            return self._req_root("/user")["login"]
        except urllib.error.HTTPError:  # Actions/installation tokens cannot call /user
            return None

    def labels(self):
        names, page = set(), 1
        while True:
            batch = self._req("GET", f"/labels?per_page=100&page={page}")
            names |= {l["name"] for l in batch}
            if len(batch) < 100:
                return names
            page += 1

    def _req_root(self, path):
        req = urllib.request.Request(f"https://api.github.com{path}", headers={
            "Authorization": f"Bearer {self.token}", "Accept": "application/vnd.github+json"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.load(resp)

    def get_issue(self, number):
        try:
            return self._req("GET", f"/issues/{number}")
        except urllib.error.HTTPError as e:
            if e.code in (404, 410):
                return None
            raise

    def find_milestone(self, title):
        for m in self._req("GET", "/milestones?state=all&per_page=100"):
            if m["title"] == title:
                return m["number"]
        return None

    def create_issue(self, title, body, labels, milestone=None):
        data = {"title": title, "body": body, "labels": labels}
        if milestone:
            data["milestone"] = milestone
        return self._req("POST", "/issues", data)


class FileIssues:
    """Read-only stand-in fed by --issues-json (issues fetched by MCP)."""

    def __init__(self, issues):
        self.issues = issues

    def list_issues(self):
        return self.issues

    def get_issue(self, number):
        return next((i for i in self.issues if i["number"] == number), None)

    def find_milestone(self, title):
        return None

    def me(self):
        return None

    def labels(self):
        return None

    def create_issue(self, *a, **k):
        raise RuntimeError("no GH_TOKEN: create via MCP using `show`, then run `record`")


def repo_slug():
    if os.environ.get("GITHUB_REPOSITORY"):
        return os.environ["GITHUB_REPOSITORY"]
    url = subprocess.run(["git", "-C", str(ROOT), "remote", "get-url", "origin"],
                         capture_output=True, text=True).stdout.strip()
    m = re.search(r"github\.com[:/]+([^/]+/[^/.]+?)(?:\.git)?/?$", url)
    return m.group(1) if m else ""


def client(args):
    if args.issues_json:
        return FileIssues(json.loads(Path(args.issues_json).read_text()))
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if not token:
        sys.exit("error: set GH_TOKEN, or pass --issues-json FILE (issues fetched via MCP)")
    return GitHub(args.repo or repo_slug(), token)


def marker_hits(issues, ticket_id):
    needle = MARKER.format(ticket_id)
    return [i for i in issues if needle in (i.get("body") or "")]


def milestone_title(ticket):
    sprint = ticket.fields.get("Sprint")
    path = PLANS / "sprints" / f"{sprint}.md" if sprint else None
    if path and path.exists():
        m = re.search(r"\*\*Milestone:\*\*\s*(.+?)(?:\s{2,}\*\*|$)", path.read_text(), re.M)
        if m and m.group(1).strip().lower() != "none":
            return m.group(1).strip()
    return None


def report(rows, headers):
    widths = [max(len(str(r[i])) for r in [headers] + rows) for i in range(len(headers))]
    for r in [headers, ["-" * w for w in widths]] + rows:
        print("  ".join(str(c).ljust(w) for c, w in zip(r, widths)).rstrip())


def cmd_check(args):
    tickets = load_tickets()
    dupes = duplicates(tickets)
    bad = 0
    for t in select(tickets, args):
        errs = list(t.errors)
        if t.id in dupes:
            errs.append(f"issue number shared with another ticket: {dupes[t.id]}")
        print(f"{'FAIL' if errs else 'ok  '} {t.id} {t.title}")
        for e in errs:
            print(f"       - {e}")
        bad += bool(errs)
    return 1 if bad else 0


def plan_push(tickets, targets, gh, trusted=()):
    dupes = duplicates(tickets)
    issues = gh.list_issues()
    allowed = {x for x in (gh.me(), *trusted) if x}
    known = gh.labels()
    rows = []
    for t in targets:
        errs = t.errors + (["issue number shared with another ticket"] if t.id in dupes else [])
        if errs:
            rows.append((t, "error", "; ".join(errs), None))
        elif t.fields["Push"] != "Ready":
            rows.append((t, "skip", "Push: Draft", None))
        elif t.issue:
            rows.append((t, "skip", f"already #{t.issue[0]}", None))
        elif (reason := t.gate()):
            rows.append((t, "blocked", reason, None))
        else:
            hits = marker_hits(issues, t.id)
            if len(hits) > 1:
                rows.append((t, "error", f"{len(hits)} issues carry its marker: {[h['number'] for h in hits]}", None))
            elif hits:
                author = (hits[0].get("user") or {}).get("login")
                if author not in allowed:
                    rows.append((t, "error", f"#{hits[0]['number']} carries the marker, opened by {author or 'unknown'}; "
                                 f"not adopted. If that is you, pass --adopt-author {author or 'LOGIN'}", None))
                else:
                    rows.append((t, "adopt", f"#{hits[0]['number']} already has its marker (author {author or 'unknown'})", hits[0]))
            elif known is not None and (missing := [l for l in t.labels if l not in known]):
                rows.append((t, "blocked", f"labels do not exist: {missing}", None))
            else:
                rows.append((t, "create", t.issue_title, None))
    return rows


def cmd_push(args):
    tickets = load_tickets()
    targets = select(tickets, args)
    gh = client(args)
    rows = plan_push(tickets, targets, gh, args.adopt_author)
    report([[t.id, a, why] for t, a, why, _ in rows], ["Ticket", "Action", "Detail"])
    todo = [r for r in rows if r[1] in ("create", "adopt")]
    failed = any(r[1] == "error" for r in rows)
    if not args.apply:
        print(f"\ndry run: {len(todo)} to push. Re-run with --apply after the user approves this preview.")
        return 1 if failed else 0
    print()
    for t, action, _, hit in todo:
        try:
            if action == "adopt":
                issue = hit
            else:
                ms = milestone_title(t)
                ms_no = gh.find_milestone(ms) if ms else None
                if ms and not ms_no:
                    print(f"note {t.id}: milestone '{ms}' does not exist; created without it")
                issue = gh.create_issue(t.issue_title, t.issue_body, t.labels, ms_no)
            t.write_tracking(issue["number"], issue["html_url"], issue.get("state", "open"))
            print(f"{'adopted' if action == 'adopt' else 'created'} {t.id} -> #{issue['number']}")
        except Exception as e:  # keep going: per-ticket failures must not block the rest
            failed = True
            print(f"FAILED {t.id}: {e}; re-run to retry (the marker prevents duplicates)")
    return 1 if failed else 0


def sprint_table(sprint, tickets):
    rows = ["| Ticket | Type | Priority | Estimate | Issue | State |", "|---|---|---|---|---|---|"]
    for t in tickets:
        if t.fields.get("Sprint") != sprint:
            continue
        issue = f"[#{t.issue[0]}]({t.issue[1]})" if t.issue else "-"
        rows.append(f"| [{t.id}](../tickets/{t.id}.md) {t.title.replace('|', '\\|')} | {t.fields.get('Type', '')} | "
                    f"{t.fields.get('Priority', '')} | {t.fields.get('Estimate', '-')} | {issue} | "
                    f"{t.tracking.get('State', '-')} |")
    return "\n".join(rows) + "\n"


def cmd_sync(args):
    tickets = load_tickets()
    targets = select(tickets, args)
    gh = client(args)
    dupes = duplicates(tickets)
    rows, failed, changes = [], False, []
    for t in targets:
        if t.errors or t.id in dupes:
            rows.append([t.id, "error", "; ".join(t.errors) or "issue number shared with another ticket"])
            failed = True
        elif not t.issue:
            rows.append([t.id, "unmapped", "no Tracking Issue (run push-tickets)"])
        else:
            try:
                issue = gh.get_issue(t.issue[0])
            except Exception as e:
                rows.append([t.id, "error", f"API: {e}"])
                failed = True
                continue
            if issue is None:
                rows.append([t.id, "missing", f"#{t.issue[0]} not found (deleted or transferred); not changed"])
                failed = True
            elif MARKER.format(t.id) not in (issue.get("body") or ""):
                rows.append([t.id, "mismatch", f"#{t.issue[0]} does not carry marker {t.id}; not changed"])
                failed = True
            else:
                state, reason = issue["state"], issue.get("state_reason") if issue["state"] == "closed" else None
                old = t.tracking.get("State")
                note = []
                if issue["title"] != t.issue_title:
                    note.append("title drift")
                if not set(t.labels) <= {(l["name"] if isinstance(l, dict) else l) for l in issue.get("labels", [])}:
                    note.append("label drift")
                if old == state and t.tracking.get("Reason") == reason:
                    status = "unchanged"
                else:
                    status = {("open", "closed"): "closed", ("closed", "open"): "reopened"}.get((old, state), "update")
                    changes.append((t, issue, state, reason))
                rows.append([t.id, status, f"#{t.issue[0]} {state}" + (f" ({'; '.join(note)}; GitHub not copied)" if note else "")])
    report(rows, ["Ticket", "Result", "Detail"])
    sprints = sorted({t.fields["Sprint"] for t in targets if t.fields.get("Sprint")})
    table_updates = []
    for s in sprints:
        path = PLANS / "sprints" / f"{s}.md"
        if not path.exists():
            print(f"warning: {path.relative_to(ROOT)} not found")
            continue
        text = path.read_text()
        if not TABLE.search(text):
            print(f"warning: {path.name} has no tickets:begin/end markers; table not generated")
            continue
        projected = {t.id: dict(t.tracking) for t in tickets}
        for t, _, state, reason in changes:
            projected[t.id]["State"] = state
        shadow = []
        for t in tickets:
            c = Ticket(t.path)
            c.tracking = projected[t.id]
            shadow.append(c)
        new = TABLE.sub(lambda m: m.group(1) + sprint_table(s, shadow) + m.group(3), text)
        if new != text:
            table_updates.append((path, new))
    if not args.apply:
        print(f"\ndry run: {len(changes)} ticket(s) and {len(table_updates)} sprint table(s) would change. Add --apply to write Markdown.")
        return 1 if failed else 0
    for t, issue, state, reason in changes:
        t.write_tracking(issue["number"], issue["html_url"], state, reason)
    for path, new in table_updates:
        path.write_text(new)
    print(f"\nwrote {len(changes)} ticket(s), {len(table_updates)} sprint table(s)")
    return 1 if failed else 0


def cmd_show(args):
    t = next((x for x in load_tickets() if x.id == args.id), None)
    if not t or t.errors:
        sys.exit(f"error: {args.id} " + ("not found" if not t else "invalid: " + "; ".join(t.errors)))
    print(json.dumps({"id": t.id, "title": t.issue_title, "labels": t.labels, "body": t.issue_body,
                      "milestone": milestone_title(t)}, indent=2))
    return 0


def cmd_record(args):
    tickets = load_tickets()
    t = next((x for x in tickets if x.id == args.id), None)
    if not t or t.errors:
        sys.exit(f"error: {args.id} " + ("not found" if not t else "invalid: " + "; ".join(t.errors)))
    if not args.url.endswith(f"/issues/{args.issue}"):
        sys.exit(f"error: --url must end with /issues/{args.issue}")
    if t.issue and t.issue[0] != args.issue:
        sys.exit(f"error: {t.id} is already mapped to #{t.issue[0]}")
    clash = [x.id for x in tickets if x.id != t.id and x.issue and x.issue[0] == args.issue]
    if clash:
        sys.exit(f"error: #{args.issue} is already recorded in {clash}")
    t.write_tracking(args.issue, args.url, args.state)
    print(f"recorded {t.id} -> #{args.issue}")
    return 0


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    def selector(sp):
        sp.add_argument("ids", nargs="*", help="ticket ids, e.g. T-018")
        sp.add_argument("--sprint", help="all tickets of a sprint, e.g. S-001")
        sp.add_argument("--all", action="store_true")

    for name, fn in (("check", cmd_check), ("push", cmd_push), ("sync", cmd_sync)):
        sp = sub.add_parser(name)
        selector(sp)
        if name != "check":
            sp.add_argument("--apply", action="store_true", help="really write (default is a dry run)")
            sp.add_argument("--issues-json", help="issues fetched via MCP instead of the REST API")
            sp.add_argument("--repo", help="owner/name (default: origin remote)")
        if name == "push":
            sp.add_argument("--adopt-author", action="append", default=[], metavar="LOGIN",
                            help="also adopt marker issues opened by LOGIN (needed with --issues-json)")
        sp.set_defaults(fn=fn)
    sp = sub.add_parser("show")
    sp.add_argument("id")
    sp.set_defaults(fn=cmd_show)
    sp = sub.add_parser("record")
    sp.add_argument("id")
    sp.add_argument("--issue", type=int, required=True)
    sp.add_argument("--url", required=True)
    sp.add_argument("--state", default="open", choices=["open", "closed"])
    sp.set_defaults(fn=cmd_record)

    args = p.parse_args(argv)
    if args.cmd in ("check", "push", "sync") and not (args.ids or args.sprint or args.all):
        p.error("choose tickets: ids, --sprint S-NNN or --all")
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())

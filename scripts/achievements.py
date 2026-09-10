#!/usr/bin/env python3
"""Publish real changes through checked PRs and report GitHub achievement progress."""
import argparse
import datetime as dt
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
TIERS = {"Pull Shark": [2, 16, 128, 1024], "Starstruck": [16, 128, 512, 4096]}


class AutomationError(Exception):
    pass


def tier_progress(count, tiers):
    reached = sum(count >= threshold for threshold in tiers)
    target = next((threshold for threshold in tiers if threshold > count), None)
    return {"count": count, "estimated_level": reached, "next_threshold": target,
            "remaining": max(0, target - count) if target else 0}


def checks_ready(checks, statuses, required_names):
    """Require the named CI jobs plus every other reported check to pass."""
    latest = {}
    for check in sorted(checks, key=lambda item: item["id"]):
        latest[(check.get("app", {}).get("id"), check["name"])] = check
    names = {check["name"] for check in latest.values()}
    names.update(status["context"] for status in statuses)
    failed = [check["name"] for check in latest.values()
              if check["status"] == "completed" and check.get("conclusion")
              not in {"success", "neutral", "skipped"}]
    failed += [status["context"] for status in statuses if status["state"] in {"failure", "error"}]
    if failed:
        raise AutomationError("CI failed: " + ", ".join(failed))
    if not set(required_names).issubset(names):
        return False
    # A required test must actually succeed, not merely be skipped.
    if any(check["name"] in required_names and check.get("conclusion") != "success"
           for check in latest.values()):
        return False
    return (all(check["status"] == "completed" for check in latest.values())
            and all(status["state"] == "success" for status in statuses))


class GitHub:
    def __init__(self, token):
        self.token = token

    def call(self, path, method="GET", data=None):
        if not path.startswith("/") or path.startswith("//"):
            raise AutomationError("API path must be relative to api.github.com")
        body = json.dumps(data).encode() if data is not None else None
        request = urllib.request.Request("https://api.github.com" + path, data=body, method=method,
            headers={"Authorization": "Bearer " + self.token, "User-Agent": "Achievement-Journal",
                     "Accept": "application/vnd.github+json", "Content-Type": "application/json",
                     "X-GitHub-Api-Version": "2022-11-28"})
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                content = response.read()
                return json.loads(content) if content else None
        except urllib.error.HTTPError as error:
            # Never print request headers or the raw response, which may echo inputs.
            raise AutomationError(f"GitHub HTTP {error.code} for {method} {path.split('?')[0]}") from None
        except (urllib.error.URLError, TimeoutError):
            raise AutomationError("GitHub connection failed. Run the same command to resume.") from None

    def items(self, path, key=None):
        result = []
        for page in range(1, 101):
            response = self.call(path + ("&" if "?" in path else "?") + f"per_page=100&page={page}")
            batch = response[key] if key else response
            result.extend(batch)
            if len(batch) < 100:
                return result
        raise AutomationError("API pagination limit reached; refusing an incomplete result")


class Runner:
    def __init__(self, args, token):
        self.args, self.token = args, token
        self.api = GitHub(token)
        self.repo = args.repo
        if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", self.repo):
            raise AutomationError("Expected --repo owner/name")
        self.base = "/repos/" + self.repo
        self.env = os.environ.copy()
        # Per-process authentication; never write credentials into Git config or URLs.
        self.env.update(GIT_CONFIG_COUNT="2", GIT_CONFIG_KEY_0="safe.directory",
                        GIT_CONFIG_VALUE_0=str(ROOT),
                        GIT_CONFIG_KEY_1="http.https://github.com/.extraheader")
        import base64
        self.env["GIT_CONFIG_VALUE_1"] = "AUTHORIZATION: basic " + base64.b64encode(
            ("x-access-token:" + token).encode()).decode()

    def git(self, *args, raw=False):
        result = subprocess.run(["git", *args], cwd=ROOT, env=self.env, capture_output=True)
        if result.returncode:
            raise AutomationError("Git operation failed: " + args[0] + ". Check the working tree and remote.")
        return result.stdout if raw else result.stdout.decode("utf-8", errors="replace").strip()

    def verify(self):
        user = self.api.call("/user")["login"]
        if user.lower() != self.repo.split("/")[0].lower():
            raise AutomationError("The token account does not match the repository owner")
        if Path(self.git("rev-parse", "--show-toplevel")).resolve() != ROOT:
            raise AutomationError("Run from the journal repository, not a parent checkout")
        remote = self.git("remote", "get-url", "origin")
        if remote not in {"https://github.com/" + self.repo, "https://github.com/" + self.repo + ".git"}:
            raise AutomationError("origin does not match --repo; credential URLs are not allowed")
        return user

    def status(self):
        user = self.verify()
        query = urllib.parse.quote(f"author:{user} is:pr is:merged")
        merged = self.api.call("/search/issues?q=" + query + "&per_page=1")
        if merged.get("incomplete_results"):
            raise AutomationError("GitHub returned incomplete search results; retry later")
        repo = self.api.call(self.base)
        report = {"account": user, "repository": self.repo,
                  "checked_at": dt.datetime.now(dt.timezone.utc).isoformat(),
                  "progress": {"Pull Shark": tier_progress(merged["total_count"], TIERS["Pull Shark"]),
                               "Starstruck": tier_progress(repo["stargazers_count"], TIERS["Starstruck"])},
                  "profile": f"https://github.com/{user}?tab=achievements",
                  "note": "Counts are visible API events, not confirmation that GitHub awarded a badge. "
                          "Pair Extraordinaire needs real collaboration; Galaxy Brain needs accepted answers."}
        output = ROOT / ".artifacts/progress.json"
        output.parent.mkdir(exist_ok=True)
        atomic_json(output, report)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return report

    def validate_paths(self, paths):
        if not isinstance(paths, list) or not paths or not all(isinstance(value, str) and value for value in paths):
            raise AutomationError("Explicit changed paths are required")
        result = []
        for value in paths:
            path = (ROOT / value).resolve()
            if not path.is_relative_to(ROOT) or path == ROOT or sensitive_path(path.relative_to(ROOT)):
                raise AutomationError("Unsafe staging path")
            result.append(str(path.relative_to(ROOT)))
        return result

    def tests(self):
        commands = [["node", "--test", *[str(p.relative_to(ROOT)) for p in sorted((ROOT / "tests").glob("*.test.mjs"))]],
                    [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", "test_*.py"]]
        commands += [["node", "--check", str(p.relative_to(ROOT))] for p in sorted((ROOT / "dist").glob("*.js"))]
        for command in commands:
            try:
                result = subprocess.run(command, cwd=ROOT, capture_output=True, timeout=600)
            except subprocess.TimeoutExpired:
                raise AutomationError("Local validation timed out; nothing was published") from None
            if result.returncode:
                raise AutomationError("Local validation failed: " + " ".join(command) + ". Run it locally for details.")
        print("Local tests and JavaScript syntax checks passed.")

    def audit_staged(self):
        names = self.git("diff", "--cached", "--name-only", "-z", raw=True).decode().split("\0")
        for name in filter(None, names):
            if sensitive_path(Path(name)):
                raise AutomationError("A credential or local artifact is staged; unstage it first")
            if self.git("ls-files", "--stage", "--", name).startswith("120000"):
                raise AutomationError("Symbolic links cannot be published by this tool")
            if self.git("diff", "--cached", "--name-only", "--diff-filter=D", "--", name):
                continue
            if self.token.encode() in self.git("show", ":" + name, raw=True):
                raise AutomationError("The provided token appears in a staged file; refusing publication")

    def wait_checks(self, sha):
        deadline = time.monotonic() + self.args.timeout
        while True:
            checks = self.api.items(self.base + f"/commits/{sha}/check-runs", "check_runs")
            statuses = self.api.call(self.base + f"/commits/{sha}/status")["statuses"]
            if checks_ready(checks, statuses, self.args.required_check):
                print("CI passed for the exact PR commit.")
                return
            if time.monotonic() >= deadline:
                raise AutomationError("CI is still pending. PR kept open; rerun the same command to resume.")
            print("Waiting for CI…", flush=True)
            time.sleep(min(10, max(0, deadline - time.monotonic())))

    def publish(self, item, merge):
        self.verify()
        branch, title, body_file = item["branch"], item["title"], item["body_file"]
        if not branch.startswith(("feature/", "fix/", "test/", "docs/", "ci/", "chore/")):
            raise AutomationError("Use a feature/, fix/, test/, docs/, ci/ or chore/ branch")
        self.git("check-ref-format", "--branch", branch)
        body_path = (ROOT / body_file).resolve()
        if not body_path.is_relative_to(ROOT) or body_path == Path(self.args.token_file).resolve():
            raise AutomationError("PR body must be a local non-credential file")
        body = body_path.read_text(encoding="utf-8")
        if self.token in body or self.token in title:
            raise AutomationError("Credential detected in PR text")
        head = urllib.parse.quote(self.repo.split("/")[0] + ":" + branch, safe="")
        existing = self.api.call(self.base + "/pulls?state=all&base=main&head=" + head)
        if existing:
            pr = existing[0]
            if pr.get("merged_at"):
                if self.git("branch", "--show-current") == branch:
                    self.git("switch", "main")
                    self.git("pull", "--ff-only", "origin", "main")
                print("Already merged: " + pr["html_url"])
                return
            if pr["state"] != "open":
                raise AutomationError("This branch has a closed, unmerged PR; use a new branch")
        else:
            current = self.git("branch", "--show-current")
            if current not in {"main", branch}:
                raise AutomationError("Switch to main or the requested branch before publishing")
            if self.git("diff", "--cached", "--name-only"):
                raise AutomationError("The index must be empty before publishing")
            paths = self.validate_paths(item["paths"])
            self.tests()
            if current == "main":
                self.git("switch", "-c", branch)
            self.git("add", "--", *paths)
            self.audit_staged()
            if self.git("diff", "--cached", "--name-only"):
                self.git("commit", "-m", title)
            elif not self.git("log", "main..HEAD", "--oneline"):
                raise AutomationError("No changes to publish; empty PRs are not created")
            self.git("push", "-u", "origin", branch)
            pr = self.api.call(self.base + "/pulls", "POST", {"title": title, "body": body, "head": branch, "base": "main"})
        print("PR: " + pr["html_url"], flush=True)
        if not merge:
            return
        sha = pr["head"]["sha"]
        self.wait_checks(sha)
        latest = self.api.call(self.base + f"/pulls/{pr['number']}")
        if latest["head"]["sha"] != sha:
            raise AutomationError("PR changed while checking; rerun to validate its new commit")
        result = self.api.call(self.base + f"/pulls/{pr['number']}/merge", "PUT", {"sha": sha, "merge_method": "merge"})
        if not result.get("merged"):
            raise AutomationError("GitHub did not merge the PR; branch protections remain unchanged")
        events = ROOT / ".artifacts/automation-events.jsonl"
        events.parent.mkdir(exist_ok=True)
        with events.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps({"pr": pr["html_url"], "sha": sha, "merged_at": dt.datetime.now(dt.timezone.utc).isoformat()}) + "\n")
        self.git("switch", "main")
        self.git("pull", "--ff-only", "origin", "main")
        print("Merged: " + pr["html_url"])


def sensitive_path(path):
    return any(part in {".git", ".artifacts", ".openai", "node_modules", "__pycache__"}
               or part.lower() == "token.txt" or part.startswith(".env")
               or part.lower().endswith((".pem", ".key")) for part in path.parts)


def atomic_json(path, value):
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(path)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default="brokenasf/achievement-journal")
    parser.add_argument("--token-file", default=str(ROOT / "token.txt"))
    parser.add_argument("--timeout", type=int, default=600)
    parser.add_argument("--required-check", action="append", default=["test"])
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("status")
    publish = sub.add_parser("publish")
    publish.add_argument("--branch", required=True)
    publish.add_argument("--title", required=True)
    publish.add_argument("--body-file", required=True)
    publish.add_argument("--paths", nargs="+", required=True)
    publish.add_argument("--merge", action="store_true")
    queue = sub.add_parser("queue")
    queue.add_argument("--file", required=True)
    queue.add_argument("--merge", action="store_true")
    args = parser.parse_args()
    try:
        token = os.environ.get("GITHUB_TOKEN") or Path(args.token_file).read_text(encoding="utf-8").strip()
        if not token:
            raise AutomationError("Token file is empty")
        runner = Runner(args, token)
        if args.command == "status":
            runner.status()
        elif args.command == "publish":
            runner.publish({"branch": args.branch, "title": args.title,
                            "body_file": args.body_file, "paths": args.paths}, args.merge)
            runner.status()
        else:
            items = json.loads(Path(args.file).read_text(encoding="utf-8"))
            if not isinstance(items, list) or not items:
                raise AutomationError("Queue must be a non-empty JSON list")
            for item in items:
                if not isinstance(item, dict) or set(item) != {"branch", "title", "body_file", "paths"}:
                    raise AutomationError("Queue item needs branch, title, body_file and paths")
            if len(items) > 1 and not args.merge:
                raise AutomationError("Multiple queue items require --merge; publish a single PR otherwise")
            for item in items:
                runner.publish(item, args.merge)
            runner.status()
    except (AutomationError, OSError, ValueError, KeyError) as error:
        message = str(error)
        if "token" in locals() and token:
            message = message.replace(token, "[REDACTED]")
        print("Stopped: " + message, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

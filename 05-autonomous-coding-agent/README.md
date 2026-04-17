# 05 — Autonomous Coding Workflow Agent

**Difficulty:** Advanced
**Time:** Full day
**What it does:** An agent that reads a GitHub issue, understands the codebase, writes the fix, tests it, and opens a pull request. You describe the problem, the agent ships the solution.

## Why build this

This is what the top engineering teams are already doing with Claude Code. Instead of manually reading issues, switching context, writing code, and opening PRs, you point an agent at an issue and it handles the entire workflow. This project teaches you how that pipeline actually works under the hood.

## What you need

- Python 3.10+
- [Claude Code](https://docs.anthropic.com/en/docs/claude-code) installed
- [GitHub CLI](https://cli.github.com/) (`gh`) installed and authenticated
- A GitHub repo to test with (create a fresh one for experiments)
- Anthropic API key

## Setup (20 minutes)

### 1. Create your project

```bash
mkdir coding-agent && cd coding-agent
python -m venv venv
source venv/bin/activate
```

### 2. Install dependencies

```bash
pip install anthropic pygithub
```

### 3. Authenticate GitHub CLI

```bash
gh auth login
```

### 4. Set your API key

```bash
export ANTHROPIC_API_KEY=your_key_here
```

### 5. Create the agent

Save this as `agent.py`:

```python
import os
import subprocess
import json
from anthropic import Anthropic

client = Anthropic()
REPO_PATH = os.getcwd()


def get_issue(repo, issue_number):
    """Fetch issue details using GitHub CLI"""
    result = subprocess.run(
        ["gh", "issue", "view", str(issue_number), "--repo", repo, "--json",
         "title,body,labels,comments"],
        capture_output=True, text=True
    )
    return json.loads(result.stdout)


def get_repo_structure():
    """Get the current repo file structure"""
    result = subprocess.run(
        ["find", ".", "-type", "f", "-not", "-path", "./.git/*",
         "-not", "-path", "./node_modules/*", "-not", "-path", "./venv/*"],
        capture_output=True, text=True
    )
    return result.stdout


def read_file(filepath):
    """Read a file's contents"""
    try:
        with open(filepath, "r") as f:
            return f.read()
    except FileNotFoundError:
        return f"File not found: {filepath}"


def write_file(filepath, content):
    """Write content to a file"""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w") as f:
        f.write(content)
    return f"Written to {filepath}"


def run_command(command):
    """Run a shell command and return output"""
    result = subprocess.run(
        command, shell=True, capture_output=True, text=True, cwd=REPO_PATH
    )
    return f"stdout: {result.stdout}\nstderr: {result.stderr}\nreturncode: {result.returncode}"


def create_branch_and_pr(repo, issue_number, branch_name, title, body):
    """Create a branch, commit changes, and open a PR"""
    commands = [
        f"git checkout -b {branch_name}",
        "git add -A",
        f'git commit -m "fix: {title}"',
        f"git push origin {branch_name}",
    ]

    for cmd in commands:
        result = run_command(cmd)
        print(f"  {cmd}: {result}")

    # Open PR using GitHub CLI
    pr_result = subprocess.run(
        ["gh", "pr", "create", "--repo", repo,
         "--title", title, "--body", body,
         "--head", branch_name],
        capture_output=True, text=True
    )
    return pr_result.stdout


def solve_issue(repo, issue_number):
    """Main workflow: read issue, understand code, fix it, open PR"""

    print(f"\n1. Fetching issue #{issue_number}...")
    issue = get_issue(repo, issue_number)
    print(f"   Title: {issue['title']}")

    print("\n2. Reading repo structure...")
    structure = get_repo_structure()

    print("\n3. Analyzing the issue and planning the fix...")

    # Send to Claude for analysis and fix
    messages = [
        {
            "role": "user",
            "content": f"""You are an expert software engineer. Here's a GitHub issue to fix.

ISSUE:
Title: {issue['title']}
Body: {issue['body']}

REPO STRUCTURE:
{structure}

Your job:
1. Identify which files need to change
2. Explain your approach in 2-3 sentences
3. List the exact files to read before making changes

Respond with JSON:
{{
    "approach": "your approach in 2-3 sentences",
    "files_to_read": ["path/to/file1.py", "path/to/file2.py"]
}}"""
        }
    ]

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2000,
        messages=messages
    )

    # Parse the plan
    plan_text = response.content[0].text
    # Extract JSON from response
    import re
    json_match = re.search(r'\{.*\}', plan_text, re.DOTALL)
    if json_match:
        plan = json.loads(json_match.group())
    else:
        print("Could not parse plan. Raw response:")
        print(plan_text)
        return

    print(f"   Approach: {plan['approach']}")
    print(f"   Files to read: {plan['files_to_read']}")

    # Read the relevant files
    print("\n4. Reading relevant files...")
    file_contents = {}
    for filepath in plan['files_to_read']:
        content = read_file(filepath)
        file_contents[filepath] = content
        print(f"   Read: {filepath}")

    # Generate the fix
    print("\n5. Generating the fix...")
    files_context = "\n\n".join(
        [f"--- {path} ---\n{content}" for path, content in file_contents.items()]
    )

    fix_messages = [
        {
            "role": "user",
            "content": f"""You are fixing this GitHub issue:

Title: {issue['title']}
Body: {issue['body']}

Your approach: {plan['approach']}

Here are the current file contents:

{files_context}

Write the complete fixed version of each file that needs to change.
Respond with JSON:
{{
    "changes": [
        {{"path": "path/to/file.py", "content": "full file content here"}},
    ],
    "pr_description": "description of what was fixed and why"
}}"""
        }
    ]

    fix_response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4000,
        messages=fix_messages
    )

    fix_text = fix_response.content[0].text
    json_match = re.search(r'\{.*\}', fix_text, re.DOTALL)
    if json_match:
        fix = json.loads(json_match.group())
    else:
        print("Could not parse fix. Raw response:")
        print(fix_text)
        return

    # Apply the changes
    print("\n6. Applying changes...")
    for change in fix['changes']:
        write_file(change['path'], change['content'])
        print(f"   Updated: {change['path']}")

    # Create branch and PR
    branch_name = f"fix/issue-{issue_number}"
    print(f"\n7. Creating branch '{branch_name}' and opening PR...")

    pr_url = create_branch_and_pr(
        repo, issue_number, branch_name,
        f"Fix #{issue_number}: {issue['title']}",
        fix['pr_description']
    )
    print(f"\n   PR created: {pr_url}")
    print("\nDone.")


if __name__ == "__main__":
    repo = input("GitHub repo (e.g. username/repo-name): ")
    issue_number = input("Issue number to fix: ")
    solve_issue(repo, int(issue_number))
```

## Try it

### 1. Create a test repo with a simple issue

```bash
# Create a new repo for testing
mkdir test-project && cd test-project
git init
```

Create a simple `app.py` with a deliberate bug, push it, and create an issue describing the bug.

### 2. Run the agent

```bash
cd coding-agent
python agent.py
```

```
GitHub repo: yourusername/test-project
Issue number: 1
```

Watch it fetch the issue, read the code, plan the fix, apply changes, and open a PR.

### 3. Review the PR on GitHub

The agent created a branch, committed the fix, and opened a pull request. Review it like you would any code review.

## Go deeper

- Add a self-review step where Claude reviews its own PR before submitting
- Add test running: agent runs the test suite after making changes and iterates if tests fail
- Support multiple issues in a batch
- Add a "code review agent" that reviews PRs from other contributors
- Connect to Linear or Jira instead of GitHub Issues
- Add Claude Code as the execution layer instead of raw file writes

## What you'll learn

- How autonomous coding agents work end to end
- How to chain AI planning with code execution
- How to use the GitHub CLI programmatically
- How to build agents that interact with real infrastructure
- Why self-review and testing loops matter for autonomous agents

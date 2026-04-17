import os
import subprocess
import json
import re
from anthropic import Anthropic

client = Anthropic()
REPO_PATH = os.getcwd()


def get_issue(repo, issue_number):
    result = subprocess.run(
        ["gh", "issue", "view", str(issue_number), "--repo", repo, "--json",
         "title,body,labels,comments"],
        capture_output=True, text=True
    )
    return json.loads(result.stdout)


def get_repo_structure():
    result = subprocess.run(
        ["find", ".", "-type", "f", "-not", "-path", "./.git/*",
         "-not", "-path", "./node_modules/*", "-not", "-path", "./venv/*"],
        capture_output=True, text=True
    )
    return result.stdout


def read_file(filepath):
    try:
        with open(filepath, "r") as f:
            return f.read()
    except FileNotFoundError:
        return f"File not found: {filepath}"


def write_file(filepath, content):
    os.makedirs(os.path.dirname(filepath) if os.path.dirname(filepath) else ".", exist_ok=True)
    with open(filepath, "w") as f:
        f.write(content)
    return f"Written to {filepath}"


def run_command(command):
    result = subprocess.run(
        command, shell=True, capture_output=True, text=True, cwd=REPO_PATH
    )
    return f"stdout: {result.stdout}\nstderr: {result.stderr}\nreturncode: {result.returncode}"


def create_branch_and_pr(repo, issue_number, branch_name, title, body):
    commands = [
        f"git checkout -b {branch_name}",
        "git add -A",
        f'git commit -m "fix: {title}"',
        f"git push origin {branch_name}",
    ]

    for cmd in commands:
        result = run_command(cmd)
        print(f"  {cmd}: {result}")

    pr_result = subprocess.run(
        ["gh", "pr", "create", "--repo", repo,
         "--title", title, "--body", body,
         "--head", branch_name],
        capture_output=True, text=True
    )
    return pr_result.stdout


def solve_issue(repo, issue_number):
    print(f"\n1. Fetching issue #{issue_number}...")
    issue = get_issue(repo, issue_number)
    print(f"   Title: {issue['title']}")

    print("\n2. Reading repo structure...")
    structure = get_repo_structure()

    print("\n3. Analyzing the issue and planning the fix...")

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

    plan_text = response.content[0].text
    json_match = re.search(r'\{.*\}', plan_text, re.DOTALL)
    if json_match:
        plan = json.loads(json_match.group())
    else:
        print("Could not parse plan. Raw response:")
        print(plan_text)
        return

    print(f"   Approach: {plan['approach']}")
    print(f"   Files to read: {plan['files_to_read']}")

    print("\n4. Reading relevant files...")
    file_contents = {}
    for filepath in plan['files_to_read']:
        content = read_file(filepath)
        file_contents[filepath] = content
        print(f"   Read: {filepath}")

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
        {{"path": "path/to/file.py", "content": "full file content here"}}
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

    print("\n6. Applying changes...")
    for change in fix['changes']:
        write_file(change['path'], change['content'])
        print(f"   Updated: {change['path']}")

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

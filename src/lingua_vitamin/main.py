"""Main."""

from collections import defaultdict
import logging
import os
import sys
import subprocess

import argparse
import datetime
from dotenv import load_dotenv
import pandas as pd

from lingua_vitamin.news import fetcher
from lingua_vitamin.translate.translator import Translator
from lingua_vitamin.common import utils


def parse_args():
    """Parse args."""
    parser = argparse.ArgumentParser(
        description="LinguaVitamin Daily News fetch & translate"
    )
    parser.add_argument(
        "--num_articles", type=int, default=5, help="Number of news articles to fetch"
    )
    parser.add_argument(
        "--source_lang", type=str, default="de", help="Source language code (e.g. de)"
    )
    parser.add_argument(
        "--target_langs",
        nargs="+",
        default=["en", "es", "zh", "fr"],
        help="Target language codes",
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default="output/news",
        help="Directory to save markdown files",
    )
    parser.add_argument(
        "--github_repo",
        type=str,
        default="",
        help="GitHub repo (e.g. user/repo)",
    )
    parser.add_argument(
        "--base_branch", type=str, default="main", help="Base branch for PR"
    )
    parser.add_argument(
        "--github_token",
        type=str,
        default=None,
        help="GitHub token (env GITHUB_TOKEN if None)",
    )

    parser.add_argument("--smtp_port", type=int, default=587, help="SMTP server port")

    parser.add_argument(
        "--smtp_server", required=False, default=os.getenv("SMTP_SERVER")
    )
    parser.add_argument("--smtp_user", required=False, default=os.getenv("SMTP_USER"))
    parser.add_argument(
        "--smtp_password", required=False, default=os.getenv("SMTP_PASSWORD")
    )
    parser.add_argument("--from_email", required=False, default=os.getenv("FROM_EMAIL"))
    parser.add_argument(
        "--to_emails", required=False, default=os.getenv("TO_EMAILS", "").split(",")
    )

    return parser.parse_args()


def git_run(*args):
    """Run git command and print output"""
    result = subprocess.run(["git"] + list(args), capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Git command failed: git {' '.join(args)}")
        print(result.stderr)
        sys.exit(1)
    return result.stdout.strip()


def create_branch_and_push(branch_name, file_path, base_branch):
    """Create branch and push."""
    logging.info(
        "Create a new branch (branch, base) = (%s, %s): %s.",
        branch_name,
        base_branch,
        file_path,
    )
    # git_run("checkout", base_branch)
    # git_run("pull", "origin", base_branch)

    git_run("checkout", "-b", branch_name)
    if isinstance(file_path, str):
        file_path = [file_path]
    for file in file_path:
        git_run("add", file)
    git_run("commit", "-m", f"Add daily news for {branch_name}")
    git_run("push", "-u", "origin", branch_name)


def main():
    """Main."""
    load_dotenv()
    args = parse_args()

    github_token = args.github_token or os.getenv("GITHUB_TOKEN")
    if not github_token:
        logging.warning(
            "GitHub token not provided via --github_token or GITHUB_TOKEN env"
        )

    # Filenames
    date = datetime.date.today()
    date_str = date.isoformat()
    # news--de--YYYY-MM-DD
    branch_name = f"{os.path.basename(args.output_dir)}--{args.source_lang}--{date_str}"
    # markdown/YYYY/MM
    md_filename = os.path.join(
        f"markdown/{date.year:04d}/{date.month:02d}", f"{branch_name}"
    )
    # AUTO--news--de--YYYY-MM-DD
    branch_name = f"AUTO--{branch_name}"
    # output/news/markdown/YYYY/MM/news--de--YYYY-MM-DD.md
    md_path = os.path.join(args.output_dir, md_filename)

    csv_path = md_path.replace("/markdown/", "/csv/") + ".csv"
    md_path += ".md"

    os.makedirs(os.path.dirname(md_path), exist_ok=True)
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)

    # Articles
    articles = fetcher.fetch_top_news_rss(
        lang=args.source_lang, top_n=args.num_articles
    )
    if not articles:
        logging.warning("No articles fetched, exiting.")
        return

    translators = {
        target: Translator(args.source_lang, target) for target in args.target_langs
    }

    translated_articles = []
    for article in articles:
        # Seems probablematic for empty content.
        content = article["content"]

        translations = {}
        for target, trans in translators.items():
            translations[target] = {
                "title": trans.translate([article["title"]])[0],
                "content": trans.translate([content])[0] if content.strip() else "",
            }

        translated_articles.append({"original": article, "translations": translations})

    lines = [
        f"# LinguaVitamin Daily News - {date_str}\n\n",
        "\n\n",
    ]
    toc = []
    df = defaultdict(lambda: [])
    for i, art in enumerate(translated_articles):
        source = args.source_lang
        lines.append(f"## Article {i}\n")
        lines.append(f"### Original ({source}):\n")

        title, content = art["original"]["title"], art["original"]["content"]
        lines.append(f"**Title:** {title}\n\n")
        lines.append(f"{content}\n\n")
        df[f"title-{source}"].append(title)
        df[f"content-{source}"].append(content)

        summary = title
        for target in ("de", "en", "zh"):
            if target in args.target_langs:
                temp = art["translations"][target]["title"]
                summary += f" | {temp}"
        summary = f"[[{i:02d}] {summary}](#article-{i})"
        toc.append(summary)

        for target, trans in art["translations"].items():
            lines.append(f"### Translation ({target}):\n")
            title, content = trans["title"], trans["content"]
            lines.append(f"**Title:** {title}\n\n")
            lines.append(f"{content}\n\n")
            df[f"title-{target}"].append(title)
            df[f"content-{target}"].append(content)
        lines.append("---\n\n")

    lines = lines[:1] + ["\n".join(f"- {t}" for t in toc)] + lines[1:]
    content = "".join(lines)
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(content)

    df = pd.DataFrame.from_dict(data=df)
    df.to_csv(csv_path)

    logging.info("Daily news written to `%s`.", md_path)

    pr_title = email_subject = f"LinguaVitamin daily news: {branch_name}"
    pr_url = None
    if github_token and args.github_repo:
        try:
            create_branch_and_push(branch_name, (md_path, csv_path), args.base_branch)

            pr_body = f"Auto-generated daily news translations for {date_str}."

            pr_url = utils.create_github_pr(
                args.github_repo,
                branch_name,
                args.base_branch,
                pr_title,
                pr_body,
                github_token,
            )
        except Exception as error:
            logging.warning("Unable to create a PR: <<<%s>>>", error)
            pr_url = None

        if pr_url:
            print(f"Created PR: {pr_url}")
        else:
            print("Failed to create PR.")

    email_body = (
        f"Daily news has been pushed and PR created: {pr_url if pr_url else 'N/A'}"
    )
    utils.send_email(
        email_subject,
        email_body,
        args.from_email,
        args.to_emails,
        args.smtp_server,
        args.smtp_port,
        args.smtp_user,
        args.smtp_password,
        body_file=md_path,
    )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format=utils.LOGGING_FORMAT)
    main()

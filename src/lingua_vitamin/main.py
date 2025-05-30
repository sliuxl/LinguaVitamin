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


_SUFFIX_CSV = ".csv"
_SUFFIX_MD = ".md"


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
        "--output_root",
        type=str,
        default="",
        help="Directory to save markdown files",
    )
    parser.add_argument(
        "--output_md",
        type=str,
        default="_posts/news/markdown",
        help="Directory to save markdown files",
    )
    parser.add_argument(
        "--output_csv",
        type=str,
        default="csv/news",
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


def create_branch_and_push(root_dir, branch_name, file_path, base_branch):
    """Create branch and push."""
    logging.info("pwd: `%s`", os.getcwd())
    if root_dir not in ("", ".", "./"):
        os.chdir(root_dir)
        logging.info("pwd: `%s`", os.getcwd())

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
    kwargs = {
        "year": f"{date.year:04d}",
        "month": f"{date.month:02d}",
        "day": f"{date.day:02d}",
        "source": args.source_lang,
        # news
        "category": args.output_md.split("/")[1],
    }
    # YYYY-MM-DD--news-de
    branch_name_suffix = "{year}-{month}-{day}--{category}-{source}".format(**kwargs)
    # _posts/news/markdown/YYYY/MM/YYYY-MM-DD--news-de.md
    md_path = os.path.join(
        args.output_root, args.output_md, branch_name_suffix + _SUFFIX_MD
    ).format(**kwargs)
    # csv/news/YYYY/MM/YYYY-MM-DD--news-de.md
    csv_path = os.path.join(
        args.output_root, args.output_csv, branch_name_suffix + _SUFFIX_CSV
    ).format(**kwargs)

    # AUTO--YYYY-MM-DD--news-de
    branch_name = f"AUTO--{branch_name_suffix}"

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
            # If either is too long, we'll skip its translation.
            gen_title = trans.translate([article["title"]])
            if gen_title is None:
                continue
            gen_content = trans.translate([content]) if content.strip() else [""]
            if gen_content is None:
                continue

            translations[target] = {
                "title": gen_title[0],
                "content": gen_content[0],
            }

        if translations:
            translated_articles.append(
                {"original": article, "translations": translations}
            )
        else:
            logging.warning("No valid translation for article: `%s`.", article)

    language_map = {
        "de": "German",
        "en": "English",
        "es": "Spanish",
        "fr": "French",
        "zh": "Chinese",
    }
    language = language_map.get(args.source_lang, "")

    template = f"""
---
title: {language} News for {date_str}
date: {date_str}
layout: post
---
    """.strip()

    lines = [
        template + "\n\n",
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
            create_branch_and_push(
                args.output_root, branch_name, (md_path, csv_path), args.base_branch
            )

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

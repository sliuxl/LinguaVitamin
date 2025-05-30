"""Main."""

import logging
import os
import sys
import subprocess

import argparse
import datetime
from dotenv import load_dotenv

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
    git_run("checkout", base_branch)
    git_run("pull", "origin", base_branch)

    git_run("checkout", "-b", branch_name)
    git_run("add", file_path)
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

    os.makedirs(args.output_dir, exist_ok=True)
    date_str = datetime.date.today().isoformat()
    branch_name = f"{os.path.basename(args.output_dir)}--{args.source_lang}--{date_str}"
    md_filename = f"{branch_name}.md"
    branch_name = f"AUTO--{branch_name}"
    md_path = os.path.join(args.output_dir, md_filename)

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

    with open(md_path, "w", encoding="utf-8") as f:
        f.write(f"# LinguaVitamin Daily News - {date_str}\n\n")
        for i, art in enumerate(translated_articles, 1):
            f.write(f"## Article {i}\n")
            f.write(f"### Original ({args.source_lang}):\n")
            f.write(f"**Title:** {art['original']['title']}\n\n")
            f.write(f"{art['original']['content']}\n\n")
            for target, trans in art["translations"].items():
                f.write(f"### Translation ({target}):\n")
                f.write(f"**Title:** {trans['title']}\n\n")
                f.write(f"{trans['content']}\n\n")
            f.write("---\n\n")

    logging.info("Daily news written to `%s`.", md_path)

    pr_title = email_subject = f"LinguaVitamin daily news: {branch_name}"
    pr_url = None
    if github_token and args.github_repo:
        try:
            create_branch_and_push(branch_name, md_path, args.base_branch)

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

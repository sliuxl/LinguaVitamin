"""Main."""

import logging
import os

import argparse
from dotenv import load_dotenv

from lingua_vitamin import pipe
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
        "--arxiv",
        type=str,
        default="",
        help="Arxiv subject to look at, e.g. cs.DC, cs.PL, etc.",
    )
    parser.add_argument(
        "--arxiv_num_days",
        type=int,
        default=1,
        help="Arxiv history to look at, one day, one week, etc.",
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


def main():
    """Main."""
    load_dotenv()
    args = parse_args()

    github_token = args.github_token or os.getenv("GITHUB_TOKEN")
    if not github_token:
        logging.warning(
            "GitHub token not provided via --github_token or GITHUB_TOKEN env"
        )

    category = args.output_md.split("/")[1]
    is_arxiv = bool(args.arxiv)
    if is_arxiv:
        tag = args.arxiv.lower().replace(".", "__")
        pipe_func = pipe.run_arxiv
    else:
        tag = args.source_lang
        pipe_func = pipe.run_news
    date_str, branch_name, md_path, csv_path = pipe.get_filenames(
        args, tag=f"{category}-{tag}"
    )

    if pipe_func(args, md_path, csv_path, date_str) is None:
        logging.warning("Nothing to process: Early stop.")
        return

    pr_title = email_subject = f"LinguaVitamin daily {category}: {branch_name}"
    pr_url = None
    if github_token and args.github_repo:
        try:
            pipe.create_branch_and_push(
                args.output_root, branch_name, (md_path, csv_path), args.base_branch
            )

            pr_body = f"Auto-generated daily {category} for {date_str}."

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

    email_body = f"Daily {category} has been pushed and PR created: {pr_url if pr_url else 'N/A'}"
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

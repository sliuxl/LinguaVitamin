"""Util functions."""

import logging
import os
import smtplib

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from github import Github


LOGGING_FORMAT = "%(asctime)s [%(filename)s:%(lineno)d] %(levelname)s - %(message)s"


def load_file(
    filename: str, mode: str = "r", log: bool = True, fix: str = "ignore"
) -> str:
    """Load content from a file."""
    if log:
        logging.info("Reading `%s`.", filename)

    if not os.path.exists(filename):
        return None

    try:
        with open(filename, mode) as ifile:  # pylint: disable=unspecified-encoding
            return ifile.read()
    except Exception as error:
        logging.exception("Unable to load file `%s`: <<<%s>>>", filename, error)
        if "b" in mode or not fix:
            return None

    try:
        with open(filename, f"{mode}b") as ifile:  # pylint: disable=unspecified-encoding
            data = ifile.read()
            if fix == "latin-1":
                text = data.decode("latin-1")
            else:
                if fix != "ignore":
                    logging.warning(
                        "Unknown fix mode = `%s`, using ignore instead.", fix
                    )
                text = data.decode("utf-8", errors="ignore")
            return text
    except Exception as error:
        logging.exception("[Retry] Unable to load file `%s`: <<<%s>>>", filename, error)

    return None


def create_github_pr(
    repo_name: str,
    branch: str,
    base_branch: str,
    pr_title: str,
    pr_body: str,
    github_token: str,
):
    """Create a pull request on GitHub."""
    logging.info(
        "Create a PR for (repo, branch, base) = (%s, %s, %s).",
        repo_name,
        branch,
        base_branch,
    )
    repo = Github(github_token).get_repo(repo_name)

    try:
        pr = repo.create_pull(
            title=pr_title, body=pr_body, head=branch, base=base_branch
        )
        logging.info("Created PR #%s: `%s`.", pr.number, pr.title)
        return pr.html_url
    except Exception as error:
        logging.warning("Failed to create PR: <<<%s>>>", error)
        return None


def send_email(
    subject: str,
    body: str,
    from_email: str,
    to_emails: list,
    smtp_server: str,
    smtp_port: int,
    smtp_user: str,
    smtp_password: str,
    body_file: str = None,
):
    """Send an email with given subject and body."""
    msg = MIMEMultipart()
    msg["From"] = from_email
    msg["To"] = ", ".join(to_emails)
    msg["Subject"] = subject

    if body_file and os.path.exists(body_file):
        with open(body_file, "r", encoding="utf-8") as f:
            body_content = f.read()
        body += f"\n\n{body_content}"

    msg.attach(MIMEText(body, "plain"))

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.sendmail(from_email, to_emails, msg.as_string())
        logging.info("Email sent successfully")
        return True
    except Exception as error:
        logging.warning("Failed to send email: <<<%s>>>", error)
        return False

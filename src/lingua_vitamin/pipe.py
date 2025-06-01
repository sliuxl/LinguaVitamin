"""Util functions for the pipeline."""

from collections import defaultdict
import logging
import os
import sys
import subprocess

import datetime
import pandas as pd

from lingua_vitamin.arxiv import fetcher as arxiv_fetcher
from lingua_vitamin.common import utils
from lingua_vitamin.news import fetcher as news_fetcher
from lingua_vitamin.translate.translator import Translator


_SUFFIX_CSV = ".csv"
_SUFFIX_MD = ".md"

LANGUAGE_MAP = {
    "de": "German",
    "en": "English",
    "es": "Spanish",
    "fr": "French",
    "zh": "Chinese",
}
KEY_TITLE = arxiv_fetcher.KEY_TITLE

_TEMPLATE = (
    """
---
title: TITLE
date: DATE
layout: post
---
""".strip()
    + "\n\n"
)


def _git_run(*args):
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
    # _git_run("checkout", base_branch)
    # _git_run("pull", "origin", base_branch)

    _git_run("checkout", "-b", branch_name)
    if isinstance(file_path, str):
        file_path = [file_path]
    for file in file_path:
        _git_run("add", file)
    _git_run("commit", "-m", f"Add daily news for {branch_name}")
    _git_run("push", "-u", "origin", branch_name)


def get_filenames(args, tag):
    """Get filenames."""
    date = datetime.date.today()
    date_str = date.isoformat()
    kwargs = {
        "year": f"{date.year:04d}",
        "month": f"{date.month:02d}",
        "day": f"{date.day:02d}",
        "tag": tag,
    }

    # YYYY-MM-DD--news-de
    branch_name_suffix = "{year}-{month}-{day}--{tag}".format(**kwargs)
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

    return date_str, branch_name, md_path, csv_path


def _translate_news(articles, source_lang: str, target_langs):
    translators = {target: Translator(source_lang, target) for target in target_langs}

    translated_articles = []
    for article in articles:
        # Seems probablematic for empty content.
        content = article["content"]

        translations = {}
        for target, trans in translators.items():
            # If either is too long, we'll skip its translation.
            gen_title = trans.translate([article[KEY_TITLE]])
            if gen_title is None:
                continue
            gen_content = trans.translate([content]) if content.strip() else [""]
            if gen_content is None:
                continue

            translations[target] = {
                KEY_TITLE: gen_title[0],
                "content": gen_content[0],
            }

        if translations:
            translated_articles.append(
                {"original": article, "translations": translations}
            )
        else:
            logging.warning("No valid translation for article: `%s`.", article)

    return translated_articles


def _translate_papers(df, column, target_langs, source_lang="en"):
    translators = {target: Translator(source_lang, target) for target in target_langs}

    aug_titles = defaultdict(lambda: [])

    titles = df[column]
    for title in titles:
        for target, trans in translators.items():
            gen_title = trans.translate([title])
            if gen_title is None:
                logging.warning("No valid translation for title: `%s`.", title)
                gen_title = ""
            else:
                gen_title = gen_title[0]

            aug_titles[target].append(gen_title)

    for target in target_langs:
        df[f"{column}-{target}"] = aug_titles[target]

    return df


def convert_news_csv_to_md(csv_path, md_path, date_str, source_lang, target_langs):
    """Convert news csv to md."""
    lines = [
        _TEMPLATE.replace(
            "TITLE", f"{LANGUAGE_MAP.get(source_lang, '')} News for {date_str}"
        ).replace("DATE", date_str),
        "\n\n",
    ]
    toc = []

    df = pd.read_csv(csv_path)
    for i, row in df.iterrows():
        lines.append(f"## Article {i}\n")

        lines.append(f"### Original ({source_lang}):\n")
        title, content = row[f"title-{source_lang}"], row[f"content-{source_lang}"]
        lines.append(f"**Title:** {title}\n\n{content}\n\n")

        summary = title
        for target in ("de", "en", "zh"):
            if target in target_langs:
                summary += " | " + row[f"title-{target}"]
        summary = f"[[{i:02d}] {summary}](#article-{i})"
        toc.append(summary)

        for target in target_langs:
            lines.append(f"### Translation ({target}):\n")
            title, content = row[f"title-{target}"], row[f"content-{target}"]
            lines.append(f"**Title:** {title}\n\n{content}\n\n")

        lines.append("---\n\n")

    lines = lines[:1] + ["\n".join(f"- {t}" for t in toc)] + lines[1:]
    os.makedirs(os.path.dirname(md_path), exist_ok=True)
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("".join(lines))

    logging.info("Daily news written to `%s`.", md_path)


def run_news(args, md_path: str, csv_path: str, date_str: str):
    """Run news."""
    articles = news_fetcher.fetch_top_news_rss(
        lang=args.source_lang, top_n=args.num_articles
    )
    if not articles:
        logging.warning("No articles fetched, exiting.")
        return None

    trans_articles = _translate_news(articles, args.source_lang, args.target_langs)

    df = defaultdict(lambda: [])
    for article in trans_articles:
        df[f"title-{args.source_lang}"].append(article["original"][KEY_TITLE])
        df[f"content-{args.source_lang}"].append(article["original"]["content"])

        for target, trans in article["translations"].items():
            df[f"title-{target}"].append(trans[KEY_TITLE])
            df[f"content-{target}"].append(trans["content"])

    os.makedirs(os.path.dirname(csv_path), exist_ok=True)
    df = pd.DataFrame.from_dict(data=df)
    df.to_csv(csv_path)
    logging.info("Daily news written to `%s`.", csv_path)

    convert_news_csv_to_md(
        csv_path, md_path, date_str, args.source_lang, args.target_langs
    )

    return md_path, csv_path


def convert_arxiv_csv_to_md(csv_path, md_path, date_str, subject):
    """Convert arxiv csv to md."""
    lines = [
        _TEMPLATE.replace("TITLE", f"{subject} @ {date_str}").replace("DATE", date_str),
        "\n\n",
    ]
    toc = []

    df = pd.read_csv(csv_path)
    for i, row in df.iterrows():
        lines.append(f"## Article {i}\n")

        title = row[KEY_TITLE]
        abstract = row[arxiv_fetcher.KEY_ABSTRACT]
        date = row[arxiv_fetcher.KEY_DATE][:10]
        authors = row[arxiv_fetcher.KEY_AUTHORS]
        url = row[arxiv_fetcher.KEY_URL]

        short_title = title
        short_date = "-".join(date.split("-")[1:])
        short_url = url.split("/")[-1]

        for lang in ("de", "zh"):
            col = f"{KEY_TITLE}-{lang}"
            title += " |"
            if col in row:
                title += f" {row[col]}"

        # TOC
        toc.append(
            f"[{i:02d}](#article-{i}) | {short_date} | {title} | [{short_url}]({url})"
        )

        # Body
        lines.append(f"### Title@{date}: {short_title}\n")
        lines.append(
            f"**Title**: {title} [{short_url}]({url})\n\n**Authors**: {authors}\n\n{abstract}\n\n"
        )

        lines.append("---\n\n")

    lines = lines[:1] + ["\n".join(f"- {t}" for t in toc)] + lines[1:]
    os.makedirs(os.path.dirname(md_path), exist_ok=True)
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("".join(lines))

    logging.info("arXiv papers (%s) written to `%s`.", subject, md_path)


def run_arxiv(args, md_path: str, csv_path: str, date_str: str):
    """Run arXiv."""
    date = (
        (datetime.date.today() - datetime.timedelta(days=args.arxiv_num_days))
        .isoformat()
        .replace("-", "")
    )

    papers = arxiv_fetcher.fetch_arxiv_papers(subject=args.arxiv, date=date)
    if not papers:
        logging.warning("No papers fetched, exiting.")
        return None

    df = pd.DataFrame(papers)
    df = _translate_papers(
        df, KEY_TITLE, args.target_langs or ("de", "zh"), source_lang="en"
    )
    df = df[sorted(df.columns)]

    os.makedirs(os.path.dirname(csv_path), exist_ok=True)
    df.to_csv(csv_path)
    logging.info("[%s] Papers from arXiv are written to `%s`.", args.arxiv, csv_path)

    convert_arxiv_csv_to_md(csv_path, md_path, date_str, args.arxiv)

    return md_path, csv_path


def main():
    """Main."""
    df = pd.read_csv("testdata/arxiv-cs__DC.csv")
    df = _translate_papers(df, KEY_TITLE, ("de", "zh"))
    logging.info(df)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format=utils.LOGGING_FORMAT)
    main()

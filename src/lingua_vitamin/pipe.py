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


_BATCH_MODE = -1
_SUFFIX_CSV = ".csv"
_SUFFIX_MD = ".md"

LANGUAGE_MAP = {
    "de": "German",
    "en": "English",
    "es": "Spanish",
    "fr": "French",
    "zh": "Chinese",
}

MAX_ARXIV_ABSTRACTS = 300

KEY_ABSTRACT = arxiv_fetcher.KEY_ABSTRACT
KEY_TITLE = arxiv_fetcher.KEY_TITLE

_TEMPLATE = (
    """
---
title: "TITLE"
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
    _git_run("checkout", base_branch)
    _git_run("pull", "origin", base_branch)

    _git_run("checkout", "-b", branch_name)
    if isinstance(file_path, str):
        file_path = [file_path]
    for file in file_path:
        _git_run("add", file)
    _git_run("commit", "-m", f"Add {branch_name}.")
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


def _translate_text(trans, text):
    gen_text = trans.translate([text])
    if gen_text is None:
        logging.warning("No valid translation for text: `%s`.", text)
        return None

    return gen_text[0]


def split_batches(lst, batch_size: int = 5):
    """Split into batches."""
    return [lst[i : i + batch_size] for i in range(0, len(lst), batch_size)]


def _translate_texts(trans, texts, batch: int = 1):
    """Batch mode."""
    results = []

    logging.info(
        "Translation in batch mode: bs = %d for %d texts ...", batch, len(texts)
    )

    if batch == 1:
        for index, text in enumerate(texts):
            if index and not index % 50:
                logging.info("   [%d/ %d] ...", index, len(texts))
            results.append(_translate_text(trans, text))
        return results

    if batch == _BATCH_MODE or len(texts) <= batch:
        results = trans.translate(texts)
        if results is None:
            return [None] * len(texts)
        return results

    # Any other batch values
    groups = split_batches(texts, batch)
    for group in groups:
        results += _translate_texts(trans, group, batch=_BATCH_MODE)
    return results


def _translate_news(articles, source_lang: str, target_langs):
    translators = {target: Translator(source_lang, target) for target in target_langs}

    translated_articles = []
    for article in articles:
        # Seems probablematic for empty content.
        content = article["content"]

        translations = {}
        for target, trans in translators.items():
            # If either is too long, we'll skip its translation.
            gen_title = _translate_text(trans, article[KEY_TITLE])
            if gen_title is None:
                continue

            gen_content = _translate_text(trans, content) if content.strip() else ""
            if gen_content is None:
                continue

            translations[target] = {
                KEY_TITLE: gen_title,
                "content": gen_content,
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
    aug_abstracts = defaultdict(lambda: [])

    titles = df[column]
    abstracts = df[KEY_ABSTRACT]

    for target, trans in translators.items():
        logging.info("Processing target lang: `%s` ...", target)
        # Global batch mode for `title`
        for index, batch_size in enumerate((1500, 5)):
            new_titles = _translate_texts(trans, titles, batch=batch_size)

            if all(t is None for t in new_titles):
                logging.warning(
                    "Batch size %d: All none values for the translation.", batch_size
                )
                if index == 0:
                    continue

            aug_titles[target] = [(t or "") for t in new_titles]
            break

        # Batch mode for `abstract`: bs = 5
        if target in ("zh",):
            new_abs = [
                (t or "")
                for t in _translate_texts(
                    trans, abstracts[:MAX_ARXIV_ABSTRACTS], batch=1
                )
            ]
            if len(new_abs) < len(abstracts):
                new_abs += [""] * (len(abstracts) - len(new_abs))
            aug_abstracts[target] = new_abs

    for target in target_langs:
        df[f"{column}-{target}"] = aug_titles[target]

        col = f"{KEY_ABSTRACT}-{target}"
        if target in aug_abstracts:
            df[col] = aug_abstracts[target]

    return df


def convert_news_csv_to_md(csv_path, md_path, date_str, source_lang, target_langs):
    """Convert news csv to md."""
    df = pd.read_csv(csv_path)

    lines = [
        _TEMPLATE.replace(
            "TITLE",
            f"{LANGUAGE_MAP.get(source_lang, '')} News for {date_str}: {len(df):03d}",
        ).replace("DATE", date_str),
        "\n\n",
    ]
    toc = []

    for i, row in df.iterrows():
        lines.append(f"## Article {i}\n")

        lines.append(f"### Original ({source_lang}):\n")
        title, content = row[f"title-{source_lang}"], row[f"content-{source_lang}"]
        lines.append(f"**Title:** {title}\n\n{content}\n\n")

        summary = title
        summary = f"[[{i:02d}] {title}](#article-{i})"
        for target in ("de", "en", "zh"):
            if target in target_langs:
                summary += " | " + row[f"title-{target}"]
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
    df = pd.read_csv(csv_path)

    lines = [
        _TEMPLATE.replace("TITLE", f"{subject} @ {date_str}: {len(df):03d}").replace(
            "DATE", date_str
        ),
        "\n\n",
    ]
    toc = []

    prev_date = None
    for i, row in df.iterrows():
        lines.append(f"## Article {i}\n")

        title = row[KEY_TITLE]
        abstract = row[KEY_ABSTRACT]
        date = row[arxiv_fetcher.KEY_DATE][:10]
        authors = row[arxiv_fetcher.KEY_AUTHORS]
        url = row[arxiv_fetcher.KEY_URL]

        short_title = title
        short_date = "-".join(date.split("-")[1:])
        short_url = url.split("/")[-1]

        week_day = datetime.datetime.strptime(date, "%Y-%m-%d").weekday() + 1
        if short_date != prev_date:
            prev_date = short_date
            short_date = f"**{short_date} ({week_day})**"

        for lang in ("de", "zh"):
            col = f"{KEY_TITLE}-{lang}"
            title += " |"
            if col in row:
                title += f" {row[col]}"

            col = f"{KEY_ABSTRACT}-{lang}"
            if col in row:
                abstract += f"\n\n{row[col]}"

        # TOC
        toc.append(
            f"[{i:02d}](#article-{i}) | {short_date} | {title} | [{short_url}]({url})"
        )

        # Body
        lines.append(
            "\n\n".join(
                (
                    f"### Title@{date} ({week_day}): {short_title}",
                    f"**Title**: {title} [{short_url}]({url})",
                    f"**Authors** ({len(authors.split(','))}): {authors}",
                    abstract,
                    "",
                )
            )
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

    papers = arxiv_fetcher.fetch_arxiv_papers(
        subject=args.arxiv, date=date, top_n=args.num_articles
    )
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
    logging.info("Translating ...")
    df = _translate_papers(df, KEY_TITLE, ("de", "zh"))
    logging.info("Columns: `%s`", list(df.columns))
    logging.info(df.transpose())


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format=utils.LOGGING_FORMAT)
    main()

# LinguaVitamin


## 1. 📖 Overview

**LinguaVitamin** is a multilingual reading and translation project designed to help learners improve their language skills through real-world content.
- It provides daily news headlines and weekly arXiv paper summaries in German, English and Chinese.
- The project supports both language acquisition and technical reading habits.


Checkout related repositories below for artifacts:

| Index | Category | Translation                                    | Github Repo                                                        | Github Pages                                | Update Frequency |
|-------|----------|------------------------------------------------|--------------------------------------------------------------------|---------------------------------------------|------------------|
| 1     | News     | `de` → `{en, zh}`<br>`en` → `{de, es, fr, zh}` | [LinguaVitaminNews](https://github.com/sliuxl/LinguaVitaminNews)   | https://sliuxl.github.io/LinguaVitaminNews  | **Daily**        |
| 2     | arXiv    | `en` → `{de, zh}`                              | [LinguaVitaminArxiv](https://github.com/sliuxl/LinguaVitaminArxiv) | https://sliuxl.github.io/LinguaVitaminArxiv | Weekly           |



## 2. 🌐 Features

- 🧠 **Language Learning Friendly**: Helps learners enhance vocabulary and fluency in a realistic context
- 📅 **Regular Updates**: Automatically fetches daily news headlines and weekly arXiv paper summaries
- 🌍 **Multilingual Translation** for news and papers:
  - German → English & Chinese: N.A. for arXiv papers
  - English → Spanish, German, French & Chinese
- 📁 **Markdown and CSV Outputs**:
  - Markdown files for easy reading
    * Its content is sent to receipt emails at the same time
  - CSV files for structured data analysis


## 3. 📂 Repository Structure

1. This repository (`LinguaVitamin`) contains the logic and core scripts
2. Outputs are structured as follows:
   1. Daily news output is stored in [LinguaVitaminNews](https://github.com/sliuxl/LinguaVitaminNews)
      - Example: [_posts/news/2025/06/2025-06-01--news-de.md](https://github.com/sliuxl/LinguaVitaminNews/blob/main/_posts/news/2025/06/2025-06-01--news-de.md)
   1. Weekly arXiv papers output is stored in [LinguaVitaminArxiv](https://github.com/sliuxl/LinguaVitaminArxiv)
      - Example: [_posts/arxiv/2025/06/2025-06-01--arxiv-cs__DC.md](https://github.com/sliuxl/LinguaVitaminArxiv/blob/main/_posts/arxiv/2025/06/2025-06-01--arxiv-cs__DC.md)


News output is structured as follows, and arXiv papers are similar:
```
LinguaVitaminNews
├── _posts
│   └── news
│       └── YYYY
│           └── MM
│               └── YYYY-MM-DD--news-$SOURCE_LANGUAGE.md
└── csv
    └── news
        └── YYYY
            └── MM
                └── YYYY-MM-DD--news-$SOURCE_LANGUAGE.md
```


## 4. ⚙️  How It Works

- Uses GitHub Actions to run daily
- Fetches news via RSS feeds, e.g., Deutsche Welle, Economist, etc
- Queries arXiv API for new papers in selected categories
- Applies translation models or APIs (HuggingFace LLMs)
  * For news titles and content
    - German → English & Chinese
    - English → German & Chinese
  * For arXiv paper titles only (~~abstract~~)
    - English → German & Chinese
- Saves output into both Markdown and CSV formats


## 5. 🚀 Getting Started

You can:
- Fork this repo and schedule your own GitHub Action
- Customize the feeds, languages and directions
- Extend to other domains, e.g. scientific categories, blog posts, etc


## 6. 🔍 Limitations

- Current LLMs are likely not the SOTA for translation, and they do make mistakes
- Current LLMs support limited sequence length up to `512` *only*, therefore we
  * **Drop** news with too long title or content
  * *Skip* arXiv paper translation with too long titles


## 7. 🧑💻 Author

Developed by [@sliuxl](https://github.com/sliuxl) over a weekend,
as a personal language-learning tool and NLP playground.


## 8. License

MIT license.

---

Enjoy your daily dose of linguistic vitamins!

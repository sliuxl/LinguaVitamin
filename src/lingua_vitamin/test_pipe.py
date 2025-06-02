"""Unit tests for pipe.py."""

import logging
import os
import tempfile
import unittest

from parameterized import parameterized

from lingua_vitamin import pipe
from lingua_vitamin.common import utils


_PWD = os.path.dirname(os.path.abspath(__file__))

_DATE = "2025-06-01"

_MD_CONTENT_DE = """
---
title: "German News for 2025-06-01: 003"
date: 2025-06-01
layout: post
---

- [[00] Merz trifft am Donnerstag Trump im Weißen Haus](#article-0) | Merz meets Trump at the White House on Thursday | 梅兹星期四在白宫见特朗普
- [[01] News kompakt: Merz spricht Einladung an Trump aus](#article-1) | News compact: Merz gives invitation to Trump | 新闻报道: Merz正在向特朗普发出邀请
- [[02] Die außenpolitischen Baustellen des Friedrich Merz](#article-2) | The foreign-policy construction sites of Friedrich Merz | Friedrich Merz的外交政策工程

## Article 0
### Original (de):
**Title:** Merz trifft am Donnerstag Trump im Weißen Haus

Es hat etwas gedauert, aber jetzt hat der Kanzler endlich einen Termin im Weißen Haus. Nach Kyjiw dürfte es die wichtigste Reise in den ersten Wochen seiner Amtszeit werden.

### Translation (en):
**Title:** Merz meets Trump at the White House on Thursday

It took some time, but now the chancellor finally has an appointment in the White House. It should be the most important trip to Kyyiv in the first weeks of his term.

### Translation (zh):
**Title:** 梅兹星期四在白宫见特朗普

花了点时间,但现在议长终于在白宫预约了. 在京城之后,这将是他任期首周最重要的旅行.

---

## Article 1
### Original (de):
**Title:** News kompakt: Merz spricht Einladung an Trump aus

Der neue Bundeskanzler hat ein erstes Telefonat mit dem US-Präsidenten geführt. Zum 80. Mal feiert Moskau den Sieg der Sowjetunion über Nazi-Deutschland. Das Wichtigste in Kürze.

### Translation (en):
**Title:** News compact: Merz gives invitation to Trump

The new chancellor conducted a first telephone call with the US President. For the 80th time Moscow celebrates the victory of the Soviet Union over Nazi Germany. The most important thing in brief.

### Translation (zh):
**Title:** 新闻报道: Merz正在向特朗普发出邀请

新的德国总理和美国总统进行了第一次通话. 莫斯科80周年纪念苏联在纳粹德国的胜利. 最重要的是,即将到来.

---

## Article 2
### Original (de):
**Title:** Die außenpolitischen Baustellen des Friedrich Merz

Die künftige Bundesregierung dürfte dank kreditfinanzierter Sondervermögen viel finanziellen Spielraum haben. Doch es warten große außenpolitische Herausforderungen auf sie, und fast alle haben mit Donald Trump zu tun.

### Translation (en):
**Title:** The foreign-policy construction sites of Friedrich Merz

The future federal government is likely to have a lot of financial room for manoeuvre thanks to loan-financed special assets. However, there are major foreign policy challenges waiting for them, and almost all of them have to do with Donald Trump.

### Translation (zh):
**Title:** Friedrich Merz的外交政策工程

未来的联邦政府可能有很多财政空间,因为有贷款支持的特许权. 但是,他们正面临巨大的外交政策挑战,几乎所有人都与唐纳德·特朗普有关.

---
""".strip()

_MD_CONTENT_EN = """
---
title: "English News for 2025-06-01: 002"
date: 2025-06-01
layout: post
---

- [[00] Elizabeth Hurley's debut with Billy Ray Cyrus, Jennifer Lopez’s daring dress mark week of red carpet moments](#article-0) | Elizabeth Hurley's Debüt mit Billy Ray Cyrus, Jennifer Lopez's wagemutige Kleid Mark Woche roter Teppich Momente | 伊丽莎白·赫里与比利·雷·雷·赛勒斯的首演,珍妮弗·洛佩斯的大胆裙子标志红地毯时刻一周
- [[01] Dodgers star Mookie Betts sustains freak toe injury while walking to bathroom](#article-1) | Dodgers Star Mookie Betts hält Freak Zee Verletzung beim Gehen zum Bad | 道奇明星明星Mookie Betts在步行上厕所时 一直保持脚趾畸形受伤状态

## Article 0
### Original (en):
**Title:** Elizabeth Hurley's debut with Billy Ray Cyrus, Jennifer Lopez’s daring dress mark week of red carpet moments

Elizabeth Hurley and Billy Ray Cyrus made their red carpet debut at an event in Rome, while Jennifer Lopez stunned as the host of the American Music Awards.

### Translation (de):
**Title:** Elizabeth Hurley's Debüt mit Billy Ray Cyrus, Jennifer Lopez's wagemutige Kleid Mark Woche roter Teppich Momente

Elizabeth Hurley und Billy Ray Cyrus gaben ihr rotes Teppichdebüt bei einer Veranstaltung in Rom, während Jennifer Lopez als Gastgeberin der American Music Awards staunte.

### Translation (zh):
**Title:** 伊丽莎白·赫里与比利·雷·雷·赛勒斯的首演,珍妮弗·洛佩斯的大胆裙子标志红地毯时刻一周

Elizabeth Hurley和Billy Ray Cyrus在罗马的一次活动上首次出演红地毯,而Jennifer Lopez则震惊地成为美国音乐奖的主办人。

---

## Article 1
### Original (en):
**Title:** Dodgers star Mookie Betts sustains freak toe injury while walking to bathroom

Los Angeles Dodgers star shortstop Mookie Betts reportedly fractured his toe when he stubbed it while walking to the bathroom in the dark.

### Translation (de):
**Title:** Dodgers Star Mookie Betts hält Freak Zee Verletzung beim Gehen zum Bad

Los Angeles Dodgers star shortstop Mookie Betts soll sich den Zeh gebrochen haben, als er ihn im Dunkeln beim Gehen zum Badezimmer stupste.

### Translation (zh):
**Title:** 道奇明星明星Mookie Betts在步行上厕所时 一直保持脚趾畸形受伤状态

据报告,洛杉矶道奇队明星短站Mookie Betts在黑暗中走进浴室时踩脚趾时,脚趾骨折。

---
""".strip()


_MD_CONTENT_ARXIV_DC = """
---
title: "cs.DC @ 2025-06-01: 001"
date: 2025-06-01
layout: post
---

- [00](#article-0) | **05-29 (4)** | From Connectivity to Autonomy: The Dawn of Self-Evolving Communication   Systems | $GERMAN_TITLE | $CHINESE_TITLE | [2505.23710v1](http://arxiv.org/abs/2505.23710v1)

## Article 0
### Title@2025-05-29 (4): From Connectivity to Autonomy: The Dawn of Self-Evolving Communication   Systems

**Title**: From Connectivity to Autonomy: The Dawn of Self-Evolving Communication   Systems | $GERMAN_TITLE | $CHINESE_TITLE [2505.23710v1](http://arxiv.org/abs/2505.23710v1)

**Authors** (5): Zeinab Nezami, Syed Danial Ali Shah, Maryam Hafeez, Karim Djemame, Syed Ali Raza Zaidi

This paper envisions 6G as a self-evolving telecom ecosystem, where AI-driven intelligence enables dynamic adaptation beyond static connectivity. We explore the key enablers of autonomous communication systems, spanning reconfigurable infrastructure, adaptive middleware, and intelligent network functions, alongside multi-agent collaboration for distributed decision-making. We explore how these methodologies align with emerging industrial IoT frameworks, ensuring seamless integration within digital manufacturing processes. Our findings emphasize the potential for improved real-time decision-making, optimizing efficiency, and reducing latency in networked control systems. The discussion addresses ethical challenges, research directions, and standardization efforts, concluding with a technology stack roadmap to guide future developments. By leveraging state-of-the-art 6G network management techniques, this research contributes to the next generation of intelligent automation solutions, bridging the gap between theoretical advancements and real-world industrial applications.

$GERMAN_ABSTRACT

$CHINESE_ABSTRACT

---
""".strip()

_MD_CONTENT_ARXIV_PL = r"""
---
title: "cs.PL @ 2025-06-01: 003"
date: 2025-06-01
layout: post
---

- [00](#article-0) | **05-29 (4)** | Extensional and Non-extensional Functions as Processes | | | [2405.03536v2](http://arxiv.org/abs/2405.03536v2)
- [01](#article-1) | 05-29 | Quantitative Verification with Neural Networks | | | [2301.06136v5](http://arxiv.org/abs/2301.06136v5)
- [02](#article-2) | **05-30 (5)** | Is spreadsheet syntax better than numeric indexing for cell selection? | | | [2505.23296v1](http://arxiv.org/abs/2505.23296v1)

## Article 0
### Title@2025-05-29 (4): Extensional and Non-extensional Functions as Processes

**Title**: Extensional and Non-extensional Functions as Processes | | [2405.03536v2](http://arxiv.org/abs/2405.03536v2)

**Authors** (2): Ken Sakayori, Davide Sangiorgi

Following Milner's seminal paper, the representation of functions as processes has received considerable attention. For pure $\lambda$-calculus, the process representations yield (at best) non-extensional $\lambda $-theories (i.e., $\beta$ rule holds, whereas $\eta$ does not).   In the paper, we study how to obtain extensional representations, and how to move between extensional and non-extensional representations. Using Internal $\pi$, $\mathrm{I}\pi$ (a subset of the $\pi$-calculus in which all outputs are bound), we develop a refinement of Milner's original encoding of functions as processes that is parametric on certain abstract components called wires. These are, intuitively, processes whose task is to connect two end-point channels. We show that when a few algebraic properties of wires hold, the encoding yields a $\lambda$-theory. Exploiting the symmetries and dualities of $\mathrm{I}\pi$, we isolate three main classes of wires. The first two have a sequential behaviour and are dual of each other; the third has a parallel behaviour and is the dual of itself. We show the adoption of the parallel wires yields an extensional $\lambda$-theory; in fact, it yields an equality that coincides with that of B\"ohm trees with infinite $\eta$. In contrast, the other two classes of wires yield non-extensional $\lambda$-theories whose equalities are those of the L\'evy-Longo and B\"ohm trees.

---

## Article 1
### Title@2025-05-29 (4): Quantitative Verification with Neural Networks

**Title**: Quantitative Verification with Neural Networks | | [2301.06136v5](http://arxiv.org/abs/2301.06136v5)

**Authors** (5): Alessandro Abate, Alec Edwards, Mirco Giacobbe, Hashan Punchihewa, Diptarko Roy

We present a data-driven approach to the quantitative verification of probabilistic programs and stochastic dynamical models. Our approach leverages neural networks to compute tight and sound bounds for the probability that a stochastic process hits a target condition within finite time. This problem subsumes a variety of quantitative verification questions, from the reachability and safety analysis of discrete-time stochastic dynamical models, to the study of assertion-violation and termination analysis of probabilistic programs. We rely on neural networks to represent supermartingale certificates that yield such probability bounds, which we compute using a counterexample-guided inductive synthesis loop: we train the neural certificate while tightening the probability bound over samples of the state space using stochastic optimisation, and then we formally check the certificate's validity over every possible state using satisfiability modulo theories; if we receive a counterexample, we add it to our set of samples and repeat the loop until validity is confirmed. We demonstrate on a diverse set of benchmarks that, thanks to the expressive power of neural networks, our method yields smaller or comparable probability bounds than existing symbolic methods in all cases, and that our approach succeeds on models that are entirely beyond the reach of such alternative techniques.

---

## Article 2
### Title@2025-05-30 (5): Is spreadsheet syntax better than numeric indexing for cell selection?

**Title**: Is spreadsheet syntax better than numeric indexing for cell selection? | | [2505.23296v1](http://arxiv.org/abs/2505.23296v1)

**Authors** (3): Philip Heltweg, Dirk Riehle, Georg-Daniel Schwarz

Selecting a subset of cells is a common task in data engineering, for example, to remove errors or select only specific parts of a table. Multiple approaches to express this selection exist. One option is numeric indexing, commonly found in general programming languages, where a tuple of numbers identifies the cell. Alternatively, the separate dimensions can be referred to using different enumeration schemes like "A1" for the first cell, commonly found in software such as spreadsheet systems.   In a large-scale controlled experiment with student participants as proxy for data practitioners, we compare the two options with respect to speed and correctness of reading and writing code.   The results show that, when reading code, participants make less mistakes using spreadsheet-style syntax. Additionally, when writing code, they make fewer mistakes and are faster when using spreadsheet syntax compared to numeric syntax.   From this, a domain-specific syntax, such as spreadsheet syntax for data engineering, appears to be a promising alternative to explore in future tools to support practitioners without a software engineering background.

---
""".strip()


class TestPipe(unittest.TestCase):
    """Unit tests for pipe.py."""

    @parameterized.expand(
        (
            ("de", ("en", "zh"), "testdata/news-de.csv", _MD_CONTENT_DE),
            ("en", ("de", "zh"), "testdata/news-en.csv", _MD_CONTENT_EN),
        )
    )
    def test_convert_news_csv_to_md(
        self, source_lang, target_langs, csv_path, expected_content
    ):
        """Unit test for convert_news_csv_to_md."""
        with tempfile.TemporaryDirectory() as temp_dir:
            md_path = os.path.join(temp_dir, "test.md")
            pipe.convert_news_csv_to_md(
                os.path.join(_PWD, csv_path),
                md_path,
                _DATE,
                source_lang,
                target_langs,
            )

            self.assertTrue(os.path.exists(md_path))
            self.assertEqual(utils.load_file(md_path).strip(), expected_content)

    @parameterized.expand(
        (
            ("cs.DC", "testdata/arxiv-cs__DC.csv", _MD_CONTENT_ARXIV_DC),
            ("cs.PL", "testdata/arxiv-cs__PL.csv", _MD_CONTENT_ARXIV_PL),
        )
    )
    def test_convert_arxiv_csv_to_md(self, subject, csv_path, expected_content):
        """Unit test for convert_arxiv_csv_to_md."""
        self.maxDiff = None
        with tempfile.TemporaryDirectory() as temp_dir:
            md_path = os.path.join(temp_dir, "test.md")
            pipe.convert_arxiv_csv_to_md(
                os.path.join(_PWD, csv_path),
                md_path,
                _DATE,
                subject,
            )

            self.assertTrue(os.path.exists(md_path))
            self.assertEqual(utils.load_file(md_path).strip(), expected_content)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format=utils.LOGGING_FORMAT)
    unittest.main()

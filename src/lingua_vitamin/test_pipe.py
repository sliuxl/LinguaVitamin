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
title: German News for 2025-06-01
date: 2025-06-01
layout: post
---

- [[00] Merz trifft am Donnerstag Trump im Weißen Haus | Merz meets Trump at the White House on Thursday | 梅兹星期四在白宫见特朗普](#article-0)
- [[01] News kompakt: Merz spricht Einladung an Trump aus | News compact: Merz gives invitation to Trump | 新闻报道: Merz正在向特朗普发出邀请](#article-1)
- [[02] Die außenpolitischen Baustellen des Friedrich Merz | The foreign-policy construction sites of Friedrich Merz | Friedrich Merz的外交政策工程](#article-2)

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
title: English News for 2025-06-01
date: 2025-06-01
layout: post
---

- [[00] Elizabeth Hurley's debut with Billy Ray Cyrus, Jennifer Lopez’s daring dress mark week of red carpet moments | Elizabeth Hurley's Debüt mit Billy Ray Cyrus, Jennifer Lopez's wagemutige Kleid Mark Woche roter Teppich Momente | 伊丽莎白·赫里与比利·雷·雷·赛勒斯的首演,珍妮弗·洛佩斯的大胆裙子标志红地毯时刻一周](#article-0)
- [[01] Dodgers star Mookie Betts sustains freak toe injury while walking to bathroom | Dodgers Star Mookie Betts hält Freak Zee Verletzung beim Gehen zum Bad | 道奇明星明星Mookie Betts在步行上厕所时 一直保持脚趾畸形受伤状态](#article-1)

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


class TestFetcher(unittest.TestCase):
    """Unit tests for pipe.py."""

    @parameterized.expand(
        (
            ("de", ("en", "zh"), "testdata/news-de.csv", _MD_CONTENT_DE),
            ("en", ("de", "zh"), "testdata/news-en.csv", _MD_CONTENT_EN),
        )
    )
    def test_convert_csv_to_md(
        self, source_lang, target_langs, csv_path, expected_content
    ):
        """Unit test for convert_csv_to_md."""
        with tempfile.TemporaryDirectory() as temp_dir:
            md_path = os.path.join(temp_dir, "test.md")
            pipe.convert_csv_to_md(
                os.path.join(_PWD, csv_path),
                md_path,
                _DATE,
                source_lang,
                target_langs,
            )

            self.assertTrue(os.path.exists(md_path))
            self.assertEqual(utils.load_file(md_path).strip(), expected_content)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format=utils.LOGGING_FORMAT)
    unittest.main()

import subprocess
import sys
import unittest

from srt_fit_id import parse_srt, reflow_srt, wrap_caption


class WrapCaptionTests(unittest.TestCase):
    def test_wraps_at_words_without_exceeding_character_limit(self):
        lines = wrap_caption("Ini adalah contoh teks subtitle Bahasa Indonesia.", max_chars=20, max_lines=3)
        self.assertEqual(lines, ["Ini adalah contoh", "teks subtitle Bahasa", "Indonesia."])
        self.assertTrue(all(len(line) <= 20 for line in lines))

    def test_rejects_a_word_or_caption_that_cannot_fit(self):
        with self.assertRaisesRegex(ValueError, "kata yang lebih panjang"):
            wrap_caption("superpanjang", max_chars=5, max_lines=2, cue_index="4")
        with self.assertRaisesRegex(ValueError, "memerlukan 4 baris"):
            wrap_caption("satu dua tiga empat lima", max_chars=8, max_lines=2, cue_index="8")


class SrtTests(unittest.TestCase):
    def test_preserves_cue_ids_and_timestamps_while_reflowing(self):
        source = (
            "1\r\n00:00:01,000 --> 00:00:03,500\r\n"
            "Ini adalah contoh teks subtitle Bahasa Indonesia.\r\n\r\n"
            "2\r\n00:00:04.000 --> 00:00:05.000\r\nHalo semua."
        )
        result = reflow_srt(source, max_chars=20, max_lines=3)
        self.assertEqual(result, (
            "1\n00:00:01,000 --> 00:00:03,500\n"
            "Ini adalah contoh\nteks subtitle Bahasa\nIndonesia.\n\n"
            "2\n00:00:04.000 --> 00:00:05.000\nHalo semua."
        ))
        cues = parse_srt(result)
        self.assertEqual([cue.index for cue in cues], ["1", "2"])
        self.assertEqual(cues[0].timecode, "00:00:01,000 --> 00:00:03,500")

    def test_preserves_optional_timestamp_settings(self):
        source = "1\n00:00:01,000 --> 00:00:02,000 X1:10 X2:20\nHalo."
        result = reflow_srt(source)
        self.assertIn("00:00:01,000 --> 00:00:02,000 X1:10 X2:20", result)

    def test_rejects_invalid_structure_duplicate_ids_and_time_range(self):
        invalid = [
            "1\n00:00:01,000 --> 00:00:02,000",
            "x\n00:00:01,000 --> 00:00:02,000\nHalo",
            "1\n00:00:03,000 --> 00:00:02,000\nHalo",
            "1\n00:00:01,999 --> 00:00:01,999\nHalo",
            "1\n00:00:01,000 --> 00:00:02,000\nHalo\n\n1\n00:00:03,000 --> 00:00:04,000\nLagi",
        ]
        for value in invalid:
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    reflow_srt(value)

    def test_empty_srt_and_invalid_limits(self):
        self.assertEqual(reflow_srt("  \n"), "")
        for max_chars, max_lines in ((0, 2), (10, 0), (True, 2)):
            with self.subTest(max_chars=max_chars, max_lines=max_lines):
                with self.assertRaises(ValueError):
                    reflow_srt("", max_chars=max_chars, max_lines=max_lines)

    def test_cli_reads_srt_and_reports_errors_without_echoing_caption(self):
        source = "1\n00:00:01,000 --> 00:00:02,000\nIni contoh subtitle yang panjang sekali."
        result = subprocess.run(
            [sys.executable, "-m", "srt_fit_id", "--max-chars", "18", "--max-lines", "3"],
            input=source,
            text=True,
            capture_output=True,
            check=True,
        )
        self.assertIn("00:00:01,000 --> 00:00:02,000", result.stdout)
        self.assertTrue(all(len(line) <= 18 for line in result.stdout.splitlines()[2:]))

        invalid = subprocess.run(
            [sys.executable, "-m", "srt_fit_id", "--max-chars", "8", "--max-lines", "1"],
            input=source,
            text=True,
            capture_output=True,
        )
        self.assertEqual(invalid.returncode, 2)
        self.assertEqual(invalid.stdout, "")
        self.assertNotIn("Ini contoh subtitle", invalid.stderr)


if __name__ == "__main__":
    unittest.main()

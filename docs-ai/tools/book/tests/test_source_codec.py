"""Exact-source and deterministic-envelope checks for compact book payloads."""
import base64
import gzip
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from book import source_codec as codec


class SourceCodecTests(unittest.TestCase):
    def encode(self, raw, name="sample.c", aliases=None):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        source = root / name
        source.write_bytes(raw)
        return codec.encode_source(source, root / "cache", aliases), source, root

    @staticmethod
    def text(record):
        return "".join(text for _, text in record["tokens"])

    def test_exact_unicode_tabs_bom_and_all_line_endings(self):
        raw = "\ufeff/* café 😀\r\n\tcontinued */\rint x = 1;\n".encode()
        record, _, _ = self.encode(raw)
        self.assertEqual(self.text(record).encode(), raw)
        self.assertNotIn("raw_base64", record)
        self.assertEqual(record["line_count"], 3)
        self.assertEqual(record["sha256"], hashlib.sha256(raw).hexdigest())

    def test_invalid_utf8_download_preserves_original_bytes(self):
        raw = b"/* \xff \xc3( \xed\xa0\x80 */\r\n"
        record, _, _ = self.encode(raw)
        self.assertEqual(base64.b64decode(record["raw_base64"]), raw)
        self.assertEqual(self.text(record), raw.decode("utf-8", errors="replace"))
        self.assertEqual(record["line_count"], 1)

    def test_line_count_does_not_treat_formfeeds_as_newlines(self):
        for text, expected in [
            ("", 0), ("\n", 1), ("\r\n", 1), ("a", 1),
            ("a\r\nb\rc\n", 3), ("\n\n", 2), ("a\n\nb", 3),
            ("a\fb\u2028c\u0085d", 1), ("a\r\n\n", 2),
        ]:
            with self.subTest(text=text):
                self.assertEqual(codec.line_count(text), expected)

    def test_no_final_newline_is_preserved(self):
        for raw in (b"", b"int x;", b"\n\nint x;\n\n"):
            with self.subTest(raw=raw):
                record, _, _ = self.encode(raw)
                self.assertEqual(self.text(record).encode(), raw)

    def test_multiline_lexer_state_and_class_table(self):
        text = "/* first\n   second */\nint x = 1;\n"
        record, _, _ = self.encode(text.encode())
        self.assertEqual(self.text(record), text)
        comment = [(record["styles"][index], value)
                   for index, value in record["tokens"] if "second" in value]
        self.assertEqual(comment, [("cm", "/* first\n   second */")])
        self.assertIn("kt", record["styles"])
        self.assertIn("mi", record["styles"])
        for index, _ in record["tokens"]:
            self.assertTrue(0 <= index < len(record["styles"]))
        for previous, current in zip(record["tokens"], record["tokens"][1:]):
            self.assertNotEqual(previous[0], current[0])

    def test_unknown_extension_uses_plain_text_without_losing_markup(self):
        text = '<script>& "text"</script>\n\t# token'
        record, _, _ = self.encode(text.encode(), "file.unknown_xnu_extension")
        self.assertEqual(record["styles"], [""])
        self.assertEqual(record["tokens"], [[0, text]])

    def test_cache_is_content_addressed_and_not_polluted_by_metadata(self):
        record, source, root = self.encode(b"int x;\n", aliases={"x": 1})
        record["path"] = "not-stored"
        record["tokens"][0][1] = "caller mutation"
        with patch.object(codec, "_tokenize", side_effect=AssertionError("cache miss")):
            again = codec.encode_source(source, root / "cache", {"other": 1})
        self.assertEqual(self.text(again), "int x;\n")
        self.assertEqual(again["aliases"], {"other": 1})
        self.assertNotIn("path", again)
        source.write_bytes(b"int y;\n")
        changed = codec.encode_source(source, root / "cache")
        self.assertEqual(self.text(changed), "int y;\n")
        self.assertNotEqual(changed["sha256"], again["sha256"])

    def test_pack_is_deterministic_and_generic(self):
        for value in ({"x": "😀\n</script>", "n": 1}, ["query", 42], "<h1>Index</h1>"):
            with self.subTest(value=value):
                first = codec.pack(value)
                self.assertEqual(first, codec.pack(value))
                self.assertEqual(codec.unpack(first), value)
                encoded = base64.b64decode(first["data"])
                self.assertEqual(encoded[4:8], b"\0\0\0\0")
                self.assertEqual(encoded[9], 255)
                self.assertEqual(json.loads(gzip.decompress(encoded)), value)
                self.assertTrue(json.dumps(first).isascii())

    def test_unpack_rejects_unknown_format(self):
        for envelope in (
            {"schema": 1, "encoding": "gzip-base64", "data": ""},
            {"schema": 2, "encoding": "plain", "data": ""},
        ):
            with self.subTest(envelope=envelope):
                with self.assertRaises(ValueError):
                    codec.unpack(envelope)


if __name__ == "__main__":
    unittest.main()

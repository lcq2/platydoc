# SPDX-License-Identifier: GPL-2.0-only
"""Shared requests and independent ARM64 Darwin fixture expectations."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def request(source=None, *, macros=None, records=None):
    result = {
        "target": "aarch64-apple-darwin",
        "main": "/inputs/layouts.c",
        "files": {
            "/inputs/layouts.c": source if source is not None else (ROOT / "fixtures/layouts.c").read_text(),
            "/inputs/types.h": (ROOT / "fixtures/types.h").read_text(),
        },
        "macros": macros or {},
    }
    if records:
        result["records"] = records
    return result


def cases():
    return [
        ("undefined", request(macros={"FLAG": None})),
        ("zero", request(macros={"FLAG": "0"})),
        ("one", request(macros={"FLAG": "1"})),
        ("selected-closure", request(records=["Outer", "Anonymous", "Flexible"])),
        ("syntax-error", request("struct Valid { int x; }; struct Broken { int x;")),
        ("missing-header", request('#include <stddef.h>\nstruct Hidden { int x; };')),
        ("host-header-denied", request('#include "/usr/include/stdio.h"\nstruct Hidden { int x; };')),
        ("incomplete", request("struct Forward;", records=["Forward"])),
        ("unknown-type", request("struct Known { int x; };", records=["Unknown"])),
        ("nested-macro-identity", request("#define ONE struct {int x;}\n#define TWO ONE a; ONE b;\nstruct Outer { TWO };")),
        ("unsafe-json-number", request("struct Big { char x[9007199254740993ULL]; };")),
        ("invalid-request", {"target": "host", "main": "/inputs/a.c", "files": {"/inputs/a.c": ""}}),
        ("unknown-target-feature", {**request("struct S { int x; };"), "target_features": ["+platydoc-made-up-feature"]}),
    ]


def validate(name, result):
    if name == "nested-macro-identity":
        assert result["status"] == "ok", result
        assert len(result["records"]) == 3
        assert len({r["id"] for r in result["records"]}) == 3
        return
    if name == "selected-closure":
        assert result["status"] == "ok", result
        by_name = {r["name"]: r for r in result["records"] if r["name"]}
        assert set(by_name) == {"Outer", "Inner", "Payload", "Anonymous", "Flexible"}, by_name
        identities = {r["id"] for r in result["records"]}
        def references(type_info):
            if type_info["kind"] == "array":
                references(type_info["element"])
            elif type_info["kind"] == "record":
                assert type_info["record_id"] in identities, type_info
        for record in result["records"]:
            for field in record["fields"]:
                references(field["type"])
        assert len(result["records"]) == 7
        assert by_name["Outer"]["fields"][1]["type"]["element"]["count"] == 3
        return
    if name not in {"undefined", "zero", "one"}:
        expected = "unsupported-layout" if name in {"nested-macro-identity", "unsafe-json-number"} else (
            "unavailable-type" if name in {"incomplete", "unknown-type"} else (
            "invalid-request" if name in {"invalid-request", "unknown-target-feature"} else "error")
        )
        assert result["status"] == expected, (name, result)
        assert result["records"] == [], (name, "error exposed layouts")
        assert any(d["severity"] in {"error", "fatal"} for d in result["diagnostics"])
        return
    assert result["status"] == "ok", result
    records = result["records"]
    by_name = {r["name"]: r for r in records if r["name"]}
    by_id = {r["id"]: r for r in records}
    assert len(by_id) == len(records), "duplicate record IDs"
    # Explicit byte sizes/alignments and field bit offsets; these do not come
    # from the compiler output being compared.
    expected = {
        "Inner": (4, 2, [0, 16]),
        "Payload": (16, 8, [0, 0]),
        "Outer": (56, 8, [0, 16, 256, 384]),
        "Packed": (5, 1, [0, 8]),
        "PackedAligned": (8, 8, [0, 8]),
        "PragmaPacked": (8, 2, [0, 16, 48]),
        "ExplicitAligned": (32, 16, [0, 128, 160]),
        "Anonymous": (16, 4, [0, 32, 64, 96]),
        "Bits": (8, 4, [0, 3, 5, 32, 32, 48]),
        "PackedBits": (3, 1, [0, 3, 16]),
        "Flexible": (4, 4, [0, 32]),
        "MacroFirst": (4, 4, [0]),
        "MacroSecond": (8, 8, [0]),
        "Conditional": {
            "undefined": (2, 1, [0, 8]),
            "zero": (12, 4, [0, 32, 64]),
            "one": (24, 8, [0, 32, 64, 128]),
        }[name],
    }
    for record_name, (size, alignment, offsets) in expected.items():
        record = by_name[record_name]
        assert record["size_bytes"] == size, (record_name, record)
        assert record["alignment_bytes"] == alignment, (record_name, record)
        assert [f["offset_bits"] for f in record["fields"]] == offsets, (record_name, record)
    fields = by_name["Conditional"]["fields"]
    assert [f["name"] for f in fields] == {
        "undefined": ["head", "tail"],
        "zero": ["head", "present_when_defined", "tail"],
        "one": ["head", "present_when_defined", "present_when_nonzero", "tail"],
    }[name]
    assert [f["bit_width"] for f in by_name["Bits"]["fields"]] == [3, 2, 5, 0, 9, None]
    rows = by_name["Outer"]["fields"][1]["type"]
    assert rows["count"] == 2 and rows["element"]["count"] == 3
    inner = by_id[rows["element"]["element"]["record_id"]]
    assert inner["name"] == "Inner"
    # rows[1][2].tag: rows offset + 1 row stride + 2 element strides + tag.
    assert 16 + rows["element"]["size_bits"] + 2 * inner["size_bytes"] * 8 + 16 == 192
    anonymous = by_name["Anonymous"]["fields"]
    assert anonymous[1]["anonymous_record"] and anonymous[2]["anonymous_record"]
    union = by_id[anonymous[1]["type"]["record_id"]]
    assert union["kind"] == "union" and [f["offset_bits"] for f in union["fields"]] == [0, 0]
    tail = by_name["Flexible"]["fields"][1]["type"]
    assert tail["flexible"] and tail["count"] is None and tail["size_bits"] is None
    assert tail["element"]["size_bits"] == 8

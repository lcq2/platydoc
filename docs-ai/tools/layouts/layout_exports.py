# SPDX-License-Identifier: GPL-2.0-only
"""Read the literal export-variable subset used by surveyed header Makefiles."""
import re
from pathlib import PurePosixPath


def exported_headers(source, makefiles, component="bsd"):
    aliases = {}
    for relative in makefiles:
        makefile = source / relative
        text = makefile.read_text().replace("\\\n", " ")
        if re.search(r"^\s*(?:ifeq|ifneq|ifdef|ifndef|else|endif)\b", text, re.M):
            raise ValueError("Conditional export rules require explicit support: " + relative)
        variables, unsupported = {}, set()
        for line in text.splitlines():
            match = re.fullmatch(r"([A-Z_]+)\s*=\s*(.*?)\s*", line)
            if match:
                variables[match[1]] = match[2].split("#", 1)[0].strip()
            else:
                assignment = re.match(r"\s*(?:(?:override|export|private)\s+)*([A-Z_]+)\s*(?::=|::=|\+=|\?=|!=|=)", line)
                if assignment:
                    unsupported.add(assignment[1])

        def expand(name, stack=()):
            if name in stack or name not in variables or name in unsupported:
                raise ValueError("Unknown/cyclic export variable: " + name)
            value = re.sub(r"\$\{([A-Z_]+)\}|\$\(([A-Z_]+)\)",
                           lambda m: expand(m[1] or m[2], (*stack, name)), variables[name])
            value = re.sub(r"\$\(sort ([^()]*)\)", lambda m: " ".join(sorted(set(m[1].split()))), value)
            if "$" in value:
                raise ValueError("Unsupported Make export expression in " + relative)
            return value

        directory = PurePosixPath(expand("EXPORT_MI_DIR"))
        if directory.is_absolute() or ".." in directory.parts:
            raise ValueError("Invalid export destination")
        for name in expand("EXPORT_MI_LIST").split():
            path = PurePosixPath(name)
            if path.is_absolute() or ".." in path.parts:
                raise ValueError("Invalid exported filename")
            virtual = f"/inputs/exports/{component}/{directory / path}"
            actual = makefile.parent.joinpath(*path.parts)
            if virtual in aliases and aliases[virtual][0].read_bytes() != actual.read_bytes():
                raise ValueError("Conflicting exported header: " + virtual)
            aliases[virtual] = (actual, relative)
    return aliases

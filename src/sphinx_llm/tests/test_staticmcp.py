# SPDX-FileCopyrightText: Copyright (c) 2026, NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
"""Tests for optional StaticMCP artifact generation."""

from __future__ import annotations

import json
from pathlib import Path, PurePosixPath

import pytest

from sphinx_llm.txt import _staticmcp_resource_path


@pytest.mark.parametrize(
    ("uri", "expected"),
    [
        (
            "file://Guide/François Mitterrand.md",
            PurePosixPath("resources/guide/francois_mitterrand_md.json"),
        ),
        (
            "file://guide/King George III.md",
            PurePosixPath("resources/guide/king_george_iii_md.json"),
        ),
    ],
)
def test_staticmcp_resource_path_follows_filename_encoding(uri, expected):
    assert _staticmcp_resource_path(uri) == expected


def test_staticmcp_resource_path_hashes_long_names():
    path = _staticmcp_resource_path(f"file://{'a' * 201}.md")

    assert len(path.name.removesuffix(".json")) == 200
    assert path.name.endswith(".json")


def test_staticmcp_files_include_only_indexed_markdown(build_example_docs):
    _, build_dir, _ = build_example_docs(
        "html",
        {
            "llms_txt_staticmcp_enabled": True,
            "llms_txt_exclude": ["apples", "nested/**"],
        },
    )

    manifest = json.loads((build_dir / "mcp.json").read_text(encoding="utf-8"))
    index = json.loads(
        (build_dir / "resources" / "index.json").read_text(encoding="utf-8")
    )
    resources = manifest["capabilities"]["resources"]

    assert manifest["protocolVersion"] == "2025-06-18"
    assert manifest["capabilities"]["tools"] == []
    assert index == {"resources": resources}
    assert resources
    assert all("apples" not in resource["uri"] for resource in resources)
    assert all("nested/" not in resource["uri"] for resource in resources)

    for resource in resources:
        response_path = build_dir.joinpath(
            *_staticmcp_resource_path(resource["uri"]).parts
        )
        response = json.loads(response_path.read_text(encoding="utf-8"))
        markdown_path = build_dir / Path(resource["uri"].removeprefix("file://"))

        assert response["uri"] == resource["uri"]
        assert response["mimeType"] == "text/markdown"
        assert response["text"] == markdown_path.read_text(encoding="utf-8")


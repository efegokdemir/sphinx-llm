# SPDX-FileCopyrightText: Copyright (c) 2026, NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
"""Tests for the sphinx-llm command-line interface."""

from __future__ import annotations

import json

from sphinx_llm.cli import main


def test_summaries_command_displays_report(tmp_path, capsys):
    report_path = tmp_path / "report.json"
    report_path.write_text(
        json.dumps(
            {
                "version": 1,
                "summaries": [
                    {
                        "target": "guide/setup",
                        "summary": "Install the package.",
                        "origin": "generated",
                        "provider": "openai-compatible",
                        "model": "example-model",
                        "cache_status": "hit",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    assert main(["summaries", "--report", str(report_path)]) == 0
    assert capsys.readouterr().out == (
        "guide/setup (generated)\n"
        "  provider: openai-compatible\n"
        "  model: example-model\n"
        "  cache: hit\n"
        "  summary: Install the package.\n"
    )


def test_summaries_command_emits_json_and_supports_older_report(tmp_path, capsys):
    report_path = tmp_path / "report.json"
    report_path.write_text(
        '{"version": 1, "summaries": '
        '[{"target": "guide/setup", "summary": "Install it.", '
        '"origin": "html_meta"}]}',
        encoding="utf-8",
    )

    assert main(["summaries", "--report", str(report_path), "--format", "json"]) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["summaries"][0]["cache_status"] == "unknown"


def test_summaries_command_reports_invalid_json(tmp_path, capsys):
    report_path = tmp_path / "report.json"
    report_path.write_text("not json", encoding="utf-8")

    assert main(["summaries", "--report", str(report_path)]) == 2
    captured = capsys.readouterr()
    assert "invalid JSON" in captured.err
    assert captured.out == ""


def test_summaries_command_handles_empty_report(tmp_path, capsys):
    report_path = tmp_path / "report.json"
    report_path.write_text('{"version": 1, "summaries": []}', encoding="utf-8")

    assert main(["summaries", "--report", str(report_path)]) == 0
    assert capsys.readouterr().out == "No summaries found.\n"

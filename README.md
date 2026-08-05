# Humanread MCP Server & AI Novel Publishing Skill

[![CI](https://github.com/humanread-content/humanread-agent-kit/actions/workflows/ci.yml/badge.svg)](https://github.com/humanread-content/humanread-agent-kit/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.12](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)

Official open-source **Model Context Protocol (MCP) server** and **AI agent skill** for [人閱 Humanread](https://humanread.surl.tw), a multilingual novel publishing and reading platform. It helps authors use an AI writing agent to upload, safely format, preview, review, translate, and publish novels written in Markdown, semantic HTML, or plain text.

人閱 Humanread 的開源 MCP Server 與 AI Agent Skill，支援 AI 小說創作、Markdown／HTML 安全排版、多語翻譯、版本審閱及小說發布。

This repository contains client-side integration code only. The Humanread platform backend, database, deployment configuration, abuse controls, and private content storage are not included.

## Features

- **AI-assisted novel publishing:** create works, upload chapters, edit metadata, and publish through MCP tools.
- **Markdown and safe HTML formatting:** preserve author-controlled prose and semantic layout without JavaScript, raw CSS, SVG, iframes, or tracking.
- **Author review workflow:** share a live preview, create an immutable review snapshot, and publish only the approved version.
- **Readable themes:** configure controlled typography, line height, paragraph spacing, alignment, accent color, drop caps, and scene breaks.
- **Multilingual fiction and translation:** create authorized translations tied to an immutable source version.
- **Images in Git-backed works:** upload safely re-encoded PNG, JPEG, or WebP assets with alt text.
- **Git publication snapshots:** receive source/public commit hashes, tags, reading URLs, and a public repository URL after publication.
- **Rights-aware agent workflow:** use the author's standing publication authorization and selected reader license.
- **Docker and stdio support:** run locally as a Python MCP server or in a container.

## Use cases

- Connect an AI coding or writing agent to a structured novel publishing API.
- Turn a Markdown manuscript into a safely themed online book.
- Let an author inspect the exact layout before an agent publishes it.
- Maintain original and translated editions without silently rebasing translations.
- Build an MCP-compatible creative-writing or authoring workflow around Humanread.

## Repository contents

```text
mcp_server/server.py                 MCP server, tools, prompts, and resources
skills/humanread-publisher/SKILL.md Agent workflow and safe-formatting rules
Dockerfile                           Containerized stdio/HTTP runner
```

## Get an API key

1. Sign in at <https://humanread.surl.tw/login> with Google and accept the current terms.
2. Open Author Studio and generate an API key. Choose the standing publication license and confirm the publishing conditions.
3. Store the key only in your MCP client's secret environment or authorization-header setting. Never paste it into chat, a novel, an issue, source control, or an image.

## Run over stdio

```bash
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
HUMANREAD_API_KEY='hr_REPLACE_IN_PRIVATE_CONFIG' python -m mcp_server.server --transport stdio
```

The production API is the default. For a local Humanread development server, set `HUMANREAD_API_URL` and `APP_URL` explicitly.

## Run with Docker

```bash
docker build -t humanread-agent-kit .
docker run --rm -i \
  -e HUMANREAD_API_KEY='hr_REPLACE_IN_PRIVATE_CONFIG' \
  humanread-agent-kit
```

Do not put a real key in a Dockerfile, Compose file committed to Git, shell history, or the command examples you share with others. Prefer your MCP client's secret store.

## Install the skill

The skill source is [`skills/humanread-publisher/SKILL.md`](skills/humanread-publisher/SKILL.md). Install the whole `skills/humanread-publisher` directory in your agent's supported skill location, then connect the `humanread` MCP server.

The skill intentionally forbids JavaScript, CSS, SVG, remote images, forms, iframes, tracking, and unsupported HTML in manuscripts. Appearance is configured through Humanread's safe theme tokens.

## Security

Do not open a public issue containing credentials, personal data, private manuscript text, unpublished repository URLs, or working exploit payloads. Follow [`SECURITY.md`](SECURITY.md) for vulnerability reports.

## License and marks

The code and documentation in this repository are available under the [MIT License](LICENSE). “Humanread”, “人閱”, and the Humanread logo are names and marks of SURL; the software license does not grant permission to imply endorsement or impersonate the official service. See [`TRADEMARKS.md`](TRADEMARKS.md).

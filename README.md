# Humanread Agent Kit

Official public MCP integration and publisher skill for [人閱 Humanread](https://humanread.surl.tw). Humanread lets authors work with an AI agent to format, preview, review, translate, and publish novels while readers use the web interface.

This repository contains client-side integration code only. The Humanread platform backend, database, deployment configuration, abuse controls, and private content storage are not included.

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

import argparse
import base64
import os
from pathlib import Path
import httpx
from mcp.server.fastmcp import FastMCP
from mcp.server.auth.middleware.auth_context import get_access_token
from mcp.server.auth.provider import AccessToken, TokenVerifier
from mcp.server.auth.settings import AuthSettings

API_URL = os.getenv("HUMANREAD_API_URL", "https://humanread.surl.tw").rstrip("/")
API_KEY = os.getenv("HUMANREAD_API_KEY", "")
PUBLIC_URL = os.getenv("APP_URL", "https://humanread.surl.tw").rstrip("/")
PUBLISHER_GUIDE = Path(__file__).resolve().parents[1] / "skills" / "humanread-publisher" / "SKILL.md"
SERVER_INSTRUCTIONS = """Humanread lets an authenticated author create, upload, review, and publish novels.
If Humanread authentication is missing, stop and tell the user to open https://humanread.surl.tw/login, sign in with Google, accept the current terms, and generate an API key in the Author Studio. Tell them to configure it privately in their MCP client as the Authorization: Bearer header, then reconnect. Never ask them to paste or reveal the key in chat, a manuscript, an issue, or a repository.
Preserve the author's prose unless editing is explicitly requested. Use Markdown, plain text, allowlisted semantic HTML, or the isolated sandbox_html format documented at humanread://publisher-guide. CSS is allowed only inside sandbox_html and only under its restricted rules. Never use JavaScript, SVG, remote resources, forms, iframes, tracking, or unsupported markup. Configure ordinary reading appearance through set_safe_theme. Configure controlled genres, tags, age rating, and warnings through set_discovery_metadata; never soften an author-supplied warning and confirm any agent-inferred warning with the author.
The public author name is a user-selected pen name, not a value for the agent to infer. Use set_pen_name only when the author explicitly supplies or approves the exact public text. Explain that it affects future review snapshots and does not rewrite already published or pending immutable versions. API-key creation records the author's standing rights confirmation, public-copy acknowledgement, and default reader license. Normal Agent publication inherits them without asking again. Change the license only when the author gives a different instruction.
After arranging content and theme, call get_author_preview and give its draft_preview_url to the author so they can inspect the current layout while signed in. This live preview is not an approval snapshot. After every content, theme, or metadata change, poll get_novel_status until sync_status is synced. Correct failures and call retry_novel_sync; do not duplicate the novel. Default to status=review only after the author confirms the preview is ready. Never call status=published unless the author has explicitly approved publishing the exact current review/snapshot. Publishing is asynchronous, so poll status and report IDs, hashes, commits, tags, and URLs."""
SERVER_INSTRUCTIONS += """
Translations are separate editions bound to one immutable published source version. Translate only when the author owns the source or list_translation_opportunities shows an active grant for the authenticated translator and target language. Create the edition with create_translation, then read its exact source with get_translation_source. Preserve meaning, attribution, chapter structure, warnings, names, and deliberate formatting; do not silently abridge, rewrite, or invent passages. Tell the author which source version/hash was translated. A revoked grant blocks new review/publication; a newer source needs a new grant before rebasing. The Agent must not work around either rule by creating an unrelated novel."""
SERVER_INSTRUCTIONS += """
Check list_notifications when managing translations. A source-version notification is informational and never authorizes automatic rebasing or overwriting translated prose. Report old/new version IDs and hashes and whether the original author must issue a new grant; mark it read only after reporting. Engagement metrics are read-only signals: never automate views, accounts, or likes. Humanread counts a visible 10-second read once per visitor/novel/day and one like per Google account/novel, but does not claim manipulation is impossible."""
SERVER_INSTRUCTIONS += """
At the first completed draft, remind the author once to keep editable source in an author-controlled private repository or local backup. Never ask for or store their GitHub token, Humanread API key, OAuth secret, .env, or private key. After publication, report public_repository_url and explain it can be cloned or downloaded as an extra backup of the public snapshot only; it does not contain later drafts or replace the private editable-source backup."""
SERVER_INSTRUCTIONS += """
Use report_platform_issue when you directly encounter a reproducible Humanread platform bug, broken API/MCP behavior, accessibility defect, concrete improvement, or credible suspected copyright infringement. For copyright, report proactively with category=copyright only when there is concrete evidence: identify the Humanread novel ID/public URL, an independently located likely source URL, why the source predates the submission, and a concise description of substantial protected overlap. Do not rely only on title, genre, common tropes, style, an AI detector, or vague similarity. Never paste private manuscript text or long excerpts; use URLs and a short non-infringing description. Do not report public-domain material merely because it is copied, but modern translations, annotations, editions, and images may remain protected. Check recent reports to avoid duplicates. Tell the user the report ID and that it is an unverified suspicion for operator review, not a legal finding; the private operator GitHub issue is not exposed. Never include credentials, authorization headers, email, personal data, or exploit payloads."""


class HumanreadTokenVerifier(TokenVerifier):
    async def verify_token(self, token: str) -> AccessToken | None:
        if not token.startswith("hr_"):
            return None
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(f"{API_URL}/api/v1/me", headers={"Authorization": f"Bearer {token}"})
            if response.status_code != 200:
                return None
            user = response.json()
            return AccessToken(token=token, client_id=f'humanread-user-{user["id"]}', scopes=["novels:write"])
        except httpx.HTTPError:
            return None


mcp = FastMCP(
    "humanread",
    instructions=SERVER_INSTRUCTIONS,
    host="0.0.0.0",
    port=8001,
    token_verifier=HumanreadTokenVerifier(),
    auth=AuthSettings(issuer_url=PUBLIC_URL, resource_server_url=f"{PUBLIC_URL}/mcp", required_scopes=["novels:write"]),
)


@mcp.resource(
    "humanread://publisher-guide",
    name="humanread-publisher-guide",
    title="Humanread Authoring and Publication Guide",
    description="Complete supported-markup, safety, review, and publication workflow for Humanread agents.",
    mime_type="text/markdown",
)
def publisher_guide() -> str:
    return PUBLISHER_GUIDE.read_text(encoding="utf-8")


@mcp.prompt(
    name="prepare_novel_for_review",
    title="Prepare a Humanread novel for author review",
    description="A safe end-to-end workflow that stops at an immutable review snapshot.",
)
def prepare_novel_for_review(title: str, summary: str = "", chapter_plan: str = "", visual_tone: str = "", classification_notes: str = "") -> str:
    return f"""Prepare a Humanread novel for review, not public release.

Author inputs:
- Title: {title}
- Summary: {summary or 'Ask the author.'}
- Chapter plan or manuscript notes: {chapter_plan or 'Ask for ordered chapter content.'}
- Visual tone: {visual_tone or 'Use conservative readable defaults.'}
- Classification/warning notes: {classification_notes or 'Suggest values, but confirm inferred warnings.'}

First read humanread://publisher-guide. Preserve supplied prose exactly unless editing was requested. Create the novel, upload chapters in order, verify each sanitized preview, apply only safe theme tokens, then set controlled discovery metadata. Call get_author_preview and give the draft_preview_url to the author, clearly saying it is a live draft and asking them to inspect the layout. Apply requested changes and share the preview again. Poll until Git sync is synced. If it fails, report the error, correct the cause, and retry sync. Only after the author says the preview is ready, call set_publication_status with review. Return the novel ID, chapter list, classification, warnings, preview URL, review version ID, content hash, source commit, and review URL. Do not call published."""


@mcp.prompt(
    name="publish_approved_novel",
    title="Publish an author-approved Humanread snapshot",
    description="Publishes only after explicit approval of the exact review snapshot.",
)
def publish_approved_novel(novel_id: int, approved_version_id: int, author_approval: str) -> str:
    return f"""Publish Humanread novel {novel_id} only if the author explicitly approved review version {approved_version_id} in this conversation.

Recorded approval statement: {author_approval}

Read humanread://publisher-guide. Call get_novel_status and verify there was no content, theme, metadata, or commit change after the approved review was created. If identity of the exact approved snapshot cannot be established, stop and request a new review; never infer consent. If it matches, call approve_review_version with the exact novel and version IDs. Do not call set_publication_status(published), because that creates a new snapshot rather than approving the reviewed one. Poll until completion and report source/public commits, publication tag, public_repository_url, and reading URL. Explain that the public repository is an extra backup of this public snapshot only. Never substitute a newer draft."""


async def call(method: str, path: str, json: dict | None = None):
    authenticated = get_access_token()
    key = authenticated.token if authenticated else API_KEY
    if not key:
        raise ValueError("Humanread authentication is missing. Tell the user to sign in at https://humanread.surl.tw/login, generate an API key in Author Studio, configure it privately as an Authorization: Bearer header, and reconnect. Never ask them to paste the key in chat.")
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.request(method, f"{API_URL}{path}", json=json, headers={"Authorization": f"Bearer {key}"})
        response.raise_for_status()
        return response.json()


@mcp.tool()
async def list_my_novels() -> list[dict]:
    """List the authenticated author's novels and their publication state."""
    return await call("GET", "/api/v1/novels")


@mcp.tool()
async def set_pen_name(pen_name: str) -> dict:
    """Set the authenticated author's public pen name after explicit approval.

    Never infer a pen name from Google profile data. The exact supplied text is
    used only for future review/publication snapshots; immutable versions retain
    their existing attribution.
    """
    return await call("PUT", "/api/v1/profile", {"pen_name": pen_name})


@mcp.tool()
async def report_platform_issue(title: str, description: str, reproduction: str = "", category: str = "bug", severity: str = "medium", client_context: str = "") -> dict:
    """Report a concrete Humanread platform issue to its private GitHub repository.

    category: bug, feature, documentation, accessibility, copyright, or other.
    severity: low, medium, high, or critical. Never include credentials, personal
    data, private manuscript text, authorization headers, or exploit payloads.
    Limited to twenty reports per authenticated account per rolling 24 hours,
    with at most five submissions per ten minutes.

    For copyright reports, include the Humanread novel ID/public URL, likely
    original source URL/date, and a concise overlap description without private
    manuscript text or long quotations. A report is suspicion, not a finding.
    """
    return await call("POST", "/api/v1/issues", {"title": title, "description": description, "reproduction": reproduction, "category": category, "severity": severity, "client_context": client_context})


@mcp.tool()
async def list_my_issue_reports() -> list[dict]:
    """List the authenticated author's recent Humanread report IDs and statuses."""
    return await call("GET", "/api/v1/issues")


@mcp.tool()
async def list_notifications(unread_only: bool = True) -> list[dict]:
    """List in-app author/translator notifications, including newly published source versions."""
    return await call("GET", f"/api/v1/notifications?unread_only={'true' if unread_only else 'false'}")


@mcp.tool()
async def mark_notification_read(notification_id: int) -> dict:
    """Mark one notification read after its consequences have been reported to the user."""
    return await call("POST", f"/api/v1/notifications/{notification_id}/read")


@mcp.tool()
async def get_novel_status(novel_id: int) -> dict:
    """Get Git sync state and draft, review, and published commit SHAs.

    Wait until sync_status is synced before requesting review or publication.
    """
    return await call("GET", f"/api/v1/novels/{novel_id}")


@mcp.tool()
async def get_author_preview(novel_id: int) -> dict:
    """Get the authenticated author's live draft-layout preview URL.

    Share draft_preview_url with the author and explain that login is required,
    it changes with the draft, and it cannot be approved. Create review only
    after the author confirms the preview is ready.
    """
    return await call("GET", f"/api/v1/novels/{novel_id}/preview")


@mcp.tool()
async def get_source_export(novel_id: int) -> dict:
    """Get a login-protected ZIP export URL for the author's editable source.

    Give the URL to the author; do not download, inspect, or re-host the archive.
    It contains no Humanread API key, GitHub token, OAuth secret, or account data.
    """
    return await call("GET", f"/api/v1/novels/{novel_id}/export")


@mcp.tool()
async def get_novel_engagement(novel_id: int) -> dict:
    """Get privacy-preserving unique views and authenticated likes for an owned novel."""
    return await call("GET", f"/api/v1/novels/{novel_id}/engagement")


@mcp.tool()
async def retry_novel_sync(novel_id: int) -> dict:
    """Retry a failed private Git/GitHub synchronization job."""
    return await call("POST", f"/api/v1/novels/{novel_id}/sync")


@mcp.tool()
async def create_novel(title: str, summary: str = "", cover_color: str = "#c86b4a") -> dict:
    """Create a draft novel. cover_color must be a CSS hex color."""
    return await call("POST", "/api/v1/novels", {"title": title, "summary": summary, "cover_color": cover_color})


@mcp.tool()
async def upload_chapter(novel_id: int, title: str, source: str, source_type: str = "markdown", position: int = 0) -> dict:
    """Upload Markdown, plain text, allowlisted HTML, or isolated sandbox_html.

    Ordinary HTML cannot contain CSS. sandbox_html may contain restricted CSS in
    style blocks for layout and animation, but never scripts, event handlers, SVG,
    iframes, forms, URLs, external resources, data/blob URLs, or tracking. Supported
    tags, CSS limits, and attributes are documented in the Humanread Publisher skill.
    Choose it only for an author-requested free layout, text map, or CSS animation;
    prefer Markdown for ordinary prose. Its preview_html is only a validation receipt,
    so share the full draft preview URL with the author for visual inspection.
    """
    payload = {"title": title, "source": source, "source_type": source_type}
    if position > 0:
        payload["position"] = position
    return await call("POST", f"/api/v1/novels/{novel_id}/chapters", payload)


@mcp.tool()
async def list_chapters(novel_id: int) -> list[dict]:
    """List owned draft chapter IDs, order, format, size, and current source hashes."""
    return await call("GET", f"/api/v1/novels/{novel_id}/chapters")


@mcp.tool()
async def update_chapter(novel_id: int, chapter_id: int, expected_source_hash: str, title: str, source: str, source_type: str = "markdown") -> dict:
    """Replace one owned draft chapter only if its current SHA-256 still matches.

    Read list_chapters immediately before updating. A mismatch returns a conflict;
    never retry with a new hash without reviewing the newer chapter with the author.
    Existing published snapshots remain immutable.
    """
    return await call("PUT", f"/api/v1/novels/{novel_id}/chapters/{chapter_id}", {"expected_source_hash": expected_source_hash, "title": title, "source": source, "source_type": source_type})


@mcp.tool()
async def delete_chapter(novel_id: int, chapter_id: int, expected_source_hash: str, author_confirmation: str) -> dict:
    """Delete one draft chapter after explicit author confirmation of that chapter.

    Read list_chapters immediately first. Never infer deletion approval or use this
    to replace content. Existing published snapshots remain immutable.
    """
    if not author_confirmation.strip():
        raise ValueError("Explicit author confirmation is required")
    return await call("DELETE", f"/api/v1/novels/{novel_id}/chapters/{chapter_id}?expected_source_hash={expected_source_hash}")


@mcp.tool()
async def update_novel_details(novel_id: int, expected_draft_commit_sha: str, title: str | None = None, summary: str | None = None, cover_color: str | None = None) -> dict:
    """Update owned draft title, summary, or cover using optimistic concurrency.

    Pass the exact draft_commit_sha from get_novel_status. The stable public slug
    and all already published snapshots remain unchanged.
    """
    return await call("PUT", f"/api/v1/novels/{novel_id}/details", {"expected_draft_commit_sha": expected_draft_commit_sha, "title": title, "summary": summary, "cover_color": cover_color})


@mcp.tool()
async def upload_image_asset(novel_id: int, image_path: str, alt_text: str) -> dict:
    """Store a local PNG, JPEG, or WebP in the novel's private repo after safe re-encoding."""
    path = Path(image_path)
    if not path.is_file() or path.stat().st_size > 10 * 1024 * 1024:
        raise ValueError("Image must be a local file no larger than 10 MB")
    return await call("POST", f"/api/v1/novels/{novel_id}/assets", {"content_base64": base64.b64encode(path.read_bytes()).decode(), "alt_text": alt_text})


@mcp.tool()
async def set_publication_status(novel_id: int, status: str, reader_license: str = "", rights_confirmed: bool = False, public_copy_acknowledged: bool = False, author_approval: str = "") -> dict:
    """Set draft/review, or publish with the author's explicit rights and license choices.

    For published, pass all-rights-reserved, CC-BY-4.0, or CC-BY-SA-4.0 plus
    both confirmations and the author's actual publication instruction.
    """
    return await call("POST", f"/api/v1/novels/{novel_id}/status", {"status": status, "reader_license": reader_license or None, "rights_confirmed": rights_confirmed, "public_copy_acknowledged": public_copy_acknowledged, "approval_statement": author_approval or None})


@mcp.tool()
async def approve_review_version(novel_id: int, version_id: int, author_approval: str = "Publish the approved review using my standing API authorization", reader_license: str = "", rights_confirmed: bool = False, public_copy_acknowledged: bool = False) -> dict:
    """Approve and publish one exact pending review version.

    Call only when the author explicitly approved this version in the current
    conversation. Humanread verifies ownership, pending state, and version ID.
    """
    if not author_approval.strip():
        raise ValueError("Explicit author approval is required")
    return await call("POST", f"/api/v1/novels/{novel_id}/reviews/{version_id}/decision", {"decision": "approve", "reader_license": reader_license, "rights_confirmed": rights_confirmed, "public_copy_acknowledged": public_copy_acknowledged, "approval_statement": author_approval})


@mcp.tool()
async def set_safe_theme(novel_id: int, font: str = "serif", font_size: int = 18, line_height: float = 2.0, paragraph_spacing: float = 1.4, text_align: str = "left", accent_color: str = "#b85c3d", drop_cap: bool = False, scene_break: str = "line") -> dict:
    """Set validated reading tokens; raw CSS is never accepted.

    font: serif, sans, or mono. font_size: 14-24. line_height: 1.4-2.4.
    text_align: left or justify. scene_break: line, stars, or dots.
    """
    return await call("PUT", f"/api/v1/novels/{novel_id}/theme", {"font": font, "font_size": font_size, "line_height": line_height, "paragraph_spacing": paragraph_spacing, "text_align": text_align, "accent_color": accent_color, "drop_cap": drop_cap, "scene_break": scene_break})


@mcp.tool()
async def set_discovery_metadata(novel_id: int, primary_genre: str = "other", secondary_genre: str = "", tags: list[str] | None = None, serial_status: str = "ongoing", language: str = "zh-Hant", age_rating: str = "all", warning_level: str = "none", content_warnings: str = "") -> dict:
    """Set controlled discovery and safety metadata.

    Genres: fantasy, scifi, mystery, thriller, romance, historical, wuxia,
    urban, youth, literary, horror, adventure, other. At most 10 tags.
    Confirm inferred content warnings with the author before publication.
    """
    return await call("PUT", f"/api/v1/novels/{novel_id}/metadata", {"primary_genre": primary_genre, "secondary_genre": secondary_genre, "tags": tags or [], "serial_status": serial_status, "language": language, "age_rating": age_rating, "warning_level": warning_level, "content_warnings": content_warnings})


@mcp.tool()
async def list_translation_opportunities() -> list[dict]:
    """List active translation grants addressed to this authenticated author."""
    return await call("GET", "/api/v1/translation-opportunities")


@mcp.tool()
async def grant_translation(novel_id: int, grantee_email: str, target_language: str) -> dict:
    """Authorize one Google-account email to translate one published source version into one language."""
    return await call("POST", f"/api/v1/novels/{novel_id}/translation-grants", {"grantee_email": grantee_email, "target_language": target_language})


@mcp.tool()
async def revoke_translation_grant(novel_id: int, grant_id: int) -> dict:
    """Revoke future review/publication authority for one translation grant."""
    return await call("DELETE", f"/api/v1/novels/{novel_id}/translation-grants/{grant_id}")


@mcp.tool()
async def create_translation(source_novel_id: int, target_language: str) -> dict:
    """Create a linked translation draft using self-ownership or an active grant."""
    return await call("POST", f"/api/v1/novels/{source_novel_id}/translations", {"target_language": target_language})


@mcp.tool()
async def get_translation_source(translation_novel_id: int) -> dict:
    """Read the exact immutable source snapshot authorized for this translation draft."""
    return await call("GET", f"/api/v1/novels/{translation_novel_id}/translation-source")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--transport", choices=["stdio", "streamable-http"], default="stdio")
    args = parser.parse_args()
    mcp.run(transport=args.transport)

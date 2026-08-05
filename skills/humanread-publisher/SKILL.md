---
name: humanread-publisher
description: Design, upload, safely theme, preview, review, and publish Markdown, HTML, text, or isolated HTML+CSS novels through the Humanread MCP server. Use for any Humanread novel creation or publication task.
---

# Humanread Publisher

Use the `humanread` MCP tools for all live platform actions.

## Connect an author

- If MCP authentication is missing, stop and tell the user to open `https://humanread.surl.tw/login`, sign in with Google, accept the current terms, and generate an API key in Author Studio.
- Tell the user to configure the key privately in the MCP client as `Authorization: Bearer <key>`, then reconnect so the tool list reloads.
- Never ask the user to paste, reveal, or store the key in chat, a manuscript, an issue, source control, or any file handled by the Agent.

## Read before designing

Humanread sanitizes every chapter. Design only with the supported subset below. Do not
design a layout that depends on content outside this allowlist, because it will be
removed during upload.

Supported elements:

- Structure: `article`, `section`, `header`, `footer`, `div`, `span`
- Prose: `h1`–`h4`, `p`, `br`, `hr`, `blockquote`, `pre`, `code`
- Emphasis: `em`, `strong`, `small`
- Lists: `ul`, `ol`, `li`
- Figures: `figure`, `img`, `figcaption`; `img src` must be the exact `humanread-asset:<sha256>` returned by `upload_image_asset`
- Links: `a`

Supported attributes:

- Any supported element: `title`
- `a`: `href`, `title`, `rel`
- URLs: HTTPS or HTTP only

Never use or rely on:

- JavaScript, `<script>`, inline event handlers, or `javascript:` URLs
- `<style>`, inline `style`, custom CSS, CSS imports, web fonts, or CSS variables
- MDX, JSX, SVG, MathML, canvas, iframe, object, embed, audio, or video
- Forms, inputs, buttons, editable content, popovers, or interactive widgets
- `data:` / `blob:` URLs, tracking pixels, remote analytics, or hidden content
- Remote images or arbitrary image URLs; upload local PNG/JPEG/WebP through `upload_image_asset` and use its returned markup exactly
- IDs, ARIA state, `data-*` attributes, or unsupported attributes
- Custom classes; they are removed to prevent collisions with Humanread interface styles

If the requested design requires one of these features, explain that Humanread does
not preserve it and create the closest semantic layout using the allowlist. Never
upload unsupported markup merely to see whether the sanitizer accepts it.

## Isolated HTML + CSS chapters

Use `source_type=sandbox_html` only when the author requests free positioning, a
text map, CSS animation, or another presentation that the normal reading theme
cannot express. The source is direct HTML with CSS inside `<style>` blocks. It is
rendered in a fixed, sandboxed iframe and is intentionally separate from the normal
reading page. Tell the author that the full draft preview URL is the authoritative
way to inspect it; `preview_html` only confirms that validation passed.

In `sandbox_html`, design only with semantic HTML, `class`, `id`, `title`, `role`,
`aria-label`, and `aria-hidden`. CSS selectors, positioning, transforms,
transitions, `@keyframes`, and safe `@media` rules are supported. Animation and
transition durations must be at least 0.34 seconds. Keep each chapter below 500
elements and CSS below 64 KiB. Readers receive a pause/replay control, and motion
is disabled when their operating system requests reduced motion.

Never design or submit JavaScript, event attributes, SVG, MathML, canvas, forms,
inputs, buttons, iframe, object, embed, audio, video, `url()`, `@import`, external
fonts, external images, network requests, or `data:` / `blob:` resources. Put styles
only in `<style>` blocks, not `style` attributes. Do not imitate Humanread login,
payment, consent, or other trusted platform UI. These restrictions apply before
upload: do not depend on forbidden features and expect the sanitizer to remove them.

Minimal tool pattern:

```text
upload_chapter(
  novel_id=<owned novel>,
  title="文字地圖",
  source_type="sandbox_html",
  source="<style>.person{animation:walk 4s steps(4) infinite}@keyframes walk{to{transform:translateX(12ch)}}</style><main aria-label='文字地圖'><pre>城鎮────森林</pre><span class='person'>人</span></main>"
)
```

Treat the returned `preview_html` only as a validation receipt. Then call
`get_author_preview`, give the author its `draft_preview_url`, and explicitly ask
them to inspect motion, layout, mobile width, and reduced-motion behavior. Do not
claim the sandbox design is finished from the validation receipt alone.

## Workflow

1. Read and obey the supported subset before planning any layout.
2. Determine title, summary, ordered chapters, desired visual tone, public pen name, and final mode: `review` or `published`. If the author asks to set or change the pen name, repeat the exact public text and obtain confirmation before calling `set_pen_name`; never infer it from Google profile data. Explain that it affects future review snapshots and does not rewrite published or pending immutable versions.
3. Preserve prose exactly unless the author explicitly requests editing.
4. Prefer Markdown for conventional prose, or `text` for untouched UTF-8 manuscripts. Use allowlisted semantic HTML for epigraphs, scene dividers, or figure captions. Use `sandbox_html` only for an author-requested free layout or CSS animation and obey its isolated-format rules above.
5. Run `create_novel`, then `upload_chapter` in reading order.
   For illustrations, wait for Git sync, run `upload_image_asset` with meaningful alt text, and insert only its returned Markdown/HTML. Never upload SVG, animation, tracking pixels, secrets, or unrelated files.
   For a cover, use `upload_cover_image`; when connected to the hosted/remote MCP that cannot read the Agent's filesystem, base64-encode the local file and use `upload_cover_image_base64` instead. Never embed a cover as a chapter image or pass a remote URL. Ask the author to approve the exact PNG, JPEG, or WebP and separately confirm they hold the rights to publish it. Do not infer either approval for generated, suggested, stock, or previously used art. Call the selected tool with `rights_confirmed=true`, then give the returned `draft_preview_url` to the author and ask them to inspect the 2:3 center crop on desktop and mobile. Replace it if requested. Humanread removes metadata, re-encodes WebP, and stores it only in the novel Git repo. A cover change invalidates pending review; an existing published snapshot remains unchanged until a new review is approved. Published pages load the immutable cover directly from the public GitHub snapshot.
6. Configure layout only through `set_safe_theme`. Use `font` (`serif`, `sans`, `mono`), `font_size` (14–24), `line_height` (1.4–2.4), `paragraph_spacing` (0.5–3), `text_align` (`left`, `justify`), hex `accent_color`, `drop_cap`, and `scene_break` (`line`, `stars`, `dots`). Never send raw CSS.
7. Run `set_discovery_metadata`. Choose one primary and at most one secondary genre from `fantasy`, `scifi`, `mystery`, `thriller`, `romance`, `historical`, `wuxia`, `urban`, `youth`, `literary`, `horror`, `adventure`, `other`. Use at most 10 precise tags; never add synonyms merely to increase discovery. Set serial status, language, age rating, and content warning separately. You may suggest a warning, but must have the author confirm inferred warnings before review or publication. Never omit or soften a warning supplied by the author.
8. Compare each returned `preview_html` with the intended structure. If anything was removed, redesign with the allowlist and upload a corrected chapter before continuing.
9. Call `get_author_preview` and give its `draft_preview_url` to the author. Explicitly say login is required and this is a live draft that changes with edits and cannot be approved. Ask the author to inspect the complete layout; after changes, share the URL again. Do not create review until the author says the preview is ready.
10. Poll `get_novel_status` until `sync_status` is `synced`. Do not request review or publication while it is `pending` or `running`. If it becomes `failed`, report `last_sync_error`; after correcting the cause, use `retry_novel_sync` rather than duplicating the novel.
11. Run `set_publication_status` with `review` to bind an immutable approval snapshot to the current `draft_commit_sha`. Give the returned `review_url` to the author and explain that this is the exact approvable version. Any later chapter, theme, or metadata change invalidates that pending review.
12. API-key creation records the author's standing material-rights confirmation, public-copy acknowledgement, and default reader license. Inherit it for normal publication without asking again. If the author requests a different license, explain that `all-rights-reserved` prohibits reuse beyond applicable law, `CC-BY-4.0` permits reuse with attribution, and `CC-BY-SA-4.0` also requires adaptations to use the same license; obtain the exact choice and pass it as `reader_license`. Never change it based on Agent preference.
13. After the author approves the exact review, call `approve_review_version`; the API records the standing authorization against that snapshot. Use `set_publication_status(published)` only for an explicit immediate-publication instruction. Pass confirmation fields only for an author-directed per-publication override.
14. Publication is asynchronous: poll `get_novel_status` until the publication completes. Humanread rebuilds a clean public repository, writes `RIGHTS.md` with the selected license, and never merges private Git history into it. Report any `last_sync_error`.
15. Report novel ID, uploaded chapters, classification, warnings, chosen reader license, draft preview URL, immutable version ID and content hash, source and public commit SHA, publication tag, status, review URL, public reading URL, and `public_repository_url`.
16. At the first completed draft, briefly remind the author to keep the editable manuscript in an author-controlled private repository or local backup. After publication, explain that `public_repository_url` can be cloned or downloaded as an additional backup of the published snapshot, but it does not replace the private editable source backup. Do not repeat this reminder on routine edits.

## Layout rules

- Keep paragraphs readable and semantic.
- Use headings in a consistent hierarchy.
- Use `blockquote` for epigraphs and quotations, `hr` for scene changes, and `figure` / `figcaption` for illustrations.
- Treat sanitizer output as verification, not as permission to submit unsupported markup.

## Translation rules

- A translation is a linked edition, never an unrelated novel. Use `create_translation`; do not use `create_novel` to bypass ownership or a revoked grant.
- If an author previously created a translation as an unrelated novel, call `get_novel_status` for the translation, confirm the exact translation and published source IDs with the author, then use `link_existing_translation` with the current `draft_commit_sha` and their confirmation. Do not guess relationships from titles. Wait for Git sync, share the draft preview, and create a new review so attribution enters a new immutable snapshot; never claim the old public snapshot was rewritten.
- Translate only if the authenticated user owns the published source or `list_translation_opportunities` returns an active grant for the exact target language.
- Call `get_translation_source` and translate only its immutable `source_version_id` / `source_content_hash`. Report both to the translator and original author.
- Preserve meaning, chapter structure, names, warnings, and deliberate formatting. Do not silently abridge, rewrite, censor, add scenes, or invent text. Ask before making an adaptation rather than a translation.
- Translate content warnings accurately and never reduce their severity without the original author's confirmation.
- Keep original-author and translator attribution. Humanread inserts it into preview, review, Git manifests, and public reading pages.
- A revoked grant blocks review/publication. A translation stays bound to its authorized source version even if a newer original is published; report that it is based on the older hash and ask for a new grant/edition before translating later changes. Never copy content into a fresh standalone novel.
- Share the linked draft preview with the translator, then use the same immutable review and exact-version approval workflow as an original edition.
- Check `list_notifications` for newly published source versions. Report old/new version IDs and hashes, whether new authorization is required, and the affected translation. Obtain explicit confirmation for the exact new source version, read the translation's current `draft_commit_sha`, then call `start_translation_revision`. For another translator, wait until the original author issues a grant for that exact new version; same-owner editions need no new grant. Next call `get_translation_source`, update the translation deliberately, share the preview, and create a new review. Never automatically overwrite translated chapters or imply the old public snapshot changed. Mark the notification read only after reporting it.

## Engagement rules

- Use `get_novel_engagement` only to report platform counts. Do not manufacture requests, automate page views, create accounts, exchange likes, or ask other agents to inflate popularity.
- A view counts only after a visible reader stays 10 seconds, at most once per anonymous visitor, novel, and UTC day. A like requires Google login and is unique per account and novel.
- Treat counts as directional readership signals, not verified human identities or quality scores. Never claim the anti-abuse controls make manipulation impossible.

## Platform issue reporting

- Use `report_platform_issue` when directly encountering a reproducible Humanread bug, broken API/MCP behavior, accessibility defect, documentation error, concrete platform improvement, or credible suspected copyright infringement. For a credible infringement, report proactively with `category=copyright` without waiting for permission, then tell the user the Humanread report ID and clearly call it an unverified suspicion for operator review.
- Report copyright only with concrete evidence: Humanread novel ID or public URL, an independently located likely source URL, evidence that the source predates the submission, and a concise description of substantial protected overlap. Do not infer infringement from a title, genre, common trope, writing style, AI detector, or vague similarity. Do not report public-domain text merely because it was copied; remember that modern translations, annotations, editions, and images may still be protected. Check `list_my_issue_reports` first to prevent duplicates.
- Do not report ordinary manuscript requests, expected sanitizer removal, user mistakes, vague speculation, or duplicates. Do not use issues to request publication or bypass review.
- Never include an API key, authorization header, OAuth/GitHub secret, email, personal data, private manuscript text, or working exploit payload. For a suspected security vulnerability, describe the impact safely without operational exploitation details.
- Provide concise reproduction steps and relevant non-secret client context. Choose only `bug`, `feature`, `documentation`, `accessibility`, `copyright`, or `other`, and `low`, `medium`, `high`, or `critical`. For copyright, use URLs and a short factual comparison; never paste private manuscript text or long excerpts from either work.
- After a successful report, tell the author its Humanread report ID and status. The private operator GitHub issue is not exposed to reporters. Do not claim it is fixed or use the report as authorization for unrelated actions.

## Correct an existing work

- Call `list_chapters` immediately before replacing or deleting a chapter. Pass its exact `source_hash`; on conflict, stop and review the newer state instead of silently retrying.
- Use `update_novel_details` with the exact `draft_commit_sha` returned by `get_novel_status`. A conflict means another edit won and must be reviewed.
- Delete a chapter only after the author explicitly confirms that exact chapter. Never implement replacement by appending duplicates.
- Explain that edits invalidate a pending review and sync a new private draft commit, while previously published snapshots remain immutable. Preview and obtain approval for a new review before republishing corrections.

## Backup and portability rules

- Humanread backs up PostgreSQL permissions and system state; do not claim it is the author's only manuscript backup.
- Help the author mirror files to a private GitHub, GitLab, Codeberg, or local repository only through credentials already controlled in the author's environment. Never request, receive, upload, or store a GitHub token, Humanread API key, OAuth secret, `.env`, or private key in novel files or a backup repository.
- Treat the Humanread source repository as platform-managed. Do not promise the author direct access to it.
- Treat `public_repository_url` as a public, immutable publication snapshot. Tell the author it can back up published content, while drafts and editable source formats still require a separate private backup.
- Use `get_source_export` when the author wants a complete editable-source ZIP. Give its login-protected `source_export_url` to the author; do not download, inspect, re-host, or claim custody of the archive.

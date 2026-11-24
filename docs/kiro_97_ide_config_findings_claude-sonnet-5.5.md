# Kiro 97 findings: IDE shows no MCP server, greyed pk-checks.json hooks (claude-sonnet-5.5)

Marks: [doc] = stated in a local file (cited), [guess] = my inference, nothing in the local files confirms it.
Files read: (not published) (KF), (not published), .kiro/hooks/*, .kiro/settings/mcp.json, .kiro/powers/pumpkin-killer-seat/{plugin,mcp}.json, both evidence notes in docs/kiro_evidence/raw/.

## A. Why the IDE "MCP Servers" panel is empty
1. [doc] KF line 24 names `.kiro/settings/mcp.json` as the workspace MCP config. Our file uses that path and has `mcpServers.pumpkin-killer` with `command`, `args`, `autoApprove`, `disabled: false`. So the location and field names match the doc. Nothing in the file is obviously wrong.
2. [doc] `ide_mcp_attempt_20261115.txt` says the CLI lists the server from this same file; the IDE chat found no such tool.
3. [doc] KF line 18 says workspace agent config is loaded only if the workspace is trusted. KF does not say the same for MCP, and the evidence note says the folder was trusted. [guess] trust is not the cause.
4. [guess] Working directory. `args` is the relative path `scripts/mcp_stdio_server.py` with no `cwd`. The CLI starts from the repo root. If the IDE spawns the process from another directory, python3 exits at once and the panel stays empty. No local doc says which directory the IDE uses.
5. [guess] The IDE reads MCP config at startup or on file change, and the file was added before the trust grant. A restart or a reconnect may be needed. `ide_mcp_attempt_20261115.txt` lists a restart as "not done".
6. [guess] The IDE may read only user-level `~/.kiro/settings/mcp.json`. No local doc says so, and KF line 24 says the opposite (workspace file). I may not edit the home folder.
7. [doc] KF line 26: the IDE has an Output tab "Kiro - MCP Logs". Nobody has read it yet. It would tell which of 4 to 6 is true. This is the next step.

## B. Why the three pk-checks.json hooks are greyed out
1. [doc] KF line 35 gives the v1 schema `{version, hooks[{name, trigger, matcher, action, timeout, enabled, confirm}]}` and says hooks work in IDE and CLI. pk-checks.json follows that schema, field by field.
2. [doc] KF line 36: our `.kiro.hook` files are the older IDE format. KF also says CLI runs do not read them. The IDE did run one (ide_hook_run_20261115.txt).
3. [guess] The IDE Agent Hooks panel may list only its own format (it shows a "Migrate" button on the old files) and show other files as read-only or disabled.
4. [guess] The IDE build in use may not support PostFileSave or the v1 file at all, even though the docs say it does. KF says its full trigger list was NOT read (line 35: "the full list is on the Hook types page, not read").
5. [guess] The `matcher` may be matched differently in the IDE (absolute path versus relative path). The first matcher `(^|/)index\.html$` would match both.

## C. The "Migrate" format
No local doc describes what the IDE's Migrate button writes. KF line 36 describes the old format and the v1 format, but not the IDE's conversion target. The brief says not to guess a format.
So: no conversion was done, no hook file and no mcp.json was changed, and nothing was backed up (nothing was altered).

## Open questions for the owner (answers need the IDE, not files)
1. Click Migrate on ONE `.kiro.hook` copy in the IDE and keep the file it writes. That gives the real target format. Then the other five hooks can be converted by script.
2. Open Output > "Kiro - MCP Logs" in the IDE after a restart and paste the first error lines. It shows whether the python3 process started and from which directory.
3. Hover over or click a greyed pk-checks hook in the IDE and copy the reason text, if one is shown.
4. Optional test once the log is read: add `"cwd"` or an absolute path in a COPY of mcp.json. Not applied here because no local doc supports a `cwd` field.

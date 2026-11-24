# Privacy gate

Set `PK_TERMS` to an owner-managed, non-empty UTF-8 file outside the release tree.
The file contains one private term per line and is never copied into the repository.

```sh
export PK_TERMS="$HOME/pk_privacy_terms.txt"
python3 -B scripts/release/privacy_gate.py --tree ../pk-release --check all
python3 -B scripts/release/privacy_gate.py --tree ../pk-release --history ../pk-release
```

Use `--check cjk`, `--check png-text`, or `--check links` to run one focused tree
check. The second command also scans the rebuilt Git history for P1–P7, P15, and
P16. The gate never prints matched material. It reports only `file:line` or
`commit:file` locations.

Exit code `0` means no BLOCK hit. Exit code `1` means at least one BLOCK hit, or
that `PK_TERMS` is unavailable or empty. REVIEW hits do not change the exit code;
a person must decide whether the cited line is appropriate for publication.

BLOCK checks cover emails, local paths, secret-shaped or assigned values,
credential/noise filenames, owner terms, metadata or archive names, oversized
files, dangling local documentation links, release placeholders, and history
identity/path rules. P1 does not report font-author addresses in
`assets/fonts/OFL-*.txt`, because those copyright notices are required by the
third-party font licences. P7 ignores a line beginning `Copyright (c)` only in
the root `LICENSE`, which preserves the owner-selected MIT copyright holder;
the same owner term remains a BLOCK hit everywhere else. REVIEW checks flag
secret-related names, balance language, Drive references, and Chinese text outside the
permitted runtime locations.

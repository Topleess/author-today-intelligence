#!/usr/bin/env python3
from __future__ import annotations
import re, subprocess, sys
from pathlib import Path

files=subprocess.check_output(["git","ls-files","-z"]).decode().split("\0")
files=[f for f in files if f]
name_forbidden=[re.compile(r"(^|/)(Cookies|Local Storage|Session Storage|Login Data)(/|$)",re.I),re.compile(r"\.(sqlite3?|db)$",re.I),re.compile(r"(^|/)raw/",re.I)]
content_patterns={
 "github_token":re.compile(rb"(?:gho_|github_pat_)[A-Za-z0-9_]{16,}"),
 "aws_key":re.compile(rb"AKIA[0-9A-Z]{16}"),
 "private_key":re.compile(rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
 "bearer_secret":re.compile(rb"Authorization\s*[:=]\s*Bearer\s+(?!guest\b)[A-Za-z0-9._~-]{16,}",re.I),
 "known_private_email":re.compile(bytes.fromhex("616c6578323030336d61696c")+b"|"+bytes.fromhex("40676d61696c2e636f6d"),re.I),
 "local_browser_profile":re.compile(rb"/opt/data/\.cache/author-today-browser/profile",re.I),
}
findings=[]
for f in files:
 if any(p.search(f) for p in name_forbidden): findings.append((f,"forbidden artifact path")); continue
 p=Path(f)
 try:data=p.read_bytes()
 except OSError:continue
 if len(data)>2_000_000: findings.append((f,"tracked file exceeds 2 MB")); continue
 for name,pat in content_patterns.items():
  if pat.search(data):findings.append((f,name))
if findings:
 for f,reason in findings:print(f"FAIL {f}: {reason}")
 sys.exit(1)
print(f"privacy scan ok: {len(files)} tracked files")

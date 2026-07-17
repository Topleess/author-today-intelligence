# Permission-gated browser worker design

**Status: disabled and not shipped.** Implement only after written Author.Today permission defines allowed authenticated analytics routes, request rates, retention and storage.

## Trust boundary

If permission is obtained, the browser worker becomes the only credential-bearing component.

```text
agent -> loopback read-only controller API -> typed Unix socket -> browser worker
                                                   |
                                                   +-> worker-only browser-profile volume
```

The controller must not mount the profile volume, expose Playwright/CDP/VNC, read worker files, or accept arbitrary URL/script/selector/header operations. The worker must not mount SQLite, the controller source, host home or Docker socket.

## Allowed typed operations

Only versioned, audited commands with strict schemas, bounded IDs/enums and positive output fields, for example:

- `GetCapabilities`
- `GetSessionStatus`
- `CollectOwnReport(report_kind, work_id?)`
- `GetJobStatus`
- `CancelJob`

Forbidden concepts include `Navigate(url)`, generic `Fetch`, `Evaluate`, selectors, screenshots, HTML/headers/cookies/storage exports, downloads and profile-file reads.

## Human login

Human and automation modes are mutually exclusive. The human UI is bound to loopback. The user enters password, CAPTCHA and 2FA directly in Chromium; form values are never logged. Automation remains locked until the human closes the handoff and the worker reports only a coarse status such as `logged_in`.

## Container controls

- distinct non-root UIDs;
- worker-only named profile volume;
- typed Unix socket in tmpfs;
- no host/Docker sockets or broad bind mounts;
- read-only root filesystems;
- `cap_drop: [ALL]`, `no-new-privileges`;
- Chromium sandbox remains enabled; never add `SYS_ADMIN` just to start it;
- loopback-only human UI;
- exact domain/path/method allowlist and fail-closed redirects;
- no automated writes, publishing, messaging, purchases, follows or likes.

## Required tests before enablement

- controller cannot list/read profile volume;
- API and logs contain no secret-canary values;
- unknown operations/fields fail closed;
- arbitrary URLs/scripts/selectors are rejected;
- human and automation modes cannot overlap;
- CAPTCHA/auth expiry stops and requires human action;
- restart preserves only approved session state in worker volume;
- worker responses are rebuilt from positive schemas, not proxied raw pages.

# Validation

The following is the retained adaptation-stage record, not a new claim that
every desktop/model test was repeated during GitHub publication. Current
publication checks are documented in the repository root VALIDATION.md.

## Requested Name

The plugin and primary local Skill are named codex_kuangdeng_zcode_innight.
Codex's actual skills/list interface discovered this exact underscore name,
enabled, with no loading errors; the previous zcode-delegate entry was absent.
The plugin validator passed and personal marketplace discovery found the
renamed plugin. All 22 offline tests passed from the renamed installed path.

The skill-creator style checker recommends hyphens and rejects underscores.
The user's exact requested spelling is retained; the runtime discovery check
above verifies that this is accepted by the installed Codex runtime.

## Historical Desktop Behavior

On 2026-09-09, Ubuntu 22.04 / GNOME 42 / X11 / x86_64 passed the desktop mouse,
keyboard, accessibility and screenshot workflow. An actual official ZCode
conversation then passed one send/wait/read task and two dependent follow-up
turns. The same session retained context and applied update/delete/reorder
requests correctly. All model records were Coding Plan GLM-5.3-Flash.

These tests establish the bounded behavior described in the two Skills. They
do not establish general long-duration coding reliability or free billing.
Original private desktop and session evidence stays on the test machine.

## Release Checks

- Plugin manifest validation and Skill frontmatter parsing passed. The primary
  Skill's underscore naming exception is described above; the generic style
  checker does not accept that spelling.
- 22 offline Python behavior tests passed, including marker/turn binding,
  preventing old completion from satisfying a new round, ambiguous markers,
  official CLI boundaries, and opt-in rather than shared personal schedules.
- The bundled archive plus patch reproduced the src directory, Cargo.toml and
  Cargo.lock of the desktop-tested runtime, by direct file comparison.
- setup-desktop.sh --check passed on the Ubuntu test host.
- The ZIP was extracted under a new path containing spaces. The installer
  built a new release binary there and installed MCP SDK 1.30.0. It used the
  host's existing Rust toolchain, Cargo cache and prepared system dependencies.
- That install exposed and fixed an artifact lookup bug when CARGO_TARGET_DIR
  is set. The corrected full installer completed successfully. Cairo Python
  bindings used by pointer feedback were also added to prerequisite checks.
- The relocated console connected to all 19 MCP tools, read ZCode's AT-SPI
  nodes and listed X11 windows. Full-screen screenshot capture passed.
- A separate SDK connection using the manifest command, expanded plugin root
  and declared environment variables also connected and listed windows.
- Before the final rename, the host CLI discovered zcode-collab@personal as available. It was left
  uninstalled to avoid duplicating the existing desktop MCP registration.

Raw acceptance outputs stay outside the ZIP. The package contains portable
source, documentation and tests, without personal preferences or screenshots.

## Limits

The installer and runtime require a prepared Linux X11 desktop, Node/npm,
Rust/Cargo, GTK3 and X11 tools. Fresh system dependency installation and a
complete clean-machine deployment have not been performed for this release.
Codex's native plugin loading in a new task has not been exercised; SDK
connectivity and marketplace discovery are separate evidence.

The desktop locked during release checks. A targeted ZCode screenshot was
correctly rejected because the window could not be focused, and a full-screen
screenshot confirmed the lock screen. This release did not repeat unlocked
targeted capture, typing or model requests; their evidence is the historical
desktop test above. The returned AT-SPI tree reached its 1000-node budget and
is not described as a complete view of the current conversation.

The deep Electron focus diagnostic may report a false warning. Full-depth
accessibility and actual text readback remain required. Wayland, ARM and
non-Ubuntu environments have not received the same acceptance testing.

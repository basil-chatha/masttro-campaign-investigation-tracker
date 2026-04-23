# Campaign Investigation Tracker

A lightweight campaign operations tool for triaging underperforming ad campaigns — built live during the Claude Code Masterclass.

## What this is

This repo is the **starting skeleton** for a hands-on, instructor-led build. Over two days, the class will turn it into a working investigation tracker using Claude Code as the primary development workflow.

The finished product lets an operator browse campaigns, spot health issues, open structured investigations, capture evidence, and progress issues through to resolution.

## Tech stack

| Layer | Technology |
|-------|------------|
| Frontend | React, Tailwind CSS, shadcn/ui |
| Backend | FastAPI (Python) |
| Database | PostgreSQL (Supabase) |

## Repo structure

```text
frontend/          → React app shell with routing and baseline styling
backend/           → FastAPI server with health endpoint and DB connectivity
```

## What's already here

- App shell, routing, and baseline component scaffolding
- FastAPI bootstrapped with a health check endpoint
- Database schema and seed data for realistic demo scenarios
- Basic test harnesses (runnable out of the box)
- Local startup flow that works without additional setup

## Data model (seeded)

The seed data provides a small, curated dataset that tells a workshop story — not a production-scale fixture. Five tables are pre-seeded in the database:

- **Campaigns** — mix of healthy, unhealthy, and ambiguous ad campaigns
- **Campaign Health** — time-series snapshots with metrics like CTR, viewability, spend, and pacing
- **Investigations** — structured triage records with question, hypothesis, status, and next action
- **Investigation Evidence** — typed evidence items (metrics, delivery notes, operator notes, QA checks)
- **AI Runs** — lightweight log of model usage tied to investigations (for economics discussion)

The backend currently maps only `campaigns` and `campaign_health` as ORM models. The remaining models, schemas, and API routes will be built during the workshop.

## What we'll build together

Over the course of the workshop, this skeleton becomes a working product while demonstrating Claude Code workflows:

1. Surface campaign health data and make a first visible change
2. Add the AI usage model scaffold and discuss token economics
3. Build a campaign detail page with investigation entry point
4. Implement investigation creation, evidence capture, and persistence end to end
5. Add investigation status progression (New → Investigating → Needs Action → Resolved)
6. Surface AI usage and recommendation data
7. Layer in shared repo standards, skills, hooks, and automation

## Getting started

### Prerequisites

- Python 3.10+ and [uv](https://docs.astral.sh/uv/)
- [Bun](https://bun.sh/)
- [Supabase CLI](https://supabase.com/docs/guides/cli) and Docker (for local Supabase)

### 1. Start local Supabase

```bash
supabase start
```

This starts PostgreSQL, Auth, and other Supabase services in Docker. The seed data in `supabase/seed.sql` is applied automatically. Note the `DB URL` from the output — you'll need it next.

### 2. Start the backend

```bash
cd backend
cp .env.example .env        # then set DATABASE_URL to the DB URL from `supabase start`
uv venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
uv pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

API docs will be at `http://localhost:8000/docs`.

### 3. Start the frontend

```bash
cd frontend
bun install
bun run dev
```

Opens at `http://localhost:5173`. The Vite dev server proxies `/api` requests to the backend.

### 4. Run backend tests

```bash
cd backend
uv run pytest
```

## Installation

This section takes you from a clean machine to a fully wired Claude Code + Codex environment for this project. It assumes you already have a terminal, `git`, and a recent Node.js (≥ 18) installed. Run every step in order — later steps depend on earlier ones.

At the end you will have:

- `claude` and `codex` CLIs installed and authenticated
- Five MCP servers connected inside Claude Code (`atlassian`, `linear-server`, `codex`, `playwright`, `exa`)
- Two Anthropic plugins enabled (`frontend-design`, `code-review`)
- Three project-scoped skills loaded (`shadcn`, `skill-creator`, `supabase-postgres-best-practices`)

### 1. Install Claude Code

**Prerequisites.** A terminal on macOS, Linux, or WSL (Windows also supported via PowerShell). An Anthropic account with either a Claude Pro/Max plan or Console API access.

**Install.** From the official installer at `claude.ai`:

```bash
# macOS, Linux, WSL
curl -fsSL https://claude.ai/install.sh | bash
```

```powershell
# Windows PowerShell
irm https://claude.ai/install.ps1 | iex
```

Open a new terminal so the `claude` binary appears on your `PATH`.

**Authenticate.** Run `claude` in any directory. On first launch it opens a browser to sign in to your Anthropic account (Pro/Max plan or Console API key — either works).

**Verify it worked.** Run the built-in diagnostic:

```bash
claude doctor
```

You should see green checks for install location, authentication, and runtime. If any item is red, see the [Claude Code troubleshooting guide](https://docs.claude.com/en/docs/claude-code/troubleshooting).

### 2. Install OpenAI Codex CLI

Claude Code delegates a second-opinion reviewer to Codex through the `codex` MCP server (see §4), and this repo's `/codex-review` slash command calls it directly. Both require the Codex CLI installed globally.

**Prerequisites.** Node.js ≥ 18 (for `npm`), plus either a ChatGPT Plus/Pro/Business/Edu/Enterprise plan or an OpenAI API key.

**Install.**

```bash
npm install -g @openai/codex
```

Do not prefix with `sudo` — fix npm permissions instead if `npm install -g` fails.

**Authenticate.** Run `codex` once from any directory and pick **Sign in with ChatGPT** (recommended) or **Sign in with API key**. The CLI stores credentials in `~/.codex/`.

**Verify it worked.**

```bash
codex --version
codex mcp-server --help
```

Both should print without error. The second command is important — it confirms the `mcp-server` subcommand that this repo's `.mcp.json` relies on is available.

### 3. Configure the local Codex MCP server

The `codex mcp-server` subcommand runs Codex as a Model Context Protocol server over stdio, which Claude Code can talk to. This repo has it pre-wired in `.mcp.json`:

```json
"codex": {
  "type": "stdio",
  "command": "codex",
  "args": ["mcp-server"]
}
```

Because the entry is already in the repo, you do not need to run `claude mcp add`. You just need to make sure the `codex` binary from §2 is on the same `PATH` that Claude Code inherits when it launches.

**Approve the project-scoped servers.** The first time you open this repo with `claude`, Claude Code shows a prompt asking whether to trust the project's `.mcp.json`. Choose **Yes** — project-scoped MCP servers only load after you trust them.

**Verify it worked.** Inside the project directory, start Claude Code and run the `/mcp` slash command:

```text
claude
> /mcp
```

You should see `codex` listed as **connected**. If it shows **failed**, the most common cause is `codex` not being on `PATH` for the process that spawned Claude Code — quit your terminal, open a fresh one, and retry.

### 4. Configure the other MCP servers used in this project

`.mcp.json` defines four more servers. All are pre-wired; you only need to provide credentials and (for the remote servers) complete an OAuth flow. For Atlassian vs Linear, just use the one you use. We personally use Linear but if you use Jira for project management, use the Atlassian MCP.

| Server | Transport | Provided by `.mcp.json` | What you need to do |
|--------|-----------|--------------------------|---------------------|
| `atlassian` | `http` (remote) | `https://mcp.atlassian.com/v1/mcp` | OAuth on first use inside Claude Code |
| `linear-server` | `http` (remote) | `https://mcp.linear.app/sse` | OAuth on first use inside Claude Code |
| `playwright` | `stdio` (local) | `npx @playwright/mcp@latest` | Nothing beyond Node.js |
| `exa` | `stdio` (local) | `npx -y exa-mcp-server` | Provide `EXA_API_KEY` (pre-filled for the workshop) |

**Authenticate the remote servers.** Start Claude Code in the project directory and run any tool that routes through the remote server — or simply trigger the auth flow manually:

```text
> /mcp
```

Select `atlassian`, then follow the browser-based OAuth flow back to the Atlassian instance you use. Repeat for `linear-server`. No local keys or installs are required for either.

**Exa API key.** The workshop `.mcp.json` includes a shared `EXA_API_KEY` so the class can run immediately. For real work, overwrite it with your own key from [dashboard.exa.ai](https://dashboard.exa.ai). Either edit `.mcp.json` directly or export the variable in your shell profile — `.mcp.json` env values take precedence when present.

**Playwright.** No setup beyond Node.js. On first invocation it may download a Chromium build into your npm cache; allow the download.

**Verify it worked.** Back inside Claude Code:

```text
> /mcp
```

All five servers (`atlassian`, `linear-server`, `codex`, `playwright`, `exa`) should show **connected**. If a remote server shows **unauthenticated**, re-run the OAuth flow from the `/mcp` menu.

### 5. Install the Claude Code plugins

Two plugins from Anthropic's official `claude-code-plugins` marketplace are enabled in this project via `.claude/settings.json`:

```json
"enabledPlugins": {
  "code-review@claude-code-plugins": true,
  "frontend-design@claude-code-plugins": true
}
```

- `frontend-design` — Anthropic's official frontend plugin. Generates distinctive, production-grade UI and avoids generic AI aesthetics.
- `code-review` — multi-agent PR reviewer with confidence-based scoring.

The `enabledPlugins` entry flags the plugins as on, but each user still needs to install them locally the first time. Do this once per machine.

**Add the marketplace.** From inside Claude Code in any directory:

```text
> /plugin marketplace add anthropics/claude-code
```

This registers the `claude-code-plugins` marketplace (sourced from the `anthropics/claude-code` GitHub repo) so you can install plugins from it by name.

**Install the two plugins this repo uses.**

```text
> /plugin install frontend-design@claude-code-plugins
> /plugin install code-review@claude-code-plugins
```

Alternatively, run `/plugin` on its own to open the interactive browser and pick them from the list.

**Verify it worked.**

```text
> /plugin
```

Both `frontend-design` and `code-review` should appear under **Installed**. When you next start Claude Code in this project, the `enabledPlugins` flags in `settings.json` will activate them automatically.

**Updating later.** Run `/plugin marketplace update claude-code-plugins` to pull the latest plugin versions.

### 6. Install Claude Code skills

Skills are self-contained folders — each with a `SKILL.md` and optional scripts or references — that Claude loads dynamically when it decides a skill is relevant. Instead of copying folders around by hand, this project installs skills with [**skills.sh**](https://skills.sh), a marketplace of skills that you can browse and fetch and clone into `.claude/skills/` (or `~/.claude/skills/`). It also records its source hash in `skills-lock.json` so the team stays on the same version.

**Prerequisites.** Node.js ≥ 18 (for `npx`). Nothing else — `npx skills` auto-fetches on first run.

**This repo already has three skills pre-installed** under `.claude/skills/`, tracked in `skills-lock.json`:

```text
.claude/skills/shadcn/                           # shadcn/ui component guidance
.claude/skills/skill-creator/                    # meta-skill for authoring new skills
.claude/skills/supabase-postgres-best-practices/ # Postgres performance rules
```

Cloning the repo is enough to get them — no install step is required on day one. But if you ever need to reinstall a skill (for example after deleting it, upgrading to a newer version, or adding a skill on a future project), use the commands below. Run them from the repo root — `skills add` writes into the current project's `.claude/skills/` directory by default.

**Install / reinstall skills for this project:**

```bash
# Anthropic's frontend-design skill
npx skills add https://github.com/anthropics/skills --skill frontend-design

# Anthropic's skill-creator (meta-skill for authoring new skills)
npx skills add https://github.com/anthropics/skills --skill skill-creator

# Supabase's Postgres best-practices skill
npx skills add https://github.com/supabase/agent-skills --skill supabase-postgres-best-practices
```

Each command:

1. Clones the source repo into a temporary cache
2. Copies the requested skill folder into `.claude/skills/<skill-name>/`
3. Updates `skills-lock.json` with the resolved source and a content hash so teammates can verify they have the same version

Commit the resulting changes to `.claude/skills/` and `skills-lock.json` so everyone on the team picks up the same skill.

**Verify it worked.** Start Claude Code in the repo and list the loaded skills:

```text
claude
> /skill
```

Each skill you installed should appear in the list. You can also inspect the folder directly:

```bash
ls .claude/skills
# expected: shadcn  skill-creator  supabase-postgres-best-practices
cat skills-lock.json
```

**General-purpose workflow for future projects.** `npx skills add` works the same way in any Claude Code project, including ones you start from scratch. The general pattern is:

```bash
npx skills add <git-repo-url> --skill <skill-name>
```

You can scope a skill two ways:

| Scope | Install from | Loaded when |
|-------|--------------|-------------|
| Project | Run `npx skills add …` from the repo root → writes to `.claude/skills/<name>/` | Claude Code is started inside that repo. Check into git so the whole team gets it. |
| Personal | Run `npx skills add … --global` (writes to `~/.claude/skills/<name>/`) | Claude Code is started anywhere. Not shared with your team. |

Any GitHub repo that contains one or more skill folders (each with a `SKILL.md`) is a valid source — Anthropic's own [`anthropics/skills`](https://github.com/anthropics/skills), Supabase's [`supabase/agent-skills`](https://github.com/supabase/agent-skills), shadcn/ui's official registry, and third-party repos all work the same way.

**Authoring new skills.** Use the `skill-creator` skill that ships with this repo — it walks you through drafting, testing, and iterating on a new skill. Once it's ready, publish the folder to a GitHub repo and teammates can install it with the same `npx skills add` pattern.

### Troubleshooting

- **`claude doctor` reports a problem** → See the official [Claude Code troubleshooting guide](https://docs.claude.com/en/docs/claude-code/troubleshooting).
- **`/mcp` shows a server as `failed`** → For `codex`, confirm `codex --version` works in the same shell you launched Claude Code from. For `playwright` or `exa`, confirm `npx --version` works. For remote servers, re-run the OAuth flow from the `/mcp` menu. See [Connect Claude Code to tools via MCP](https://docs.claude.com/en/docs/claude-code/mcp).
- **Plugins don't show up after `/plugin install`** → Run `/plugin marketplace update claude-code-plugins`, then reinstall. See [Create and distribute a plugin marketplace](https://docs.claude.com/en/docs/claude-code/plugin-marketplaces).
- **Skills don't trigger** → Confirm the folder is at `.claude/skills/<name>/SKILL.md` (or `~/.claude/skills/<name>/SKILL.md`) and the frontmatter `description` clearly describes when to use the skill. See [Extend Claude with skills](https://docs.claude.com/en/docs/claude-code/skills).
- **Codex won't sign in** → See the official [Codex CLI README](https://github.com/openai/codex/blob/main/README.md) and [Codex CLI docs](https://developers.openai.com/codex/cli).

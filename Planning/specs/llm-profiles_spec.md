# LLM Profiles Specification

**Version:** v1
**Date:** 2026-05-21

Allows users to save one or more named LLM configurations ("profiles") and select one when starting a game. API keys are encrypted at rest using a machine-derived key. The game engine falls back to stub mode when no profile is selected.

---

## Overview

```
Settings Panel (Vue)
  ├─ List saved profiles
  ├─ Add / edit / delete profile
  └─ Test connection button

New Game Screen (Vue)
  └─ "AI profile" dropdown  →  None | <profile name>

SimRun
  └─ llm_profile_id (nullable FK → llm_profiles)

Engine startup
  └─ LLMConfig.resolve(profile_id) → LLMConfig
```

---

## Data Model

### New table: `llm_profiles`

| Column | Type | Notes |
|--------|------|-------|
| `profile_id` | String PK | UUID |
| `name` | String | User-facing label, unique, e.g. "Claude API", "Local Ollama" |
| `provider` | String | `"anthropic"` \| `"openai_compat"` |
| `model` | String | e.g. `"claude-sonnet-4-6"`, `"llama3.2"` |
| `encrypted_api_key` | String | Fernet-encrypted, base64; empty string for local models |
| `base_url` | String | Required for `openai_compat`; empty for Anthropic |
| `temperature` | Float | Default 0.7 |
| `max_tokens` | Integer | Default 500 |
| `timeout` | Integer | Seconds; default 30 |
| `created_at` | DateTime | UTC |

### Change to `sim_runs`

Add column:

| Column | Type | Notes |
|--------|------|-------|
| `llm_profile_id` | String (nullable FK) | References `llm_profiles.profile_id`; NULL = stub mode |

---

## Encryption

**Library:** `cryptography` (Fernet — AES-128-CBC + HMAC-SHA256)

**Key derivation:**
- Seed: `str(uuid.getnode())` — MAC address as a stable machine identifier
- Derive 32-byte key: `hashlib.sha256(seed.encode()).digest()`
- Encode to URL-safe base64 → valid Fernet key

**Module:** `engine/llm/crypto.py`

```python
def encrypt_api_key(plaintext: str) -> str: ...  # returns base64 Fernet token
def decrypt_api_key(ciphertext: str) -> str: ...  # returns plaintext; raises on bad key
```

**Threat model:** protects against casual file inspection and accidental log exposure. Does not protect against an attacker with full filesystem access (they could derive the same key). This is appropriate for a local desktop/server application.

**Local models** (Ollama, LM Studio): `api_key` is an empty string. `encrypt_api_key("")` is stored; `decrypt_api_key(...)` returns `""`.

---

## Config Resolution (updated priority order)

```
1. llm_profile_id on SimRun  →  load profile, decrypt key  →  LLMConfig
2. city.llm_config_json      →  existing per-city override (backward compat)
3. Environment variables     →  LLM_PROVIDER, LLM_MODEL, etc.
4. Stub fallback             →  no LLM call made
```

New helper on `LLMConfig`:

```python
@classmethod
def from_profile(cls, profile: LLMProfile) -> "LLMConfig":
    """Decrypt API key and return LLMConfig."""
```

---

## API Routes

Router: `api/routes/llm_profiles.py` — prefix `/llm-profiles`

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/llm-profiles` | List all profiles (api_key omitted from response) |
| `POST` | `/llm-profiles` | Create profile; api_key encrypted before storage |
| `PUT` | `/llm-profiles/{profile_id}` | Update profile; re-encrypts api_key if provided |
| `DELETE` | `/llm-profiles/{profile_id}` | Delete profile |
| `POST` | `/llm-profiles/{profile_id}/test` | Attempt a minimal LLM call; return `{"ok": true}` or `{"ok": false, "error": "..."}` |

**API key handling:**
- On create/update: client sends plaintext key; server encrypts before writing
- On read: `encrypted_api_key` is never returned; response includes a boolean `has_api_key` instead

### Request schema (create / update)

```json
{
  "name": "Claude API",
  "provider": "anthropic",
  "model": "claude-sonnet-4-6",
  "api_key": "sk-ant-...",
  "base_url": "",
  "temperature": 0.7,
  "max_tokens": 500,
  "timeout": 30
}
```

### Response schema (list / create / update)

```json
{
  "profile_id": "uuid",
  "name": "Claude API",
  "provider": "anthropic",
  "model": "claude-sonnet-4-6",
  "has_api_key": true,
  "base_url": "",
  "temperature": 0.7,
  "max_tokens": 500,
  "timeout": 30
}
```

---

## SimRun API changes

`POST /sim/start` request body gains an optional field:

```json
{
  "city_id": "...",
  "llm_profile_id": "uuid-or-null"
}
```

When `llm_profile_id` is provided, it is stored on the `SimRun` row and used by the engine for all LLM calls in that run.

---

## Frontend

### Settings panel

- Accessible from a top-level "Settings" button (always visible in header)
- Shows a list of saved profiles: name, provider, model
- "Add profile" button → inline form
- Each row has Edit and Delete actions
- Edit opens an inline form pre-populated (api_key field blank, placeholder "leave blank to keep existing")
- "Test" button on each row: calls `/llm-profiles/{id}/test`, shows ✓ or error message
- "Default for new games" selector: `None (stub mode)` + one entry per profile. Persists
  to `localStorage` (`defaultLlmProfileId`) via `store.setDefaultLlmProfile`. Cleared
  automatically when the chosen profile is deleted. This is a per-browser preference; it does
  not change any existing run.

### New Game screen

- Existing "Start Game" / new run form gains an "AI" dropdown
- Options: `None (stub mode)` + one entry per saved profile
- Default: the saved `defaultLlmProfileId` preference if it still exists server-side, else `None`
- Selection stored as `llm_profile_id` in the start request
- The title-screen quick-start (no dropdown shown) applies the saved default directly,
  validated against the live profile list so a stale id falls back to `None` instead of erroring

### Loading a run

- A run's `llm_profile_id` is persisted on the `SimRun` row and restored on resume
  (`/sim/switch` → session). Loading a saved game keeps its own AI setting, independent of
  the new-game default.

**Done when:**
- The AI Settings panel shows a "Default for new games" selector listing `None` plus every saved profile; choosing one persists to `localStorage` under `defaultLlmProfileId`  `[human-required]`
- Deleting the profile currently set as the new-game default clears the stored default (selector returns to `None`)  `[human-required]`
- With a default set, starting a new game from the title screen creates a run whose `llm_profile_id` equals that default; with no default it is `null` (stub mode)  `[human-required]`
- When the stored default names a profile that no longer exists server-side, starting a new game falls back to `None` rather than erroring  `[human-required]`
- A profile passed to `/sim/start` is stored on the `SimRun`; omitting it yields stub mode (`llm_profile_id` is null) — `tests/test_sim_llm_profile.py`  `[automated]`
- Resuming a saved run via `/sim/switch` restores that run's own `llm_profile_id` even after the in-memory session is dropped — `tests/test_sim_llm_profile.py`  `[automated]`

---

## File Structure

```
engine/llm/
    crypto.py          ← encrypt_api_key, decrypt_api_key, derive_fernet_key

db/
    models.py          ← LLMProfile table, llm_profile_id on SimRun

api/routes/
    llm_profiles.py    ← CRUD + test endpoint

frontend/src/
    components/
        LLMSettings.vue     ← profile list + add/edit/delete form
    views/ or existing new-game flow
        (llm_profile_id added to start-run request)
```

---

## Tests

- `tests/test_llm_crypto.py` — encrypt/decrypt round-trip; empty string; wrong key produces error
- `tests/test_llm_profiles.py` — CRUD via API test client; api_key not returned in list; test endpoint happy/sad paths
- Existing `tests/test_llm.py` — no changes needed (StubLLMClient path unchanged)

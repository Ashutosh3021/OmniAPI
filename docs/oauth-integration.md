# OAuth sign-in — frontend integration contract

Sign-in is **Google / GitHub only**. There is no password anywhere: the
account is created the first time a provider signs in, and it is identified
by the provider account that was used.

Base path: `/api/v1/auth/oauth` (i.e. `{NEXT_PUBLIC_API_URL}/auth/oauth`).

---

## 1. The flow, end to end

```
/sign-in page
  └─ GET  /auth/oauth/providers                  → which buttons to render
  └─ user clicks "Continue with Google"
       └─ browser navigates to GET /auth/oauth/google       (302 → Google)
            └─ Google calls back GET /auth/oauth/google/callback   (on the API)
                 └─ 302 → {OAUTH_SUCCESS_REDIRECT_URL}?code=<one-time>
                      └─ frontend page /auth/callback
                           └─ POST /auth/oauth/exchange  { code }  → token pair
                                └─ store tokens, go to /dashboard
```

The `code` in the redirect is **single-use** and expires after
`OAUTH_CODE_TTL_SECONDS` (default 300 s). It is not a token — it must be
exchanged before it can do anything.

---

## 2. Endpoints

### `GET /auth/oauth/providers` — which buttons to show

Public. Always safe to call.

```json
{
  "providers": [
    { "id": "google", "name": "Google", "configured": true },
    { "id": "github", "name": "GitHub", "configured": false }
  ]
}
```

Render a button only for `configured: true`. A provider with no credentials
on the server is simply not offered (it is not an error).

### `GET /auth/oauth/{provider}` — start sign-in

Public. **Navigate the browser to it** (a full page load, not `fetch` — it
returns `302 Location:` to the provider). Do not follow it with XHR.

- `{provider}` is `google` or `github`; anything else returns 404/400.
- Rate limited: `RATE_LIMIT_OAUTH_PER_IP` (default 20) per
  `RATE_LIMIT_AUTH_WINDOW_SECONDS` (default 900 s). On 429, show a
  "too many attempts, try again in a few minutes" message.

### `GET /auth/oauth/{provider}/callback` — server-side only

Never called by frontend code. The provider calls it on the API host; it
validates the `state`, links or creates the user, and redirects the browser
to `OAUTH_SUCCESS_REDIRECT_URL?code=<one-time>`.

On failure it redirects to `OAUTH_FAILURE_REDIRECT_URL?error=<reason>` where
`error` is one of:

| `error` value | Meaning |
|---|---|
| `access_denied` | The user cancelled at the provider |
| `missing_code` | The provider did not return a code |
| `invalid_state` | Unknown, expired or replayed `state` — restart the flow |
| `invalid_code` | The provider rejected the code — restart the flow |
| `provider_unavailable` | The provider did not answer — retry later |
| `unverified_email` | The provider account's email is not verified |

### `POST /auth/oauth/exchange` — trade the code for tokens

```http
POST /auth/oauth/exchange
Content-Type: application/json

{ "code": "..." }
```

**200 — exactly the shape `/auth/login` used to return**, so existing token
storage code should work unchanged:

```json
{
  "access_token": "eyJ...",
  "refresh_token": "opaque-string",
  "token_type": "bearer"
}
```

**401** when the code is expired, already redeemed or malformed:

```json
{ "detail": "This sign-in link has expired. Please try again." }
```

Always clear the `code` from the URL (and state) after a successful
exchange — replaying it fails.

### `POST /auth/refresh` — rotate the pair

```json
{ "refresh_token": "..." }
```

Returns the same `Token` shape. **Rotation is enforced**: the presented
refresh token is revoked and replaced, so the response **must** overwrite the
stored pair. Presenting a token that was already used revokes the whole
family — the user is signed out and must sign in again.

### `POST /auth/logout` — revoke server-side

```json
{ "refresh_token": "..." }
```

Returns `204`. Signing out is not just deleting local state: without this
the refresh token stays valid until it expires.

### `GET /auth/me` — current user

Unchanged. Requires `Authorization: Bearer <access_token>`:

```json
{ "user_id": 1, "email": "a@b.c", "full_name": "A B", "tier": "free", "created_at": "..." }
```

`PATCH /auth/me` with `{ "full_name": "..." }` is also unchanged.

---

## 3. Endpoints that no longer exist

These all return **404**. Any form that posts to them is dead code:

| Removed | Was |
|---|---|
| `POST /auth/register` | Create account with password |
| `POST /auth/login` | Sign in with password |
| `POST /auth/change-password` | Change password |
| `POST /auth/forgot-password` | Start password reset |
| `POST /auth/reset-password` | Finish password reset |

The UI must contain **no password field** anywhere — not on sign-in, not in
profile settings. An account exists only once its provider has signed in.

---

## 4. The `/auth/callback` page

The backend's `OAUTH_SUCCESS_REDIRECT_URL` must point at a page on the
frontend, defaulting to:

```
/auth/callback          (full: https://<frontend>/auth/callback)
```

Responsibilities:

1. Read `code` from the query string (also handle `?error=` — show the
   sign-in page with the reason).
2. `POST /auth/oauth/exchange` with the code.
3. Store `access_token` + `refresh_token` exactly as the old login did
   (same storage keys, same auth context).
4. Replace the URL (strip `code`) so a refresh does not re-post a
   redeemed code.
5. Redirect to `/dashboard`.

**This route must be reachable while signed out** — exclude it from whatever
middleware/guard redirects unauthenticated visitors to `/login`. There is no
`/login` form anymore; that page becomes a "continue with Google/GitHub"
screen.

---

## 5. Recommended UI shape

- **Sign-in page**: call `GET /auth/oauth/providers` on mount; render one
  button per `configured` provider. Navigating = `window.location.href =
  \`${API}/auth/oauth/${provider}\``.
- **`/auth/callback`**: as above; show a spinner, never a form.
- **Auth state**: unchanged — the token pair in storage, the same refresh
  interceptor on 401. The only difference is how the pair is obtained.
- **Error surface**: map `?error=` values from §2 to friendly copy.

---

## 6. Server configuration the frontend depends on

Set on the backend (Render), never in the frontend bundle:

| Variable | Effect on the frontend |
|---|---|
| `OAUTH_REDIRECT_BASE_URL` | Must be the API's public origin — it builds the callback URI registered with the providers |
| `OAUTH_SUCCESS_REDIRECT_URL` | Where the browser lands with `?code=` — must be the `/auth/callback` page |
| `OAUTH_FAILURE_REDIRECT_URL` | Where the browser lands with `?error=` — usually the sign-in page |
| `GOOGLE_CLIENT_ID` / `GITHUB_CLIENT_ID` + secrets | Whether a provider button exists at all |

Redirect URIs that must be registered in the provider consoles:

```
https://<api-host>/api/v1/auth/oauth/google/callback
https://<api-host>/api/v1/auth/oauth/github/callback
```

Local development:

```
http://localhost:8000/api/v1/auth/oauth/google/callback
http://localhost:8000/api/v1/auth/oauth/github/callback
```

---

## 7. Checklist for the frontend lane

- [ ] `/auth/callback` page exists, is excluded from the auth guard
- [ ] Sign-in page reads `GET /auth/oauth/providers` (no hardcoded provider list)
- [ ] Buttons navigate with a full page load, not `fetch`
- [ ] `POST /auth/oauth/exchange` response stored with the existing token logic
- [ ] `code` cleared from the URL after exchange
- [ ] All password fields, the register form, and forgot/reset password routes removed
- [ ] `/auth/register`, `/auth/login` calls removed (they 404)
- [ ] 401 → refresh interceptor still works against `POST /auth/refresh`
      (rotation: always overwrite both tokens)
- [ ] `POST /auth/logout` called on sign-out with the stored refresh token
- [ ] `?error=` from the failure redirect surfaced to the user

# GDPR form: country + postal code UI design

Covers the client-side JS in `gdpr.py` (`headerScripts`/`footerScripts`)
that lets a user pick a country (Mapbox `MapboxSearchBox`, `types:
'country'`) and enter a postal code (plain text input, validated via a
debounced call to Mapbox's structured forward geocoder).

## Fields involved

- `countryName` (hidden text input) — display value, driven by the
  Mapbox country search box, not typed directly by the user.
- `countryCode` (hidden field) — ISO country code of the selected
  country. Source of truth for "which country is selected."
- `postalCode` (visible text input) — the only field the user types
  into directly for location.
- `latitude` / `longitude` / `city` / `region` (hidden) — derived from
  the last successful postal code lookup.
- `#postalcode-error` (DOM node, present/absent) — the single
  validity signal: if present, the current country/postal-code pair
  is not valid and submission should be blocked.

### Root design rule

`countryCode` means "which country is selected" and **nothing else**.
It must never be cleared to signal "the postal code is invalid" —
that conflates two independent facts and breaks the debounce loop
(see "Bug history" below). Validity of the postal code is signalled
purely by the presence/absence of `#postalcode-error`.

## States

State = (`countryCode` blank or set) x (`postalCode` blank or
non-blank) x (error shown or not).

| # | countryCode | postalCode | error shown | meaning |
|---|---|---|---|---|
| S0 | blank | blank | no | Nothing entered. Valid opt-out state — `postProcess`'s "No Data" branch removes the principal from any map listing. |
| S1 | set | blank | no | Country picked, postal code not entered yet. Valid, incomplete. |
| S2 | blank | non-blank | no | Postal code typed before any country picked. Can't validate yet — no country to search within. |
| S3 | set | non-blank | no | Postal code confirmed valid for this country. Ready to submit. |
| S4 | set | non-blank | **yes** | Postal code typed but does not resolve for this country. Must block submission. |

There is no state with `countryCode` blank and an error shown caused
by postal-code validation, on the *live* `lookupPostalCode` path:
without a country there is nothing to validate against, so it must
not run at all — it only ever clears a leftover error, never sets
one, when `countryCode` is blank. Two other mechanisms can still show
`#postalcode-error` while `countryCode` is blank: the submit-attempt
check (see "Submission gate" below) and a country-search API failure
(see "Country search fails" below) — neither is a postal-code
validation state.

## Events / transitions

**Pick a country** (`onCountrySelected`, fires on the Mapbox search
box's `retrieve` event):
- Sets `countryName` / `countryCode` from the selected feature.
- Does **not** clear `postalCode`. (The original design cleared it
  unconditionally on every country selection; testing showed this
  destroys a postal code the user typed before picking any country —
  see "Known issues found in testing" below.)
- Calls `lookupPostalCode()`, which now runs its normal logic against
  whatever value is already in the field:
  - `postalCode` blank -> clears any stale error. Lands S1 (same as
    before).
  - `postalCode` non-blank -> the `!postalCode || !countryCode` guard
    now passes, since `countryCode` was just set, so this re-validates
    the existing postal code against the newly-selected country and
    lands in S3 (matches) or S4 (doesn't match) — exactly as if the
    user had just typed that value.
- This makes "pick a country" and "edit postal code" the same code
  path with no special-casing: selecting a country is just another
  trigger for `lookupPostalCode()`.

**Edit postal code** (`blur`, or debounced `input`, both call
`lookupPostalCode()`):
- `postalCode` now blank -> clear error, return. Lands in S0 or S1
  depending on `countryCode`.
- `postalCode` non-blank, `countryCode` blank -> guard returns
  immediately, no fetch, no error. Stays S2. (Nothing to search
  within yet; this is not a failure state.)
- `postalCode` non-blank, `countryCode` set -> fetch Mapbox's
  structured forward geocoder (`postcode=`, `country=`,
  `autocomplete=false`).
  - Response has a postcode-level match (`context.postcode` present)
    in the right country (`context.country.country_code ===
    countryCode`) -> clear error, populate
    `latitude`/`longitude`/`city`/`region`. Lands in S3.
  - Otherwise (no features, a country-only fallback match, or a
    match in the wrong country) -> show error. `countryCode` is left
    untouched. Lands in S4.

Because `countryCode` is never cleared on failure, every further
keystroke in S4 still passes the guard and re-runs the lookup — the
user can correct a bad postal code without having to reselect the
country.

**Clear country** (`onCountryCleared`, fires on the Mapbox search
box's `clear` event — deleting all text or clicking its "x" icon):
- Clears `countryName` / `countryCode` only, plus any stale
  `#postalcode-error`.
- Does **not** clear `postalCode`. A postal code remains meaningful
  data on its own even without a country selected — the same
  asymmetry as never auto-clearing `countryCode` from the postal-code
  side, just in the other direction. Only "pick a country" ever
  re-validates an existing postal code; clearing the country never
  discards one.
- Lands in S0 (if `postalCode` was already blank) or S2 (if
  `postalCode` was set) — the same S2 reached by typing a postal code
  before picking any country.

**Country search fails** (`onCountrySearchError`, fires on the Mapbox
search box's `suggesterror` event — the suggestions API call itself
failed, e.g. network/auth/rate-limit; distinct from "no country
matched the query," which is not an error and fires `suggest` with an
empty list instead):
- Shows "Could not reach the country lookup service." in
  `#postalcode-error`, via the same `showPostalCodeError` used by
  postal-code lookup failures.
- Does not touch `countryCode` or `postalCode`.
- This is a second path, alongside the submit-attempt gate below,
  where `#postalcode-error` can appear while `countryCode` is blank
  on a *live* path. It doesn't add a new (countryCode, postalCode)
  state — it's an infrastructure-failure signal reusing the same DOM
  node, orthogonal to postal-code validation.

## Submission gate — revised after testing found it insufficient

**Original design (flawed):** block submit only when
`#postalcode-error` exists (state S4), and let S1/S2 (exactly one of
`countryCode`/`postalCode` blank) reach the server, relying on
`postProcess`'s `HTTPBadRequest` as the backstop.

**Why this was wrong:** testing (2026-08-25) showed the Save button
can be clicked in S1 (country picked, no postal code entered) with
nothing client-side stopping it. The only backstop is a bare
`HTTPBadRequest` from the server — not a validation message, an error
page. From the user's point of view the form simply let the
submission through with a country but no postal code. See "Known
issues found in testing" below.

**Revised gate:** block submit (`preventDefault`) for every state
except S0 (both blank — the intentional opt-out) and S3 (both set, no
error). On the form's `submit` event:

- `countryCode` blank and `postalCode` blank -> allow (S0).
- `countryCode` set and `postalCode` set and no `#postalcode-error`
  -> allow (S3).
- Anything else (S1, S2, or S4) -> `preventDefault()` and show a
  message in `#postalcode-error` explaining what's missing:
  - S1 (country set, no postal code): "Please enter a postal code, or
    clear the selected country to skip location sharing."
  - S2 (postal code set, no country): "Please select a country to
    validate this postal code, or clear the postal code to skip
    location sharing."
  - S4: the lookup-failure message is already showing; leave it as is.

This means `#postalcode-error` can now appear while `countryCode` is
blank (S2), but only as a result of a submit *attempt* — not from the
live `lookupPostalCode` path, whose guard still skips S2 silently
while the user is just typing. The "no state with `countryCode` blank
and error shown" invariant in "States" above still holds for the live
path; the submit-attempt check is a separate mechanism layered on top,
reusing the same `#postalcode-error` element rather than adding a new
field.

**Status: implemented.** `onCountrySelected` no longer clears
`postalCode` — it only sets `countryName`/`countryCode` and calls
`lookupPostalCode()`. The submit listener on the form owning
`#form-action-Save` now runs `checkSubmittable`, which blocks
everything except S0 and S3 and shows a contextual message in
`#postalcode-error` for S1/S2 (S4 already has its own message from
`lookupPostalCode`).

## Known issues found in testing (2026-08-25)

Reported against the first implementation pass (a `submit` listener
that only checked for `#postalcode-error`, plus the original
`onCountrySelected` that always cleared `postalCode`):

1. **Submitting with a country selected but no postal code
   succeeded.** Root cause: the submit gate only checked for
   `#postalcode-error`, which is never set in S1 — no fetch is ever
   attempted when `postalCode` is blank, so there's nothing to fail.
   S1 was originally meant to be "submittable, blocked server-side,"
   but that backstop is a raw `HTTPBadRequest`, not a usable
   validation experience, so in practice nothing stopped the
   submission from the user's perspective. Fixed by the revised
   submission gate above, which blocks S1/S2 client-side with an
   explanatory message instead of deferring to the server.
2. **Typing a postal code before picking a country, then picking a
   country, wiped the postal code.** Root cause: `onCountrySelected`
   unconditionally cleared `postalCode` on every country selection,
   including the S2 -> S1 transition, where there was no "previous
   country" for the code to be stale against — the field was cleared
   even though the code had never been validated against anything.
   Fixed by removing the unconditional clear (see the revised "Pick a
   country" transition above): the existing postal code is now
   re-validated against the newly-picked country instead of being
   discarded.

## Bug history (why the root design rule exists)

The original implementation cleared `countryCode` in the lookup
failure branch, intending it as a defense-in-depth signal so a
bypassed/JS-disabled submission would still be caught by
`postProcess`'s "exactly one of countryCode/postalCode blank" check.
In practice this broke the UI: once a lookup failed, `countryCode`
went blank, and every subsequent edit to `postalCode` hit the
`!postalCode || !countryCode` guard and silently no-opped — the user
could not correct a typo without reselecting the country from
scratch. Fixed by leaving `countryCode` untouched on failure and
signalling validity through `#postalcode-error` alone.

## Test plan

- Select a country, enter no postal code, click Save -> submit
  blocked client-side, message asks for a postal code (or to clear
  the country), `countryCode` retained.
- Type a postal code with no country selected, click Save -> submit
  blocked client-side, message asks for a country (or to clear the
  postal code).
- Select a country, enter a postal code that doesn't resolve -> error
  shown, `countryCode` retained, submit blocked.
- From the state above, correct the postal code to a valid one ->
  error clears without reselecting the country,
  `latitude`/`longitude`/`city`/`region` populate, submit allowed.
- Type a postal code before selecting any country, then select a
  country -> postal code is preserved (not cleared) and immediately
  re-validated against that country: lands in S3 (valid, no error) or
  S4 (error shown), same result as if it had been typed after the
  country.
- Set a valid country + postal code, then change the country -> the
  same postal code is re-validated against the new country instead of
  being cleared; lands in S3 (still happens to match) or S4 (error
  shown, code left in the field for correction).
- Leave both fields blank and submit -> principal is removed from any
  map listing ("No Data" branch), no error, submit allowed.

## Implementation reference

Save button HTML:
<input type="submit" id="form-action-Save" name="form.action.Save" value="Save" class="action btn" accesskey="#">
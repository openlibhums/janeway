# Reader Preference Storage

Janeway persists small, reader-chosen preferences (e.g. **accessibility mode**,
the **reading options bar**'s font/colour/size) the same way: on the
`Account` for logged-in readers, in the session for anonymous ones, with the
anonymous choice carried onto the account on login and carried back into the
session on logout. This generic store lives in `src/core/logic.py` and was
generalised from the original accessibility-mode work so a new preference
doesn't have to reinvent that persistence.

> [!WARNING]
> This store is for small, low-stakes reader-facing choices only — never
> secrets. Values are plainly loaded: the reading-options bar template seeds
> its stored value straight into the page as visible JSON (`json_script`),
> and even a preference that's never rendered into a page still sits in
> Django's session and in a plain `Account` field, readable by anyone with
> session or admin/model access. Don't put tokens, keys, or anything
> sensitive through this mechanism.

## How it works

A preference is one `PreferenceDescriptor`: a session key, the matching
`Account` field, the "unset" default, and a `clean` function that sanitises a
raw value (identity if you don't pass one).

```python
ACCESSIBILITY_MODE_DESCRIPTOR = PreferenceDescriptor(
    session_key="accessibility_mode",
    account_field="accessibility_mode",
    default=False,
    clean=bool,
)
```

## Login and logout behaviour

### Principles
- **Anonymous default is off** (or whatever `default` is registered as).
- **On login**, if the reader explicitly changed the preference during the
  anonymous session, that choice wins and updates the account. If they never
  touched it, the account's existing preference is applied instead. This
  matters so a reader who switches a preference on to use the site doesn't
  lose it just by logging in.
- **The preference is sticky across logout** — logging out never changes the
  current value; the account simply keeps whatever it last had saved. That
  isn't necessarily the same value the anonymous session held before they
  first logged in, since it could have been changed again while logged in.

### State Storage
| Reader state | Storage location | Lifetime |
| --- | --- | --- |
| Anonymous, never touched it | nowhere — reads fall back to `default` | n/a |
| Anonymous, explicitly changed it | `request.session[session_key]` | Until the session expires or the browser is closed, or until the reader logs in (then migrated onto the account and cleared) |
| Logged in | `Account.<account_field>` | Indefinite — follows the reader across devices and sessions until changed again |
| After logout | re-seeded into the fresh session from the account's last value, only if it isn't `default` | Until the session expires/browser closes, or until the reader logs in again |



### Login: value changes

| Anonymous session | Account before | Value after login | Account after login | Rule |
| --- | --- | --- | --- | --- |
| Untouched | Off | Off | Off | Nothing to apply |
| Untouched | On | On | On | Account preference applied |
| Explicit On | Off | On | On ← updated | Explicit action wins and writes back |
| Explicit On | On | On | On | Consistent |
| Explicit Off | Off | Off | Off | Consistent |
| Explicit Off | On | Off | Off ← updated | Explicit Off wins and writes back, even though it *disables* a previously-enabled account preference — this is the case naive "value equals default, so treat it as untouched" logic would get wrong; what matters is that the session *key is present*, not what it's set to |

### Logout: value changes

Simpler than login — no explicit/untouched distinction, since there's no new
choice being made. Whatever the account holds is just carried forward.

| Mode at logout | Account | Value after logout | Account after logout | Rule |
| --- | --- | --- | --- | --- |
| On | On | On | On | Stays on — sticky |
| Off | Off | Off | Off | Stays off |

## Adding a new preference

1. **Add the field** to `Account` (e.g. a `BooleanField`, `CharField`, or
   `JSONField`) and its migration.
2. **Write a `clean` function** if the value needs sanitising beyond a plain
   type coercion — see `clean_text_format_preferences()` for a dict example
   that drops anything unrecognised. A bare bool can just pass `clean=bool`.
3. **Register a descriptor** in `src/core/logic.py` and add it to
   `PREFERENCE_DESCRIPTORS`:

   ```python
   MY_PREFERENCE_DESCRIPTOR = PreferenceDescriptor(
       session_key="my_preference",
       account_field="my_preference",
       default=False,  # must match the value logout treats as "nothing to reseed"
       clean=my_clean_function,
   )
   PREFERENCE_DESCRIPTORS = [
       ACCESSIBILITY_MODE_DESCRIPTOR,
       TEXT_FORMAT_PREFERENCES_DESCRIPTOR,
       MY_PREFERENCE_DESCRIPTOR,
   ]
   ```

4. **Read it** with `get_preference(request, MY_PREFERENCE_DESCRIPTOR)`
5. **Write your own save view.** 
6. **Tests.** The full login/logout truth table (untouched vs. explicit
   on/off/reset) is already exercised once, generically, against the bool
   case in `AccessibilityModePersistenceTests`. Add tests only for what's
   actually specific to your value

### Reserved consideration: `default`

`default` isn't just a read fallback — `reseed_session_preferences` only
re-seeds a session key when the account value is `!= default`, so it also
defines what "nothing set" means for logout. 

## See also

`docs/md/reading-options-bar.md` is a worked example of a preference (a dict
of font/colour/size choices) built on top of this store, including its own
save endpoint and JS-side seeding of the stored value into the page.

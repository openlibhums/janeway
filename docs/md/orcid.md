# ORCID

Janeway lets users register and log in with their ORCID account.

## Setting up ORCID login

It can be set up in a few steps.

1. Create an API client on orcid.org.

2. Enter each production domain for your Janeway instance as a redirect URI on orcid.org. If Janeway is set to domain mode, each journal will need its own redirect URI.  

| Type | Redirect URI |
|------|-------------|
| Press (and everything within it)| `https://<press-domain>/` |
| Individual Journal — domain config | `https://<journal-domain>/` |
| Individual Journal — no press and on path config | `https://<press-domain>/<journal_code>/login/orcid/` |

3. Enable ORCID and copy the keys from your client into the Django settings file (`src/core/settings.py`). Replace _`CLIENT_SECRET`_ and _`CLIENT_ID`_ with the values from orcid.org.

    ```py
    ENABLE_ORCID = True
    ORCID_CLIENT_SECRET = "CLIENT_SECRET"
    ORCID_CLIENT_ID = "CLIENT_ID"
    ```

    Note that the URLs for the ORCID API are fixed, so you can leave the defaults in `src/core/janeway_global_settings.py`.

## Testing ORCID login manually

You can test the ORCID login flow locally, by creating a test client, adjusting your hosts file, and resetting the Janeway domain for the site you want to test.

The following steps were written for Ubuntu, and are meant for testing the press site.

1. Create a test client on orcid.org and enter a normal domain of your choosing (it won’t be accessed), with `http` and the Janeway port you use for development. An example is `http://www.openlibhums.org:8000/`.

2. Edit your hosts file to put in the domain from the redirect URI that orcid.org knows about, in place of the `localhost` domain:

    ```sh
    sudo vim /etc/hosts
    ```

    ```
    127.0.0.1 DOMAIN
    ```

    An example:

    ```
    127.0.0.1 www.openlibhums.org
    ```

    This will let orcid.org redirect your browser to the domain it knows about when authentication is finished, while allowing your browser to load the normal Janeway development server.

3. Restart the networking service for the change to take effect.

    ```sh
    sudo systemctl restart NetworkManager
    ```

4. Edit your Janeway site domain to the same domain, keeping the port number.

    ```sh
    python src/manage.py alter_domains press
    ```

    It will prompt you to enter a domain.

    ```
    Altering domain for PRESS_NAME, current domain: localhost
    Enter the new domain you wish to set:
    ```

    Enter the domain and port.

    ```
    Enter the new domain you wish to set: DOMAIN:PORT
    ```

    An example:

    ```
    Enter the new domain you wish to set: www.openlibhums.org:8000
    ```

    If it was successful, you will see this:

    ```
    Altering domain record...... [Ok]
    ```

5. Load the site at the new domain with `http` and the correct port (e.g. `http://www.openlibhums.org:8000/`) and test away.

## Troubleshooting

If the redirect URI for a journal or press is not correctly registered on the ORCID site, users will see an error when trying to sign in with ORCID or perform any other ORCID-related action:

> invalid_request: Missing parameter: redirect_uri — "&lt;journal URL&gt;" does not match registered client "&lt;client id&gt;"

### Determine the correct URI

The URI to register depends on whether you are configuring a press or a journal, and for journals, whether it uses domain or path configuration.

**To identify journal configuration type:** open the journal in a browser and look at the URL.
- Own domain (e.g. `https://myjournal.org/`) → **domain configuration**
- Press domain with journal code (e.g. `https://press.org/myjournal/`) → **path configuration**

See [Setting up ORCID login](#setting-up-orcid-login) for the format of the redirect URI.


### Verify

Go to the journal or press and click to sign in with ORCID. You do not need to complete the sign in; if the ORCID login page loads without error, the redirect URI is correctly registered.
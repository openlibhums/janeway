# ORCID

Janeway lets users register and log in with their ORCID account.

## Setting up ORCID login

It can be set up in a few steps.

1. Create an API client on orcid.org.

2. Enter each production domain for your Janeway instance as a redirect URL on orcid.org. If Janeway is set to domain mode, each journal will need its own redirect URI.

3. Enable ORCID and copy the keys from your client into the Django settings file (`src/core/settings.py`).

```py
ENABLE_ORCID = True
ORCID_CLIENT_SECRET = "your client secret"
ORCID_CLIENT_ID = "your client ID"
```

Note that the URLs for the ORCID API are fixed, so you can leave the defaults in `src/core/janeway_global_settings.py`.

## Testing ORCID login manually

You can test the ORCID login flow locally, by creating a test client, adjusting your hosts file, and resetting the Janeway domain for the site you want to test.

The following steps were written for Ubuntu, and are meant for testing the press site.

1. Create a test client on orcid.org and enter a normal domain of your choosing (it won’t be accessed) with `http` and the Janeway port you use for development: `http://www.openlibhums.org:8000/`

2. Edit your hosts file to put in the domain from the redirect URI that orcid.org knows about, in place of the `localhost` domain:

```sh
sudo vim /etc/hosts
```

```
127.0.0.1 www.openlibhums.org
```

This will let orcid.org redirect your browser to the domain it knows about when authentication is finished, while allowing your browser to load the normal Janeway development server.

3. Restart the networking service for the change to take effect.

```
sudo systemctl restart NetworkManager
```

4. Edit your Janeway site domain to the same domain, keeping the port number.

```
python src/manage.py alter_domains press
Altering domain for Test A, current domain: localhost:8000
Enter the new domain you wish to set: www.openlibhums.org:8000
Altering domain record...... [Ok]
```

5. Load the site at the new domain with `http` and the correct port (`http://www.openlibhums.org:8000/`) and test away.

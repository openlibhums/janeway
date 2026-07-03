# Manual user interface testing

This guide offers tips for testing the Janeway user interface manually during development.

## Using multiple accounts and roles

When testing a user interface manually, you often need to be logged in with several different accounts that have different roles.

You can use Firefox container tabs to switch quickly between roles.

## Testing on multiple devices at home

When you are on secure local network, you can run the Janeway local server in such a way that you can test it on other devices in addition to your development machine.

### Linux

1. Run your development server with an additional argument to specify an IP of four zeroes, and the same port as normal: `python src/manage.py runserver 0.0.0.0:8000`.

2. Find out the IP address of your development machine on your local network. This can be done with the `ip` utility by running `ip r`. An example: `192.168.68.121`.

3. Create a Domain Alias record in the Janeway admin interface (go to `localhost:8000/admin/core/domainalias`).

   - Enter the IP address from the previous step in the **Domain** field. An example: `192.168.68.121`.
   - Leave the **Is secure** field unticked.
   - Untick the **301** field, since you do not want Janeway to redirect devices that access this IP.
   - Select the journal or press site that you want to access.
   - Save the domain alias.

4. Visit this IP and port on your other device(s). For example, go to `192.168.68.121:8000`.

## Switching between themes

On a development installation, you can quickly switch to a different front-office theme by adding a query parameter.

For example, adding `?theme=material` to the URL will load the page in the Material theme.

Caveats:

- This only works when `DEBUG` is turned on.
- The Hourglass press theme (used by the Open Library of Humanities) does not support this feature.
- It does not work when using accessibility mode

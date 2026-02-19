# Manual user interface testing

This guide offers tips for testing Janeway manually during development.

## Using multiple accounts and roles

When testing a user interface manually, you often need to be logged in with several different accounts that have different roles.

You can use Firefox container tabs to switch quickly between roles.

## Testing on a phone or other device at home

When you are on secure local network, you can run the Janeway local server in such a way that you can test it on other devices.

1. Run your development server with an additional argument to specify an IP of four zeroes, and the same port as normal: `python src/manage.py 0.0.0.0:8000`.

2. Find out the IP address of your development machine on your local network. On Linux this can be done with the `ip` utility by running `ip r`. An example: `192.168.68.121`.

3. Create a Domain Alias record in the Janeway admin interface (go to `localhost:8000/admin/core/domainalias`).
  - Enter the IP address from the previous step in the **Domain** field. An example: `192.168.68.121`.
  - Leave the **Is secure** field unticked.
  - Untick the **301** field, since you do not want Janeway to redirect devices that access this IP.
  - Select the journal or press site that you want to access.
  - Save the domain alias.

4. Visit this IP and port on your other device(s). For example, go to `192.168.68.121:8000`.

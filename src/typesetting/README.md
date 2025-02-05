# typesetting
This is a plugin for Janeway that replaces the Production and Proofing stages with an alternative process.

## Install
1. Clone this repository into the Janeway plugins folder.
2. From the `src` directory run `python3 manage.py install_plugins typesetting`.
3. Run the Janeway command  for running required migrations: `python3 manage.py migrate`
4. Restart your server (Apache, Passenger, etc)
5. You can then edit your workflow to add this plugin.

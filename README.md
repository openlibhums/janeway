![Janeway Logo](http://www.openlibhums.org/hosted_files/Janeway-Logo-05.png "Logo Title Text 1")

Janeway is a journal platform designed for publishing scholarly articles.

# Technology
Janeway is written in Python (3.4+) and utilises the Django framework. 

# Installation instructions
The following is for Debian/Ubuntu-based systems (16.04).

Step 1: Install virtualevwrapper and create a project

Step 2: Install system dependencies. On Debian-based systems:

    sudo apt-get install libxml2-dev libxslt1-dev python3-dev zlib1g-dev lib32z1-dev libffi-dev libssl-dev libjpeg-dev

Step 3: pip install -r requirements.txt

Step 4: cp src/core/example_settings.py src/core/settings.py

Step 5: Update settings.py for your env (database login etc.)

# Janeway design principles
1. No code should appear to work "by magic". Readability is key.

2. Testing will be applied to security modules and whenever a post-launch bugfix is committed. We do not aim for total testing but selective regression testing.

3. Security bugs jump the development queue and are a priority.

4. We will never accept commits of, or ourselves write, paywall features into Janeway.

# Licensing
Janeway is available under the terms of the GNU AFFERO GENERAL PUBLIC LICENSE (Version 3, 19 November 2007).

# Contributions

We welcome all code contributions via Pull Requests where they can be reviewed and suggestions for enhancements via Issues. We do not currently have a  code of conduct for this repo but expect contributors to be courteous to one another.

# Contacts
If you wish to get in touch about Janeway, contact information is provided below.

Project Lead - Martin Paul Eve, martin.eve@bbk.ac.uk

Lead Developer - Andy Byers, a.byers@bbk.ac.uk

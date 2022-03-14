Technical Configuration
=======================

This section will discuss the technical configuration of Janeway focusing on the Django settings file. 

.. note:: This section is currently a work in progress.


Django Settings
---------------
Unlike traditional Django applications Janeway has two settings files, they are generally located in `src/core/`.

- janeway_global_settings.py
- settings.py (created during the installation process)

Global Settings
---------------
The global settings file is created by the Janeway team and is managed through version control. Generally speak you should not need to change anything in this file as you can use your local `settings.py` file to override variables.

Local Settings
--------------
This file is usually created during the setup process and can be based on the provided `example_settings.py` file.

- DEBUG
  - Should be set to False in any environment where an external user can access the install.
- URL_CONFIG
  - Set to either 'domain' or 'path' dependind on whether the primary way to access sites is via individual domains for each or path based urls eg. journal.press.com or press.com/journal/.
- DATABASES
  - You can set the database connection details for the install.
- CAPTCHA_TYPE
  - Can be one of three different variables: 'simple_math', 'recaptcha' or 'hcaptcha'.
    - simple_math
      - A very simple captcha using a basic mathematical question.
    - recaptcha
      - Uses Google's reCaptcha2. Has been shown to be less effective recently but v3 is not GDPR compliant. You should complete 'RECAPTCHA_PRIVATE_KEY' and 'RECAPTCHA_PUBLIC_KEY' otherwise you will get an error.
    - hcaptcha
      - Uses hcaptcha, a new addition to Janeway. You should complete 'HCAPTCHA_SITEKEY' and 'HCAPTCHA_SECRET' otherwise you will get an error.
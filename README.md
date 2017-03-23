NoJARsBot
=========

This is a relatively simple `discord.py`-based bot which will remove messages
containing obvious links to JAR files and embedded JARs unless users have the
configured roles or permissions.

Licensing
---------

NoJARsBot is licensed under the Artistic License 2.0. You may read up on the license
in the [LICENSE file](https://github.com/gdude2002/NoJARsBot/blob/master/LICENSE),
or [at choosealicense.com](http://choosealicense.com/licenses/artistic-2.0/).

Setup
-----

1. Install Python 3.5 or later
2. Install requirements - `python3.5 -m pip install -r requirements.txt`
3. Copy `config.yml.example` to `config.yml` and fill it out
4. `python3.5 -m app`

Usage
-----

As long as the bot is online, it should remove the following:

* Messages containing embedded `.jar` files
* Messages containing urls ending in `/*.jar`

If you need more than this, feel free to submit a PR.

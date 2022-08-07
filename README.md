# PaperGlobe-Web 🪄🗺

PaperGlobe-Web is a web app that wraps [PaperGlobe](https://github.com/joachimesque/paper-globe), so you can transform an image of the Earth to a template that you can cut and assemble by yourself.

Of course you’re not limited to the Earth, you can use any other planet or quasi-spherical object as a source, as long as its surface is projected in the correct way. The image of the planet must be a cylindrical projection. Right now it works with [Equirectangular](https://en.wikipedia.org/wiki/Equirectangular_projection), [Mercator](https://en.wikipedia.org/wiki/Mercator_projection) or [Gall stereographic](https://en.wikipedia.org/wiki/Gall_stereographic_projection) projections. PaperGlobe could work with any other projection, but the results won’t make you happy.

![](https://paperglo.be/static/images/paper-globe-opengraph.jpg)

## Requirements
- Python >= 3.6
- [Docker](https://docs.docker.com/engine/install/)
- [Docker compose](https://docs.docker.com/compose/install/)

## Development

First, copy `exemple.env` to `.env` and setup your app variables.

Then you can launch the app:

```bash
./run up --build
```

Then you can visit `http://localhost:8123`

To shut down the dev server, press Control-C (`^C`).

### Translations

#### Adding a new language

Let’s say you want to translate the website in Spanish.

First off, you’ll need to edit `app/config.py` to add a line to the `LANGUAGES` dict, with the language code and the language name: `"es": "Español",`.

Then you must generate a new reference file:

```bash
./run translate:init es
```

That new reference file is now found at `app/translations/es/LC_MESSAGES/messages.po`. This is the file you have to edit, by filling the empty strings `msgstr ""`. Check out the French reference file (`app/translations/fr/LC_MESSAGES/messages.po`) to see how it is done.

#### Updating the language references after a code update

If the website’s code changes, the translation files will also need reflect those changes. The following command will do that, and format the existing translations.

```bash
./run translate:update
```

#### Compiling the language files

After writing the translations, you will need to compile in order to test your translation. Here’s the command to do that. The `messages.po` file will make a `messages.mo` file that can be use by the application to provide all the necessary translations.

```bash
./run translate:compile
```

After this compilation you will need to restart your web app.

## Licenses

Some code and structure was based on [@alexOarga’s Docker Nginx Flask Celery MySQL Redis](https://github.com/alexOarga/docker-nginx-flask-celery-mysql-redis) 

The `./run` script was based on [@mouse-reeve’s `./bw-dev` script for BookWyrm](https://github.com/bookwyrm-social/bookwyrm/) and as such is shared under the same license.

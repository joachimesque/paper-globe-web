# PaperGlobe-Web 🪄🗺

PaperGlobe-Web is a web app that wraps [PaperGlobe](https://github.com/joachimesque/paper-globe), so you can transform an image of the Earth to a template that you can cut and assemble by yourself.

Of course you’re not limited to the Earth, you can use any other planet or quasi-spherical object as a source, as long as its surface is projected in the correct way. The image of the planet must be a cylindrical projection. Right now it works with [Equirectangular](https://en.wikipedia.org/wiki/Equirectangular_projection), [Mercator](https://en.wikipedia.org/wiki/Mercator_projection) or [Gall stereographic](https://en.wikipedia.org/wiki/Gall_stereographic_projection) projections. PaperGlobe could work with any other projection, but the results won’t make you happy.

![](https://repository-images.githubusercontent.com/513955992/0b1beb9c-7e3d-4535-8feb-ba6dadaff4f8)

## Requirements
- Python >= 3.6
- [Docker](https://docs.docker.com/engine/install/)
- [Docker compose](https://docs.docker.com/compose/install/)

## Development

First, copy `exemple.env` to `.env` and setup your app variables.

Then you can launch the app:

```bash
docker compose up --build
```

In order to bring it down run:

```bash
docker compose down
```

Go to:
  - http://localhost:8123

## Licenses

Some code and structure was based on [@alexOarga’s Docker Nginx Flask Celery MySQL Redis](https://github.com/alexOarga/docker-nginx-flask-celery-mysql-redis) 

The `./dev` script was based on [@mouse-reeve’s `./bw-dev` script for BookWyrm](https://github.com/bookwyrm-social/bookwyrm/) and as such is shared under the same license.

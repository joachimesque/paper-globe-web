#!/usr/bin/env python3

"""Downloads and checks external front-end libs

Avoid CDNs for front-end libraries:
https://blog.wesleyac.com/posts/why-not-javascript-cdn

Generate SRI hashes for files:
https://www.srihash.org/
"""

import base64
import hashlib
import json
import os

import requests
import click


@click.command()
@click.argument(
    "input_file",
    type=click.Path(exists=True, file_okay=True),
    metavar="<input_file>",
    default="frontend-deps.json",
)
@click.argument(
    "output_dir",
    type=click.Path(exists=True, dir_okay=True, writable=True),
    metavar="<dir>",
    default="vendor/",
)
def cli(input_file, output_dir):
    """Downloads (and checks) external front-end libs from <input_file> to <output_dir>"""

    with open(input_file, encoding="utf-8") as file:
        libs = json.load(file)
        for lib in libs.values():
            url = lib["url"]
            filename = lib["filename"]

            destination = os.path.join(output_dir, filename)
            resource_data = requests.get(url).content

            if len(lib) > 2 and lib["hash"] != "":
                (ache_name, ache_result) = lib["hash"].split("-", maxsplit=1)
                ache = hashlib.new(ache_name)
                ache.update(resource_data)

                integrity_checksum = base64.b64encode(ache.digest()).decode("utf-8")
                if integrity_checksum == ache_result:
                    click.echo(f"{filename} SRI check OK")
                else:
                    raise Exception(f"SRI check failed for {filename}")
            else:
                click.echo(f"Warning: Could not check SRI for {filename}")

            with open(destination, "wb") as file:
                file.write(resource_data)


if __name__ == "__main__":
    cli() # pylint: disable=no-value-for-parameter

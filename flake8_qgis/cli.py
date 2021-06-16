#!/usr/bin/env python

# Third party modules
import click

# First party modules
import flake8_qgis


@click.group()
@click.version_option(version=flake8_qgis.__version__)
def entry_point():
    """Awesomeproject spreads pure awesomeness."""

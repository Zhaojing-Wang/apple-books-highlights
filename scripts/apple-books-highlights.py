#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pathlib
import click

from apple_books_highlights.models import BookList
from apple_books_highlights import booksdb


def get_booklist(path: pathlib.Path, refresh: bool) -> BookList:

    book_list = BookList(path)
    annos = booksdb.fetch_annotations(refresh)
    book_list.populate_annotations(annos)
    return book_list


@click.group()
@click.option('--bookdir', '-b', type=click.Path(), 
              envvar='APPLE_BOOKS_HIGHLIGHT_DIRECTORY', default='./books')
@click.pass_context
def cli(ctx, bookdir):

    # create directory if it doesn't exist
    p = pathlib.Path(bookdir)
    p.mkdir(parents=True, exist_ok=True)

    ctx.obj['BOOKDIR'] = p


@cli.command()
@click.option('--norefresh', '-n', default=False, is_flag=True)
@click.pass_context
def list(ctx, norefresh):

    bookdir = ctx.obj['BOOKDIR']
    bl = get_booklist(bookdir, not norefresh)

    books = [b for b in bl.books.values()]
    books = sorted(books, key=lambda b: b.title)
    for book in books:
        print(book)


@cli.command()
@click.option('--force', '-f', is_flag=True)
@click.option('--norefresh', '-n', default=False, is_flag=True)
@click.pass_context
def sync(ctx, force, norefresh):

    bookdir = ctx.obj['BOOKDIR']
    bl = get_booklist(bookdir, not norefresh)

    bl.write_modified(bookdir, force)


if __name__ == '__main__':
    cli(obj={})

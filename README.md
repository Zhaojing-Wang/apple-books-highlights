> Fork from [jladicos/apple-books-highlights](https://github.com/jladicos/apple-books-highlights) and upgrade by OpenAI Codex.

# Apple Books Highlights & Notes Export

Export your Apple Books highlights and notes to markdown files.  Modified from [fork][] by [matttrent][], who modified from [original][] by [shrsv][].

[fork]: https://github.com/matttrent/ibooks-highlights
[matttrent]: https://github.com/matttrent
[original]: https://github.com/shrsv/ibooks_highlights_export
[shrsv]:    https://github.com/shrsv


## What it does

The scripts first opens Apple Books and closes it after a number of seconds, to force a refresh of the local sqlite database that Apple Books uses to track annotations. This is useful if you're like me and read books on your iPhone or iPad. It then reads this sqlite database and proceeds to generate a markdown file corresponding to each book in the database, and populate it with the associated highlights and notes.

It preserves each book's identifier (and some other data) in the YAML header of the markdown file. You can actually rename the file and the next run of the script will find and update the appropriate file.  Additionally, it creates a **My notes** section for additional free-form notes that it won't overwrite on subsequent updates.

## Usage

Simplest way to get your highlights, though you might want to create a `virtualenv` first:

```
$ python3 setup.py install
$ apple-books-highlights.py sync
$ ll books
```

I've personally used a bash alias like this, so I can call `sync-books` from terminal anywhere on my system to update the annotations:

```
alias sync-books="apple-books-highlights.py --bookdir 'absolute/path/to/folder' sync"
```

## What you get per book

```
---
asset_id: E00F1E187CE35F700419AE8312F79913
author: Yuval Noah Harari
modified_date: '2021-09-04T16:41:44'
title: Sapiens A Brief History of Humankind
---

# Sapiens A Brief History of Humankind

By Yuval Noah Harari

## My Notes <a name="my_notes_dont_delete"></a>



## Book Highlights & Notes <a name="apple_books_notes_dont_delete"></a>

### 2: The Tree of Knowledge

This was the key to Sapiens’ success. In a one-on-one brawl, a Neanderthal would probably have beaten a Sapiens. But in a conflict of hundreds, Neanderthals wouldn’t stand a chance. Neanderthals could share information about the whereabouts of lions, but they probably could not tell – and revise – stories about tribal spirits. Without an ability to compose fiction, Neanderthals were unable to cooperate effectively in large numbers, nor could they adapt their social behaviour to rapidly changing challenges. NOTE: Very interesting example of how composing fiction gave sapiens an evolutionary advantage_
```

## Options

To get a list of books (asterisk means there's unsynced highlights):

```
$ apple-books-highlights.py list

D36605A6   1	Bayesian Methods for Hackers
80EE27E1   27	Dune
E5875B57 * 30	Making of the Atomic Bomb
7029A581   17	Meditations - Modern Library Translation
547526C9   50	Musashi
F6C97901   77	The Idea Factory
```

To set output directory:

```
$ apple-books-highlights.py -b other-books sync
```

Change default output directory via environment variable:

```
export APPLE_BOOKS_HIGHLIGHT_DIRECTORY=some/other/folder
```

Override Apple Books database locations (useful if Apple changes paths):

```
export APPLE_BOOKS_ANNOTATION_DB_DIR=~/Library/Containers/com.apple.iBooksX/Data/Documents/AEAnnotation
export APPLE_BOOKS_BOOK_DB_DIR=~/Library/Containers/com.apple.iBooksX/Data/Documents/BKLibrary
```

To disable the automatic opening (and closing) of Apple Books, which is used to force a refresh of the database of annotations:

```
$ apple-books-highlights.py sync -n
```
or
```
$ apple-books-highlights.py list -n
```

## TODO

- [ ] `¯\_(ツ)_/¯`

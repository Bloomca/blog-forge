# Blog-forge

> This is a prototype, so currently it is pretty challenging to use it by yourself :)

This is a simple static site generator with support for multiple sites at once. I constantly have many ideas to write about, but tags are not good enough for me, so I decided to write something simple to be able to share general styles and layouts, but with an ability to override at site-specific level.

## Stack

The application is written in Python, using [Flask](http://flask.pocoo.org/) for development and [Frozen Flask](https://github.com/Frozen-Flask/Frozen-Flask) for generating site. Articles are supposed to be written in markdown, with meta info in [YAML](https://learn.getgrav.org/advanced/yaml) format, separated by a new line from the main content.

## Licence

MIT

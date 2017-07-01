# encoding=utf8

"""
This application allows you to manage several static page websites in one repo.
It allows you to share templates and static files between them, so it is much
easier to create new blogs/sites with similar content
"""

import sys
from os import listdir
from os.path import isfile, join, isdir
import io
from flask import Flask, render_template, send_from_directory
import jinja2
from markdown import markdown

def get_immediate_subdirectories(a_dir):
    """
    List of all subdirectories inside given directory
    """
    return [name for name in listdir(a_dir)
            if isdir(join(a_dir, name))]

def create_app(site):
    """
    create application function – because we support several sites
    we need to know which one we are using right now
    """
    config = {}
    config['DEBUG'] = True

    print sys.path[0]

    app = Flask(__name__)
    app.config.from_object(config)

    my_loader = jinja2.ChoiceLoader([
        app.jinja_loader,
        jinja2.FileSystemLoader(join('sites', site, 'templates')),
    ])
    app.jinja_loader = my_loader

    @app.route('/assets/<path:filename>')
    def assets(filename):
        """
        We have to combine global and local assets
        """
        folders = [
            'assets',
            join('sites', site, 'assets')
        ]
        for directory in folders:
            try:
                return send_from_directory(directory, filename)
            except Exception:
                pass
        raise Exception

    directory = join('sites', site, 'pages')
    sections = get_immediate_subdirectories(directory)

    print sections

    @app.route('/<path:section_name>/')
    def section(section_name):
        """
        We divide all content into sections with one level deepness
        """
        section_folder = join(directory, section_name)
        files = [f for f in listdir(section_folder) if isfile(join(section_folder, f))]
        filtered_files = [f for f in files if f.endswith('.md')]
        return render_template('topic.html', sections=sections, files=filtered_files)

    @app.route('/')
    def hello_world():
        return '\n\n'.join(sections)

    @app.route('/<path:section>/<path:path>/')
    def page(section, path):
        file_path = join('sites', site, 'pages', section, path + '.md')
        # needed to correctly parse cyrillic
        with io.open(file_path, 'r', encoding='utf-8') as f:
            article = markdown(f.read())
            return render_template('article.html', article=article, sections=sections)

    app.run(port=8000)

if __name__ == '__main__':
    site = sys.argv[1]
    create_app(site)

    # if len(sys.argv) > 1 and sys.argv[1] == "build":
    #     freezer.freeze()
    # app.run(port=8000)

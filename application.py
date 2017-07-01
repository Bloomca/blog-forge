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
import yaml


def get_immediate_subdirectories(a_dir):
    """
    List of all subdirectories inside given directory
    """
    return [name for name in listdir(a_dir)
            if isdir(join(a_dir, name))]

def read_file(file_path):
    """
    read and parse md file
    outputting content and yaml config
    """
    # needed to parse cyrillic correctly
    with io.open(file_path, 'r', encoding='utf-8') as f:
        raw_file = f.read()
        parsed_article = raw_file.split('\n\n', 1)
        article = markdown(parsed_article[1])
        return {'meta': yaml.load(parsed_article[0]), 'text': article}

def create_app(site):
    """
    create application function – because we support several sites
    we need to know which one we are using right now
    """
    config = {}
    config['DEBUG'] = True

    app = Flask(__name__)
    app.config.from_object(config)

    my_loader = jinja2.ChoiceLoader([
        app.jinja_loader,
        jinja2.FileSystemLoader(join('sites', site, 'templates')),
    ])
    app.jinja_loader = my_loader

    @app.template_filter('md')
    def md(text):
        """Parse text as markdown"""
        return markdown(text)


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
    section_dirs = get_immediate_subdirectories(directory)
    sections = []
    for section_dir in section_dirs:
        info = read_file(join(directory, section_dir, '__info.md'))['meta']
        section_info = {'title': info['title'], 'section': section_dir}
        sections.append(section_info)

    # we need to merge meta in each section & page, so we read it here
    file_path = join('sites', site, 'pages', '__info.md')
    index_article = read_file(file_path)
    meta = index_article['meta']

    @app.route('/')
    def index():
        return render_template(
            'article.html',
            article=index_article['text'],
            section_name='',
            sections=sections, meta=meta)
            
    @app.route('/<path:section>/')
    def section(section):
        """
        We divide all content into sections with one level deepness
        """
        section_folder = join(directory, section)
        files = [f for f in listdir(section_folder) if isfile(join(section_folder, f))]
        filtered_files = [f for f in files if f.endswith('.md') and f != '__info.md']
        links = []
        for f in filtered_files:
            page_meta = read_file(join(section_folder, f))['meta']
            page_meta['url'] = f.rsplit('.', 1)[0]
            links.append(page_meta)
        
        section_file = read_file(join(section_folder, '__info.md'))
        return render_template(
            'topic.html',
            section_name=section,
            section=section_file['meta'],
            links=links,
            sections=sections, files=filtered_files, meta=meta)

    @app.route('/<path:section>/<path:path>/')
    def page(section, path):
        file_path = join('sites', site, 'pages', section, path + '.md')
        article = read_file(file_path)
        page_meta = meta.copy()
        page_meta.update(article['meta'])
        return render_template(
            'article.html',
            article=article['text'],
            section_name=section,
            sections=sections, meta=page_meta)

    app.run(port=8000)

if __name__ == '__main__':
    site = sys.argv[1]
    create_app(site)

    # if len(sys.argv) > 1 and sys.argv[1] == "build":
    #     freezer.freeze()
    # app.run(port=8000)

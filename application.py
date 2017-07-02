# encoding=utf8

"""
This application allows you to manage several static page websites in one repo.
It allows you to share templates and static files between them, so it is much
easier to create new blogs/sites with similar content
"""

import sys
from datetime import datetime
from os import listdir, walk
from os.path import isfile, join, isdir
import io
from flask import Flask, render_template, send_from_directory
from flask_frozen import Freezer
from werkzeug.contrib.atom import AtomFeed
import jinja2
from markdown import markdown
import yaml

def get_immediate_subdirectories(a_dir):
    """
    List of all subdirectories inside given directory
    """
    return [name for name in listdir(a_dir)
            if isdir(join(a_dir, name))]

def get_content_files(section_folder, section):
    """
    Get all content files from directory, excluding __info.md
    """
    files = [f for f in listdir(section_folder) if isfile(join(section_folder, f))]
    filtered_files = [f for f in files if f.endswith('.md') and f != '__info.md']
    files = []
    for f in filtered_files:
        file_content = read_file(join(section_folder, f))
        file_content['meta']['url'] = f.rsplit('.', 1)[0]
        file_content['meta']['section'] = section
        file_content['meta']['full_url'] = section + '/' + file_content['meta']['url']
        files.append(file_content)

    return sorted(files, key=lambda file: file['meta']['date'], reverse=True)

def read_file(file_path):
    """
    read and parse md file
    outputting content and yaml config
    """
    # needed to parse cyrillic correctly
    with io.open(file_path, 'r', encoding='utf-8') as f:
        raw_file = f.read()
        parsed_article = raw_file.split('\n\n', 1)
        article = markdown(parsed_article[1], extensions=['codehilite'])
        return {'meta': yaml.load(parsed_article[0]), 'text': article}

def create_app(site, IS_PRODUCTION):
    """
    create application function – because we support several sites
    we need to know which one we are using right now
    """
    config = {}
    config['DEBUG'] = True

    app = Flask(__name__)
    app.config.from_object(config)

    my_loader = jinja2.ChoiceLoader([
        jinja2.FileSystemLoader(join('sites', site, 'templates')),
        app.jinja_loader,
    ])
    app.jinja_loader = my_loader

    @app.template_filter('md')
    def md(text):
        if text is None:
            text = ''
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
    meta['production'] = IS_PRODUCTION

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
        files = get_content_files(section_folder, section)
        links = [f['meta'] for f in files]
        section_file = read_file(join(section_folder, '__info.md'))
        return render_template(
            'topic.html',
            section_name=section,
            section=section_file['meta'],
            links=links,
            sections=sections, meta=meta)

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

    @app.route('/feed.atom')
    def feed():
        feed = AtomFeed('Recent Articles',
                        feed_url=meta['base_url'] + 'feed.atom',
                        url=meta['base_url'],
                        subtitle='Recent articles')

        posts = []
        for section_dir in section_dirs:
            section_folder = join(directory, section_dir)
            files = get_content_files(section_folder, section_dir)
            posts = posts + files

        sorted_ports = sorted(posts, key=lambda file: file['meta']['date'], reverse=True)

        for post in sorted_ports:
            publish_date = post['meta']['date']
            day = publish_date.today()
            today_with_time = datetime(
                year=day.year,
                month=day.month,
                day=day.day,
            )

            feed.add(post['meta']['title'], post['text'],
                     content_type='html',
                     author=meta['author'],
                     url=meta['base_url'] + post['meta']['full_url'],
                     id=post['meta']['title'],
                     updated=today_with_time,
                     published=today_with_time)

        return feed.get_response()

    return app

if __name__ == '__main__':
    SITE = sys.argv[1]
    IS_PRODUCTION = len(sys.argv) > 2 and sys.argv[2] == 'build'
    APP = create_app(SITE, IS_PRODUCTION)

    if IS_PRODUCTION:
        FREEZER = Freezer(APP)
        FREEZER.freeze()
    else:
        extra_dirs = [join('sites', SITE, 'pages')]
        extra_files = extra_dirs[:]
        for extra_dir in extra_dirs:
            for dirname, dirs, files in walk(extra_dir):
                for filename in files:
                    filename = join(dirname, filename)
                    if isfile(filename):
                        extra_files.append(filename)
        APP.run(port=8000, debug=True, extra_files=extra_files)

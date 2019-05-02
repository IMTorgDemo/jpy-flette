#!/usr/bin/env python3

import os, sys, glob
import shutil
import click
from jinja2 import Template
from pyquery import PyQuery
import yaml
import pandas as pd

import nbformat
from nbconvert import HTMLExporter
from nbconvert.filters.markdown_mistune import IPythonRenderer, MarkdownWithMath, mistune
from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.formatters import HtmlFormatter
from pygments.util import ClassNotFound

def resource(*args):
    return os.path.join(os.path.dirname(os.path.realpath(__file__)), *args)

# add `data-lang` attribute to pygments-generated html
class FletteIPythonRenderer(IPythonRenderer):
    def block_code(self, code, lang):
        if lang:
            try:
                lexer = get_lexer_by_name(lang, stripall=True)
            except ClassNotFound:
                code = lang + '\n' + code
                lang = None

        if not lang:
            return '\n<pre><code>{}</code></pre>\n'.format(mistune.escape(code))

        formatter = HtmlFormatter()

        # fix
        prettylang_map = {"idl": "IDL", "text": ""}
        prettylang = prettylang_map.get(lang, lang)
        hl = highlight(code, lexer, formatter)
        hl = hl.replace('"><pre>', ' highlight-with-lang" data-lang="{}"><pre>'
                        ''.format(prettylang))
        return hl

class FletteHTMLExporter(HTMLExporter):
    def markdown2html(self, source):
        renderer = FletteIPythonRenderer(escape=False,
                                         anchor_link_text=self.anchor_link_text)
        return MarkdownWithMath(renderer=renderer).render(source)

@click.command()
@click.argument("configfile", default="")
def cli(configfile):
    # default config
    with open(resource("fletteconf-default.yaml")) as f:
        config = yaml.load(f, Loader=yaml.FullLoader)

    # load config file
    configfile = os.path.abspath(configfile)
    if os.path.isdir(configfile):
        configfile = os.path.join(configfile, "fletteconf.yaml")

    try:
        with open(configfile) as f:
            config.update(yaml.load(f, Loader=yaml.FullLoader))
    except:
        pass

    # load template from theme
    themedir = resource("theme-"+config["theme"])
    if not os.path.isdir(themedir):
        themedir = config["theme"] # absolute theme directory

    with open(os.path.join(themedir, "template.html.j2")) as tf:
        tmpl = Template(tf.read())

    # setup html exporter
    html_exporter = FletteHTMLExporter()
    html_exporter.template_file = "basic"

    # directories
    nbdir = os.path.join(os.path.dirname(configfile), config["source"])
    wwwdir = os.path.join(os.path.dirname(configfile), config["target"])
    metafile = os.path.join(os.path.dirname(configfile), config["metadata"])

    # parse notebooks
    notebook_files = sorted(glob.glob(os.path.join(nbdir, "*.ipynb")))
    if len(notebook_files) == 0:
        print("\033[31merror\033[0m no notebooks found in {}".format(nbdir))
        sys.exit(1)
    
    # parse metadata
    if config["metadata"] != '':
        try:
            meta = pd.read_csv(metafile)
        except:
            print("\033[31merror\033[0m no .csv file found in {}".format(metafile))

        meta.sort_values(by="index", inplace=True)
        #str( meta.index[meta.notebook == rel_fn][0] )
        filenames = [ os.path.splitext(os.path.relpath(nb_fn, nbdir))[0] for nb_fn in notebook_files ]
        if len(notebook_files) != meta.shape[0]:
            print("\033[31merror\033[0m notebooks do not match metafile")       #TODO: show which ones are missing
            sys.exit(1)
        notebooks = [ os.path.join(nbdir, nb_fn+".ipynb") for nb_fn in meta.notebook]

    data = []
    with click.progressbar(notebooks, label="process notebooks") as bar:
        for nb_fn in bar:
            #nb_fn: '/Users/jason.beach/Desktop/Projects/jpy-flette/docs/notebooks/00.index.ipynb'
            rel_fn = os.path.splitext(os.path.relpath(nb_fn, nbdir))[0]     
            #rel_fn: '00.index'

            # read notebook
            nb = nbformat.read(nb_fn, as_version=4)
            nb.metadata["language_info"]["pygments_lexer"] = "ipython"
            body, _ = html_exporter.from_notebook_node(nb)

            # toc
            toc = []
            titles = PyQuery(body).remove("a.anchor-link")("h1,h2,h3,h4,h5,h6")
            for h in titles.items():
                li = PyQuery("<li class='nav-item'><a>{}</a></li>")
                li("a").html(h.html())
                li("a").attr("href", "#"+h.attr("id"))
                li.addClass("indent-{}".format(h.outer_html()[2]))
                toc.append(li)

            # fix: html_exporter self-closes empty html tags (<i/> -> <i></i>)
            body = PyQuery(body).outer_html(method="html")

            # template variables
            if 'meta' in locals():
                htmlfile = rel_fn+".html"
                htmlfile_indx = str( meta.index[meta.notebook == rel_fn][0] )  # if metadata file exists use kv (notebook_name, numeric_prefix)
            else:
                htmlfile = rel_fn.split(".", 1)[1]+".html"  # remove numeric prefix
            print(htmlfile)
            data.append(dict(htmlfile=htmlfile, body=body,
                             title=toc[0]("a").html(method="html"),
                             toc=[t.outer_html(method="html") for t in toc]))

    if config["title_sidebar"] == True:
        config["title_sidebar"] = data[0]["title"]

    # render
    for i,d in enumerate(data):
        htmlfile_full = os.path.join(wwwdir, d["htmlfile"])
        os.makedirs(os.path.dirname(htmlfile_full), exist_ok=True)
        with open(htmlfile_full, "w") as f:
            c = tmpl.render(toc_pre=[data[j] for j in range(len(data)) if j<i],
                            toc_post=[data[j] for j in range(len(data)) if j>i],
                            **config, **d)
            f.write(c)

    # copy theme files
    with open(os.path.join(themedir, "jpy-flette-theme.yaml")) as f:
        theme_files = yaml.load(f, Loader=yaml.FullLoader)

    with click.progressbar(theme_files, label="copy theme files ") as bar:
        for f in bar:
            try:  # e.g. "- node_modules/jquery.js: static/jquery.js"
                srcf, trgf = list(f.items())[0]
            except:  # e.g. "- static/fonts/graviola/stylesheet.css"
                srcf = trgf = f

            if os.path.isfile(os.path.join(themedir, srcf)):
                os.makedirs(os.path.dirname(os.path.join(wwwdir, trgf)),
                            exist_ok=True)
                shutil.copy(os.path.join(themedir, srcf),
                            os.path.join(wwwdir, trgf))
            else:
                print("\n\033[31merror\033[0m {} is not a file".format(srcf))

if __name__ == '__main__':
    cli()
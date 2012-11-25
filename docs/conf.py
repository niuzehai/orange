# -*- coding: utf-8 -*-
#
# reference documentation build configuration file, created by
# sphinx-quickstart on Wed Nov 17 12:52:23 2010.
#
# This file is execfile()d with the current directory set to its containing dir.
#
# Note that not all possible configuration values are present in this
# autogenerated file.
#
# All configuration values have a default; values that are commented out
# serve to show the default.

import imp, inspect, sys, os

class Mock(object):
    __all__ = []

    def __init__(self, *args, **kwargs):
        pass

    def __call__(self, *args, **kwargs):
        return Mock()

    @classmethod
    def __getattr__(cls, name):
        if name in ('__file__', '__path__'):
            return '/dev/null'
        elif name[0] == name[0].upper():
            mockType = type(name, (), {})
            mockType.__module__ = __name__
            return mockType
        else:
            return Mock()

MOCK_MODULES = ['orange', 'orangeom', 'Orange.core.ExampleTable', 'Orange.core.Example',
                'Orange.core.Value', 'Orange.core.StringValue,', 'Orange.core.Domain', 'scipy',
                'scipy.stats', 'scipy.sparse', 'scipy.optimize', 'scipy.linalg']

for mod_name in MOCK_MODULES:
    sys.modules[mod_name] = Mock()

#rewrite formatargs function with different defaults
PATH = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))

sys.path.insert(0, PATH)
import myinspect
import sphinx.ext.autodoc
import numpydoc
sphinx.ext.autodoc.inspect = myinspect
numpydoc.docscrape.inspect = myinspect

module_setup = imp.load_source('module_setup', os.path.join(PATH, '..', 'setup.py'))
VERSION = module_setup.VERSION
AUTHOR = module_setup.AUTHOR
NAME = module_setup.NAME

TITLE = "%s Documentation v%s" % (NAME, VERSION)

#disable deprecation decorators for the documentation
os.environ["orange_no_deprecated_members"] = "1"

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
sys.path.append(os.path.abspath(os.path.join(PATH, "..")))
import Orange

# -- General configuration -----------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be extensions
# coming with Sphinx (named 'sphinx.ext.*') or your custom ones.
extensions = ['sphinx.ext.autodoc', 'sphinx.ext.doctest', 'sphinx.ext.intersphinx', 'sphinx.ext.todo', 'sphinx.ext.coverage', 'sphinx.ext.pngmath', 'sphinx.ext.ifconfig', 'numpydoc']


# Numpydoc generates autosummary directives for all undocumented members. Orange documentation only includes documented
# member, so _str_member_list is modified to return [] where a list of undocumented members is originally returned.
numpydoc.docscrape_sphinx.SphinxDocString._str_member_list # if numpydoc changes, this line will cause an error
numpydoc.docscrape_sphinx.SphinxDocString._str_member_list = lambda x, y : []


# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# The suffix of source filenames.
source_suffix = '.rst'

# The encoding of source files.
#source_encoding = 'utf-8'

# The master toctree document.
master_doc = 'index'

# General information about the project.
project = TITLE
copyright = AUTHOR

# The version info for the project you're documenting, acts as replacement for
# |version| and |release|, also used in various other places throughout the
# built documents.
#
# The short X.Y version.
version = VERSION
# The full version, including alpha/beta/rc tags.
release = VERSION

# The language for content autogenerated by Sphinx. Refer to documentation
# for a list of supported languages.
#language = None

# There are two options for replacing |today|: either, you set today to some
# non-false value, then it is used:
#today = ''
# Else, today_fmt is used as the format for a strftime call.
#today_fmt = '%B %d, %Y'

# List of documents that shouldn't be included in the build.
#unused_docs = []

# List of directories, relative to source directory, that shouldn't be searched
# for source files.
exclude_trees = ['build', 'sphinx-ext']

# The reST default role (used for this markup: `text`) to use for all documents.
#default_role = None

# If true, '()' will be appended to :func: etc. cross-reference text.
#add_function_parentheses = True

# If true, the current module name will be prepended to all description
# unit titles (such as .. function::).
#add_module_names = True

# If true, sectionauthor and moduleauthor directives will be shown in the
# output. They are ignored by default.
#show_authors = False

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = 'sphinx'

# A list of ignored prefixes for module index sorting.
#modindex_common_prefix = []


# -- Options for HTML output ---------------------------------------------------

# The theme to use for HTML and HTML Help pages.  Major themes that come with
# Sphinx are currently 'default' and 'sphinxdoc'.
html_theme = 'orange_theme'

# Theme options are theme-specific and customize the look and feel of a theme
# further.  For a list of options available for each theme, see the
# documentation.
html_theme_options = {"collapsiblesidebar": "false"}

if html_theme == "orange_theme":
    html_theme_options.update({"orangeheaderfooter": "false"})

# Add any paths that contain custom themes here, relative to this directory.
html_theme_path = [os.path.join(PATH, "sphinx-ext", "themes")]

# The name for this set of Sphinx documents.  If None, it defaults to
# "<project> v<release> documentation".
html_title = TITLE

# A shorter title for the navigation bar.  Default is the same as html_title.
#html_short_title = None

# The name of an image file (relative to this directory) to place at the top
# of the sidebar.
#html_logo = None

# The name of an image file (within the static path) to use as favicon of the
# docs.  This file should be a Windows icon file (.ico) being 16x16 or 32x32
# pixels large.
#html_favicon = None

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = []

# If not '', a 'Last updated on:' timestamp is inserted at every page bottom,
# using the given strftime format.
#html_last_updated_fmt = '%b %d, %Y'

# If true, SmartyPants will be used to convert quotes and dashes to
# typographically correct entities.
#html_use_smartypants = True

# Custom sidebar templates, maps document names to template names.
#html_sidebars = {}

# Additional templates that should be rendered to pages, maps page names to
# template names.
#html_additional_pages = {}

# If false, no module index is generated.
#html_use_modindex = True

# If false, no index is generated.
#html_use_index = True

# If true, the index is split into individual pages for each letter.
#html_split_index = False

# If true, links to the reST sources are added to the pages.
#html_show_sourcelink = True

# If true, an OpenSearch description file will be output, and all pages will
# contain a <link> tag referring to it.  The value of this option must be the
# base URL from which the finished HTML is served.
#html_use_opensearch = ''

# If nonempty, this is the file name suffix for HTML files (e.g. ".xhtml").
#html_file_suffix = ''

# Output file base name for HTML help builder.
htmlhelp_basename = 'referencedoc'


# -- Options for LaTeX output --------------------------------------------------

# The paper size ('letter' or 'a4').
#latex_paper_size = 'letter'

# The font size ('10pt', '11pt' or '12pt').
#latex_font_size = '10pt'

# Grouping the document tree into LaTeX files. List of tuples
# (source start file, target name, title, author, documentclass [howto/manual]).
latex_documents = [
  ('index', 'reference.tex', TITLE,
   AUTHOR, 'manual'),
]

# The name of an image file (relative to this directory) to place at the top of
# the title page.
#latex_logo = None

# For "manual" documents, if this is true, then toplevel headings are parts,
# not chapters.
#latex_use_parts = False

# Additional stuff for the LaTeX preamble.
#latex_preamble = ''

# Documents to append as an appendix to all manuals.
#latex_appendices = []

# If false, no module index is generated.
#latex_use_modindex = True

# -- Options for Epub output ---------------------------------------------------

# Bibliographic Dublin Core info.
epub_title = TITLE
epub_author = AUTHOR
epub_publisher = AUTHOR
epub_copyright = AUTHOR

# The language of the text. It defaults to the language option
# or en if the language is not set.
epub_language = 'en'

# The scheme of the identifier. Typical schemes are ISBN or URL.
#epub_scheme = ''

# The unique identifier of the text. This can be a ISBN number
# or the project homepage.
#epub_identifier = ''

# A unique identification for the text.
#epub_uid = ''

# HTML files that should be inserted before the pages created by sphinx.
# The format is a list of tuples containing the path and title.
#epub_pre_files = []

# HTML files that should be inserted after the pages created by sphinx.
# The format is a list of tuples containing the path and title.
#epub_post_files = []

# A list of files that should not be packed into the epub file.
epub_exclude_files = ["index.html", "genindex.html", "py-modindex.html", "search.html"]

# The depth of the table of contents in toc.ncx.
#epub_tocdepth = 3

# Allow duplicate toc entries.
#epub_tocdup = True

# Example configuration for intersphinx: refer to the Python standard library.
intersphinx_mapping = {'http://docs.python.org/': None}

import types
from sphinx.ext import autodoc

def maybe_skip_member(app, what, name, obj, skip, options):
    #print app, what, name, obj, skip, options

    #allow class methods that begin with __ and end with __
    if isinstance(obj, types.MethodType) \
        and not isinstance(options.members, list) \
        and name.startswith("__") \
        and name.endswith("__") \
        and (obj.__doc__ != None or options.get("undoc-members", False)):
            return False

class SingletonDocumenter(autodoc.ModuleLevelDocumenter):
    """
    Specialized Documenter subclass for singleton items.
    """
    objtype = 'singleton'
    directivetype = 'data'

    member_order = 40

    @classmethod
    def can_document_member(cls, member, membername, isattr, parent):
        return isinstance(parent, autodoc.ModuleDocumenter) and isattr

    def document_members(self, all_members=False):
        pass

    def add_content(self, more_content, no_docstring=False):
        self.add_line(u'Singleton instance of :py:class:`~%s`.' % (self.object.__class__.__name__,), '<autodoc>')

def setup(app):
    app.connect('autodoc-skip-member', maybe_skip_member)
    app.add_autodocumenter(SingletonDocumenter)

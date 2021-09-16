# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import os
import sys
sys.path.insert(0, os.path.abspath('..'))

# -- Project information -----------------------------------------------------

project = 'DKUtils'
copyright = '2020, DataKitchen'
author = 'DataKitchen'

# The full version, including alpha/beta/rc tags
release = u'1.11.0'

# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    'sphinx.ext.napoleon',
    'sphinx.ext.autosectionlabel',
    'sphinx.ext.autosummary',
    'sphinx.ext.autodoc',
    'sphinx.ext.coverage',
    'sphinx.ext.mathjax',
    'sphinx.ext.ifconfig',
    'sphinx.ext.inheritance_diagram',
    'sphinx.ext.viewcode',
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = 'sphinx_rtd_theme'

html_theme_options = {
    # RTD Global options
    'display_version': True,
    'prev_next_buttons_location': 'both',

    # RTD Toc options
    'collapse_navigation': False,
    'sticky_navigation': True,
    'navigation_depth': 3,
    'includehidden': False,
}

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
# html_static_path = ['_static']

# -- Options for autodoc extension -------------------------------------------

# group special methods & non special methods, rather than alphabetical
autodoc_member_order = 'groupwise'

# pull signatures for C functions as needed
autodoc_docstring_signature = True

# for classes, show docstrings for class and class.__init__()
autoclass_content = 'both'

autodoc_default_flags = [
    'show-inheritance',
    'undoc-members',
    'special-members',
    # 'private-members',
    # 'inherited-members',
]

# Never document these methods/attributes
autodoc_exclude_always = {
    '__class__',
    '__delattr__',
    '__dict__',
    '__format__',
    '__hash__',
    '__module__',
    '__new__',
    '__reduce__',
    '__reduce_ex__',
    '__sizeof__',
    '__slots__',
    '__subclasshook__',
    '__weakref__',
}

# Document these only if their docstrings don't match those of their base classes
autodoc_exclude_if_no_redoc_base_classes = [object, type]
autodoc_exclude_if_no_redoc = {
    '__init__',
    '__getattribute__',
    '__setattribute__',
    '__getattr__',
    '__setattr__',
    '__getitem__',
    '__setitem__',
    '__str__',
    '__repr__',
    '__iter__',
    'next',
    '__next__',
    'close',
    '__del__',
}


def autodoc_skip_member(app, what, name, obj, skip, options):
    """
  Do not generate documentation for functions/methods/classes/objects that
  either:

    1. Appear above in ``autodoc_exclude_always``
    2. Start with ``Abstract`` or have ``.Abstract`` in the name
    3. Have an attribute called ``_skipdoc`` set to *True*
    4. Have the same docstring as the method with the same name defined in
       a base class that appears in ``autodoc_exclude_if_no_redoc_base_classes``

  Parameters
  ----------
  app
    Sphinx application
  what : str
    Type of object (e.g. ``module``, ``function``, ``class``)
  name : str
    Name of object within module scope
  obj : object
    Object to skip or not
  skip : bool
    Whether or not Sphinx would skip this, given pre-set options
  options : object
    Options given to the directive, whose boolean properties are set to True
    if their corresponding flag was given in the directive

  Returns
  -------
  bool
    True if object should be skipped, False otherwise
  """

    if not skip:
        if name in autodoc_exclude_always:
            skip = True
        elif name.startswith('Abstract') or '.Abstract' in name:
            skip = True
        elif getattr(obj, '_skipdoc', False):
            skip = True
        elif name in autodoc_exclude_if_no_redoc:
            for cls in autodoc_exclude_if_no_redoc_base_classes:
                if isinstance(obj, cls):
                    base_doc = getattr(getattr(cls, name, None), '__doc__', '')
                    obj_doc = getattr(obj, '__doc__', '')
                    skip |= (obj_doc == base_doc)

    return skip


def setup(app):
    """Implement custom autodoc skipping and css"""
    app.connect('autodoc-skip-member', autodoc_skip_member)
    app.add_css_file('css/custom.css')


# -- Options for napoleon extension ------------------------------------------

napoleon_google_docstring = False
napoleon_numpy_docstring = True
napoleon_include_init_with_doc = True
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = True
napoleon_use_admonition_for_examples = False
napoleon_use_admonition_for_notes = False
napoleon_use_admonition_for_references = False
napoleon_use_ivar = True
napoleon_use_param = True
napoleon_use_rtype = True

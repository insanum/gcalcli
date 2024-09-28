try:
    from ._version import __version__ as __version__
except ImportError:
    import warnings
    warnings.warn('Failed to load __version__ from setuptools-scm')
    __version__ = '__unknown__'

__program__ = 'gcalcli'

#-*- coding: utf-8 -*-

#BASED ON
# https://stackoverflow.com/questions/39499453/package-only-binary-compiled-so-files-of-a-python-library-compiled-with-cython/56043918#56043918

#For Onlybuilding some. 
import fnmatch
from setuptools.command.build_py import build_py as build_py_orig


import os
from os.path import join

from setuptools import setup, find_packages
from setuptools.extension import Extension

extensions = []
name = 'zopache'
version = '0.1'
readme = open('README.md').read()
history = open(join('docs', 'HISTORY.txt')).read()

class build_py(build_py_orig):
    def build_packages(self):
        pass

install_requires = [
    'biscuits',
    'crom',
    'cromlech.auth',
    'cromlech.browser',
    'cromlech.content',
    'cromlech.file',
    'cromlech.i18n',
    'cromlech.configuration',
    'cromlech.dawnlight',
    'cromlech.grok',
    'cromlech.i18n',
    'cromlech.security',
    'cromlech.location',
    'cromlech.webob',
    'cromlech.zodb',
    'dolmen.container',
    'dolmen.forms.base',
    'dolmen.forms.ztk',
    'dolmen.message',
    'dolmen.tales',
    'dolmen.template',
    'dolmen.view',
    'dolmen.viewlet',
    'dolmen.widget.file',
    'googlemaps',
    'unicode-slugify',
    'pyramid_mailer',
    'setuptools',
    'zopache',
    'zopache.copy',
    'zope.interface',
    'zope.location',
    'zope.schema',
    'arrow',
    'beautifulsoup4',    
    'jsmin',
    'DateTime',
    'dolmen.forms.base >= 2.0',
    'fanstatic',
    'pillow',
    'repoze.sendmail',
    'setuptools',
    'zope.cachedescriptors',
    'z3c.schema',
    'zope.event',
    'zope.interface',
    'zope.lifecycleevent',
    'zope.password',    
    'zope.schema',
    'restrictedpython',    
    ]

tests_require = [
    'cromlech.browser [test]',
    'dolmen.forms.ztk >= 2.0',
    ]

setup(
      name=name,
      cmdclass={
            'build_py' : build_py,
        },

      version=version,
      description="Zopache the core of the JSON Wikie",
      long_description=u"%s\n\n%s" % (readme, history),
      keywords='JSON NEWS WIKI',
      author='The Cromlech/Dolmen Team + Chrisotpher Lozinski',
      author_email='lozinski@PythonLinks.info',
      url='http://www.pythonlinks.info/json-wiki',
      license='Commercial', 
      packages=find_packages('src', exclude=['ez_setup']),
      package_dir={'': 'src'},
      namespace_packages=['zopache'],
      include_package_data=True,
      package_data={
        "zopache": ["*.zcml",
             "*.pt",
             "*.png",
             "*.js",                    
             "*.svg"]
      } ,       
      zip_safe=False,
      tests_require=tests_require,
      install_requires=install_requires,
      extras_require={'test': tests_require},
      test_suite="zopache.crud",
      classifiers=[
          'Environment :: Web Environment',
          'Operating System :: OS Independent',
          'Programming Language :: Python',
          ],
       entry_points={
           'paste.app_factory': [
                'demo = zopache.application.wsgi:demo_application',
                ],
           'fanstatic.libraries': [
                'ttwicons = zopache.ttw:library',
                'zmiicons = zopache.zmi:library',
                ],
        },
              
      )

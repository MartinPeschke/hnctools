from setuptools import setup, find_packages
import sys, os

version = '0.0.4'

setup(name='hnc',
      version=version,
      description="",
      long_description="""\
""",
      classifiers=[], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
      keywords='',
      author='Martin Peschke',
      author_email='martin@hackandcraft.com',
      url='',
      license='',
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
      include_package_data=True,
      zip_safe=True,
      install_requires=[
          # -*- Extra requirements: -*-
        "babel", "pyramid", "simplejson", "httplib2"
      ],
      entry_points="""
      # -*- Entry points: -*-
      """,
      )

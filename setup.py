#!/usr/bin/env python
# -*- coding: latin1 -*-

def main():
    from setuptools import setup
    import glob
    import os
    import os.path

    setup(name="whatup",
          version="0.90",
          description="An automatic time tracker",
          long_description="""
          Automatically tracks time, inspired by 
          `arbtt <http://darcs.nomeata.de/arbtt/doc/users_guide/>`_.
          """,
          author=u"Andreas Kloeckner",
          author_email="inform@tiker.net",
          license = "GPL",
          classifiers=[
              'Development Status :: 4 - Beta',
              'Environment :: Console',
              'Intended Audience :: End Users/Desktop',
              'Operating System :: POSIX',
              'Programming Language :: Python',
              'Topic :: Office/Business',
              'Topic :: Utilities',
              ],
          zip_safe=False,

          install_requires=[
              "SqlAlchemy>=0.5.1",
              "netifaces",
              ],

          scripts=["bin/whatup"],
          packages=["whatup"],
         )

if __name__ == "__main__":
    import distribute_setup
    distribute_setup.use_setuptools()

    main()

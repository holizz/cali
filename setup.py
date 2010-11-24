import distutils.core

distutils.core.setup(
        name = 'cali',
        version = open('VERSION').read().strip(),
        description = 'Interactive cal(1) (but the name ical was taken)',
        author = 'Tom Adams',
        author_email = 'tom@holizz.com',
        url = 'http://github.com/holizz/cali',
        license = 'ISC',

        classifiers = [
            'Environment :: Console :: Curses',
            'Intended Audience :: End Users/Desktop',
            'License :: OSI Approved :: ISC License (ISCL)',
            'Programming Language :: Python',
            'Topic :: Office/Business :: News/Diary'
            ],

        scripts = ['bin/cali']
        )

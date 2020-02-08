"""
A collection of recurring, platform-wide data reports
"""
import os


VERSION = '1.0.0'
README = open(os.path.join(os.path.dirname(__file__), 'README.rst')).read()
CHANGELOG = open(os.path.join(os.path.dirname(__file__), 'CHANGELOG.rst')).read()


setup(
    name='openedx-recurring-reports',
    version=VERSION,
    description=__doc__,
    long_description=README + '\n\n' + CHANGELOG,
    author='Stanford-Online',
    # author_email='oscm@edx.org',
    # url='https://github.com/edx/completion',
    packages=[
        'recurring_reports',
    ],
    entry_points={
        'lms.djangoapp': [
            'recurring_reports = recurring_reports.apps:CompletionAppConfig',
        ],
    },
    include_package_data=True,
    install_requires=load_requirements('requirements/base.in'),
    tests_require=load_requirements('requirements/test.in'),
    license="AGPL 3.0",
    zip_safe=False,
    keywords='Django edx',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU Affero General Public License v3 or later (AGPLv3+)',
        'Natural Language :: English',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
    ],
)

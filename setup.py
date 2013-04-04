import os
from setuptools import setup


def parse_requirments(fn, dependency_links):
    requirements = []

    if not os.path.exists(fn):
        return requirements, dependency_links

    with open(fn, 'rb') as f:
        for dep in f:
            dep = dep.strip()
            # need to make github requirements work with
            # setuptools like it would work with `pip -r`
            # URLs will not work, so we transform them to
            # dependency_links and requirements
            if dep.startswith('git'):
                dependency_links.append(dep)
                _, dep = dep.rsplit('#egg=', 1)
                dep = dep.replace('-', '==', 1)
            requirements.append(dep)

    return requirements, dependency_links


requirements, dependency_links = parse_requirments('requirements.txt', [])
test_requirements, dependency_links = parse_requirments(
    'test_requirements.txt', dependency_links)


setup(
    name='gonzo',
    packages=['gonzo', ],
    version='0.1',
    author='onefinestay',
    author_email='engineering@onefinestay.com',
    url='https://github.com/onefinestay/gonzo',
    install_requires=requirements,
    tests_require=test_requirements,
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Programming Language :: Python",
        "Intended Audience :: Developers",
        "Natural Language :: English",
        "Topic :: Software Development",
        "Topic :: Utilities",
        "Environment :: Console",
    ],
    description='A release and deployment environment management utility.',
    long_description=open('README.md').read(),
    include_package_data=True,
    entry_points={
        'console_scripts': [
            'gonzo = gonzo.scripts.base:main'
        ]
    },
)

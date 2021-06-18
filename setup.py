from setuptools import setup

def readme():
    """ Readme function """

    with open('README.md') as f:
        return f.read()

with open("requirements.txt", "r") as fh:
    requirements = fh.readlines()


setup(name='yamlwidgets',
      version='0.1',
      description='IPython widgets for a YAML file',
      long_description=readme(),
      classifiers=[
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.0',
        'Topic :: Scientific/Engineering',
      ],
      keywords='yaml, iPython',
      url='https://github.com/jsemer/yamlwidgets',
      author='Joel S. Emer',
      author_email='jsemer@mit.edu',
      license='MIT',
      packages=['yamlwidgets'],
      install_requires=[req for req in requirements if req[:2] != "# "],
      include_package_data=False,
      zip_safe=False)

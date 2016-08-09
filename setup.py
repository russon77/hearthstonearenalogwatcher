from setuptools import setup


def readme():
    with open('README.rst') as f:
        return f.read()


setup(name='hearthstonearenalogwatcher',
      version='0.1',
      description='provide an interface for getting hearthstone arena events: '
                  'entering, exiting, hero selected, card drafted',
      long_description=readme(),
      url='https://www.github.com/russon77/hearthstonearenalogwatcher',
      author='Tristan Kernan',
      author_email='russon77@gmail.com',
      keywords='hearthstone',
      license='MIT',
      packages=['hearthstonearenalogwatcher'],
      zip_safe=False,
      include_package_data=True,
      install_requires=[])

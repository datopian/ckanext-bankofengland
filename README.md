[![Tests](https://github.com/Datopian/ckanext-bankofengland/workflows/Tests/badge.svg?branch=main)](https://github.com/Datopian/ckanext-bankofengland/actions)

# ckanext-bankofengland

This extension is home to the customizations of the admin CKAN portal for the Bank of England.


## Requirements

Compatibility with core CKAN versions:

| CKAN version    | Compatible?   |
| --------------- | ------------- |
| 2.6 and earlier | not tested    |
| 2.7             | not tested    |
| 2.8             | not tested    |
| 2.9             | yes    |


## Installation

To install ckanext-bankofengland:

1. Activate your CKAN virtual environment, for example:

     . /usr/lib/ckan/default/bin/activate

2. Clone the source and install it on the virtualenv

    git clone https://github.com/Datopian/ckanext-bankofengland.git
    cd ckanext-bankofengland
    pip install -e .

3. Add `bankofengland` to the `ckan.plugins` setting in your CKAN
   config file (by default the config file is located at
   `/etc/ckan/default/ckan.ini`).

4. Restart CKAN. For example if you've deployed CKAN with Apache on Ubuntu:

     sudo service apache2 reload


## Developer installation

To install ckanext-bankofengland for development, activate your CKAN virtualenv and
do:

    git clone https://github.com/Datopian/ckanext-bankofengland.git
    cd ckanext-bankofengland
    python setup.py develop


## License

[AGPL](https://www.gnu.org/licenses/agpl-3.0.en.html)

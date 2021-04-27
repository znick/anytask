EasyCI
=======


local install
-------------

Development installation commands:

    # ... clone ...
    # ... cd ...
    git submodule init
    git submodule update
    virtualenv venv
    . venv/bin/activate
    pip install 'pip==20.3.4' 'setuptools==44.0.0' --upgrade
    pip install -r requirements_local.txt
    cd flask
    ./easyCI.py

testing
------------

To run tests:

    cd flask
    python -m pytest -v
    
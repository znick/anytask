Anytask [![Build Status](https://github.com/znick/anytask/actions/workflows/anytask.yml/badge.svg)](https://github.com/znick/anytask/actions)
=======

Used Python3.8

local install
-------------

Development installation commands:

    # ... clone ...
    # ... cd ...
    . deploy_local_beta/run.sh
    ./anytask/manage.py runserver 127.0.0.1:8019 -v 3 --traceback

To activate environment in already deployed project run
    
    . deploy_local_beta/activate.sh

Run deploy_local_beta/run.sh -h for more information.

jpy-flette
==========

*jpy-flette* is a lightweight (~150 lines) python static website generator which uses jupyter notebooks as input. It's fantastic for documenting scientific projects, documentation, or just to share your thoughts with the world.

Installation
------------

Install *jpy-flette* with pip:

.. code:: bash

    pip install jpy-flette


You could also download or clone the source code from the `repository <https://github.com/r4lv/jpy-flette>`_:

.. code:: bash

    git clone "https://github.com/r4lv/jpy-flette"
    cd "jpy-flette"
    python setup.py install




Usage
-----

    Make sure you check the `documentation <https://r4lv.github.io/jpy-flette>`_, which is actually built using *jpy-flette* itself!

*jpy-flette* transforms a directory full of ``.ipynb`` jupyter notebooks into a website with multiple pages. Let's assume the following directory structure:

.. code:: text

    ~/my/directory
              └── notebooks
                  ├── 00.index.ipynb
                  └── 01.advanced-usage.ipynb
    
After calling

.. code:: bash

    jpy-flette ~/my/directory/notebooks

you would obtain

.. code:: text

    ~/my/directory
              ├── docs
              │   ├── index.html
              │   ├── advanced-usage.html
              │   └── static
              │       ├── style.css
              │       └── script.js
              └── notebooks
                  ├── 00.index.ipynb
                  └── 01.advanced-usage.ipynb


``~/my/directory/docs`` is then ready to be published!




Notebook Requirements
------------

Notebooks can be indexed one of two ways: i) within the file name (i.e. 00.index.ipynb), ii) within the metadata.csv file.



All notebooks must conform to the following format:
* must have a Title
* does not need Sections
* # Title
* ## Section
* ### SubSection

In addition, the index notebook is used to create the side-bar Title

This will allow the side-bar table-of-contents to be created, correctly.





Develop
------------



.. code:: bash

    pipenv --python 3
    pipenv install
    jpy_flette/jpy_flette.py ./docs/notebooks/
    cd docs/docs
    python3 -m http.server 8000 --bind 127.0.0.1
    #clean up
    cd -
    rm -r docs/docs
    #exit pipenv
    exit


.. code:: bash

    pipenv shell
    pipenv --version
    exit




Deploy with GithubPages
------------


????

END
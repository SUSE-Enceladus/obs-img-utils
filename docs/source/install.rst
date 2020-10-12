Installation
============

openSUSE package
----------------

Perform the following commands as root:

.. code-block:: console

   $ zypper ar http://download.opensuse.org/repositories/Cloud:/Tools/<distribution>
   $ zypper refresh
   $ zypper in obs-img-utils

PyPI
----

.. code-block:: console

   $ pip install obs-img-utils

Development
-----------

Install the latest development version from GitHub:

.. code-block:: console

   $ pip install git+https://github.com/SUSE-Enceladus/obs-img-utils.git

Branch
------

Install a specific branch from GitHub:

.. code-block:: console

   $ pip install git+https://github.com/SUSE-Enceladus/obs-img-utils.git@{branch/release}

See `PyPI
docs <https://pip.pypa.io/en/stable/reference/pip_install/#vcs-support>`__
for more information on vcs support.

Requirements
============

- Click
- lxml
- PyYaml
- xmltodict
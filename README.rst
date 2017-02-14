====================
Signoxe Server Setup
====================

This guide assumes that the system on which the sever is to be installed is of
the SUSE family, so either openSUSE Leap or openSUSE Tumbleweed.


Step 1: Installing required software
------------------------------------

Since this is a Python 3 project we need to install Python 3 on our system. The
``zypper`` command can be used to install packages on openSUSE systems.

.. code-block:: bash

    sudo zypper install python3 python3-pip python3-virtualenv python3-devel

The following command will install basic developer tools such GCC on our system
so that we can compile software.

.. code-block:: bash

    sudo zypper install -tpattern devel_basis


While not necessary, it is also nice to install PostgreSQL server so we have
the same database server as the live server installed locally for testing.

.. code-block:: bash

    sudo zypper install postgresql95-server postgresql95-devel

The following a development packages that are required by some of the packages
we use.

.. code-block:: bash

    sudo zypper install libffi-devel libopenssl-devel

Step 2: Downloading the project code
------------------------------------

In order to download the project code and push changes to it you need to use
git. The ``git clone`` command can be used to make a local copy of the code.
However since this is a private project you will need to authenticate yourself
each time you update the code or push changes.

There are two ways to authenticate. The first is to use your username and
password, which is easy to set up the first time, but is annoying on a long run
since you will have to enter it each time you make any remote operation on git.
The other option is to use SSH authentication, which is harder to set up
initially but once set up it doesn't need you to supply a username and password
each time.

You can find instructions for setting up SSH access in the `Bitbucket
Documentation`_. Once you have followed those instructions you can clone this
repository with the following command:

.. code-block:: bash

    git clone git@bitbucket.org:signoxe/signoxe-server.git


Step 3: Creating a virtual environment for our project
------------------------------------------------------

Generally while working on Python projects we should use a virtual Python
environment called a virtualenv. Using a virtualenv allows us to install
whatever packages our project requires without installing them globally and
interfering with the main system.

To manage virtualenvs we will install a Python package called ``pew``. Python
packages are installed using the ``pip`` command. If both Python 2 and Python 3
are installed -- which is usually the case -- you should use ``pip2`` to
install packages for Python 2 and ``pip3`` to install packages for Python 3.
Now let's install pew.

.. code-block:: bash

    pip3 install --user --upgrade pew

We used ``--user`` to install the package just for the current user, not the
whole system, and we used ``--upgrade`` to upgrade the package if it's already
installed.

Now we'll create a new virtual environment for our project using pew. Enter the
directory where you have cloned the project and run the following command. Change
Working directory to that of signoxe-server ``cd signoxe-server``:

.. code-block:: bash

    pew new -r requirements-dev.pip -a . signoxe-server

In the above command ``pew new`` creates a new virtualenv; the
``-r requirements-dev.pip`` tell it that it should install all the software listed
in the requirements-dev.pip file; the ``-a .`` tells pew that we want to use the
current directory as the project directory; and finally ``signoxe-server`` is the
name we are giving this virtualenv.

To install some of the dependencies like jpeg library (if the above command shows
an error) , install them using

.. code-block:: bash

    sudo zypper install libjpeg8-devel

Now whenever you want to work on the project you can just type
``pew workon signoxe-server`` and it will go to your project directory and set up
its virtual environment.

Step 4: Running the project
---------------------------

Django projects can be run using the ``manage.py runserver`` command. After
activating the project's virtual environment using pew, you can start the
project server as follows:

.. code-block:: bash

    python manage.py runserver 0:4000

The ``0:4000`` here will tell the server to listen on all addresses and on port
4000. This way you can access the server on any computer on the same network.
If you leave out ``0:4000`` the default port will be 8000 and the server will
only be available at ``localhost:4000``. A simpler way to run the command is to
issue ``make run`` in the project directory, that has the same effect. You can
now access the site at http://localhost:4000 or http://127.0.0.1:4000 etc.

As you modify the project code, this development server will automatically pick
up the changes and restart.


.. _Bitbucket Documentation: https://confluence.atlassian.com/bitbucket/set-up-ssh-for-git-728138079.html

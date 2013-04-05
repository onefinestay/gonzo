gonzo
=====

Instance and release management made easy


Documentation
-------------

`Documentation on Read the Docs <http://gonzo.readthedocs.org/en/latest/>`_


Configuration
-------------

TODO...


Command Line Interface
----------------------

To set project environment configuration use ``gonzo config``::

    $ gonzo config
    mode: None
    region: None
    $ gonzo config --mode aws
    mode: aws
    region: eu-west-1
    $ gonzo config --region us-west-1
    mode: aws
    region: us-west-1

You can then use ``gonzo`` to set targets for fabric commands

Add the ``gonzo`` tasks to your fabfile::

    $ cat fabfile.py

    from gonzo.tasks import gonzo
    __all__ = ['gonzo']

You can then run::

    $ fab gonzo.instance:production-ecommerce-web-003 run_comand

to target an inividual instance, and::

    $ fab gonzo.group:production-ecommerce-web run_comand

to target an entire host group


Fabric task library
-------------------

To use the gonzo library of fabric tasks, simply import the relevent task
modules for namespaced tasks::

    from gonzo.tasks import apache

These can then be called using the standard fabric syntax::

    $ fab -H ... apache.restart

Alternatively import the tasks directly::

    from gonzo.tasks.apache import restart

These commands won't be namespaced::

    $ fab -H ... restart

You can patch in your own commands to the gonzo namespaces to provide a clean
CLI::

    from fabric.api import task, sudo
    from gonzo.tasks import apache

    def maintenance_mode(off=False):
        """ Set server into maintenance mode.
        """

        if off:
            sudo("a2ensite onefinestay && a2dissite 00maintenance")
        else:
            sudo("a2ensite 00maintenance && a2dissite onefinestay")

    apache.maintenance_mode = task(maintenance_mode)


TODO
----

* tidy up config
* document config
* releasing
* project based stuff
    * project name [for ``/srv/project_name``] (git setting?)
* tests


License
-------

Apache 2.0 - see LICENSE for details

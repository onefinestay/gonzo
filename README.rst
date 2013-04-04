gonzo
=====

Instance and release management made easy


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



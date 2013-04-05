gonzo
=====

Instance and release management made easy

Manage instances running in *Amazon Web Services* or using *Openstack* using
a single consistent interface::

    $ gonzo list

    fullstack-hq-uat-064          m1.small   ACTIVE   david    20d 20h 4m 23s
    fullstack-hq-uat-069          m1.small   ACTIVE   fergus   7d 23h 45m 3s
    staging-jenkins-slave-003     m1.large   ACTIVE   matthew  60d 4h 18m 40s


Easily target instances or groups of instances with ``fab`` commands
and manage your code deployments using included fabric tasks::

    $ fab gonzo.group:prouction-ecommerce-web push_release rollforward


Documentation
-------------

`Documentation on Read the Docs <http://gonzo.readthedocs.org/en/latest/>`_


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

* project based stuff
    * project name [for ``/srv/project_name``] (git setting?)
* tests
* tidy release project root ``/srv/*`` targetting


License
-------

Apache 2.0 - see LICENSE for details

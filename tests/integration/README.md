vagrant-devstack installation guide
=====
Guide to easily spin up an openstack cluster using vagrant and devstack


vagrant setup
----

[Download and install Vagrant](http://docs.vagrantup.com/v2/installation/)

Setup vagrant instance
``` bash
mkdir 1404-ubuntu
cd 1404-ubuntu
vagrant box add 1404-ubuntu https://cloud-images.ubuntu.com/vagrant/trusty/current/trusty-server-cloudimg-amd64-vagrant-disk1.box
vagrant init 1404-ubuntu
```


Set 'VagrantFile'


```bash
VAGRANTFILE_API_VERSION = "2"

Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|
  config.vm.box = "1404-ubuntu"
  config.vm.network "private_network", ip: "10.10.1.10"

  config.vm.provider "virtualbox" do |vb|
    vb.customize ["modifyvm", :id, "--memory", "4048"]
  end
end

```

Spin up Vagrant instance
```
vagrant up
vagrant ssh
```

devstack setup
---
* run the following devstack setup bash script as **root**


```bash
#!/bin/sh
useradd -m stack -d /home/stack -p stack
adduser stack sudo
DEBIAN_FRONTEND=noninteractive sudo apt-get -qqy update || sudo yum update -qy
DEBIAN_FRONTEND=noninteractive sudo apt-get install -qqy git || sudo yum install -qy git
sudo chown stack:stack /home/stack
cd /home/stack
git clone https://git.openstack.org/openstack-dev/devstack
chown -R stack:stack /home/stack
cd devstack
echo '[[local|localrc]]' > local.conf
echo ADMIN_PASSWORD=password >> local.conf
echo MYSQL_PASSWORD=password >> local.conf
echo RABBIT_PASSWORD=password >> local.conf
echo SERVICE_PASSWORD=password >> local.conf
echo SERVICE_TOKEN=tokentoken >> local.conf
echo FIXED_RANGE=10.11.12.0/24 >> local.conf
echo FIXED_NETWORK_SIZE=50 >> local.conf
echo FLAT_INTERFACE=eth1 >> local.conf
echo HOST_IP=10.10.1.10 >> local.conf
su - stack /home/stack/devstack/stack.sh    # May take upto 30 minutes to complete
```

Your openstack cluster should now be running, visit http://10.10.1.10 using admin/password  to verify everything is working.




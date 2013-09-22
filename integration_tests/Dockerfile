# gonzo-integration-test
#
# base image for the gonzo integration suite
# VERSION 0.1

FROM base

# python/pip/virtualenv
RUN apt-get update
RUN apt-get install -y -q python-all wget openssh-server

# we need to create privilege separation directory
RUN mkdir /var/run/sshd

# from http://www.pip-installer.org/en/latest/installing.html
RUN wget https://bitbucket.org/pypa/setuptools/raw/bootstrap/ez_setup.py
RUN wget https://raw.github.com/pypa/pip/master/contrib/get-pip.py
RUN python ez_setup.py
RUN python get-pip.py
RUN pip install virtualenv

RUN useradd gonzo --create-home --groups=sudo
RUN echo 'gonzo:password' |chpasswd

RUN virtualenv /srv/existing

EXPOSE 22
CMD /usr/sbin/sshd -D

import time

import boto

from gonzo.config import config_proxy as config


class Iam(object):
    """ Some helpers for IAM interaction  """

    def __init__(self):
        acces_key_id = config.CLOUD['AWS_ACCESS_KEY_ID']
        secret_access_key = config.CLOUD['AWS_SECRET_ACCESS_KEY']
        self.conn = boto.connect_iam(
            aws_access_key_id=acces_key_id,
            aws_secret_access_key=secret_access_key)

    def role_exists(self, role_name):
        boto_roles = self.conn.list_roles()
        roles = [
            role['role_name'] for role in
            boto_roles['list_roles_response']['list_roles_result']['roles']]

        for role in roles:
            if role == role_name:
                return True
        return False

    def create_role(self, role_name):
        return self.conn.create_role(role_name)

    def instance_profile_exists(self, profile_name):
        boto_instance_profiles = self.conn.list_instance_profiles()
        instance_profiles = [
            profile['instance_profile_name'] for profile in
            boto_instance_profiles[
                'list_instance_profiles_response'
            ]['list_instance_profiles_result']['instance_profiles']
        ]

        for instance_profile in instance_profiles:
            if instance_profile == profile_name:
                return True
        return False

    def create_instance_profile(self, profile_name):
        return self.conn.create_instance_profile(profile_name)

    def role_has_profile(self, role_name, profile_name):
        boto_profile_roles = self.conn.list_instance_profiles_for_role(
            role_name)

        instance_profiles = [
            profile['instance_profile_name'] for profile in
            boto_profile_roles[
                'list_instance_profiles_for_role_response'
            ]['list_instance_profiles_for_role_result']['instance_profiles']
        ]

        for instance_profile in instance_profiles:
            if instance_profile == profile_name:
                return True
        return False

    def add_profile_to_role(self, role_name, profile_name):
        # Note arg order (to match role_has_profile)
        self.conn.add_role_to_instance_profile(profile_name, role_name)

    def ensure_gonzo_roles(self, name):
        if not self.role_exists(name):
            self.create_role(name)
            time.sleep(5)  # seems to take a while to appear
        if not self.instance_profile_exists(name):
            self.create_instance_profile(name)
            time.sleep(5)  # seems to take a while to appear
        if not self.role_has_profile(name, name):
            self.add_profile_to_role(name, name)

import boto3
import requests
import configparser
from urllib.request import urlopen
import os
import logging

__version__ = '0.2'


class Configs:
    def __init__(self, default_configs, config_file_path=None):
        self._config_file_path = config_file_path or 'config_local.ini'
        self._default_configs = default_configs

    @staticmethod
    def _is_amazon_instance():
        meta_url = 'http://169.254.169.254/latest/meta-data/ami-id'
        try:
            response = urlopen(meta_url).read()
            if 'ami' in str(response):
                return True
        except Exception as e:
            logging.warning(e)
            return False

        return False

    @staticmethod
    def _get_instance_id():
        try:
            r = requests.get('http://169.254.169.254/latest/meta-data/instance-id')
            r.raise_for_status()
        except requests.exceptions.HTTPError as e:
            logging.exception(e)
            return None

        return r.text

    @staticmethod
    def _get_instance_tags(fid):
        # When given an instance ID as str e.g. 'i-1234567', return the instance 'Name' from the name tag.
        ec2 = boto3.resource('ec2')
        ec2instance = ec2.Instance(fid)

        tags = {}
        for tag in ec2instance.tags:
            tags[tag["Key"]] = tag["Value"]

        return tags

    def _get_server_settings(self):
        # server mode
        instance_id = self._get_instance_id()
        if not instance_id:
            return self._default_configs

        amazon_instance_tags = self._get_instance_tags(instance_id)

        result = {}
        for name, value in self._default_configs.items():
            if name in amazon_instance_tags:
                result[name] = amazon_instance_tags[name]
            else:
                result[name] = value
        return result

    def _get_ini_configs(self):
        ini_config = configparser.ConfigParser()
        ini_config.read(self._config_file_path)
        result = {}
        if 'settings' in ini_config.sections():
            for k, value in ini_config['settings'].items():
                key = k.upper()
                if isinstance(self._default_configs[key], bool):
                    result[key] = ini_config.getboolean('settings', key)
                else:
                    result[key] = value

        return result

    def _get_local_settings(self):
        # local mode
        ini_configs = self._get_ini_configs()
        if ini_configs:
            result = {}
            for name, value in self._default_configs.items():
                if name in ini_configs:
                    result[name] = ini_configs[name]
                else:
                    result[name] = value
            return result

        return self._default_configs

    def get_configs(self):
        if os.path.isfile(self._config_file_path):
            return self._get_local_settings()

        if self._is_amazon_instance():
            return self._get_server_settings()

        logging.warning('Config not found. Returned default values')
        return self._default_configs

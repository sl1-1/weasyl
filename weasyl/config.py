from __future__ import absolute_import

import ConfigParser
import os

from weasyl import macro


class WeasylConfigParser(ConfigParser.ConfigParser, object):
    """
    Allows Weasyl config options to be set via ENV instead of the config file.
    To set a ENV variable for a config section it should be named like WEASYL_SECTION_OPTION
    """

    def get(self, section, option, raw=False, vars=None):
        env_variable = "_".join(['WEASYL', section.upper(), option.upper()])
        return os.environ.get(env_variable, super(WeasylConfigParser, self).get(section, option, raw, vars))


_in_test = False


config_obj = WeasylConfigParser()
config_obj.read([macro.MACRO_CFG_SITE_CONFIG])


def config_read_setting(setting, value=None, section='general'):
    """
    Retrieves a value from the weasyl config.
    Defaults to 'general' section. If the key or section is missing, returns
    `value`, default None.
    """
    try:
        return config_obj.get(section, setting)
    except (ConfigParser.NoOptionError, ConfigParser.NoSectionError):
        return value


def config_read_bool(setting, value=False, section='general'):
    """
    Retrieves a boolean value from the weasyl config.
    Defaults to 'general' section. If the key or section is missing, or
    the value isn't a valid boolean, returns `value`, default False.
    """
    try:
        return config_obj.getboolean(section, setting)
    except (ConfigParser.NoOptionError, ConfigParser.NoSectionError, ValueError):
        return value

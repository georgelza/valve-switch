#
########################################################################################################################
#
#
#  	Project     	: 	Valveswitch
#
#   File            :   apputils.py
#
#	By              :   George Leonard ( georgelza@gmail.com )
#
#   Created     	:   8 Apr 2023
#
#   Notes       	:
#
#######################################################################################################################

__author__      = "George Leonard"
__email__       = "georgelza@gmail.com"
__version__     = "0.0.1"
__copyright__   = "Copyright 2022, George Leonard"

import configparser
from datetime import datetime

def get_config_params(configfile, descriptor=""):
    """ Get/Read config file contents """

    parser = configparser.ConfigParser()
    parser.read(configfile)

    params = {}
    for section_name in parser.sections():
        items = {}
        for itemname, itemvalue in parser.items(section_name):
            items[itemname] = itemvalue

        params[section_name] = items

    return params
# end def 


def print_params(configfile, my_logger, descriptor=""):
    """ Get/Read config file contents """

    my_logger.info(' ')
    my_logger.info(' ####################################### ')
    my_logger.info(' #                                     # ')
    my_logger.info(' #             Valve Switch            # ')
    my_logger.info(' #                                     # ')
    my_logger.info(' #          by: George Leonard         # ')
    my_logger.info(' #          georgelza@gmail.com        # ')
    my_logger.info(' #                                     # ')
    my_logger.info(' #       {time}    # '.format(
        time=str(datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")),
    ))
    my_logger.info(' #                                     # ')
    my_logger.info(' ####################################### ')
    my_logger.info(' ')

    parser = configparser.ConfigParser()
    parser.read(configfile)

    for section_name in parser.sections():
        my_logger.info('{time}, [{section_name}]. '.format(
                time=str(datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")),
                section_name=section_name,
            ))            
        for itemname, itemvalue in parser.items(section_name):
            my_logger.info('{time}, {itemname} {itemvalue}. '.format(
                    time=str(datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")),
                    itemname=itemname,
                    itemvalue=itemvalue
                ))
        my_logger.info(' ')

# -*- coding: utf-8 -*-
import os

from pyjobs_crawlers.run import start_crawlers

from crawlers import PyJobsWebConnector
from pyjobsweb.commands import AppContextCommand


class CrawlCommand(AppContextCommand):

    def get_parser(self, prog_name):
        parser = super(CrawlCommand, self).get_parser(prog_name)

        parser.add_argument("-p", "--processes",
                            help='Number of processes used (set 0 to use main process)',
                            dest='processes', default=0)

        parser.add_argument("-d", "--debug",
                            help='Enable debug',
                            dest='debug', default=0)
        return parser

    def take_action(self, parsed_args):
        super(CrawlCommand, self).take_action(parsed_args)
        start_crawlers(connector_class=PyJobsWebConnector,
                       processes=parsed_args.processes,
                       debug=parsed_args.debug)

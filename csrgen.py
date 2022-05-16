#!/usr/bin/env python3
import argparse
import re
import os
from jinja2 import Template

description = """
Simple script to handle generating Certificate Signing Requests (CSR)
This has the ability to generate CSRs with and without a provided key.
Also can handle multiple domains as Subject Alternative Name (SAN) records.
"""


def check_file(file):
    if os.stat(file).st_size > 0:
        return file


def check_domain(input):
    if check_file(input):
        return input, True
    else:
        domain_template = re.compile(
            "^(?=.{1,255}$)(?!-)[A-Za-z0-9\-]{1,63}(\.[A-Za-z0-9\-]{1,63})*\.?(?<!-)$")
        if domain_template.match(input):
            return input
        else:
            raise argparse.ArgumentError(
                "Unable to determine if this is a domain or a file. Please check your input.")


def parse_arguments():
    parser = argparse.ArgumentParser(description=description,
                                     formatter_class=argparse.RawTextHelpFormatter)
    subparser = parser.add_subparsers(dest="command")

    csr = subparser.add_parser("csr", help="Create CSR",
                               formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    csr.add_argument('-k', "--key", type=check_file, help='Specify a key')
    csr.add_argument('-d', "--domain", type=check_domain, required=True,
                     help="Specify a domain or a file with list of domains")

    config = subparser.add_parser("config", help="Create config file")
    config.add_argument("-c", "--country", help="Country short code")
    config.add_argument("-l", "--locality", help="Locality/City")
    config.add_argument("-s", "--state", help="State Name")
    config.add_argument("-o", "--org", help="Orginization Name", required=True)

    if parser.parse_args().command:
        return parser.parse_args()
    else:
        parser.print_help()


def main(args):

    print("end test")


if __name__ == '__main__':
    main(parse_arguments())

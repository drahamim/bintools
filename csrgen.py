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
config_template = """[ req ]
        default_bits           = 2048
        distinguished_name     = req_distinguished_name
        prompt                 = no
        req_extensions         = v3_req
[ req_distinguished_name ]
    {% if c is not none -%}
        C                      = {{s}}
    {%- endif %}
    {%- if l is not none -%}
        L                      = {{l}}
    {%- endif %}
    {%- if s is not none -%}
        ST                     = {{s}}
    {%- endif %}
    {%- if o is not none -%}
        O                      = {{o}}
    {%- endif %}
{{'    CN                     = {{ cn }}
[ v3_req ]
    subjectAltName          = @alt_names

[alt_names]
    DNS.1 = {{ cn }}
    {%- for domain in sans %}
        {%- if domain %}
    DNS.{{ loop.index +1 }} = {{ domain }}
        {%- endif %}
    {%- endfor %}
'}}
"""


def check_file(file):
    try:
        os.stat(file).st_size > 1
    except:
        return False
    else:
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
    config.add_argument("-o", "--org", help="Organization Name", required=True)

    if parser.parse_args().command:
        return parser.parse_args()
    else:
        parser.print_help()


def main(args):
    tm = Template(config_template)
    if args.command == 'config':

       print(tm.render(c=args.country, l=args.locality,
                  s=args.state, o=args.org))

    else:
        print("test failed")


if __name__ == '__main__':
    main(parse_arguments())

#!/usr/bin/env python3
import argparse
import fnmatch
import re
import os
import subprocess
import readline
from jinja2 import Template, Environment, FileSystemLoader

file_loader = FileSystemLoader('.')
env = Environment(loader=file_loader)


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
            return input.lower()
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
    csr.add_argument("-o", "--org", help="Organization Name")

    config = subparser.add_parser("config", help="Create config file")
    config.add_argument("-c", "--country", help="Country short code")
    config.add_argument("-l", "--locality", help="Locality/City")
    config.add_argument("-s", "--state", help="State Name")
    config.add_argument("-o", "--org", help="Organization Name", required=True)

    if parser.parse_args().command:
        return parser.parse_args()
    else:
        parser.print_help()
        exit()


def gen_csr_config(args, config_file):
    tm = env.get_template(config_file)
    print(config_file)
    SANS = list()
    print("Generating CSR configuration..")
    if type(args.domain) is tuple:
        domain_file, is_file = args.domain
        with open(domain_file) as fp:
            domain = fp.readline()
            count = 0
            while domain:
                print(domain)
                if count == 0:
                    CN = domain.strip().lower()
                    domain = fp.readline()
                    count += 1
                elif 1 <= count <= 100:
                    SANS.append(domain.strip().lower())
                    domain = fp.readline()
                    count += 1
                else:
                    print("Too many domains! Please limit to 100")
                    exit(1)
            print(CN)
    else:
        domain = args.domain
        CN = domain.strip().lower()

    generated_csr_config = open(args.domain + '_csr_config', 'w')
    generated_csr_config.write(tm.render(cn=CN, sans=SANS))
    generated_csr_config.close()

    return str(args.domain + '_csr_config')


def main(args):
    if args.command == 'csr':
        # Look for csrgen config files
        config_file_search = fnmatch.filter(os.listdir(), "*_gen_config")
        if len(config_file_search) == 0:
            print("No config files found please run with 'config -h' to create one")
            exit()
        elif len(config_file_search) > 1:   # Check if there is more then one config file
            if args.org:
                # Check if any of the config files match the specified Org
                if check_file({args.org + "_gen_config"}):
                    csr_config_out = gen_csr_config(
                        args, {args.org + "_gen_config"})
            else:
                print("Please specify Organization name with -o <Org>")
                exit()
        else:  # There is only one found so assume its the right one\
            csr_config_out = gen_csr_config(args, config_file_search[0])

        # Validate key argument and file
        if args.key:
            if check_file(args.key):
                try:
                    subprocess.call(['openssl', 'rsa', '-in',
                                    args.key, '-check'])
                except:
                    print("Key specified is not a valid rsa key.")
            else:
                print("Key file specified doesn't exist.")
        else:
            print("No key specified. Creating a new one.")
            subprocess.call(['openssl', 'genrsa', '-out',
                             args.domain + '.key', '2048'])
            print("Key Generated")

        if args.key:
            print("Generatinc CSR")
            subprocess.call(['openssl', 'req', '-new', '-config', csr_config_out,
                             '-key',  + args.key, '-out', args.domain + '.csr'])
        else:
            print("Generatinc CSR")
            subprocess.call(['openssl', 'req', '-new', '-config', csr_config_out,
                             '-key', args.domain + '.key', '-out', args.domain + '.csr'])

    if args.command == 'config':
        tm = Template(config_template)
        config_file_name = args.org + "_gen_config"
        print("Creating config template file: {filename}".format(
            filename=config_file_name))
        config_file = open(config_file_name, "w")
        config_file.write(tm.render(c=args.country, l=args.locality,
                                    s=args.state, o=args.org))
        config_file.close()


if __name__ == '__main__':
    main(parse_arguments())

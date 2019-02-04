import datetime
import json
import os
import re

import requests

from commitment import GitHubCredentials, GitHubClient

VALID_FORMATS = ("csv", )

credentials = GitHubCredentials(
    repo="DemocracyClub/GDSRegisters",
    name=os.environ['MORPH_GITHUB_USERNAME'],
    email=os.environ['MORPH_GITHUB_EMAIL'],
    api_key=os.environ['MORPH_GITHUB_API_KEY']
)
client = GitHubClient(credentials)

def make_url(name, domain=None, data_format="csv"):
    assert data_format in VALID_FORMATS
    if not domain:
        domain = "www.registers.service.gov.uk"
    URL_FMT = "https://{domain}/registers/{name}/download-{format}"
    return URL_FMT.format(
        domain=domain,
        name=name,
        format=data_format
    )


def get_all_register_names():
    all_names = set()
    # Check registers listed in the register register
    req = requests.get(make_url("register"))
    for register in req.text.splitlines():
        register_name = register.split(",")[3].strip('"')
        all_names.add(register_name)

    # Check "upcoming" registers
    req = requests.get(
        "https://www.registers.service.gov.uk/registers-in-progress"
    )
    for name in re.findall("/registers/([^\"\' ]+)", req.text):
        all_names.add(name)
    return list(all_names)

def save_register_data(register_name):
    dir_path = "registers/{}/".format(register_name)
    os.makedirs(dir_path, exist_ok=True)
    for data_format in VALID_FORMATS:
        url = make_url(register_name, data_format=data_format)
        file_name = "{}.{}".format(register_name, data_format)
        dir_and_file = os.path.join(dir_path, file_name)

        req = requests.get(url)
        content = req.text

        client.push_file(content, dir_and_file, "Updated on {}".format(
            datetime.datetime.now().isoformat()
        ))


if __name__ == "__main__":
    for name in get_all_register_names():
        save_register_data(name)

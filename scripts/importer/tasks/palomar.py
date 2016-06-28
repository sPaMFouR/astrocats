"""Import tasks for the Palomar Transient Factory (PTF).
"""
import os

import requests
from bs4 import BeautifulSoup

from scripts import PATH

from ...utils import is_number


def do_ptf(catalog):
    # response =
    # urllib.request.urlopen('http://wiserep.weizmann.ac.il/objects/list')
    # bs = BeautifulSoup(response, 'html5lib')
    # select = bs.find('select', {'name': 'objid'})
    # options = select.findAll('option')
    # for option in options:
    #    print(option.text)
    #    name = option.text
    #    if ((name.startswith('PTF') and is_number(name[3:5])) or
    #        name.startswith('PTFS') or name.startswith('iPTF')):
    # name = catalog.add_entry(name)

    if catalog.current_task.load_archive(catalog.args):
        with open(os.path.join(PATH.REPO_EXTERNAL,
                               'PTF/update.html'), 'r') as f:
            html = f.read()
    else:
        session = requests.Session()
        response = session.get('http://wiserep.weizmann.ac.il/spectra/update')
        html = response.text
        with open(os.path.join(PATH.REPO_EXTERNAL,
                               'PTF/update.html'), 'w') as f:
            f.write(html)

    bs = BeautifulSoup(html, 'html5lib')
    select = bs.find('select', {'name': 'objid'})
    options = select.findAll('option')
    for option in options:
        name = option.text
        if (((name.startswith('PTF') and is_number(name[3:5])) or
             name.startswith('PTFS') or name.startswith('iPTF'))):
            if '(' in name:
                alias = name.split('(')[0].strip(' ')
                name = name.split('(')[-1].strip(') ').replace('sn', 'SN')
                name = catalog.add_entry(name)
                source = catalog.events[name].add_source(bibcode='2012PASP..124..668Y')
                catalog.events[name].add_quantity('alias', alias, source)
            else:
                # events, name = catalog.add_entry(tasks, args,
                #                                 events, name, log)
                name, source = catalog.new_event(name,
                                                 bibcode='2012PASP..124..668Y')

    with open(os.path.join(PATH.REPO_EXTERNAL, 'PTF/old-ptf-events.csv')) as f:
        for suffix in f.read().splitlines():
            name = catalog.add_entry('PTF' + suffix)
    with open(os.path.join(PATH.REPO_EXTERNAL, 'PTF/perly-2016.csv')) as f:
        for row in f.read().splitlines():
            cols = [x.strip() for x in row.split(',')]
            alias = ''
            if cols[8]:
                name = cols[8]
                alias = 'PTF' + cols[0]
            else:
                name = 'PTF' + cols[0]
            name = catalog.add_entry(name)
            source = catalog.events[name].add_source(bibcode='2016arXiv160408207P')
            catalog.events[name].add_quantity('alias', name, source)
            if alias:
                catalog.events[name].add_quantity('alias', alias, source)
            catalog.events[name].add_quantity('ra', cols[1], source)
            catalog.events[name].add_quantity('dec', cols[2], source)
            catalog.events[name].add_quantity('claimedtype', 'SLSN-' + cols[3], source)
            catalog.events[name].add_quantity(
                'redshift', cols[4], source, kind='spectroscopic')
            maxdate = cols[6].replace('-', '/')
            upl = maxdate.startswith('<')
            catalog.events[name].add_quantity(
                'maxdate', maxdate.lstrip('<'), source, upperlimit=upl)
            catalog.events[name].add_quantity(
                'ebv', cols[7], source, kind='spectroscopic')
            name = catalog.add_entry('PTF' + suffix)

    catalog.journal_events()
    return
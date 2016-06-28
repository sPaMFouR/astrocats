"""General data import tasks.
"""
import csv
import os

from astropy.time import Time as astrotime

from scripts import PATH
from scripts.utils import pbar

from ..funcs import make_date_string


def do_psst(catalog):
    current_task = catalog.current_task
    # 2016arXiv160204156S
    file_path = os.path.join(
        PATH.REPO_EXTERNAL, '2016arXiv160204156S-tab1.tsv')
    with open(file_path, 'r') as f:
        data = list(csv.reader(f, delimiter='\t',
                               quotechar='"', skipinitialspace=True))
        for r, row in enumerate(pbar(data, current_task)):
            if row[0][0] == '#':
                continue
            (catalog.events,
             name,
             source) = catalog.new_event(row[0],
                                        bibcode='2016arXiv160204156S')
            catalog.events[name].add_quantity(
                'claimedtype', row[3].replace('SN', '').strip('() '), source)
            catalog.events[name].add_quantity('redshift', row[5].strip(
                '() '), source, kind='spectroscopic')

    file_path = os.path.join(
        PATH.REPO_EXTERNAL, '2016arXiv160204156S-tab2.tsv')
    with open(file_path, 'r') as f:
        data = list(csv.reader(f, delimiter='\t',
                               quotechar='"', skipinitialspace=True))
        for r, row in enumerate(pbar(data, current_task)):
            if row[0][0] == '#':
                continue
            (catalog.events,
             name,
             source) = catalog.new_event(row[0],
                                        bibcode='2016arXiv160204156S')
            catalog.events[name].add_quantity('ra', row[1], source)
            catalog.events[name].add_quantity('dec', row[2], source)
            mldt = astrotime(float(row[4]), format='mjd').datetime
            discoverdate = make_date_string(mldt.year, mldt.month, mldt.day)
            catalog.events[name].add_quantity('discoverdate', discoverdate, source)

    catalog.journal_events()

    # 1606.04795
    file_path = os.path.join(PATH.REPO_EXTERNAL, '1606.04795.tsv')
    with open(file_path, 'r') as f:
        data = list(csv.reader(f, delimiter='\t',
                               quotechar='"', skipinitialspace=True))
        for r, row in enumerate(pbar(data, current_task)):
            if row[0][0] == '#':
                continue
            (catalog.events,
             name,
             source) = catalog.new_event(row[0],
                                        srcname='Smartt et al. 2016',
                                        url='http://arxiv.org/abs/1606.04795')
            catalog.events[name].add_quantity('ra', row[1], source)
            catalog.events[name].add_quantity('dec', row[2], source)
            mldt = astrotime(float(row[3]), format='mjd').datetime
            discoverdate = make_date_string(mldt.year, mldt.month, mldt.day)
            catalog.events[name].add_quantity('discoverdate', discoverdate, source)
            catalog.events[name].add_quantity('claimedtype', row[6], source)
            catalog.events[name].add_quantity(
                'redshift', row[7], source, kind='spectroscopic')
            for alias in [x.strip() for x in row[8].split(',')]:
                catalog.events[name].add_quantity('alias', alias, source)

    catalog.journal_events()

    return
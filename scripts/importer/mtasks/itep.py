"""General data import tasks.
"""
import csv
import os
import re
from collections import OrderedDict
from html import unescape

from cdecimal import Decimal
from scripts import PATH
from scripts.utils import pbar

from ..funcs import jd_to_mjd


def do_itep(catalog):
    current_task = catalog.current_task
    itepbadsources = ['2004ApJ...602..571B']
    needsbib = []
    with open(os.path.join(PATH.REPO_EXTERNAL,
                           'itep-refs.txt'), 'r') as refs_file:
        refrep = refs_file.read().splitlines()
    refrepf = dict(list(zip(refrep[1::2], refrep[::2])))
    fname = os.path.join(PATH.REPO_EXTERNAL, 'itep-lc-cat-28dec2015.txt')
    tsvin = list(csv.reader(open(fname, 'r'),
                            delimiter='|', skipinitialspace=True))
    curname = ''
    for rr, row in enumerate(pbar(tsvin, current_task)):
        if rr <= 1 or len(row) < 7:
            continue
        oldname = 'SN' + row[0].strip()
        mjd = str(jd_to_mjd(Decimal(row[1].strip())))
        band = row[2].strip()
        magnitude = row[3].strip()
        e_magnitude = row[4].strip()
        reference = row[6].strip().strip(',')

        if curname != oldname:
            curname = oldname
            name = catalog.add_event(oldname)

            sec_reference = ('Sternberg Astronomical Institute '
                             'Supernova Light Curve Catalogue')
            sec_refurl = 'http://dau.itep.ru/sn/node/72'
            sec_source = catalog.events[name].add_source(
                srcname=sec_reference, url=sec_refurl, secondary=True)
            catalog.events[name].add_quantity('alias', oldname, sec_source)

            year = re.findall(r'\d+', name)[0]
            catalog.events[name].add_quantity('discoverdate', year, sec_source)
        if reference in refrepf:
            bibcode = unescape(refrepf[reference])
            source = catalog.events[name].add_source(bibcode=bibcode)
        else:
            needsbib.append(reference)
            source = catalog.events[name].add_source(
                srcname=reference) if reference else ''

        if bibcode not in itepbadsources:
            catalog.events[name].add_photometry(time=mjd, band=band,
                           magnitude=magnitude,
                           e_magnitude=e_magnitude, source=sec_source + ',' +
                           source)

    # Write out references that could use aa bibcode
    needsbib = list(OrderedDict.fromkeys(needsbib))
    with open('../itep-needsbib.txt', 'w') as bib_file:
        bib_file.writelines(['%ss\n' % ii for ii in needsbib])
    catalog.journal_events()
    return
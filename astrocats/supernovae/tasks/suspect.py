"""Import tasks for SUSPECT.
"""
import csv
import json
import os
import re
import urllib
from glob import glob
from html import unescape
from math import floor

from astropy.time import Time as astrotime
from bs4 import BeautifulSoup

from astrocats.catalog.utils import (get_sig_digits, is_number, jd_to_mjd,
                                     pbar, pbar_strings, pretty_num, uniq_cdl)
from cdecimal import Decimal


def do_suspect_photo(catalog):
    current_task = catalog.get_current_task_str()
    with open(os.path.join(catalog.get_current_task_repo(),
                           'suspectreferences.csv'), 'r') as f:
        tsvin = csv.reader(f, delimiter=',', skipinitialspace=True)
        suspectrefdict = {}
        for row in tsvin:
            suspectrefdict[row[0]] = row[1]

    file_names = glob(os.path.join(
        catalog.get_current_task_repo(), 'SUSPECT/*.html'))
    for datafile in pbar_strings(file_names, desc=current_task):
        basename = os.path.basename(datafile)
        basesplit = basename.split('-')
        oldname = basesplit[1]
        name = catalog.add_entry(oldname)
        if name.startswith('SN') and is_number(name[2:]):
            name = name + 'A'
        band = basesplit[3].split('.')[0]
        ei = int(basesplit[2])
        bandlink = 'file://' + os.path.abspath(datafile)
        bandresp = urllib.request.urlopen(bandlink)
        bandsoup = BeautifulSoup(bandresp, 'html5lib')
        bandtable = bandsoup.find('table')

        names = bandsoup.body.findAll(text=re.compile('Name'))
        reference = ''
        for link in bandsoup.body.findAll('a'):
            if 'adsabs' in link['href']:
                reference = str(link).replace('"', "'")

        bibcode = unescape(suspectrefdict[reference])
        source = catalog.entries[name].add_source(bibcode=bibcode)

        sec_ref = 'SUSPECT'
        sec_refurl = 'https://www.nhn.ou.edu/~suspect/'
        sec_source = catalog.entries[name].add_source(
            srcname=sec_ref, url=sec_refurl, secondary=True)
        catalog.entries[name].add_quantity('alias', oldname, sec_source)

        if ei == 1:
            year = re.findall(r'\d+', name)[0]
            catalog.entries[name].add_quantity(
                'discoverdate', year, sec_source)
            catalog.entries[name].add_quantity(
                'host', names[1].split(':')[1].strip(), sec_source)

            redshifts = bandsoup.body.findAll(text=re.compile('Redshift'))
            if redshifts:
                catalog.entries[name].add_quantity(
                    'redshift', redshifts[0].split(':')[1].strip(),
                    sec_source, kind='heliocentric')
            # hvels = bandsoup.body.findAll(text=re.compile('Heliocentric
            # Velocity'))
            # if hvels:
            #     vel = hvels[0].split(':')[1].strip().split(' ')[0]
            #     catalog.entries[name].add_quantity('velocity', vel, sec_source,
            # kind='heliocentric')
            types = bandsoup.body.findAll(text=re.compile('Type'))

            catalog.entries[name].add_quantity(
                'claimedtype', types[0].split(':')[1].strip().split(' ')[0],
                sec_source)

        for r, row in enumerate(bandtable.findAll('tr')):
            if r == 0:
                continue
            col = row.findAll('td')
            mjd = str(jd_to_mjd(Decimal(col[0].contents[0])))
            mag = col[3].contents[0]
            if mag.isspace():
                mag = ''
            else:
                mag = str(mag)
            e_magnitude = col[4].contents[0]
            if e_magnitude.isspace():
                e_magnitude = ''
            else:
                e_magnitude = str(e_magnitude)
            catalog.entries[name].add_photometry(
                time=mjd, band=band, magnitude=mag, e_magnitude=e_magnitude,
                source=sec_source + ',' + source)

    catalog.journal_entries()
    return


def do_suspect_spectra(catalog):
    current_task = catalog.get_current_task_str()
    with open(os.path.join(catalog.get_current_task_repo(),
                           'Suspect/sources.json'), 'r') as f:
        sourcedict = json.loads(f.read())

    with open(os.path.join(catalog.get_current_task_repo(),
                           'Suspect/filename-changes.txt'), 'r') as f:
        rows = f.readlines()
        changedict = {}
        for row in rows:
            if not row.strip() or row[0] == "#":
                continue
            items = row.strip().split(' ')
            changedict[items[1]] = items[0]

    suspectcnt = 0
    folders = next(os.walk(os.path.join(
        catalog.get_current_task_repo(), 'Suspect')))[1]
    for folder in pbar(folders, current_task):
        eventfolders = next(os.walk(os.path.join(
            catalog.get_current_task_repo(), 'Suspect/') + folder))[1]
        oldname = ''
        for eventfolder in pbar(eventfolders, current_task):
            name = eventfolder
            if is_number(name[:4]):
                name = 'SN' + name
            name = catalog.get_preferred_name(name)
            if oldname and name != oldname:
                catalog.journal_entries()
            oldname = name
            name = catalog.add_entry(name)
            sec_ref = 'SUSPECT'
            sec_refurl = 'https://www.nhn.ou.edu/~suspect/'
            sec_bibc = '2001AAS...199.8408R'
            sec_source = catalog.entries[name].add_source(
                srcname=sec_ref, url=sec_refurl, bibcode=sec_bibc,
                secondary=True)
            catalog.entries[name].add_quantity('alias', name, sec_source)
            fpath = os.path.join(catalog.get_current_task_repo(),
                                 'Suspect', folder, eventfolder)
            eventspectra = next(os.walk(fpath))[2]
            for spectrum in eventspectra:
                sources = [sec_source]
                bibcode = ''
                if spectrum in changedict:
                    specalias = changedict[spectrum]
                else:
                    specalias = spectrum
                if specalias in sourcedict:
                    bibcode = sourcedict[specalias]
                elif name in sourcedict:
                    bibcode = sourcedict[name]
                if bibcode:
                    source = catalog.entries[name].add_source(
                        bibcode=unescape(bibcode))
                    sources += [source]
                sources = uniq_cdl(sources)

                date = spectrum.split('_')[1]
                year = date[:4]
                month = date[4:6]
                day = date[6:]
                sig = get_sig_digits(day) + 5
                day_fmt = str(floor(float(day))).zfill(2)
                time = astrotime(year + '-' + month + '-' + day_fmt).mjd
                time = time + float(day) - floor(float(day))
                time = pretty_num(time, sig=sig)

                fpath = os.path.join(catalog.get_current_task_repo(), 'Suspect',
                                     folder,
                                     eventfolder, spectrum)
                with open() as f:
                    specdata = list(csv.reader(
                        f, delimiter=' ', skipinitialspace=True))
                    specdata = list(filter(None, specdata))
                    newspec = []
                    oldval = ''
                    for row in specdata:
                        if row[1] == oldval:
                            continue
                        newspec.append(row)
                        oldval = row[1]
                    specdata = newspec
                haserrors = len(specdata[0]) == 3 and specdata[
                    0][2] and specdata[0][2] != 'NaN'
                specdata = [list(i) for i in zip(*specdata)]

                wavelengths = specdata[0]
                fluxes = specdata[1]
                errors = ''
                if haserrors:
                    errors = specdata[2]

                catalog.entries[name].add_spectrum(
                    'Angstrom', 'Uncalibrated', u_time='MJD',
                    time=time,
                    wavelengths=wavelengths, fluxes=fluxes, errors=errors,
                    errorunit='Uncalibrated',
                    source=sources, filename=spectrum)
                suspectcnt = suspectcnt + 1
                if catalog.args.travis and suspectcnt % catalog.TRAVIS_QUERY_LIMIT == 0:
                    break

    catalog.journal_entries()
    return

#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""De-identify the Rizgary lumbar MRI DICOM studies.

WHAT IT DOES
    Reads every study under Data/cases/ (both the zipped studies and any loose
    DICOM files), strips direct patient identifiers from the headers, and writes
    a clean copy to a separate output tree. Originals are never modified.

    A linkage file mapping case ID -> original patient name and birth date is
    written OUTSIDE the project folder, so it never lands in git or in a shared
    copy of the dataset.

WHAT IT REMOVES
    Direct identifiers: patient name, patient ID, birth date, other patient IDs
    and names, address, telephone, referring/performing/operator physician
    names, institution name and address, station name, accession number, and
    all private tags.

WHAT IT KEEPS ON PURPOSE
    PatientSex and PatientAge  -- research variables, not identifiers on their own.
    StudyDate                  -- reduced to the year only (see DATE_POLICY).
    Every acquisition parameter -- sequence, TR/TE, field strength, pixel spacing,
                                  slice thickness, orientation and position. These
                                  are needed for the science and identify nobody.

WHAT IT DELIBERATELY DOES NOT DO
    It does not regenerate SOP/Study/Series UIDs. Re-mapping UIDs consistently
    across a study is easy to get wrong, and a broken UID hierarchy will stop the
    series loading in MicroDicom or any viewer. UIDs are not names; leaving them
    is the safer trade for an internal research copy. If the data is ever to be
    published, revisit this and use a proper tool such as dcmtk or CTP.

    It does not touch burned-in pixel annotations. Siemens lumbar MRI does not
    normally burn patient details into the image, but if any study proves to be a
    secondary capture with visible text, that must be handled separately -- the
    script flags such studies rather than silently passing them.

USAGE
    python tools/deidentify_dicom.py --dry-run     # report only, change nothing
    python tools/deidentify_dicom.py               # write the clean copy
"""
import argparse
import csv
import io
import os
import re
import sys
import zipfile
import warnings

warnings.filterwarnings('ignore')

try:
    import pydicom
    from pydicom.errors import InvalidDicomError
except ImportError:
    sys.exit('pydicom is required:  pip install pydicom')

PROJECT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCE = os.path.join(PROJECT, 'Data', 'cases')
OUTPUT = os.path.join(PROJECT, 'Data_deidentified', 'cases')

# The linkage file lives OUTSIDE the project directory on purpose.
LINKAGE = os.path.join(os.path.dirname(PROJECT), 'RIZGARY_LINKAGE_DO_NOT_SHARE.csv')

# Tags emptied. Keyword -> replacement ('' means blank).
BLANK_TAGS = [
    'PatientBirthDate', 'PatientBirthTime', 'OtherPatientIDs', 'OtherPatientNames',
    'PatientAddress', 'PatientTelephoneNumbers', 'PatientMotherBirthName',
    'ReferringPhysicianName', 'ReferringPhysicianAddress',
    'ReferringPhysicianTelephoneNumbers', 'PerformingPhysicianName',
    'NameOfPhysiciansReadingStudy', 'OperatorsName', 'PhysiciansOfRecord',
    'RequestingPhysician', 'InstitutionName', 'InstitutionAddress',
    'InstitutionalDepartmentName', 'StationName', 'AccessionNumber',
    'StudyID', 'PatientComments', 'AdditionalPatientHistory',
    'MedicalRecordLocator', 'MilitaryRank', 'BranchOfService',
    'CountryOfResidence', 'RegionOfResidence', 'CurrentPatientLocation',
    'IssuerOfPatientID', 'PerformedProcedureStepID',
    'RequestAttributesSequence', 'ReferencedPatientSequence',
]

# Dates reduced to the year, so seasonality analysis stays possible while the
# exact scan date -- which can re-identify against an appointment book -- does not.
DATE_TAGS = ['StudyDate', 'SeriesDate', 'AcquisitionDate', 'ContentDate']
TIME_TAGS = ['StudyTime', 'SeriesTime', 'AcquisitionTime', 'ContentTime']
DATE_POLICY = 'year'          # 'year' -> 20250512 becomes 20250101; 'blank' -> removed


def case_id_from_path(path):
    m = re.search(r'case[\s._-]*(\d+)', path, re.I)
    return m.group(1) if m else None


def deidentify(ds, case_id):
    """Strip identifiers from one dataset in place. Returns what was found."""
    found = {}
    for kw in ('PatientName', 'PatientID'):
        v = str(getattr(ds, kw, '') or '').strip()
        if v:
            found[kw] = v
    v = str(getattr(ds, 'PatientBirthDate', '') or '').strip()
    if v:
        found['PatientBirthDate'] = v

    label = 'RIZGARY_{}'.format(case_id) if case_id else 'RIZGARY_UNKNOWN'
    ds.PatientName = label
    ds.PatientID = label

    for kw in BLANK_TAGS:
        if kw in ds:
            try:
                setattr(ds, kw, '')
            except Exception:
                del ds[kw]

    for kw in DATE_TAGS:
        v = str(getattr(ds, kw, '') or '')
        if v:
            setattr(ds, kw, (v[:4] + '0101') if DATE_POLICY == 'year' else '')
    for kw in TIME_TAGS:
        if kw in ds:
            setattr(ds, kw, '')

    ds.remove_private_tags()
    ds.PatientIdentityRemoved = 'YES'
    ds.DeidentificationMethod = 'Rizgary research de-identification; direct identifiers removed, dates reduced to year, private tags removed'
    return found


def flag_burned_in(ds):
    """Return True if the header suggests text may be burned into the pixels."""
    if str(getattr(ds, 'BurnedInAnnotation', '') or '').upper() == 'YES':
        return True
    return str(getattr(ds, 'Modality', '') or '').upper() in ('SC', 'OT')


def process(dry_run=False):
    if not os.path.isdir(SOURCE):
        sys.exit('Source not found: {}'.format(SOURCE))

    linkage, stats = {}, {'studies': 0, 'files': 0, 'named': 0, 'burned': [], 'errors': []}

    for root, _dirs, files in os.walk(SOURCE):
        for name in files:
            src = os.path.join(root, name)
            rel = os.path.relpath(src, SOURCE)
            cid = case_id_from_path(rel)

            if name.lower().endswith('.zip'):
                stats['studies'] += 1
                dst = os.path.join(OUTPUT, rel)
                if not dry_run:
                    os.makedirs(os.path.dirname(dst), exist_ok=True)
                try:
                    zin = zipfile.ZipFile(src)
                    zout = None if dry_run else zipfile.ZipFile(dst, 'w', zipfile.ZIP_DEFLATED)
                    for item in zin.namelist():
                        if item.endswith('/'):
                            continue
                        raw = zin.read(item)
                        try:
                            ds = pydicom.dcmread(io.BytesIO(raw), force=True)
                            if not hasattr(ds, 'SOPClassUID') and 'PatientName' not in ds:
                                raise InvalidDicomError
                        except Exception:
                            if zout:
                                zout.writestr(item, raw)
                            continue
                        got = deidentify(ds, cid)
                        if got.get('PatientName'):
                            stats['named'] += 1
                            linkage.setdefault(cid or '?', got)
                        if flag_burned_in(ds):
                            stats['burned'].append(rel)
                        stats['files'] += 1
                        if zout:
                            buf = io.BytesIO()
                            ds.save_as(buf, enforce_file_format=True)
                            zout.writestr(item, buf.getvalue())
                    if zout:
                        zout.close()
                except Exception as e:
                    stats['errors'].append('{}: {}'.format(rel, str(e)[:80]))
                continue

            if name.lower() in ('desktop.ini',):
                continue

            try:
                ds = pydicom.dcmread(src, force=True)
                if 'PatientName' not in ds and not hasattr(ds, 'SOPClassUID'):
                    continue
            except Exception:
                continue
            got = deidentify(ds, cid)
            if got.get('PatientName'):
                stats['named'] += 1
                linkage.setdefault(cid or '?', got)
            if flag_burned_in(ds):
                stats['burned'].append(rel)
            stats['files'] += 1
            if not dry_run:
                dst = os.path.join(OUTPUT, rel)
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                ds.save_as(dst, enforce_file_format=True)

    print('studies (zips) : {}'.format(stats['studies']))
    print('DICOM files    : {}'.format(stats['files']))
    print('files carrying a patient name: {}'.format(stats['named']))
    print('distinct cases linked        : {}'.format(len(linkage)))
    if stats['burned']:
        print('\n!! possible burned-in annotation, review manually: {} file(s)'.format(len(stats['burned'])))
        for b in stats['burned'][:5]:
            print('   ', b)
    if stats['errors']:
        print('\nerrors: {}'.format(len(stats['errors'])))
        for e in stats['errors'][:5]:
            print('   ', e)

    if dry_run:
        print('\nDRY RUN -- nothing written. Re-run without --dry-run to produce the clean copy.')
        return

    with io.open(LINKAGE, 'w', encoding='utf-8', newline='') as fh:
        w = csv.writer(fh)
        w.writerow(['case_id', 'original_patient_name', 'original_patient_id', 'original_birth_date'])
        for cid in sorted(linkage, key=lambda x: (len(x), x)):
            r = linkage[cid]
            w.writerow([cid, r.get('PatientName', ''), r.get('PatientID', ''), r.get('PatientBirthDate', '')])

    print('\nclean copy : {}'.format(OUTPUT))
    print('linkage    : {}'.format(LINKAGE))
    print('\nThe linkage file is stored outside the project folder deliberately.')
    print('Keep it access-restricted. It is the only way back to a patient identity.')


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description='De-identify Rizgary lumbar MRI DICOM studies.')
    ap.add_argument('--dry-run', action='store_true', help='report what would change, write nothing')
    process(dry_run=ap.parse_args().dry_run)

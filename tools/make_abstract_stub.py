#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Generate metadata-and-abstract stub PDFs for papers whose full text cannot be obtained.

Matches the house format already used in papers_pdf/ for paywalled records: a single
page carrying the bibliographic record and the published abstract, so the library has a
readable placeholder and JabRef has something to open.

These are NOT the papers. Each is clearly banded as a stub so it cannot be mistaken for
the full text.
"""
import io
import os

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'papers_pdf')

RECORDS = [
    dict(
        idx=111, year=1968, first='Cohen',
        slug='Weighted_Kappa_Nominal_Scale_Agreement_with_Provision_for_Scaled',
        title='Weighted kappa: Nominal scale agreement with provision for scaled disagreement or partial credit',
        authors='Cohen J.',
        venue='Psychological Bulletin', vol='70', issue='4', pages='213-220',
        doi='10.1037/h0026256',
        url='https://psycnet.apa.org/doiLanding?doi=10.1037%2Fh0026256',
        reason='Publisher paywall (APA PsycNET). Full text not retrievable.',
        role='Origin of the weighted kappa statistic. Chapter 3 adopts quadratic-weighted '
             'kappa as a primary agreement metric because severity grades are ordinal, so '
             'a one-grade disagreement must not be penalised as heavily as a two-grade one.',
        abstract=(
            'A previously described coefficient of agreement for nominal scales, kappa, treats '
            'all disagreements equally. A generalization to weighted kappa (Kw) is presented. '
            'The Kw provides for the incorporation of ratio-scaled degrees of disagreement (or '
            'agreement) to each of the cells of the k x k table of joint nominal scale '
            'assignments such that disagreements of varying gravity (or agreements of varying '
            'degree) are weighted accordingly. Although providing for partial credit, Kw is '
            'fully chance corrected. Its sampling characteristics and procedures for hypothesis '
            'testing and setting confidence limits are given. Under certain conditions, Kw '
            'equals product-moment r.'),
    ),
    dict(
        idx=112, year=2004, first='Warfield',
        slug='STAPLE_Simultaneous_Truth_and_Performance_Level_Estimation',
        title='Simultaneous truth and performance level estimation (STAPLE): an algorithm for the validation of image segmentation',
        authors='Warfield SK, Zou KH, Wells WM.',
        venue='IEEE Transactions on Medical Imaging', vol='23', issue='7', pages='903-921',
        doi='10.1109/TMI.2004.828354',
        url='https://ieeexplore.ieee.org/document/1309714/',
        reason='IEEE Xplore subscription required. An author manuscript is available at PMC3788853 '
               '(PMID 15250643) if institutional access is unavailable.',
        role='The standard method for fusing several raters into one reference standard. Relevant '
             'to Chapter 3 wherever multiple readers contribute to the reference standard, and to '
             'the harmonised central-canal regrading proposed for external validation.',
        abstract=(
            'Characterizing the performance of image segmentation approaches has been a persistent '
            'challenge. Performance analysis is important since segmentation algorithms often have '
            'limited accuracy and precision. Interactive drawing of the desired segmentation by '
            'human raters has often been the only acceptable approach, and yet suffers from '
            'intra-rater and inter-rater variability. Automated algorithms have been sought in '
            'order to remove the variability introduced by manual raters, but such algorithms must '
            'be assessed to ensure they are suitable for the task. The performance of raters '
            '(human or algorithmic) generating segmentations of medical images has been difficult '
            'to quantify because of the difficulty of obtaining or estimating a known true '
            'segmentation for clinical data. The authors present an expectation-maximization '
            'algorithm for simultaneous truth and performance level estimation (STAPLE). The '
            'algorithm considers a collection of segmentations and computes a probabilistic '
            'estimate of the true segmentation and a measure of the performance level represented '
            'by each segmentation.'),
    ),
    dict(
        idx=113, year=2006, first='Vickers',
        slug='Decision_Curve_Analysis_A_Novel_Method_for_Evaluating_Prediction_Models',
        title='Decision curve analysis: a novel method for evaluating prediction models',
        authors='Vickers AJ, Elkin EB.',
        venue='Medical Decision Making', vol='26', issue='6', pages='565-574',
        doi='10.1177/0272989X06295361',
        url='https://journals.sagepub.com/doi/10.1177/0272989X06295361',
        reason='SAGE paywall. An author manuscript is freely available at PMC2577036.',
        role='Origin of decision curve analysis. Chapter 3 lists DCA among the evaluation methods '
             'for judging whether a model is clinically useful, not merely discriminative, which '
             'matters because accuracy is close to uninformative under this severity distribution.',
        abstract=(
            'Diagnostic and prognostic models are typically evaluated with measures of accuracy '
            'that do not address clinical consequences. Decision-analytic techniques allow '
            'assessment of clinical outcomes, but often require collection of additional '
            'information, and may be cumbersome to apply to models that yield a continuous result. '
            'The authors sought a method for evaluating and comparing prediction models that '
            'incorporates clinical consequences, requires only the data set on which the models '
            'are tested, and can be applied to models that have either continuous or dichotomous '
            'results. The authors describe decision curve analysis, a simple, novel method of '
            'evaluating predictive models. They start by assuming that the threshold probability '
            'of a disease or event at which a patient would opt for treatment is informative of '
            'how the patient weighs the relative harms of a false-positive and a false-negative '
            'prediction. This theoretical relationship is then used to derive the net benefit of '
            'the model across different threshold probabilities. Plotting net benefit against '
            'threshold probability yields the decision curve. Decision curve analysis identifies '
            'the range of threshold probabilities in which a model is of value, the magnitude of '
            'benefit, and which of several models is optimal.'),
    ),
    dict(
        idx=114, year=2024, first='Collins',
        slug='TRIPOD+AI_Statement_Updated_Guidance_for_Reporting_Clinical_Prediction',
        title='TRIPOD+AI statement: updated guidance for reporting clinical prediction models that use regression or machine learning methods',
        authors=('Collins GS, Moons KGM, Dhiman P, Riley RD, Beam AL, Van Calster B, Ghassemi M, '
                 'Liu X, Reitsma JB, van Smeden M, Boulesteix AL, Camaradou JC, Celi LA, Denaxas S, '
                 'Denniston AK, Glocker B, Golub RM, Harvey H, Heinze G, Hoffman MM, Kengne AP, '
                 'Lam E, Lee N, Loder EW, Maier-Hein L, Mateen BA, McCradden MD, Oakden-Rayner L, '
                 'Ordish J, Parnell R, Rose S, Singh K, Wynants L, Logullo P.'),
        venue='BMJ', vol='385', issue='', pages='e078378',
        doi='10.1136/bmj-2023-078378',
        url='https://www.ncbi.nlm.nih.gov/pmc/articles/PMC11019967/',
        reason=('Full text is in fact open access at PMC11019967. NOTE: the PMC record '
                'PMC11025451 that was originally consulted is a CORRECTION notice '
                '(doi:10.1136/bmj.q902) amending author affiliations, not the article itself. '
                'A Korean translation is held locally as record 115.'),
        role='The reporting standard Chapter 3 commits to for prediction-model work. Supersedes '
             'TRIPOD 2015 by adding guidance on machine learning, fairness, open science and '
             'patient involvement.',
        abstract=(
            'The TRIPOD+AI statement provides updated reporting recommendations for studies '
            'developing or evaluating clinical prediction models, whether they use regression or '
            'machine learning methods. It supersedes the original 2015 TRIPOD statement, which '
            'predated the widespread use of artificial intelligence in prediction modelling. '
            'TRIPOD+AI presents a harmonised, method-agnostic framework rather than separate '
            'guidance for statistical and machine learning approaches. The checklist contains 27 '
            'items spanning title, abstract, introduction, methods, results and discussion, with '
            'specific guidance for reporting in abstracts. Key additions relative to TRIPOD 2015 '
            'emphasise fairness considerations, open science practices including data and code '
            'availability, and patient and public involvement. The aim is to improve the '
            'transparency, completeness and appraisability of prediction model studies, to reduce '
            'research waste and bias, and to support safe implementation across diverse '
            'healthcare contexts.'),
    ),
    dict(
        idx=115, year=2025, first='Collins_KoreanTranslation',
        slug='TRIPOD+AI_Statement_Korean_Translation_Ewha_Medical_Journal',
        title='TRIPOD+AI statement: updated guidance for reporting clinical prediction models that use regression or machine learning methods: a Korean translation',
        authors=('Collins GS, Moons KGM, Dhiman P, Riley RD, Beam AL, Van Calster B, et al. '
                 'Korean translation by Huh S (Hallym University); proofreading by Seo YJ (InfoLumi); '
                 'back-translation by Yoo JJ (Soonchunhyang University Bucheon Hospital), '
                 'confirmed by Collins GS.'),
        venue='Ewha Medical Journal', vol='48', issue='3', pages='e48',
        doi='10.12771/emj.2025.00668',
        url='https://e-emj.org/upload/pdf/emj-2025-00668.pdf',
        reason=('Full text held locally but published in KOREAN. This English-language record '
                'supplies the abstract of the original English statement so the item is usable in '
                'the library. NOT an independent work: it is an authorised Korean translation of '
                'record 114 (Collins et al., BMJ 2024;385:e078378), produced with the permission '
                'of the TRIPOD Group.'),
        role=('Cite the English original (record 114) for the reporting standard itself. This '
              'translation is catalogued for completeness only and should not be cited as a '
              'separate source, since doing so would misrepresent one guideline as two.'),
        abstract=(
            '[English abstract of the original statement, which this document translates.] '
            'The TRIPOD+AI statement provides updated reporting recommendations for studies '
            'developing or evaluating clinical prediction models, whether they use regression or '
            'machine learning methods. It supersedes the original 2015 TRIPOD statement. '
            'TRIPOD+AI presents a harmonised, method-agnostic framework rather than separate '
            'guidance for statistical and machine learning approaches. The checklist contains 27 '
            'items spanning title, abstract, introduction, methods, results and discussion. Key '
            'additions emphasise fairness considerations, open science practices, and patient and '
            'public involvement. The aim is to improve transparency and completeness of prediction '
            'model studies, reduce research waste and bias, and support safe implementation.'),
    ),
]


def build(rec):
    name = '{}_{}_{}_{}.pdf'.format(rec['idx'], rec['year'], rec['first'], rec['slug'])
    path = os.path.join(OUT, name)

    ss = getSampleStyleSheet()
    band = ParagraphStyle('band', parent=ss['Normal'], fontSize=9.5, leading=13,
                          textColor=colors.white, backColor=colors.HexColor('#8B0000'),
                          borderPadding=6, spaceAfter=10)
    h = ParagraphStyle('h', parent=ss['Heading1'], fontSize=13, leading=17, spaceAfter=8)
    lab = ParagraphStyle('lab', parent=ss['Normal'], fontSize=8.5, leading=11,
                         textColor=colors.HexColor('#555555'), spaceBefore=6)
    body = ParagraphStyle('body', parent=ss['Normal'], fontSize=10, leading=14, spaceAfter=2)
    abst = ParagraphStyle('abst', parent=ss['Normal'], fontSize=10, leading=14.5,
                          spaceBefore=4, spaceAfter=8)
    foot = ParagraphStyle('foot', parent=ss['Normal'], fontSize=8, leading=11,
                          textColor=colors.HexColor('#777777'), spaceBefore=14)

    doc = SimpleDocTemplate(path, pagesize=A4,
                            leftMargin=22 * mm, rightMargin=22 * mm,
                            topMargin=18 * mm, bottomMargin=18 * mm,
                            title=rec['title'], author=rec['authors'][:200],
                            subject='Metadata and abstract record - full text not held')

    citation = '{}. <i>{}</i>'.format(rec['venue'], '')
    bits = [rec['venue']]
    if rec['vol']:
        bits.append('vol. ' + rec['vol'])
    if rec['issue']:
        bits.append('no. ' + rec['issue'])
    if rec['pages']:
        bits.append('pp. ' + rec['pages'])
    bits.append(str(rec['year']))
    citation = ', '.join(bits)

    flow = [
        Paragraph('METADATA &amp; ABSTRACT RECORD &mdash; FULL TEXT NOT HELD IN THIS LIBRARY.'
                  ' This page is a catalogue placeholder, not the published article.', band),
        Paragraph('Inventory Record #{}'.format(rec['idx']), lab),
        Paragraph(rec['title'], h),
        Paragraph('<b>Authors</b>', lab), Paragraph(rec['authors'], body),
        Paragraph('<b>Published in</b>', lab), Paragraph(citation, body),
        Paragraph('<b>DOI</b>', lab), Paragraph(rec['doi'], body),
        Paragraph('<b>Source</b>', lab), Paragraph(rec['url'], body),
        Paragraph('<b>Why the full text is not held</b>', lab), Paragraph(rec['reason'], body),
        Paragraph('<b>Role in this programme</b>', lab), Paragraph(rec['role'], body),
        Spacer(1, 6),
        Paragraph('<b>ABSTRACT</b>', lab),
        Paragraph(rec['abstract'], abst),
        Paragraph('Abstract reproduced from the publisher record for identification and '
                  'cataloguing. Generated for the Rizgary lumbar spine research programme '
                  '(Dr. Polla Fattah). Obtain the full text before citing substantive content.',
                  foot),
    ]
    doc.build(flow)
    return name, os.path.getsize(path)


if __name__ == '__main__':
    for r in RECORDS:
        n, s = build(r)
        print('  {:>6,} bytes  {}'.format(s, n))
    print('\n{} stub records written to {}'.format(len(RECORDS), OUT))

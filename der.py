#!/usr/bin/env python3

"""
Runs Diarization Error Rate (DER) calculation

Usage: python3 der.py ref_diar.json hyp_diar.json
       where *_diar.json is a serialized list of 3-tuples of:
       (speaker ID, start time, end time)
"""

import json
import logging
from pyannote.core import Segment, Timeline, Annotation
from pyannote.metrics.diarization import DiarizationErrorRate
import sys
logging.basicConfig(level=logging.DEBUG)

def convert_to_pyannote(diar, filename=None):
    annotation = Annotation(uri=filename)
    for (sid, offset, end) in diar:
        annotation[Segment(offset, end)] = sid
    return annotation

def run_der(argv):
    if len(argv) != 3:
        logging.error("Must specify ref_diar.json and hyp_diar.json")
        sys.exit(-1)

    # Load reference (ground truth)
    try:
        ref = json.load(open(argv[1]))
    except Exception as inst:
        logging.error("Run-time error={} while loading a ref file={}".format(
                inst, argv[1]))

    # hypothesis (diarization result from your algorithm)
    try:
        hyp = json.load(open(argv[2]))
    except Exception as inst:
        logging.error("Run-time error={} while loading a hyp file={}".format(
                inst, argv[2]))

    ref = convert_to_pyannote(ref, filename=argv[2])
    hyp = convert_to_pyannote(hyp, filename=argv[2])

    # Calculate DER and print.
    metric = DiarizationErrorRate()
    error = metric(ref, hyp, detailed=True)
    logging.info("DER={:.3f}".format(error['diarization error rate']))
    logging.info("Detailed DER info=\n{}".format(error))

    # Detailed report
    report = metric.report(display=False)
    logging.info(report)


    logging.info("Done!")

if __name__ == '__main__':
    run_der(sys.argv)

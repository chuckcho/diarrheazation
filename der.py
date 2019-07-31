#!/usr/bin/env python3

"""
Runs Diarization Error Rate (DER) calculation

Usage: python3 der.py ref_diar.json hyp_diar.json
       where *_diar.json is a serialized list of 3-tuples of:
       (speaker ID, start time, end time)
"""

import json
import logging
import calder as der
#import simpleder as der
import sys
logging.basicConfig(level=logging.DEBUG)

def a_bit_of_massaging(x):
    """ Converts a list of lists (of mixed numeric types) into a list of tuples
    (of float only)
    """
    return [ (e[0], float(e[1]), float(e[2])) for e in x ]

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

    # DER is picky as it requires a list of tuples, but json converts tuples
    # into lists, also DER assumes all numbers are in float type (not int).
    # Hence, a bit of massaging is needed
    ref, hyp = a_bit_of_massaging(ref), a_bit_of_massaging(hyp)

    # Calculate DER and print.
    error = der.DER(ref, hyp)
    logging.info("DER={:.3f}".format(error))
    logging.info("Done!")

if __name__ == '__main__':
    run_der(sys.argv)

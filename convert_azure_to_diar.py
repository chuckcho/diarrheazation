#!/usr/bin/env python3

"""
Converts Azure STT output to a diarization file (which will be eventually
consumed by DER calculation script)

Usage: python3 convert_azure_to_diar.py input_azure_out.json output_diar.json
"""

import json
import logging
import sys
logging.basicConfig(level=logging.DEBUG)

def parse_azure_stt_results(results, ignore_null=True):
    """ Parse Azure STT result json file, and optionally ignore null as an
    SpeakerId.
    """
    diar = []
    assert len(results["AudioFileResults"]) == 1
    seg_results = results["AudioFileResults"][0]["SegmentResults"]
    for seg in seg_results:
        sid = seg["SpeakerId"]
        if ignore_null and sid == None:
            continue
        offset = seg["Offset"] / 1.e6
        end = offset + seg["Duration"] / 1.e6
        diar_seg = (sid, offset, end)
        diar.append(diar_seg)
    return diar

def sort_diar(diar):
    """ Sort by the offset/start time
    """
    return sorted(diar, key=lambda x: x[2])

def check_overlap(diar):
    """ Check if intervals overlap, and if so, warn
    """
    if len(diar) <= 1:
        logging.warn("Trivially small set (len<=1)")
        return
    for d1, d2 in zip(diar, diar[1:]):
        if d1[2] > d2[1]:
            logging.warn("d1=({},{}), d2=({},{}): There's an overlap! " \
                    "Panic!".format(d1[1], d1[2], d2[1], d2[2]))
    return

def round_diar(diar, dec_pt=1):
    """ Round diarization times at the given decimal point
    """
    diar2 = []
    for d in diar:
        diar2.append((d[0], round(d[1], dec_pt), round(d[2], dec_pt)))
    return diar2


def convert(argv):
    if len(argv) != 3:
        logging.error("Must specify input.json and output.json")
        sys.exit(-1)
    try:
        tr = json.load(open(argv[1]))
    except Exception as inst:
        logging.error("Run-time error={} while loading an input file={}".format(
                inst, argv[1]))

    diar = parse_azure_stt_results(tr)

    # Make sure diarization results are sorted by the offset
    diar = sort_diar(diar)

    # SimpleDER hates, oops, ignores overlaps. Better to check beforehand.
    # Azure probably doesn't support overlapping diarization anyway.
    check_overlap(diar)

    # Remove long decimal points
    diar = round_diar(diar)

    try:
        with open(argv[2], 'w') as fout:
            json.dump(diar, fout)
    except Exception as inst:
        logging.error("Run-time error={} while saving an output file={}".format(
                inst, argv[2]))

    logging.info("Done!")

if __name__ == '__main__':
    convert(sys.argv)

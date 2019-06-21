#!/usr/bin/env python3

"""
Converts Azure/Google STT output to a diarization file (which will be eventually
consumed by DER calculation script)
This will automatically detect which STT service produced the transcript json
file.

Usage: python3 convert_to_diar.py input_out.json output_diar.json
"""

import json
import logging
import sys
logging.basicConfig(level=logging.DEBUG)

def parse_stt_results(results):
    if "AudioFileResults" in results:
        logging.info("Azure transcript detected.")
        return parse_azure_stt_results(results)
    elif "results" in results:
        logging.info("Google transcript detected.")
        return parse_google_stt_results(results)
    else:
        logging.error("Currently supported STT services: Azure or Google. " \
                "Panic!")
        sys.exit(-3)

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
        offset = seg["Offset"] / 1.e7
        end = offset + seg["Duration"] / 1.e7
        diar_seg = (sid, offset, end)
        diar.append(diar_seg)
    return diar

def parse_google_stt_results(results):
    """ Parse Google Cloud STT result json file
    """
    diar = []
    for res in results["results"]:
        assert "alternatives" in res
        alts = res["alternatives"]
        assert len(alts) == 1
        assert "words" in alts[0]
        assert len(alts[0]["words"]) >= 1
        for word in alts[0]["words"]:
            if "speakerTag" not in word:
                continue

            start_time = word["startTime"]
            assert start_time.endswith("s")
            start_time = float(start_time[:-1])

            end_time = word["endTime"]
            assert end_time.endswith("s")
            end_time = float(end_time[:-1])

            speaker_tag = str(word["speakerTag"])

            diar_seg = (speaker_tag, start_time, end_time)
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
        if d1[1] > d2[1]:
            logging.error("d1=({},{}), d2=({},{}): Sort timelines first! " \
                    "Stop!".format(d1[1], d1[2], d2[1], d2[2]))
            eye.exit(-2)
        if d1[2] > d2[1]:
            logging.warn("d1=({},{}), d2=({},{}): There's an overlap! " \
                    "Panic!".format(d1[1], d1[2], d2[1], d2[2]))
    return

def round_diar(diar, dec_pt=2):
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

    # Extract speaker IDs and time intervals
    diar = parse_stt_results(tr)

    # Make sure diarization results are sorted by the offset
    diar = sort_diar(diar)

    # Remove long decimal points
    diar = round_diar(diar)

    # SimpleDER hates, oops, ignores overlaps. Better to check beforehand.
    # Azure probably doesn't support overlapping diarization anyway.
    check_overlap(diar)

    try:
        with open(argv[2], 'w') as fout:
            json.dump(diar, fout)
    except Exception as inst:
        logging.error("Run-time error={} while saving an output file={}".format(
                inst, argv[2]))

    logging.info("Done!")

if __name__ == '__main__':
    convert(sys.argv)

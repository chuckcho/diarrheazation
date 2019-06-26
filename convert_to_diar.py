#!/usr/bin/env python3

"""
Converts Azure/Google STT output to a diarization file (which will be eventually
consumed by DER calculation script)
This will automatically detect which STT service produced the transcript json
file.

Usage: python3 convert_to_diar.py input_out.json output_diar.json
"""

import argparse
import json
import logging
import sys
logging.basicConfig(level=logging.DEBUG)

def parse_stt_results(results, treat_null_as="ignore"):
    if "AudioFileResults" in results:
        logging.info("Azure transcript detected.")
        return parse_azure_stt_results(results, treat_null_as)
    elif "results" in results:
        logging.info("Google transcript detected.")
        return parse_google_stt_results(results)
    else:
        logging.error("Currently supported STT services: Azure or Google. " \
                "Panic!")
        sys.exit(-3)

def parse_azure_stt_results(results, treat_null_as="ignore"):
    """ Parse Azure STT result json file, and optionally ignore null as an
    SpeakerId.
        treat_null_as=="ignore": ignore null
        treat_null_as=="prev": match null speaker as the last speaker
        treat_null_as=="next": match null speaker as the immediate next speaker
    """

    treat_null_as = treat_null_as.lower()
    diar = []
    assert len(results["AudioFileResults"]) == 1
    seg_results = results["AudioFileResults"][0]["SegmentResults"]
    for seg in seg_results:
        sid = seg["SpeakerId"]
        if sid == None:
            if treat_null_as.startswith("i"):
                continue
            # For prev/next speakers, add a marker with P or N for now.
            # At a second pass, assign real speaker IDs for these markers
            elif treat_null_as.startswith("p"):
                sid = "_P_"
            elif treat_null_as.startswith("n"):
                sid = "_N_"
            else:
                logging.error("Invalid treat_null_as value. Exitting...")
                sys.exit(-4)
        offset = seg["Offset"] / 1.e7
        end = offset + seg["Duration"] / 1.e7
        diar_seg = (sid, offset, end)
        diar.append(diar_seg)

    if treat_null_as.startswith("i"):
        return diar
    elif treat_null_as.startswith("p"):
        # Forward pass to replace "_P_" with a real speaker ID
        diar2 = []
        psid = None
        for d in diar:
            (sid, offset, end) = d
            if sid == "_P_":
                if psid:
                    sid = psid
                    # sid <- psid
                    diar2.append((sid, offset, end))
                else:
                    logging.warn("Previous speaker unavailable. Ignoring...")
                    continue
            else:
                psid = sid
                # Just, as is.
                diar2.append(d)
        return diar2
    elif treat_null_as.startswith("n"):
        # Backward pass to replace "_N_" with a real speaker ID
        diar2 = []
        nsid = None
        for d in reversed(diar):
            (sid, offset, end) = d
            if sid == "_N_":
                if nsid:
                    sid = nsid
                    # sid <- nsid
                    diar2.append((sid, offset, end))
                else:
                    logging.warn("Next speaker unavailable. Ignoring...")
                    continue
            else:
                nsid = sid
                # Just, as is.
                diar2.append(d)
        # Now, reverse the result
        diar2.reverse()
        return diar2

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

def trim_diar(diar, start_time, end_time, offset_start=False):
    """ Trim diarization timelines given start,end times and a flag to offset
    the start_time (start_time becomes 0.0 in the output)
    """

    # Limit start/end times
    if not start_time:
        start_time = 0.0
    if not end_time:
        end_time = max(diar, key=lambda x:x[2])[2]

    # argparse may have passed strings not numerics
    start_time, end_time = float(start_time), float(end_time)

    # Sanity check
    assert start_time < end_time

    # Setting offset
    if offset_start:
        offset = start_time
    else:
        offset = 0.0

    diar2 = []

    for d in diar:
        # If the start of the interval is later than the specified end time,
        # ignore
        if d[1] >= end_time:
            continue
        # If the end of the interval is earlier than the specified start time,
        # ignore
        if d[2] <= start_time:
            continue

        # Put together a timeline
        d_start = max(d[1], start_time) - offset
        d_end = min(d[2], end_time) - offset
        diar2.append( (d[0], d_start, d_end) )

    return diar2

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

def convert():
    parser = argparse.ArgumentParser()
    parser.add_argument("input", help="Input transcription json file")
    parser.add_argument("output", help="Output diarization json file")
    parser.add_argument("-s", "--start-time", help="Start time in second for " \
            "processing")
    parser.add_argument("-e", "--end-time", help="End time in second for " \
            "processing")
    parser.add_argument("-o", "--offset-start", help="Offset start time.",
            action="store_true")
    parser.add_argument("-n", "--treat-null-as", help="How to treat Azure's " \
            "'null' speaker ID. One of 'ignore', 'previous', or 'next'",
            default="i")
    args = parser.parse_args()

    try:
        tr = json.load(open(args.input))
    except Exception as inst:
        logging.error("Run-time error={} while loading an input file={}".format(
                inst, args.input))

    # Extract speaker IDs and time intervals
    diar = parse_stt_results(tr, args.treat_null_as)

    # Slice and dice timelines if specified
    if args.start_time or args.end_time:
        diar = trim_diar(diar,
                start_time=args.start_time,
                end_time=args.end_time,
                offset_start=args.offset_start)

    # Make sure diarization results are sorted by the offset
    diar = sort_diar(diar)

    # Remove long decimal points
    diar = round_diar(diar)

    # SimpleDER hates, oops, ignores overlaps. Better to check beforehand.
    # Azure probably doesn't support overlapping diarization anyway.
    check_overlap(diar)

    try:
        with open(args.output, 'w') as fout:
            json.dump(diar, fout)
    except Exception as inst:
        logging.error("Run-time error={} while saving an output file={}".format(
                inst, args.output))

    logging.info("Done!")

if __name__ == '__main__':
    convert()

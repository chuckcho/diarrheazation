# Diarrheazation

A "quick" and "dirty" tool for diarization, hence the name.

## Requirements
1. [SimpleDER](https://github.com/wq2012/SimpleDER)

Run `pip3 install -r requirementx.txt` to install requirements.

## Usage
1. Convert Azure or Google STT results by running `convert_to_diar.py input.json diar.json`
2. Run evaluation by `python3 der.py gt_diar.json diar.json` where `gt_diar.json` is a ground-truth diarization file

## An example
1. Run:
```
python3 convert_to_diar.py sample/kip_azure_out.json sample/kip_azure_diar.json
```
2. Run (note that this GT diarization is a made-up example hence inaccurate. it's there for an illustration purpose):
```
python3 der.py sample/kip_gt_diar_fake.json sample/kip_azure_diar.json
```
3. The above should yield a caculated DER of 0.269 or 26.9%.

## Another example
For now, Google allows up to a minute of audio for their beta version of diarization. Hence, 00:01:00 to 00:01:59 of original audio was passed to Google to get [the result](./sample/kip_google_out_s60_e119.json).
The following will convert and trim Azure results to compensate for this trimming/offsetting (each additional arguments meaning start time = 60 sec. end time = 119 sec. and offseting the start time)
```
python3 convert_to_diar.py sample/kip_azure_out.json sample/kip_azure_diar_s60_e119.json -s 60 -e 119 -o
```

With that, we can compare diarization results between Google and Azure (how well they match up -- 0.0 if they yield exactly same diarization results).
```
# Convert Google results
python3 convert_to_diar.py sample/kip_google_out_s60_e119.json sample/kip_google_diar_s60_e119.json

# Calculate DER for Azure results
python3 der.py sample/kip_gt_diar_s60_e119.json sample/kip_azure_diar_s60_e119.json

# Calculate DER for Google results
python3 der.py sample/kip_gt_diar_s60_e119.json sample/kip_google_diar_s60_e119.json
```
DER for Azure should be 88.3% and DER for Google should be 51.5%.

## Visualization / listening to diarized segments
A popular open-source audio tool Audacity can handle "label tracks" for visualization and playing predefined segments.
The following will convert diariazation json file into a "label track" file that can be loaded in Audacity. (`jq` is required)
```
cat sample/kip_azure_diar_s60_e119.json | jq -r '.[] | [.[1,2,0]] | @tsv' > sample/kip_azure_diar_s60_e119.tsv
```

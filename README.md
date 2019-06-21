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
python3 der.py sample/kip_gt_diar.json sample/kip_azure_diar.json
```
3. The above should yield a caculated DER of 0.269 or 26.9%.

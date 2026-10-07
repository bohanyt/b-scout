"""Dev-only candidate tuning; never evaluate held-out or claim retained evidence."""
import argparse
from dataclasses import asdict, replace
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))


def main():
    import av
    from bscout.common import canonical,sha256
    from bscout.corpus import load_corpus
    from bscout.frames import read_id
    from bscout.ledger import DecodeConfig,presented,select_video
    from bscout.regional import RegionalConfig,TileSignals
    from bscout.evaluation_b import evaluate_fixture
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--media",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    spec,truth,frozen=load_corpus()
    report={"scope":"dev-only candidate tuning; no retained-evidence success claims", "T1":frozen,"trials":[]}
    for threshold in (32.0,48.0,64.0):
        config=replace(RegionalConfig(),short_delta=threshold,stable_delta=threshold)
        trial={"configuration":asdict(config),"configuration_sha256":config.sha256,"fixtures":[]}
        for fixture in truth["fixtures"]:
            if fixture["split"] != "dev":continue
            source=args.media/fixture["filename"]
            tracker=TileSignals(config);candidates=[];ids={};start=time.perf_counter();before=sha256(source)
            with av.open(str(source),options=dict(DecodeConfig().demux_options)) as container:
                stream=select_video(container,config=DecodeConfig())
                for position,frame in enumerate(presented(container,stream)):
                    ids[position]=read_id(frame,spec["harness"])
                    closed,_=tracker.observe(frame,position);candidates.extend(closed)
            candidates.extend(tracker.finish())
            evaluation=evaluate_fixture(fixture,candidates,[],ids,spec["harness"]["region_xywh"],known_timing=fixture["name"]!="no_timing")
            trial["fixtures"].append({"id":fixture["id"],"split":"dev","scanned_frames":len(ids),
                                      "source_sha256":before,"source_unchanged":sha256(source)==before,
                                      "candidate_count":evaluation["candidate_count"],
                                      "non_harness_candidate_count":evaluation["non_harness_candidate_count"],
                                      "noise_count":evaluation["false_or_noise_candidate_count"],
                                      "easy_candidate_metrics":evaluation["metrics"]["easy"],
                                      "challenge_candidate_metrics":evaluation["metrics"]["challenge"],
                                      "elapsed_seconds":time.perf_counter()-start})
            print(f"dev threshold={threshold:g} {fixture['id']} candidates={len(candidates)} easy_misses={evaluation['metrics']['easy']['candidate_miss_ids']}",flush=True)
        report["trials"].append(trial)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    with args.out.open("xb") as output:output.write(canonical(report))


if __name__=="__main__":main()

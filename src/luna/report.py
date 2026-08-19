from dataclasses import asdict

def build_report(tracks, validations, duplicate_groups, artwork, rename_plan):
    missing=sum(not track.title or not track.artist or not track.album for track in tracks)
    artwork_missing=sum(not item.has_artwork for item in artwork)
    suspicious=sum(1 for item in rename_plan if item.status=="change")
    wasted=sum(track.path.stat().st_size for group in duplicate_groups for track in group.tracks[1:])
    return {"tracks":len(tracks),"formats":sorted({track.path.suffix.lower() for track in tracks}),"metadata_issues":sum(not x.valid for x in validations),"missing_core_metadata":missing,"duplicate_groups":len(duplicate_groups),"duplicate_wasted_bytes":wasted,"missing_artwork":artwork_missing,"suspicious_filenames":suspicious,"proposed_renames":suspicious}

def render_report(report):
    return "\n".join(["Luna library health",f"Tracks: {report['tracks']}",f"Formats: {', '.join(report['formats']) or 'none'}",f"Metadata issues: {report['metadata_issues']}",f"Duplicate groups: {report['duplicate_groups']}",f"Estimated duplicate waste: {report['duplicate_wasted_bytes']} bytes",f"Missing artwork: {report['missing_artwork']}",f"Filename suggestions: {report['proposed_renames']}"])

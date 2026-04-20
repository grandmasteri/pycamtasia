"""Speed changes with full timeline re-sync.

Ported from the tested camtasia_stretch.py script that successfully
rescaled a project from 1.07x audio to 1.0x on 2026-04-08.
"""

from __future__ import annotations

from fractions import Fraction
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from camtasia.project import Project

from camtasia.timing import parse_scalar, scalar_to_string


def _frac(value: int | float | str) -> Fraction:
    """Parse a tick value that may be int, float, or string fraction."""
    if isinstance(value, str) and "/" in value:
        return Fraction(value)
    return Fraction(value)


def _scale_tick(value: int | float | str, factor: Fraction) -> int | str:
    """Scale a tick value by *factor*, preserving type for fraction strings."""
    f = _frac(value) * factor
    if isinstance(value, str) and "/" in value:
        return f"{f.numerator}/{f.denominator}" if f.denominator != 1 else int(f)
    return round(float(f))


def _scale_clip_timing(clip: dict[str, Any], factor: Fraction) -> None:
    """Scale start, duration, and mediaDuration of a clip on the timeline."""
    clip["start"] = _scale_tick(clip["start"], factor)
    clip["duration"] = _scale_tick(clip["duration"], factor)
    # Scale mediaDuration for regular clips (StitchedMedia/Group handle their own)
    if clip.get("_type") not in ("StitchedMedia", "Group", "UnifiedMedia", "IMFile", "ScreenIMFile") and "mediaDuration" in clip:
        clip["mediaDuration"] = _scale_tick(clip["mediaDuration"], factor)
    # Scale effect start/duration times
    for effect in clip.get("effects", []):
        if "start" in effect:
            effect["start"] = _scale_tick(effect["start"], factor)
        if "duration" in effect:
            effect["duration"] = _scale_tick(effect["duration"], factor)


def _adjust_scalar(clip: dict[str, Any], factor: Fraction) -> None:
    """For speed-changed clips, adjust scalar: new = old * factor."""
    old = parse_scalar(clip.get("scalar", 1))
    new = old * factor
    clip["scalar"] = scalar_to_string(new)


def _has_speed_change(clip: dict[str, Any]) -> bool:
    """Check if a clip has clipSpeedAttribute set."""
    return (
        clip.get("metadata", {})
        .get("clipSpeedAttribute", {})
        .get("value") is True
    )


def _process_clip(clip: dict[str, Any], factor: Fraction) -> None:
    """Recursively scale a clip and its nested structures."""
    ctype = clip.get("_type", "")
    _scale_clip_timing(clip, factor)

    if _has_speed_change(clip):
        _adjust_scalar(clip, factor)
        # Recalculate mediaDuration from new duration/scalar to maintain invariant
        if ctype not in ("StitchedMedia", "Group", "UnifiedMedia", "IMFile", "ScreenIMFile"):
            new_scalar = _frac(clip.get("scalar", 1))
            if new_scalar != 0:
                md = _frac(clip["duration"]) / new_scalar
                clip["mediaDuration"] = int(md) if md == int(md) else f"{md.numerator}/{md.denominator}"

    if ctype == "StitchedMedia":
        clip["mediaStart"] = _scale_tick(clip.get("mediaStart", 0), factor)
        clip["mediaDuration"] = _scale_tick(clip.get("mediaDuration", 0), factor)
        for inner in clip.get("medias", []):
            if inner.get('_type') == 'UnifiedMedia':
                # Let _process_clip handle UnifiedMedia path including video/audio children
                _process_clip(inner, factor)
            else:
                inner["start"] = _scale_tick(inner["start"], factor)
                inner["duration"] = _scale_tick(inner["duration"], factor)
                inner["mediaStart"] = _scale_tick(inner.get("mediaStart", 0), factor)
                inner["mediaDuration"] = _scale_tick(inner.get("mediaDuration", 0), factor)
                inner["scalar"] = clip.get("scalar", 1)
                # Only scale effects here for non-UnifiedMedia; UnifiedMedia handles its own via _process_clip
                for effect in inner.get('effects', []):
                    if 'start' in effect:
                        effect['start'] = _scale_tick(effect['start'], factor)
                    if 'duration' in effect:
                        effect['duration'] = _scale_tick(effect['duration'], factor)

    elif ctype == "Group":
        if "mediaDuration" in clip:
            clip["mediaDuration"] = _scale_tick(clip["mediaDuration"], factor)
        if "mediaStart" in clip:
            clip["mediaStart"] = _scale_tick(clip.get("mediaStart", 0), factor)
        for track in clip.get("tracks", []):
            for inner in track.get("medias", []):
                _process_clip(inner, factor)

    elif ctype == "UnifiedMedia":
        # Only scale mediaDuration for non-speed-changed clips;
        # speed-changed clips have mediaDuration invariant (handled by _adjust_scalar above)
        if 'mediaDuration' in clip and not _has_speed_change(clip):
            clip['mediaDuration'] = _scale_tick(clip['mediaDuration'], factor)
        for child_key in ("video", "audio"):
            child = clip.get(child_key)
            if child:
                _process_clip(child, factor)


def rescale_project(project_data: dict[str, Any], factor: Fraction) -> None:
    """Scale all timing values in a project by *factor*.

    Mutates *project_data* in-place. For clips with existing speed changes,
    adjusts their scalar so source-media alignment is preserved.

    Args:
        project_data: The raw project JSON dict.
        factor: Multiplicative factor for all tick values.
            Values > 1 stretch (slow down), < 1 compress (speed up).
    """
    scene = project_data["timeline"]["sceneTrack"]["scenes"][0]["csml"]

    # Scale all tracks
    for track in scene["tracks"]:
        for clip in track.get("medias", []):
            _process_clip(clip, factor)
        for tr in track.get("transitions", []):
            tr["duration"] = round(float(Fraction(tr["duration"]) * factor))

    # Scale timeline markers
    toc = project_data["timeline"].get("parameters", {}).get("toc", {})
    for kf in toc.get("keyframes", []):
        kf["time"] = round(float(Fraction(kf["time"]) * factor))
        if "endTime" in kf:
            kf["endTime"] = round(float(Fraction(kf["endTime"]) * factor))

    # Post-rescale: fix 1-tick overlaps caused by independent rounding
    for track in scene["tracks"]:
        medias = sorted(track.get("medias", []), key=lambda m: int(_frac(m.get("start", 0))))
        for i in range(len(medias) - 1):
            a_end = int(_frac(medias[i].get("start", 0))) + int(_frac(medias[i].get("duration", 0)))
            b_start = int(_frac(medias[i + 1].get("start", 0)))
            if a_end > b_start:  # overlap
                overlap = a_end - b_start
                if int(_frac(medias[i]['duration'])) > overlap:
                    medias[i]['duration'] = int(_frac(medias[i]['duration'])) - overlap
                    # Recalculate mediaDuration
                    s = _frac(medias[i].get('scalar', 1))
                    if s != 0 and medias[i].get('_type') not in ('IMFile', 'ScreenIMFile', 'StitchedMedia', 'Group', 'UnifiedMedia'):
                        md = _frac(medias[i]['duration']) / s
                        medias[i]['mediaDuration'] = int(md) if md == int(md) else f'{md.numerator}/{md.denominator}'
                    from camtasia.timeline.track import _propagate_start_to_unified
                    _propagate_start_to_unified(medias[i])


def set_audio_speed(
    project_data: dict[str, Any],
    target_speed: float = 1.0,
) -> Fraction:
    """Rescale the project so audio clips play at *target_speed*.

    Finds audio clips with a non-unity scalar, calculates the stretch
    factor needed, and calls :func:`rescale_project`.

    Args:
        project_data: The raw project JSON dict.
        target_speed: Desired audio playback speed (1.0 = normal).

    Returns:
        The stretch factor that was applied.

    Raises:
        ValueError: No speed-changed audio clips found.
    """
    target = Fraction(target_speed).limit_denominator(10_000)
    if target <= 0:
        raise ValueError(f'target_speed must be positive, got {target_speed}')
    scene = project_data["timeline"]["sceneTrack"]["scenes"][0]["csml"]

    def _find_speed_audio(clip: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]] | None:
        """Return (parent_unified_or_none, target_amfile) or None."""
        ctype = clip.get("_type", "")
        if ctype == "AMFile" and _has_speed_change(clip):
            return (clip, clip)
        if ctype == "UnifiedMedia":
            audio = clip.get("audio")
            if audio and audio.get("_type") == "AMFile" and _has_speed_change(audio):
                return (clip, audio)
        if ctype == "StitchedMedia":
            for inner in clip.get("medias", []):
                result = _find_speed_audio(inner)
                if result is not None:
                    return result
        if ctype == "Group":
            for inner_track in clip.get("tracks", []):
                for inner in inner_track.get("medias", []):
                    result = _find_speed_audio(inner)
                    if result is not None:
                        return result
        return None

    # Find the first audio clip with a speed change
    for track in scene["tracks"]:
        for clip in track.get("medias", []):
            found = _find_speed_audio(clip)
            if found is not None:
                parent_clip, target_clip = found
                current = parse_scalar(target_clip["scalar"])
                # scalar < 1 means audio was sped up; we need to stretch
                # factor = current_scalar / target_scalar
                target_scalar = Fraction(1) / target
                factor = target_scalar / current

                # Reset this clip directly: scalar=1, duration=mediaDuration
                # Save desired final state, rescale everything, then apply
                # to avoid double-scaling this clip.
                final_scalar: Any
                final_duration = target_clip["mediaDuration"]
                final_speed_attr: bool
                if target == 1:
                    final_scalar = 1
                    final_speed_attr = False
                else:
                    final_scalar = scalar_to_string(Fraction(1) / target)
                    final_speed_attr = True

                # Rescale everything (including this clip)
                rescale_project(project_data, factor)

                # Now overwrite this clip with the correct final state
                target_clip["scalar"] = final_scalar
                target_clip["duration"] = round(float(Fraction(final_duration) * Fraction(1) / target)) if target != 1 else final_duration
                target_clip["metadata"]["clipSpeedAttribute"]["value"] = final_speed_attr
                target_clip["mediaDuration"] = final_duration
                if parent_clip.get('_type') == 'UnifiedMedia' and parent_clip is not target_clip:
                    parent_clip['scalar'] = target_clip['scalar']
                    parent_clip['duration'] = target_clip['duration']
                    parent_clip['mediaDuration'] = target_clip['mediaDuration']
                    # Update parent's own clipSpeedAttribute
                    parent_clip.setdefault('metadata', {}).setdefault(
                        'clipSpeedAttribute', {'type': 'bool', 'value': False}
                    )['value'] = final_speed_attr
                    video = parent_clip.get('video')
                    if video and isinstance(video, dict):
                        video.setdefault('metadata', {}).setdefault(
                            'clipSpeedAttribute', {'type': 'bool', 'value': False}
                        )['value'] = final_speed_attr
                    from camtasia.timeline.track import _propagate_start_to_unified
                    _propagate_start_to_unified(parent_clip)
                return factor

    raise ValueError("No speed-changed audio clips found")


def rescale(project: Project, factor: float | Fraction) -> None:
    """Scale all timing in a project by factor.

    This is a convenience wrapper around rescale_project() that
    accepts a Project object.
    """
    rescale_project(project._data, Fraction(factor).limit_denominator(100000))


def normalize_audio_speed(project: Project, target_speed: float = 1.0) -> Fraction:
    """Rescale project so audio plays at target_speed.

    Returns the stretch factor applied.
    """
    return set_audio_speed(project._data, target_speed)

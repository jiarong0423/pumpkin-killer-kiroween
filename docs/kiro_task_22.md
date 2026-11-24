# Kiro task 22 - verify CC0 sound sources on the web (web allowed, files only, NO downloads)

## Why
`docs/audio_sources.md` (task 20) lists candidate CC0 music and sound-effect sources, but nothing was verified because that task had no web access. The owner wants the sources verified on the real pages
and the exact files chosen for each game event. You have web search and web fetch. You must not download any audio file: you read the pages and record what you saw.

## Do exactly this
1. Read `docs/audio_sources.md`, `docs/audio_event_map.json` (the events and what each needs) and `docs/sound_design.md`.
2. For EVERY candidate source in `docs/audio_sources.md`, open its page with web fetch and record, as you actually see it: the page title and author, the license text shown on the page (CC0 / CC-BY / other), the file list or the pack contents,
   direct file names, file formats (ogg / wav / mp3), sizes if shown, whether a login is needed to download, and the date. If a page cannot be opened, say so. Search for additional CC0 sources only for events that have no verified candidate
   (thrown shuriken whirr, thrown-shield sideways spin, dice rattle, ghost shimmer, heartbeat, a dark-fantasy music bed with a loop, a tension drone, a victory sting, a defeat sting).
   Accept only: CC0 / public domain, or a license that clearly says no attribution is required. Reject CC-BY, CC-BY-SA, CC-BY-NC, "royalty free" with conditions, and anything with an unclear license.
3. Write `docs/audio_sources_verified.md`: (a) a table of sources actually opened, with the page license text quoted in at most 10 words, `opened: yes/no`, accepted or rejected and why; (b) a table "event -> chosen file" for as many of the 30 events in the event map as can be covered, with
   the exact page URL, exact file name inside the pack, format, license, and attribution note ("none required, credit as a courtesy"); (c) the events still uncovered (these keep the synthesized fallback); (d) a download plan: the exact list of files with sizes if known, one pack per folder
   `(not published)`, and the licence file or page snapshot to keep next to each (`LICENSE_<source>.txt` with the URL, the date and the license text you saw).
4. Update `docs/audio_event_map.json` ONLY by adding a `candidate_file` field per event (do not change the existing `file`, `synth` or other fields) so the main line can wire files in later. Keep it valid JSON. Also keep `js/audio.js` unchanged.
5. Do not download or write any audio. Do not use git or shell. Do not create images.
6. Finish with a 6-line summary: how many pages you really opened, how many sources were rejected and why, how many of the 30 events are covered, and what you could not verify.

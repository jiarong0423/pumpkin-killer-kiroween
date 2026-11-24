# Halloween / magical music candidates (read from public pages, nothing downloaded, nothing heard)

Task: `docs/kiro_task_24.md`. Goal: music that feels like a wizard-school film (celesta, bells, harp, soft choir, shimmering strings, mysterious waltz) in a Halloween setting, CC0 / public domain only.

How this list was made:

- I read the pages with web fetch and wrote down only what the fetched text showed. I did not hear any file. Every statement about mood is **unverified by ear** and comes from the title, tags or description on the page.
- The fetch tool often returned only part of an OpenGameArt page (the "License(s)" and "Author" lines were missing on many pages). A page whose license line I could not read is **not accepted**, even if a search snippet or a comment says CC0. That is stated in each row.
- Verdicts: **accept** (license text and author seen), **hold** (CC0 text seen on the page but the author or file list is missing from what I could read; the main line can settle it in one look), **reject**.
- The rules in `docs/audio_sources.md` apply: CC0 / public domain only, no CC-BY, no attribution-required files.
- What we already have (`assets/audio/CREDITS.md`): Creepy Ambient Loop (epb9000), Lost in a Bad Place (congusbongus), Short Jingle (OO), Game Over dark (Robin Lamb). None of them has celesta, harp or choir.
- `docs/audio_generation_options.md` does **not exist** in this workspace (file search found nothing), so the Colab AI route is only mentioned in section (d) as an idea.

## (a) Pages opened

OGA = OpenGameArt. "n/s" = not shown in the text I could read.

| # | URL | opened | title | author / performer | license text on the page | format, file, size | length | verdict |
|---|---|---|---|---|---|---|---|---|
| 1 | https://opengameart.org/content/artifact-room | yes | Artifact Room | Fupi | "License(s): CC0" (tags: magic, mysterious, celestial choir, harp) | `Artifact.ogg` 822.4 Kb, `Artifact.flac` 2 Mb | n/s | **accept**: CC0 and author seen; tags match the brief |
| 2 | https://opengameart.org/content/haunted-track | yes | Haunted Track | Gena Sealov | "License(s): CC0"; credit "appreciated, not necessary" | `haunted_track_minor.ogg` 2.8 Mb, `.mp3` 3.3 Mb, `.flac` 27 Mb; same three for "major". The page lists `haunted_track_minor.ogg` twice, the second entry is probably the major file (page typo) | n/s | **accept**: CC0 and author seen; "spooky and slow paced" |
| 3 | https://opengameart.org/content/4-music-box-tracks | yes | 4 Music Box Tracks | n/s | "CC0. No credit required." | `4_music_box_tracks_ogg.zip` 14.2 Mb (looping oggs), `4_music_box_tracks_mid.zip` 4.1 Kb. Tracks: `musicbox1_spooky_waltz`, `musicbox2_cute_tune`, `musicbox3_sad_tune`, `musicbox4_happy_polka` | n/s | **hold**: CC0 text seen, but the author line was not in the text I got |
| 4 | https://opengameart.org/content/moonlit-lullaby-for-the-lost | yes | Moonlit Lullaby for the Lost | n/s (thanks @2DPIXX in the text) | "CC0 / Public Domain. No Rights Reserved." | file list empty in the text I got | n/s | **hold**: CC0 text seen; no author, no file names. Description: graveyard, lantern, distant church bell |
| 5 | https://opengameart.org/content/4-atmospheric-ghostly-loops | yes | 4 Atmospheric ghostly loops | Independent.nu (submitted by qubodup) | "License(s): CC0" | `independent_nu_ljudbank-atmosphere_moody.7z` 3.4 Mb | n/s | **accept** for license and author; it is a 7z, contents not visible |
| 6 | https://opengameart.org/content/lose-game-short-music-clip | yes | Lose Game Short Music Clip | Robin Lamb | "License(s): CC0" | `losegamemusic.ogg` 135.2 Kb, `losegamemusic.wav` 1.2 Mb | n/s (short clip) | **accept**, but it is not magical and we already use another Robin Lamb defeat clip |
| 7 | https://commons.wikimedia.org/wiki/File:Erik_Satie_-_gymnopedies_-_la_1_ere._lent_et_douloureux.ogg | yes | Satie, Gymnopédies, la 1ère, lent et douloureux (piano) | Robin Alciatore (via Musopen) | "released into the public domain by its author, Robin Alciatore" | Ogg Vorbis, 3.53 MB | 3 min 4 s | **accept**: Musopen asks for a courtesy credit |
| 8 | https://commons.wikimedia.org/wiki/File:Musopen_-_In_the_Hall_Of_The_Mountain_King.ogg | yes | In the Hall of the Mountain King (Grieg) | Czech National Symphony Orchestra, released by Musopen | "released into the public domain by its author, Musopen" | Ogg Vorbis, 2.06 MB | 2 min 34 s | **accept** |
| 9 | https://commons.wikimedia.org/wiki/File:Modest_Mussorgsky_-_night_on_bald_mountain.ogg | yes | Night on Bald Mountain (Mussorgsky) | Musopen; page says performer "might be" Skidmore College Orchestra | "released into the public domain by its author, Musopen" | Ogg Vorbis, 12.27 MB | 12 min 13 s | **accept** with a note: the performer is not certain |
| 10 | https://commons.wikimedia.org/wiki/File:Apprentice.ogg | yes | "Apprentice" (sound sample from Sorcerer's Apprentice) | FortunateTheognis (metadata: Josh Perschbacher); categories mention organ music | "release this work into the public domain" | Ogg, 756 KB | 48 s | **accept**, low value: a short self-made sample, unclear what it sounds like |
| 11 | https://commons.wikimedia.org/wiki/File:Grieg_-_Peer_Gynt_Suite_No._1,_Op._46_-_IV._In_the_Hall_of_the_Mountain_King_(Musopen_Symphony).flac | yes | Mountain King (Musopen Symphony) | Musopen Symphony | PD release text, plus a notice that Musopen's own works are "fully copyrighted" | FLAC 24.58 MB | 2 min 34 s | reject: mixed message on the page; use row 8 instead |
| 12 | https://opengameart.org/content/waltz-of-the-ghosts | yes | Waltz of the Ghosts | Aureolus_Omicron | "License(s): CC-BY 4.0, OGA-BY 3.0" | `waltz_of_the_ghosts.ogg` 2.4 Mb | n/s | reject: attribution required |
| 13 | https://opengameart.org/content/gothic-horror-symphonic-waltz | yes | Gothic Horror Symphonic Waltz | n/s | The text I got is a moderator note saying the author's extra conditions do not fit OGA licenses and the page is marked with a licensing issue | n/s | n/s | reject: licensing issue |
| 14 | https://opengameart.org/content/the-magic-box-looping | yes | The Magic Box (Looping) | Eric Matyas (soundimage.org) | "Please credit as" (attribution required) | `the_magic_box_lopping.ogg` 2.2 Mb | 0:53 | reject: attribution required |
| 15 | https://opengameart.org/content/the-wizards-concoction-looping | yes | The Wizard's Concoction (Looping) | Eric Matyas | "Please credit as" | n/s | 0:44 | reject: attribution required |
| 16 | https://opengameart.org/content/gentle-lullaby-loop | yes | Gentle Lullaby Loop (music box) | frances (Frances Calceta) | "License(s): CC-BY 3.0" | `lullaby.ogg` 693.4 Kb | n/s | reject: CC-BY |
| 17 | https://opengameart.org/content/soothing-music-pack | yes | Soothing Music Pack | AstralTempest | "License(s): OGA-BY 3.0" | oggs, 0.87 to 5.2 Mb | n/s | reject: attribution required |
| 18 | https://opengameart.org/content/lullaby-1 | yes | Lullaby (musical box) | n/s | no license line; "Please just mention my username and this site" | `lullaby.zip` 31.3 Mb (FLAC + MIDI) | 3:00, 6/8, 38 BPM (dotted) | reject: credit requested, license not shown |
| 19 | https://opengameart.org/content/waltz | yes | Waltz (orchestral) | Peter Eastman (named in the credit line) | "Please credit Peter Eastman" | `Waltz.ogg` 1.6 Mb | n/s | reject: credit requested, license not shown |
| 20 | https://opengameart.org/content/gem-waltz-free-music-loop | yes | Gem Waltz | Haley Halcyon | credit line only, no license line | n/s | n/s | reject: license not shown |
| 21 | https://opengameart.org/content/haunted-memories | yes | Haunted Memories | n/s | "Credit is not required" but no license name | `haunted_memories.wav` 11.6 Mb | n/s | reject: license not shown |
| 22 | https://opengameart.org/content/skeleton-waltz-theme | yes | Skeleton Waltz Theme | n/s | none in the text | n/s | n/s | reject: license not shown |
| 23 | https://opengameart.org/content/death-waltz | yes | Death Waltz | n/s | "Attribution is not required" but no license name | MIDI only | n/s | reject: license not shown, MIDI |
| 24 | https://opengameart.org/content/baby-black-magi | yes | Baby Black Magi | bobjt (named in the credit line) | "None necessary" but no license name | n/s | n/s | reject: license not shown |
| 25 | https://opengameart.org/content/fantasy-choir-3-orchestral-pieces | yes | Fantasy Choir-3 orchestral pieces | César da Rocha (cesisco), per credit line in a search snippet and his comment | License line not in the text I got. A commenter says CC0. | `FantasyChoir24bit` (from a snippet) | n/s | reject for now: license unread. Worth a one-minute check, see (d) |
| 26 | https://opengameart.org/content/fantasy-music-and-drum-loops-pack | yes | Fantasy Music and Drum Loops Pack | "North Fantasy Music" | "If used, please credit" | 15 wav files | n/s | reject: credit requested, license not shown |
| 27 | https://opengameart.org/content/lanterns-in-the-hollowed-forest | yes | Lanterns in the Hollowed Forest | n/s | none in the text | n/s | n/s | reject: no license or author in the text I got (it is listed in `docs/audio_sources.md` from a snippet only) |
| 28 | https://opengameart.org/content/spooky-loop | yes | Spooky Loop | n/s | only a comment in the text I got; a search snippet said CC0 and `Spook.mp3` 790.3 Kb | n/s | n/s | reject: license unread |
| 29 | https://opengameart.org/content/mysterious | yes | Mysterious | "nene" (a commenter replies as the author) | CC0 is claimed only in a comment | n/s | n/s | reject: license unread |
| 30 | https://opengameart.org/content/loop-lonely-witch | yes | Loop: Lonely Witch | HorrorPen (named in a comment) | none in the text | n/s | "about 1 minute" per snippet | reject: license unread |
| 31 | https://opengameart.org/content/victory-fanfare-short | yes | Victory Fanfare Short | cynicmusic.com | asks to be contacted for permission | n/s | n/s | reject: permission conditions |
| 32 | https://opengameart.org/content/cc0-fantasy-music-sounds | yes | CC0 Fantasy Music & Sounds (collection) | Sir Gawain (curator) | collection text says "licensed unter CC0" | list of track titles, no files | n/a | not a track; used only to find titles |
| 33 | https://opengameart.org/content/classical-music-box-collection | yes | Classical Music Box - Collection | n/s | page body came back empty (date only) | n/s | n/s | reject: nothing readable |
| 34 | https://opengameart.org/content/victory-fanfare | yes | Victory Fanfare (church organ) | n/s | page body came back empty | n/s | n/s | reject: nothing readable |
| 35 | https://opengameart.org/content/cc0-calm-relaxing-music | yes | CC0 - Calm / Relaxing Music (collection) | n/a | comments only | n/a | n/a | not useful |
| 36 | https://commons.wikimedia.org/wiki/File:Saint-Sa%C3%ABns_-_Danse_macabre_(Fourestier,_1953).flac | yes | Danse macabre (Fourestier, 1953) | Fourestier (uploader Flopinot2012) | page carries the US notice that pre-1972 recordings are protected under the Music Modernization Act | FLAC 16.01 MB | 7 min 19 s | reject: US protection notice |
| 37 | https://commons.wikimedia.org/wiki/File:Dance_Of_The_Sugar_Plum_Fairies.ogg | yes | Dance of the Sugar Plum Fairies (celesta) | Kevin MacLeod | "attribution – You must give appropriate credit" (CC-BY) | Ogg 1.81 MB, 143 kbps | 1 min 46 s | reject: CC-BY. Page tags: celesta, "Bright, Calming, Mystical", 120 bpm |
| 38 | https://commons.wikimedia.org/wiki/File:Satie_Gymnopedie_No_1_performed_by_Michael_Laucke.flac | yes | Gymnopédie No. 1, guitar | Michael Laucke | page shows an attribution + share-alike block | FLAC 9.76 MB | 2 min 52 s | reject: share-alike text |
| 39 | https://commons.wikimedia.org/wiki/File:Toccata_et_Fugue_BWV565.ogg | yes | Toccata et Fugue BWV565 (organ) | Ashtar Moïra | license section empty in the text I got (upload note only says the composition is old) | Ogg 5.84 MB | 8 min 34 s | reject: recording license unread |
| 40 | https://commons.wikimedia.org/wiki/File:Clair_de_Lune_by_Claude_Debussy_(1905,_piano_solo).opus | yes | Clair de Lune (1905, piano solo) | n/s (imported from YouTube) | no license text | Opus 4.97 MB | 4 min 36 s | reject: no license text |
| 41 | https://archive.org/details/02-saint-saens-danse-macabre | yes | Camille Saint-Saens: Danse Macabre | uploader Dr. FennecFox | no license shown | 6.9M item | n/s | reject: no license |
| 42 | https://musopen.org/music/1462-danse-macabre-op-40/ | **could not open** (HTTP 403) | Danse Macabre, op. 40 | n/a | n/a | n/a | n/a | not assessed |
| 43 | https://dnd.opengameart.org/content/moonlit-lullaby-for-the-lost, https://forum.opengameart.org/content/4-music-box-tracks | **could not open** (certificate error). The plain `opengameart.org` address worked for both, see rows 3 and 4 | | | | | | |
| 44 | https://freemusicarchive.org/faq and the FMA search URL with the CC0 license filter | yes | Free Music Archive FAQ, search page | n/a | FAQ says CC0 tracks exist but its CC0 line wrongly says "Attribution is required" | search page listed unrelated experimental tracks (e.g. 16:09 "dfo") | n/a | no candidate found. I did not find a celesta or harp CC0 track on FMA |
| 45 | https://citizen-dj.labs.loc.gov/loc-fma/use/ | yes (very long page, I only saw the start and end) | Citizen DJ / Free Music Archive | n/a | page is a list of loop excerpts | n/a | n/a | no candidate found |
| 46 | https://github.com/SoundSafari/CC0-1.0-Music | yes | SoundSafari CC0 corpus | n/a | repo says it holds CC0 music from other sites, no per-file license | ~7000 songs, ~40 GB | n/a | reject as a source: no per-file license on the page |
| 47 | https://archive.org/details/New_Midnight_Cassette_System | yes | New Midnight Cassette System | Frank Edward Nora | "released under the ... CC0 1.0" (on the page) | MP3s, 34 tracks | 55 h | license ok, but generative electronic music, wrong mood. Not shortlisted |
| 48 | https://archive.org/details/aichemists_music_archive | yes (large file list) | aichemist's music archive | aichemist | I did not find the license text in what I read | MP3s | n/a | reject: license unread |
| 49 | Not opened (search result only): archive.org items for Satie by the Boston Symphony (1930), Sorcerer's Apprentice (Mitropoulos, 1941), Night on Bald Mountain (Stokowski, 1953), Nutcracker Suite (Ormandy, 1945); Pixabay celesta search; chosic.com CC0 page; sounddino.com | no | | | | | | not assessed. Old commercial recordings are not clearly free just because they are old (see row 36) |

## (b) Ranked shortlist (accepted items only, at most 10)

Mood fit is **unverified by ear** for every item. "Loops cleanly" is unknown unless the page says so, and no accepted page says so.

How to loop any file (main line, ffmpeg): trim to a musical length, then crossfade the tail into the head for 2 s (`acrossfade` on a copy of the first 2 s appended after the last 2 s is removed), or play it as two overlapping players with a 2 s fade in the audio module. Check the join by ear. A 3/4 piece at 80 BPM does not fill 24 s with whole bars (32 beats is 10 2/3 bars), so loop waltzes at their own length instead of the 24 s grid in `docs/audio_event_map.json`.

| rank | item (row) | role in the game | mood fit (unverified) | loops cleanly? | how to loop |
|---|---|---|---|---|---|
| 1 | Artifact Room, Fupi (1) | **battle bed** (calm), title | Page tags: magic, mysterious, celestial choir, harp. This is the closest match to the brief on paper. | unknown. Description says "looping track". | trim to the page's loop length once heard, 2 s crossfade |
| 2 | Haunted Track, Gena Sealov (2) | battle bed alternative, title | "Spooky and slow paced", minor and major versions. Instruments unknown. Minor fits D minor; major could be a calmer title mood. | unknown | 2 s crossfade; the page offers FLAC, so use that as the source |
| 3 | Gymnopédie No. 1, Alciatore / Musopen (7) | title screen, calm round-start layer, quiet bed under `victory` | Solo piano, slow and dreamy. Soft, not celesta, but close to "music box" in feel. | no, it is a piece with an ending | use as is for title, or crossfade the last 2 s into the first 2 s |
| 4 | 4 Atmospheric ghostly loops, Independent.nu (5) | tension layer (replace or add to `tension_drone`) | Titled dark, moody, ghostly; tags include "magic". A 7z archive, contents unseen. | "loops" in the title | unpack, pick one, 2 s crossfade |
| 5 | In the Hall of the Mountain King, Czech NSO / Musopen (8) | tension layer for the last rounds, or a build for the final throw | Orchestral, creeping then loud (from the composition, not from the page). Dramatic, not magical. | no | cut a 24 s part, 2 s fades |
| 6 | Night on Bald Mountain, Musopen (9) | long source for a tension or defeat cue | Dark orchestral, 12 min, so cut a short part. Performer uncertain. | no | cut a section, fade in and out |
| 7 | Apprentice sample, FortunateTheognis (10) | short stinger idea only | 48 s sample, sound unknown. | no | skip unless the main line likes it |
| 8 | Lose Game Short Music Clip, Robin Lamb (6) | alternative defeat sting | Short loss clip, not magical. | no, it is a sting | none |

Held for a one-minute check by the main line (not counted as accepted):

- **4 Music Box Tracks, `musicbox1_spooky_waltz` (3).** CC0 text seen. If the page shows an author, this is probably the best "mysterious waltz" and "music box" pick. Roles: title bed, battle bed.
- **Moonlit Lullaby for the Lost (4).** CC0 text seen. The description (graveyard, lantern, church bell) fits the game. Needs the author name and the file name. Roles: title, victory/defeat bed.
- **Fantasy Choir-3 orchestral pieces (25).** Soft-choir candidate. Needs the license line read on the page.

## (c) Download URLs

OpenGameArt pages showed file names and sizes but the fetch did not show the link targets. For all OGA items use "link not shown, open the page and use the download button" on the page URL.

| item | page URL | file to take | direct download URL |
|---|---|---|---|
| Artifact Room | https://opengameart.org/content/artifact-room | `Artifact.ogg` (or `Artifact.flac`) | link not shown, open the page and use the download button |
| Haunted Track | https://opengameart.org/content/haunted-track | `haunted_track_minor.ogg` / `.flac`, and the major version | link not shown, open the page and use the download button |
| 4 Atmospheric ghostly loops | https://opengameart.org/content/4-atmospheric-ghostly-loops | `independent_nu_ljudbank-atmosphere_moody.7z` | link not shown, open the page and use the download button |
| Lose Game Short Music Clip | https://opengameart.org/content/lose-game-short-music-clip | `losegamemusic.ogg` | link not shown, open the page and use the download button |
| Gymnopédie No. 1 (Alciatore) | https://commons.wikimedia.org/wiki/File:Erik_Satie_-_gymnopedies_-_la_1_ere._lent_et_douloureux.ogg | the Ogg file | link not shown, open the page and use the download button |
| Mountain King (Czech NSO) | https://commons.wikimedia.org/wiki/File:Musopen_-_In_the_Hall_Of_The_Mountain_King.ogg | the Ogg file | link not shown, open the page and use the download button |
| Night on Bald Mountain | https://commons.wikimedia.org/wiki/File:Modest_Mussorgsky_-_night_on_bald_mountain.ogg | the Ogg file | link not shown, open the page and use the download button |
| Apprentice sample | https://commons.wikimedia.org/wiki/File:Apprentice.ogg | the Ogg file | link not shown, open the page and use the download button |
| (hold) 4 Music Box Tracks | https://opengameart.org/content/4-music-box-tracks | `4_music_box_tracks_ogg.zip` | link not shown, open the page and use the download button |
| (hold) Moonlit Lullaby for the Lost | https://opengameart.org/content/moonlit-lullaby-for-the-lost | file name not shown | link not shown, open the page and use the download button |

Credits to add to `assets/audio/CREDITS.md` for anything used: title, author as shown above, page URL, the license text seen. Musopen asks for a courtesy credit on its files.

## (d) What is still missing, and what could fill it

- **No CC0 celesta track found.** The one celesta piece I opened (Sugar Plum Fairy, Kevin MacLeod) is CC-BY, so it is rejected. Nothing on OGA or FMA that I opened mentions celesta with a CC0 license.
- **No CC0 harp glissando or shimmering string layer found.** Artifact Room lists harp in its tags, but I cannot tell how prominent it is.
- **No victory sting with celesta, bells and harp.** The installed victory sting is the plain Short Jingle.
- **No soft-choir sting for defeat.** Fantasy Choir-3 may fill it once its license line is read.
- **Public-domain classical with a free recording is thin.** Only Satie (piano), Mountain King and Night on Bald Mountain passed. Danse Macabre, Sorcerer's Apprentice, Toccata, Clair de lune and Sugar Plum had no recording with a clear free license on the pages I could read. Musopen's own page returned 403, so its recordings of these pieces are still unchecked.
- **Ways to fill the gaps:**
  - Synthesize them in code. The audio module already has bell and shimmer recipes (`bell_strike`, `shimmer`, `chime_two`, `arpeggio_up` in `docs/audio_event_map.json`). A celesta-like layer (sine plus a bell partial, fast decay) and a harp-like glissando (rising plucked sines in D minor) on the victory and round-start events cost nothing in licensing and use no downloads.
  - The Colab AI audio route in `docs/audio_generation_options.md`: that file is not in this workspace, so I cannot say what it covers. If the owner wants it, it could make a 24 s celesta/bell loop and a victory sting. The generated files would need their own license check.
  - Ask the main line to open Musopen in a browser (my fetch got HTTP 403) and look for orchestral recordings of Danse Macabre and Sugar Plum with the public domain license shown.

# Kiro task 24 - find copyright-free Halloween / magical music (web allowed, files only, NO downloads)

## Why
The owner listens to the game and says the sound does not feel magical enough, "like a wizard-school film": think celesta and bells, harp glissandi, soft choir, shimmering strings, mysterious waltz feel, in a Halloween setting.
We can use only music that is CC0 / public domain with a clear license on the page. The owner wants YOU to find and verify candidates. You cannot download or hear anything: you read the pages. The main line will download only the files you verify.
Do NOT try to imitate or name any copyrighted film score; search by mood and instrument words instead.

## Do exactly this
1. Read `docs/audio_sources.md`, `docs/audio_event_map.json` (music section: layers bed / rhythm / tension / victory / defeat, 80 BPM, D minor, 24 s loops) and `assets/audio/CREDITS.md` (what we already have).
2. Search and OPEN (web fetch) pages for these kinds of sources, record what you really saw:
   a. OpenGameArt CC0 music tagged fantasy, magic, mystical, celesta, music box, harp, choir, orchestral, Halloween, haunted, waltz, lullaby; prefer loops 30 s to 3 min.
   b. Public-domain classical pieces whose RECORDING is also free to use (the composition being old is not enough: the recording must be CC0 / public domain too): Musopen, Internet Archive, Wikimedia Commons, Free Music Archive CC0 filter. Spooky and magical candidates to check (examples, verify each page):
      Saint-Saens "Danse Macabre", Grieg "In the Hall of the Mountain King", Mussorgsky "Night on Bald Mountain", Bach "Toccata and Fugue in D minor" (organ), Tchaikovsky "Dance of the Sugar Plum Fairy" (celesta), Satie "Gnossienne" / "Gymnopedie", Dukas "The Sorcerer's Apprentice", Debussy "Clair de lune" (harp-like piano), Mozart "Eine kleine Nachtmusik" is NOT fitting; use judgement.
   c. Other CC0 libraries with a clear license statement (e.g. a site-wide CC0 page).
   Accept only: CC0 / public domain, with the license text visible on the page and a clear author or performer. Reject CC-BY, CC-BY-SA, CC-BY-NC, "free for non-commercial", "royalty free with conditions", missing or unclear license, and any page whose license you could not read.
3. Write `docs/halloween_music_candidates.md`: (a) a table of pages opened (URL, opened yes/no, title, author or performer, license text on the page in at most 10 words, format and file name and size if shown, length, verdict accept/reject and why); (b) a ranked shortlist of at most 10 accepted items with the role each can play in the game (battle bed, tension layer, title, victory sting, defeat sting), how well the mood fits (say it is unverified by ear), whether it loops cleanly (unknown unless the page says so) and how to loop it (crossfade 2 s, the main line can do it with ffmpeg); (c) the exact direct download URL of each accepted file as shown on the page, or "link not shown, open the page and use the download button"; (d) what is still missing (for example a victory sting with celesta) and what could fill it (the Colab AI audio route in `docs/audio_generation_options.md` if present).
4. Do not download or write any audio. Do not edit other files. Do not use git or shell. Do not create images.
5. Finish with a 6-line summary: pages opened, accepted count, the single best pick for the battle bed and why, and what you could not verify.

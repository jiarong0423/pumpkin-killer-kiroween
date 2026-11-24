# Audio generation options (Kiro task 23)

Question from the owner: can Colab (A100 40 GB) generate the music and sound effects, and what is safe to use in the contest?

Short answer: yes, a Colab A100 can run several text-to-audio models. The job uses Stable Audio Open 1.0 under the Stability AI Community License, after the owner reads the license pages in section 2.3. Stable Audio 3 (same license), MOSS-SoundEffect v2.0 (Apache 2.0) and ACE-Step 1.5 (MIT, music only) are permitted by their license text, but I could not confirm where MOSS and ACE-Step got their training audio. MusicGen, AudioGen, AudioLDM 2, Tango, Tango 2 and TangoFlux have non-commercial weights and must not be used.

Status: research from public pages plus code and data files. **Nobody has run the job and nobody has heard any generated sound.** Kiro did not download any model or audio file and did not run any code. Statements about how the models sound are general expectations, marked as such, not results. This is not legal advice.

Content from the pages below was paraphrased. Quotes are 10 words or fewer.

## 1. Model table

`opened` means the page loaded and I read it in this task. A field I could not find on an opened page says "not stated".

### 1.1 Licenses and use in the contest entry

| Model | Publisher | Weights license (as written on the page) | Code license | Outputs in a contest entry | Restrictions seen |
|---|---|---|---|---|---|
| Stable Audio Open 1.0 | Stability AI | Card: "Stability AI Community License" | Not stated on the pages opened (stable-audio-tools README has no license line) | Community License: you own the outputs as far as the law allows. Commercial purposes need registration. | Free below USD 1M annual revenue (you plus affiliates), above that the license ends. Must follow the Acceptable Use Policy. No using outputs to build a new foundation model. Distributing the model or a derivative needs a copy of the agreement, a Notice file and "Powered by Stability AI". Card lists as out of scope audio meant to create hostile or alienating environments. Gated on Hugging Face (raw file gave HTTP 401). |
| Stable Audio Open Small | Stability AI | Card: "Stability AI Community License" | Not stated | Same as above | Same as above. |
| Stable Audio 3 (small-sfx, small-music, medium) | Stability AI | Card: "Stability AI Community License". The card also says the T5Gemma text encoder is redistributed under the Gemma Terms of Use. | Repo README: refer to the Community License | Same as above. Stability's knowledge-base page says generated sounds may be used in games. That page is about the Stable Audio product; for self-hosted weights it points back to the Community License. | Same as above, plus the Gemma Terms of Use (page not opened). Stable Audio 3 Large is API only. |
| MusicGen (small, medium, large, melody) | Meta FAIR | Card: "model weights are released under CC-BY-NC 4.0" | MIT (card and audiocraft README) | **Do not use.** Non-commercial weights. | Non-commercial. |
| AudioGen (inside audiocraft) | Meta FAIR | audiocraft README: weights in the repo are CC-BY-NC 4.0. The AudioGen model card was not opened. | MIT (README) | **Do not use.** | Non-commercial. |
| AudioLDM 2 (`cvssp/audioldm2`) | CVSSP / Haohe Liu et al. | Card metadata: `license: cc-by-nc-sa-4.0` | GitHub page could not be read (empty result) | **Do not use.** | Non-commercial, share-alike. The large and music checkpoints have their own cards that I did not open. |
| Tango / Tango 2 (`declare-lab/tango2`) | declare-lab | Card metadata: `license: cc-by-nc-sa-4.0` | Not stated on the pages opened | **Do not use.** | Non-commercial, share-alike. Other Tango cards not opened. |
| TangoFlux | declare-lab | Card: "for non-commercial research use only", also bound by the Stable Audio Open license | Not stated | **Do not use.** | Non-commercial. |
| MOSS-SoundEffect v2.0 | OpenMOSS-Team | Card metadata: `license: apache-2.0`. MOSS-TTS README says the family is under Apache 2.0. | Same repository, Apache 2.0 | Permitted by the license text. Training data is not described on the pages opened, so provenance is unknown to me. | Text encoder is Qwen3 (card tag `Qwen/Qwen3-1.7B`); its license and the DAC VAE license were not opened. |
| ACE-Step 1.5 (music only) | ACE-Step | Card: "License: [MIT]". The card also claims commercial-ready and legally compliant training data. | Not stated | Permitted by the license text. The training-data claims are the publisher's own and I did not check them. | Card page only; the repository and the license file were not opened. |

### 1.2 Technical facts

| Model | Max clip | Sample rate / channels | VRAM | Speed on A100 | SFX vs music | Library and install |
|---|---|---|---|---|---|---|
| Stable Audio Open 1.0 | 47 s | 44.1 kHz stereo | Not stated | Not stated | Card says it is better at sound effects and field recordings than at music, and cannot make realistic vocals. Prompt engineering may be needed. | `diffusers` (`StableAudioPipeline`, card example uses fp16, 200 steps, `negative_prompt`) or `stable-audio-tools`. `pip install -U diffusers transformers accelerate soundfile` |
| Stable Audio Open Small | 11 s | 44.1 kHz stereo | Not stated | Not stated; card example uses 8 steps and cfg 1.0 | Same limits as the 1.0 card | `stable-audio-tools` only. `pip install "stable-audio-tools[train]"` is the line the README shows |
| Stable Audio 3 | small 120 s, medium 380 s | 44.1 kHz stereo | Peak on H200: small 1.7 to 2.4 GB, medium 5.1 to 6.5 GB (README) | README times are for H200 (small 0.41 s for 5 s of audio, medium 0.60 s). No A100 number. | `small-sfx` is SFX only, `small-music` music only, `medium` both. Cards state no quality verdict beyond the paper. | `stable-audio-3` repo, installed with `uv sync`. `pyproject.toml` pins `torch==2.7.1` and needs `transformers>=5.8.0`. Medium needs Flash Attention 2. |
| MusicGen small | Not on the card. The card example uses 256 tokens at 50 tokens per second, about 5 s. | 32 kHz mono | Not stated | Not stated | Music only. Card says it sometimes ends songs and collapses to silence. | `transformers` (`MusicgenForConditionalGeneration`) or audiocraft. `pip install --upgrade transformers scipy` |
| AudioLDM 2 | Set by `audio_length_in_s`; card examples use 10 s | 16 kHz (card writes the WAV at 16000) | Not stated | Not stated; examples use 200 steps | Sound effects, speech and music. 16 kHz cannot hold bright top end. Card: quality varies a lot with the seed. | `diffusers` (`AudioLDM2Pipeline`). `pip install --upgrade diffusers transformers accelerate` |
| Tango 2 | Not stated | 16 kHz (card) | Not stated | Not stated; default 100 steps, 200 advised | Sound effects mostly | `tango` package from the declare-lab repo, see its README |
| TangoFlux | 30 s | 44.1 kHz | Not stated | Not stated | Text to audio | `pip install git+https://github.com/declare-lab/TangoFlux` |
| MOSS-SoundEffect v2.0 | 30 s | 48 kHz; channel count not stated | Not stated | Not stated; default 100 steps. First call compiles for a few minutes. | Card lists ambience, urban, creatures, human actions and short musical clips | Clone `OpenMOSS/MOSS-TTS`, then `pip install -e ".[torch-cu128]"` inside `moss_soundeffect_v2` in a clean Python 3.12 environment (pins `numpy==1.26`, `transformers==4.57`, `torch==2.9`). |
| ACE-Step 1.5 | Loops to 10-minute pieces (card) | Not stated | Card claims under 4 GB | Card claims a full song in under 2 s on an A100 | Music only | See the card |

Every number in the "Not stated" cells needs a real run on the A100 to fill in. I did not measure anything.

## 2. Verdict

### 2.1 Safe to use for this entry (after the owner's checks)

- **Stable Audio Open 1.0 is the model the Colab job uses** (`colab/audio_job.py`). Reasons: the Community License lets a small project use the outputs, the training data is listed as CC0, CC-BY and CC Sampling+ audio with Stability's copyright filtering (card), it makes sound effects better than music (card), and its `diffusers` call is written out in full on the card, so the job code follows a documented call. It also takes a negative prompt and a seed.
- **Stable Audio 3 `small-sfx` and `medium` are the upgrade to try next**, same license. They are newer, trained on licensed data (AudioSparx) plus Freesound CC data (card), and have a dedicated SFX model. I did not write the job for them: the README does not show the return type of `generate`, a negative prompt or a seed argument, and the install pins `torch==2.7.1`, which fights the Colab default. The post-processing script works on their output unchanged.
- **MOSS-SoundEffect v2.0** has the cleanest license text (Apache 2.0) but I could not see where its training audio comes from, and it needs a pinned Python 3.12 environment. Allowed by its license; not used by the job. If the owner wants a second source for ambience, read the OpenMOSS repository for a data statement first.
- **ACE-Step 1.5** (MIT) is an option only for the music beds. Not used by the job.

### 2.2 Must not be used

| Model | Why |
|---|---|
| MusicGen (all sizes), AudioGen | Weights are CC-BY-NC 4.0, non-commercial. |
| AudioLDM 2 | Weights are CC BY-NC-SA 4.0. |
| Tango, Tango 2 | Weights are CC BY-NC-SA 4.0. |
| TangoFlux | Non-commercial research use only, and tied to the Stable Audio Open license. |

Whether a contest entry counts as "commercial" is a question about the contest and the license, and I cannot answer it. The contest rule is that third-party models must be authorised. A non-commercial weight license does not clearly authorise a game entry, so these models fail the rule on the page text alone.

### 2.3 What the owner should read before generating

Open these pages yourself, on the day, and keep a note of what they say:

1. https://huggingface.co/stabilityai/stable-audio-open-1.0 : model card, the terms to accept, the "commercial use" note, the out-of-scope list.
2. https://stability.ai/license : the Community License summary, the USD 1M limit, registration.
3. https://stability.ai/community-license-agreement : the license text. Section III says commercial use needs registration; section IV(a) covers attribution; section IV(b) the Acceptable Use Policy.
4. https://stability.ai/use-policy : acceptable use. It prohibits misleading people about AI-made content, so say in the entry that the audio is AI generated.
5. The contest rules: do they treat a free entry as non-commercial, and do they ask for a list of generated assets?
6. If you try Stable Audio 3: https://huggingface.co/stabilityai/stable-audio-3-small-sfx and the Gemma Terms of Use (I did not open the Gemma page).

Practical steps that cost nothing: register with Stability AI at stability.ai/license, put a credit line ("Sound effects generated with Stable Audio Open 1.0, Stability AI Community License") in the entry and in `assets/audio/CREDITS.md`, and keep `generation_log.jsonl` from the job as the record of model, seed and prompt for every file.

Reading of the attribution clause (mine, not legal advice): it is written for distributing the model or a derivative of it. The agreement's definition of "Derivative Works" excludes model outputs, so shipping WAV or OGG files may not trigger it. The credit line is cheap, so add it anyway.

## 3. Quality notes

What follows comes from the model cards where marked "(card)" and otherwise from general experience with this kind of model. None of it was heard on this project.

**Models do reasonably well:** ambient beds and drones, wind and air movement, whooshes, big impacts and booms, magic shimmer and chimes, wood and metal textures. Stable Audio Open's card says it is stronger at effects than at music (card).

**Models do badly:**

- Precise short clean hits (a UI tick, a dice tick). The model tends to add a tail, a second hit or noise. Ask for 1 s and cut.
- Loop seams. A generated clip does not end where it began, so a loop clicks or jumps.
- Tempo and rhythm. A heartbeat at one beat per 0.9 s, or an 80 BPM bed, will drift. Treat the numbers in the prompt as hints.
- Tonal accuracy. A bell chime may be out of tune with D minor. The game's sound design keeps bells inside the key.
- Speech and vocals (card: not realistic). The ghost wail prompt asks for a wordless sound; a voice may still creep in.
- Variation between seeds is large (AudioLDM 2 card says so; expect the same here). This is why the job makes 3 variants per sound.

**Fixes that need no model**, all in `scripts/postprocess_audio.py` (numpy only):

| Problem | Fix |
|---|---|
| Silence or noise at the start and end | Trim below 45 dB under the clip peak, keep 2 ms before and 10 ms after |
| Clip is longer than needed | Cut to the planned duration |
| Click at start or end | Fade in 5 ms, fade out 30 ms |
| Levels differ between files | Normalise the peak to -3 dBFS |
| Loop seam | Crossfade the tail into the head (80 ms), then check `loop_seam_ratio` (near 1 or below is fine) |
| Stereo files for effects | Mix to mono (music stays stereo) |

An 80 ms crossfade is short for a music pad. If a bed or drone seam is audible, raise `loop_crossfade_ms` for that job to 1000 ms or more. The script checks only the sample step at the seam. It does not hear a change of pitch or rhythm across the seam.

## 4. What Kiro can do for sound

**Kiro can:**

- Design the prompts and the mix. `colab/audio_jobs.json` holds 34 prompts (30 events, 4 music) with negative prompts, durations, 3 variants, seeds and post-processing settings. `docs/sound_design.md` holds the mix.
- Write the Colab job, the post-processing and loop-check script, and the tests (`colab/audio_job.py`, `scripts/postprocess_audio.py`, `scripts/test_postprocess_audio.py`).
- Wire the finished files into `js/audio.js` and `docs/audio_event_map.json`: set `file`, `source` and the credits entry for each file the owner approves, and extend the tests so a missing or misnamed file is caught.
- Re-tune prompts after the owner reports what is wrong ("too long", "has a voice", "clicks at the loop").

**Kiro cannot:**

- Hear anything. Every judgment about quality, mood or loop smoothness has to come from the owner's ears.
- Run Colab, run the job or run the tests. Kiro here has no shell and no GPU.
- Download models or audio, convert WAV to OGG, or accept license terms on the owner's behalf.
- Decide whether the license fits the contest. The owner reads the pages in 2.3.

## 5. Pages and whether I opened them

| Page | Opened |
|---|---|
| https://huggingface.co/stabilityai/stable-audio-open-1.0 | yes |
| https://huggingface.co/stabilityai/stable-audio-open-1.0/raw/main/README.md | no (HTTP 401, gated) |
| https://huggingface.co/stabilityai/stable-audio-open-small | yes |
| https://huggingface.co/facebook/musicgen-small | yes |
| https://huggingface.co/facebook/musicgen-small/raw/main/README.md | yes |
| https://huggingface.co/cvssp/audioldm2 | yes |
| https://huggingface.co/cvssp/audioldm2/raw/main/README.md | yes |
| https://huggingface.co/declare-lab/tango2 | yes |
| https://huggingface.co/declare-lab/tango2/raw/main/README.md | yes |
| https://huggingface.co/declare-lab/TangoFlux/raw/main/README.md | yes |
| https://stability.ai/license | yes |
| https://stability.ai/community-license-agreement | yes |
| https://stability.ai/use-policy | yes |
| https://kb.stability.ai/knowledge-base/stable-audio-commerical-and-usage-licensing | yes |
| https://stability-ai.squarespace.com/news-updates/meet-stable-audio-3-the-model-family-built-for-artistic-experimentation-with-open-weight-models (Stability's Stable Audio 3 announcement, mirror host) | yes |
| https://github.com/Stability-AI/stable-audio-tools | yes |
| https://github.com/facebookresearch/audiocraft | yes |
| https://github.com/declare-lab/tango | yes |
| https://github.com/Stability-AI/stable-audio-3 | yes |
| https://raw.githubusercontent.com/Stability-AI/stable-audio-3/main/pyproject.toml | yes |
| https://github.com/Stability-AI/stable-audio-3/blob/main/docs/guides/prompting.md | yes |
| https://github.com/Stability-AI/stable-audio-3/blob/main/docs/guides/model-overview.md | yes |
| https://huggingface.co/stabilityai/stable-audio-3-small-sfx | yes |
| https://huggingface.co/stabilityai/stable-audio-3-medium | yes |
| https://huggingface.co/collections/stabilityai/stable-audio-3 | yes |
| https://huggingface.co/OpenMOSS-Team/MOSS-SoundEffect-v2.0 | yes |
| https://huggingface.co/OpenMOSS-Team/MOSS-SoundEffect-v2.0/raw/main/README.md | yes |
| https://github.com/OpenMOSS/MOSS-TTS | yes |
| https://github.com/OpenMOSS/MOSS-TTS/tree/main/moss_soundeffect_v2 | yes |
| https://huggingface.co/ACE-Step/Ace-Step1.5 | yes (card only) |
| https://arxiv.org/html/2605.17991 (Stable Audio 3 report) | partly: the tool returned a long selection and I read only the opening |
| https://github.com/haoheliu/AudioLDM2 | no (empty result) |
| https://arxiv.org/abs/2407.14358 (Stable Audio Open paper) | no (empty result) |
| https://github.com/Stability-AI/stable-audio-3/blob/main/docs/inference.md | no (404) |
| Gemma Terms of Use, Qwen3 license, DAC VAE license, Tango code license | not tried |

Web search results (snippets only, pages not read unless listed above) led me to Stable Audio 3, MOSS-SoundEffect v2.0 and ACE-Step.

## 6. Not verified

- Anything about how the models sound.
- Speed and VRAM on the A100 for every model except what the Stable Audio 3 README states for H200.
- Whether Stable Audio Open 1.0 loads with the pinned `transformers<5` and the current `diffusers`. The card says to upgrade `diffusers`; the job was not run.
- Code licenses for stable-audio-tools, AudioLDM 2, Tango.
- Training-data provenance of MOSS-SoundEffect v2.0.
- Whether the Stable Audio 3 Hugging Face repos are gated (the cards loaded, the raw file of the older model gave 401).
- The license pages change. Read them again on the day you generate.

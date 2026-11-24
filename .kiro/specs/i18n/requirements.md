# Requirements: Bilingual UI (zh-TW / en)

## Introduction

Every visible string of the game comes from a dictionary, so the game can be
played in Traditional Chinese or English. The player switches language with one
button and the choice is remembered. Game rules and layout do not change.

## Requirements

### 1. Dictionaries

**User story:** As a translator, I want one flat key-to-string file per
language, so that I can review and fix wording without touching game code.

1. THE system SHALL provide `assets/i18n/zh-TW.json` and `assets/i18n/en.json`
   as flat maps from a stable key to a string.
2. THE two dictionaries SHALL contain exactly the same set of keys.
3. WHERE a string takes parameters, THE system SHALL write them as `{name}`
   placeholders, and both languages SHALL use the same set of placeholders for
   that key.
4. THE dictionaries SHALL NOT contain empty strings.
5. THE dictionaries SHALL contain hero names, skill names, tooltips, HUD text,
   floating texts, the tutorial box, the game-over banner and the page title.

### 2. Lookup

**User story:** As a developer, I want a single `t(key, params)` call, so that
a missing translation never breaks the game.

1. WHEN `t(key, params)` is called, THE system SHALL return the string for the
   current language with `{name}` placeholders replaced by `params`.
2. IF the current language has no string for the key, THEN THE system SHALL
   return the zh-TW string.
3. IF zh-TW has no string for the key either, THEN THE system SHALL return the
   key itself.
4. IF a placeholder has no matching parameter, THEN THE system SHALL leave the
   placeholder text unchanged.

### 3. Language choice

**User story:** As a player, I want the game to start in my language and to
remember my choice.

1. WHEN the page loads with no saved choice, THE system SHALL pick the language
   from `navigator.language` (`en*` gives English, `zh*` gives zh-TW) and
   default to zh-TW for anything else.
2. WHEN the page loads with a saved choice, THE system SHALL use the saved
   language.
3. WHEN the player presses the language button, THE system SHALL switch
   between zh-TW and English, re-render every DOM text, tooltip and the page
   title immediately, and save the choice.
4. IF `localStorage` is missing, blocked or throws, THEN THE system SHALL still
   switch the language for the current page view and SHALL NOT raise an error.
5. THE system SHALL set the `lang` attribute of the `<html>` element to the
   current language.

### 4. Everything visible is translated

**User story:** As an English-speaking player, I want no Chinese text left on
screen.

1. THE `index.html` file SHALL NOT contain CJK characters outside comments.
2. WHEN the language changes, THE system SHALL draw canvas text (HUD, angle
   label, banners, fence label, unit labels, shield labels) in the new language
   from the next frame, and floating texts created afterwards SHALL use it.
3. THE English text SHALL use the game terms Pumpkin Guard, floating shield,
   fence, wind, power, angle, Lock, Move, Defend and Ultimate.

### 5. Loading

1. THE browser build SHALL load the dictionaries with `fetch` from relative
   URLs under `assets/i18n/`.
2. THE Node build SHALL load the same files with `fs`.
3. IF a dictionary fails to load, THEN THE system SHALL log the error to the
   console and keep the game playable, showing keys in place of missing text.

### 6. No change to the game

1. THE change SHALL NOT alter game rules, physics, timing or layout, apart
   from the added language button.

# Ask: two layout problems on a short landscape phone screen (start screen and settings sheet)

Paste this whole file to the assistant you are asking, and attach the two screenshots named in section 5. It is self-contained. Please answer the numbered questions at the end with concrete layouts and numbers, and say which parts are opinion and which come from shipped games or platform documentation.

## 1. The game and the screen
- A turn-based artillery duel in the browser (one HTML file, canvas 2D for the match, plain HTML and CSS for the start screen and the settings sheet, no framework).
- Target: Android phones, Chrome, landscape. The visible viewport is short. The 15 sizes tested have widths from 640 to 960 css px and heights from 300 to 540 css px. One real phone gave 756 x 360 css px at devicePixelRatio 3 in fullscreen and 756 x 266 css px with the browser bars showing.
- The project's own rule (from Apple's 44 pt and Google's 48 dp guidance): every control that a finger presses must be at least 44 css px in both directions, and controls must not overlap.

## 2. Problem A: the start screen
Design decision already made by the owner: the start screen is laid out once as an 800 x 360 picture and scaled as one picture by `--start-fit = min(width / 800, height / 360)`. A 44 px control in the layout is therefore 44 x fit px on the screen: 36.7 px at 667 x 300, 40 px at 873 x 330.
A script that opens the start screen in real Chrome at 15 viewport sizes (widths 640 to 960, heights 300 to 540) and checks every pressed control (at least 44 px, no overlaps) printed 14 failing lines at 7 of the 15 sizes on the current version; the other 8 sizes pass. Every failing line is "undersized start controls": a control that is smaller than 44 px on the screen. The script reports each kind of failure once per size and team mode, so the real number of undersized controls can be higher. The 7 sizes:
1. at 640 x 360, 720 x 405, 667 x 375 and 667 x 300: the 8 hero thumbnails together with the Daily match, Friends / seats and Start Battle buttons (in the 3 versus 3 mode also the three slot chips);
2. at 873 x 330, 915 x 350 and 844 x 330: the Daily match, Friends / seats and Start Battle buttons (in the 3 versus 3 mode also the three slot chips).
With the scale rule above a 44 px control becomes smaller than 44 px on screens smaller than the 800 x 360 picture. (An earlier overlap of the three slot chips with the Friends / seats button in the 3 versus 3 mode was fixed by moving that button to the top-left corner of the picture; no control overlaps another any more at the 15 sizes.)
Start screen content: left a card of the selected hero (portrait, HP and attack bars), top left a "Friends / seats" button, in the middle the title, in the team modes a row of three slot chips (small tabs "1 2 3" that choose which unit of the team you are picking a hero for), team size buttons 1v1 / 2v2 / 3v3, the hero grid 4 x 2, a hint line, the Start Battle and Daily match buttons; right the battlefield picker card; top right the settings gear.

## 3. Problem B: the settings sheet
A modal sheet centred on the screen: a title row with a 44 px close button, then a 2 column grid of 8 rows (effects volume with on/off and a slider, reduce motion, music volume, language with two buttons, friends / seats, how to play, AI level with three buttons, restart), each row at least 52 px high with 44 px buttons, and one note line at the bottom.
Problem: an automatic test at random viewport sizes reported that the sheet does not fit (it is taller than the free height) at heights just above 300 px; it needs a little over 300 px of height, and at about 330 px and above it fits. The exact figures were not kept, so treat them as approximate. On the real 756 x 360 phone it fits with little room (screenshot 2).

## 4. Constraints
- Plain HTML and CSS (grid, flex, clamp, container queries are fine), small JavaScript if needed. No frameworks.
- Keep the 44 px rule for pressed controls; keep both languages (Traditional Chinese labels are about the same length as the English ones).
- Do not change what the controls do. The match itself is a canvas and is not part of this question.

## 5. Screenshots to attach
1. `docs/media/ask_5_start_screen_3v3_667x375_current.jpg` - the start screen in 3 versus 3 at 667 x 375 on the current version (the whole 800 x 360 picture is scaled by min(667 / 800, 375 / 360) = 0.83 here, so a 44 px control is 36.7 px; the image is the 667 x 375 view enlarged to 800 x 450, so the controls look about 44 px in the image).
2. `docs/media/ask_3_real_phone_settings_before_fix.jpg` - the settings sheet on the real phone at 756 x 360.

## 6. Questions (please answer each with numbers)
1. For a start screen that must hold a hero card, a 4 x 2 hero grid, team size, a seats button, two action buttons and a battlefield card in 300 to 540 px of height: which layouts do shipped mobile games use (one row carousel, tabs, a drawer, two columns) and which keeps every pressed control at 44 px without scaling the whole screen down?
2. The scale-the-whole-picture rule makes every control smaller than 44 px on short screens by construction. What is the better rule: scale only the artwork and let the controls keep a 44 px floor and reflow, or keep the picture and relax the floor to a stated minimum (for example 36 px with a 44 px invisible touch area)? Give the numbers you would pick and why.
3. For the settings sheet at 300 to 330 px of height: the best compact layout (3 columns, tabs, a scrolling body with a sticky header and a close button, a paged sheet, fewer rows) with sizes, keeping 44 px buttons? Which rows would you drop or move (for example "how to play" and "restart" into a second page)?
4. What minimum viewport height should a landscape phone game promise to support, and what should it do below that (a message to enlarge the window, a scrolling sheet)? Cite the platform guidance if you know it.
5. What is the smallest experiment to decide between the options, and what should the pass rule be (for example "no overlaps and every pressed control at least 44 px at every viewport in the layout script's list (15 sizes), measured by script")?

## 7. Answer format
Start with a 5-line recommendation. Then answer 1 to 5. End with the first three changes you would make, in order, with the smallest CSS sketch for each.

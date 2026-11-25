/* ROOM-FLOW lobby view model (the "second page"): what the lobby shows and allows, computed from one relay room_state.
   Pure: no DOM, no network. Used by index.html, tested by scripts/test_lobby_model.js. Names are plain text; the page never puts them in HTML. */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory();
  else root.LobbyModel = factory();
}(typeof self !== 'undefined' ? self : this, function () {
  'use strict';
  var TEAMS = ['red', 'white'];

  function list(value) { return Array.isArray(value) ? value : []; }
  function seatsOf(state) { return list(state && state.seats).filter(function (s) { return s && typeof s.seat_id === 'string'; }); }
  function sizeOf(state) { var n = state && state.team_size; return Number.isInteger(n) && n >= 1 && n <= 3 ? n : 1; }
  function seatNumber(id) { var n = parseInt(String(id).split('-')[1], 10); return isNaN(n) ? 0 : n; }
  function teamSeats(state, team) { return seatsOf(state).filter(function (s) { return s.team === team; }).sort(function (a, b) { return seatNumber(a.seat_id) - seatNumber(b.seat_id); }); }
  function held(seat, n) { return n > 1 ? Math.max(seat.claim || 0, list(seat.units).length) : 1; }
  function nameOf(state, seatId) { var s = seatsOf(state).find(function (x) { return x.seat_id === seatId; }); return s ? (s.name || '') : ''; }

  function view(state, me) {
    var n = sizeOf(state), seats = seatsOf(state), mine = seats.find(function (s) { return s.seat_id === me; }) || null;
    var started = !!(state && state.started), invites = list(state && state.invites);
    var amHost = !!(mine && state && state.host_seat_id === me);
    var myPlayer = !!(mine && (mine.team === 'red' || mine.team === 'white') && !mine.ai && !mine.agent);
    var out = { code: (state && state.code) || '', teamSize: n, started: started, lobby: !!(state && state.lobby), amHost: amHost, myTeam: mine ? mine.team : null,
      myClaim: mine ? held(mine, n) : 0, myLocked: !!(mine && mine.ready), teams: {}, free: {}, count: { seated: 0, total: 2 * n } };
    TEAMS.forEach(function (team) {
      var cells = [];
      teamSeats(state, team).forEach(function (s) {
        var places = held(s, n), units = list(s.units);
        for (var k = 0; k < places; k++) {
          cells.push({ kind: 'seat', team: team, seatId: s.seat_id, name: s.name || '', mine: s.seat_id === me, host: state && state.host_seat_id === s.seat_id, ai: !!s.ai, agent: !!s.agent,
            invitedBy: s.invited_by || null, invitedByName: s.invited_by ? nameOf(state, s.invited_by) : '', hero: units[k] || null, locked: !!s.ready, first: k === 0 });
          if (!s.ai) out.count.seated += 1;
        }
      });
      invites.filter(function (t) { return t && t.team === team; }).forEach(function (t) { cells.push({ kind: 'invite', team: team, by: t.by, byName: nameOf(state, t.by), expiresIn: t.expires_in }); });
      out.free[team] = Math.max(0, n - cells.length);
      while (cells.length < n) cells.push({ kind: 'free', team: team });
      var mineHeld = cells.filter(function (c) { return c.kind === 'seat' && c.mine; }).length;
      cells.forEach(function (c) {
        c.action = null;
        if (started || !myPlayer || out.myLocked) return;
        if (team === out.myTeam) {
          if (c.kind === 'free' && n > 1) c.action = 'take';
          else if (c.kind === 'seat' && c.mine && mineHeld > 1) c.action = 'release';
        } else if (c.kind === 'free') c.action = 'switch';
      });
      out.teams[team] = cells;
    });
    var full = out.free.red === 0 && out.free.white === 0 && invites.length === 0;
    var allowAi = !!(state && state.allow_ai), allowAgents = !!(state && state.allow_mcp);
    out.hostOnly = { locked: !amHost };
    out.refresh = { enabled: amHost && !started && !seats.some(function (s) { return s.seat_id !== me && !s.ai && s.team !== 'spectator'; }) };
    out.options = { allowAi: allowAi, allowAgents: allowAgents, enabled: amHost && !started };
    out.start = { shown: !started, pressed: !!(state && state.begin), fillsWithAi: !full && allowAi,
      enabled: amHost && !started && (full || allowAi), reason: !amHost ? 'host_only' : started ? 'started' : (full || allowAi) ? null : 'not_full' };
    var waiting = [];
    seats.filter(function (s) { return (s.team === 'red' || s.team === 'white') && !s.ready; }).forEach(function (s) { waiting.push({ kind: 'unlocked', name: s.name || '', seatId: s.seat_id, ai: !!s.ai }); });
    invites.forEach(function (t) { waiting.push({ kind: 'invite', name: nameOf(state, t.by), seatId: t.by }); });
    if (!allowAi) TEAMS.forEach(function (team) { if (out.free[team] > 0) waiting.push({ kind: 'free', team: team, n: out.free[team] }); });
    else TEAMS.forEach(function (team) { if (out.free[team] > 0 && out.start.pressed) waiting.push({ kind: 'free', team: team, n: out.free[team] }); });
    out.waiting = waiting;
    out.myInvite = invites.find(function (t) { return t && t.by === me; }) || null;
    var myAgent = seats.some(function (s) { return s.invited_by === me; });
    out.canInvite = !started && myPlayer && allowAgents && !out.myInvite && !myAgent && !!out.myTeam && out.free[out.myTeam] > 0;
    return out;
  }

  function welcome(prev, next, me) {   // the host sees who came in; a newcomer sees the room. A side change gives a seat a new id but no new player: nothing
    var players = function (st) { return seatsOf(st).filter(function (s) { return !s.ai && s.team !== 'spectator'; }); };
    if (!prev || !seatsOf(prev).length) return seatsOf(next).some(function (s) { return s.seat_id === me; }) ? [{ kind: 'self', code: (next && next.code) || '' }] : [];
    if (!seatsOf(prev).some(function (s) { return s.seat_id === me; }) || players(next).length <= players(prev).length) return [];
    var before = {}; seatsOf(prev).forEach(function (s) { before[s.seat_id] = true; });
    return players(next).filter(function (s) { return !before[s.seat_id] && s.seat_id !== me; }).map(function (s) { return { kind: 'joined', name: s.name || '', seatId: s.seat_id }; });
  }

  function takenByMates(state, me) {
    var mine = seatsOf(state).find(function (s) { return s.seat_id === me; });
    if (!mine) return [];
    var out = [];
    teamSeats(state, mine.team).forEach(function (s) { if (s.seat_id !== me) list(s.units).forEach(function (h) { if (out.indexOf(h) < 0) out.push(h); }); });
    return out;
  }

  function nextHero(all, current, takenByOthers, myOtherPicks) {
    var pool = list(all), i = pool.indexOf(current);
    for (var k = 1; k <= pool.length; k++) {
      var h = pool[(i + k + pool.length) % pool.length];
      if (list(takenByOthers).indexOf(h) < 0 && list(myOtherPicks).indexOf(h) < 0) return h;
    }
    return current;
  }

  return { view: view, welcome: welcome, takenByMates: takenByMates, nextHero: nextHero };
}));

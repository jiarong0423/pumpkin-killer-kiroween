/* Ordered, reconnecting relay transport. It owns no DOM or game simulation. */
(function (root, factory) {
  'use strict';
  var api = factory();
  if (typeof module === 'object' && module && module.exports) module.exports = api;
  else root.RelayClient = api;
})(typeof self !== 'undefined' ? self : this, function () {
  'use strict';

  var RECONNECT_DELAYS_MS = [1000, 2000, 4000, 8000];
  var RECONNECT_LIMIT_MS = 60000;
  var MAX_TEAM_SIZE = 3;
  var TEAM_UNIT = /^(left|right)_([0-2])$/;
  var HASH_FORMAT = /^[0-9a-f]{8}$/;

  function validTeamSize(value) {
    return typeof value === 'number' && Math.floor(value) === value && value >= 1 && value <= MAX_TEAM_SIZE;
  }

  /* A team-battle unit id is `left_0`..`left_2` or `right_0`..`right_2`, below the team size. Frame (local or world) is the caller's business. */
  function isTeamUnitId(id, teamSize) {
    var match = typeof id === 'string' ? TEAM_UNIT.exec(id) : null;
    return !!match && Number(match[2]) < (validTeamSize(teamSize) ? teamSize : 1);
  }

  /* Optional room fields shared by create_room, join and ready. Nothing is added for a one-versus-one room, so its wire stays what it was. */
  // ROOM-FLOW R7: seat names. The same rule as clean_name in scripts/pk_relay.py; scripts/name_vectors.json pins both. A name is only ever shown as plain text.
  var NAME_WIDTH = 10, NAME_INPUT = 64;   // display units (a CJK or full-width character is 2) and code points looked at
  var EMOJI_RANGES = [[0x1F000, 0x1FAFF], [0x2600, 0x27BF], [0x2B00, 0x2BFF], [0x2300, 0x23FF]];
  var WIDE_RANGES = [[0x1100, 0x115F], [0x2E80, 0x303E], [0x3041, 0x33FF], [0x3400, 0x4DBF], [0x4E00, 0x9FFF], [0xA000, 0xA4CF], [0xA960, 0xA97F],
    [0xAC00, 0xD7A3], [0xF900, 0xFAFF], [0xFE10, 0xFE19], [0xFE30, 0xFE6F], [0xFF00, 0xFF60], [0xFFE0, 0xFFE6], [0x20000, 0x2FFFD], [0x30000, 0x3FFFD]];
  var BLANK_LETTERS = [0x115F, 0x1160, 0x2800, 0x3164, 0xFFA0];   // drawn as nothing: an invisible name
  var DROPPED = /[\p{C}\p{Mn}\p{Me}\p{Zl}\p{Zp}]/u, SPACE = /\p{Zs}/u;
  function inRanges(point, ranges) { return ranges.some(function (r) { return point >= r[0] && point <= r[1]; }); }
  function cleanName(value) {   // repeats until stable: dropping a character can put two letters side by side that NFC then joins (Hangul jamo)
    if (typeof value !== 'string') return '';
    for (var result = cleanNameOnce(value), again = cleanNameOnce(result); again !== result; again = cleanNameOnce(result)) result = again;
    return result;
  }
  function cleanNameOnce(value) {
    var text = Array.from(Array.from(value).slice(0, NAME_INPUT * 2).join('').normalize('NFC')).slice(0, NAME_INPUT);
    var out = [], width = 0, full = false, haveEmoji = false, attach = '';
    text.forEach(function (ch) {
      var point = ch.codePointAt(0);
      if (inRanges(point, EMOJI_RANGES)) {
        var tone = point >= 0x1F3FB && point <= 0x1F3FF, flag = point >= 0x1F1E6 && point <= 0x1F1FF;
        if (!haveEmoji && !tone) { haveEmoji = true; attach = flag ? 'flag' : 'base'; out.push(ch); }
        else if ((tone && attach.indexOf('base') >= 0) || (flag && attach === 'flag')) { out.push(ch); attach = tone ? attach.replace('base', '') : ''; }
        else attach = '';
        return;
      }
      if (point === 0xFE0F && attach.indexOf('base') >= 0 && out[out.length - 1] !== ch) { out.push(ch); return; }
      attach = '';
      if (BLANK_LETTERS.indexOf(point) >= 0 || DROPPED.test(ch)) return;
      if (SPACE.test(ch)) { if (!out.length || out[out.length - 1] === ' ') return; ch = ' '; point = 32; }
      var size = inRanges(point, WIDE_RANGES) ? 2 : 1;
      if (full || width + size > NAME_WIDTH) { full = true; return; }
      out.push(ch); width += size;
    });
    return out.join('').replace(/^ +| +$/g, '');
  }

  function addRoomOptions(message, options) {
    if (!options) return message;
    if (options.name !== undefined) message.name = cleanName(options.name);
    if (options.lobby === true) message.lobby = true;   // ROOM-FLOW R12: a lobby room starts on the host's `begin`
    if (options.claim !== undefined) {
      if (!(Number.isInteger(options.claim) && options.claim >= 1 && options.claim <= MAX_TEAM_SIZE)) throw new RangeError('claim must be an integer from 1 to ' + MAX_TEAM_SIZE);
      message.claim = options.claim;
    }
    if (options.teamSize !== undefined && options.teamSize !== 1) {
      if (!validTeamSize(options.teamSize)) throw new RangeError('teamSize must be an integer from 1 to ' + MAX_TEAM_SIZE);
      message.team_size = options.teamSize;
    }
    if (options.units !== undefined) {
      if (!Array.isArray(options.units) || options.units.length > MAX_TEAM_SIZE ||
          options.units.some(function (hero) { return typeof hero !== 'string' || !hero; })) {
        throw new TypeError('units must be at most ' + MAX_TEAM_SIZE + ' hero ids');
      }
      message.units = options.units.slice();
    }
    if (typeof options.scene === 'string') message.scene = options.scene;
    if (options.solo === true) message.solo = true;
    if (typeof options.hostSideChoice === 'string') message.host_side_choice = options.hostSideChoice;
    return message;
  }

  function copyLog(log) { return log.slice(); }

  function relaySocketUrl(value) {
    if (typeof value !== 'string' || !value) return '';
    var parsed = new URL(value);
    if (parsed.pathname === '' || parsed.pathname === '/') {
      parsed.pathname = '/ws';
    }
    return parsed.toString();
  }

  function mapPoint(point, perspective) {
    if (!point || typeof point !== 'object') return point;
    var copy = Object.assign({}, point);
    if (typeof copy.x === 'number') copy.x = perspective.x(copy.x);
    return copy;
  }

  function mapRelayMessage(message, perspective, toWorld) {
    if (!perspective || !message || typeof message !== 'object') return message;
    var copy = Object.assign({}, message);
    // The relay is permanently world-frame. Only action/judge payloads carry
    // coordinates or directions, so room bootstrap seat names stay untouched.
    if (copy.type && copy.type !== 'action' && copy.type !== 'judge') return copy;
    ['x', 'startX', 'targetX', 'resultX', 'claimedX', 'knockback'].forEach(function (key) {
      if (typeof copy[key] === 'number') copy[key] = perspective.x(copy[key]);
    });
    ['start', 'claimed_landing', 'position', 'result'].forEach(function (key) {
      if (copy[key] && typeof copy[key] === 'object') copy[key] = mapPoint(copy[key], perspective);
    });
    if (typeof copy.unit === 'string') copy.unit = toWorld ? perspective.worldUnitId(copy.unit) : perspective.unitId(copy.unit);
    if (copy.side === 'left' || copy.side === 'right') copy.side = toWorld ? perspective.worldSide(copy.side) : perspective.side(copy.side);
    if (typeof copy.dirX === 'number') copy.dirX = toWorld ? perspective.worldDirX(copy.dirX) : perspective.dirX(copy.dirX);
    if (typeof copy.wind === 'number') copy.wind = perspective.wind(copy.wind);
    return copy;
  }

  function createClient(options) {
    if (!options || typeof options.socketFactory !== 'function') throw new TypeError('socketFactory is required');
    if (typeof options.now !== 'function') throw new TypeError('now is required');
    if (typeof options.setTimeoutFn !== 'function') throw new TypeError('setTimeoutFn is required');

    var socketFactory = options.socketFactory;
    var now = options.now;
    var setTimeoutFn = options.setTimeoutFn;
    var perspective = options.perspective || null;
    var socket = null;
    var deliberateClose = false;
    var expectedSeq = 1;
    var lastSeq = 0;
    var replayUntil = 0;   // the newest sequence number the relay says exists: below it this client is still catching up
    var buffered = Object.create(null);
    var listeners = [];
    var statusListeners = [];
    var reconnectStartedAt = null;
    var reconnectAttempt = 0;
    var seatToken = typeof options.seatToken === 'string' ? options.seatToken : '';
    var hashesByRound = Object.create(null);
    var match = {
      status: 'connecting', seat: null, round: null, phase: null,
      seed: null, scene: null, teamSize: 1, heroes: null, owners: null, log: []
    };

    function snapshot() {
      return {
        status: match.status,
        seat: match.seat,
        round: match.round,
        phase: match.phase,
        seed: match.seed,
        scene: match.scene,
        teamSize: match.teamSize,
        heroes: match.heroes,
        owners: match.owners,
        log: copyLog(match.log)
      };
    }

    function notifyStatus() {
      var state = snapshot();
      statusListeners.slice().forEach(function (listener) { listener(state.status, state); });
    }

    function setStatus(value) {
      if (match.status === value) return;
      if (match.status === 'reconnecting' && value !== 'closed') { reconnectStartedAt = null; reconnectAttempt = 0; }   // back to a live state: the next drop starts a fresh 60 s window (R5A-2)
      match.status = value;
      notifyStatus();
    }

    function notifyMessage(message) {
      var state = snapshot();
      listeners.slice().forEach(function (listener) { listener(message, state); });
    }

    // Connection model (red-team R3B-1, R4B-1..3, R5A-1..4). A real WebSocket throws InvalidStateError on send() while CONNECTING, and a client can sit between two
    // sockets, so nothing is written unless the socket is open:
    //  - bootstrapMsg: the create_room / join that has not yet been answered with a seat token. It is NOT queued; it is written first on EVERY new socket until a token
    //    arrives (a seat that never got a token has nothing to resume).
    //  - a seated client resumes FIRST on a reconnect socket; messages sent while no socket was open follow it from the outbox.
    //  - the outbox survives socket changes, is bounded, and is dropped only by close().
    //  - awaitingAnswer: a resume / replay was written on a reconnect socket and its room_state has not come back; only an error in that window ends the client.
    var outbox = [];
    var bootstrapMsg = null;
    var awaitingAnswer = false;
    var MAX_OUTBOX = 16;
    var TRANSIENT_ERRORS = ['seat_in_use', 'server_busy', 'rate_limited'];
    // Lost messages (red-team R6A-2; the sequence-number-and-acknowledge rule of game netcode): an action or end_turn that was written on a socket which then died may never have
    // reached the relay. Each stays in `unacked` until its own echo (same seat_id, ordered log) comes back; after a resume, once the replayed log has been applied, whatever
    // is still unacknowledged is sent again. The relay refuses duplicates (action_already_submitted, stale_or_out_of_turn), so a resend is safe. judge is NOT tracked: in 1v1
    // the relay has no duplicate guard for it. `written` = written to the current socket; `resend` = was written before the last drop.
    var unacked = [];
    var mySeatId = '';
    var resendAt = null;
    function track(kind, message) {
      var entry = { kind: kind, message: message, written: send(message) === true, resend: false };
      if (!seatToken) return;                       // not seated yet: nothing to resume, nothing to resend
      unacked.push(entry);
      if (unacked.length > MAX_OUTBOX) unacked.shift();
    }
    function markDropped() { unacked.forEach(function (entry) { entry.resend = entry.resend || entry.written; entry.written = false; }); }   // what was written to a socket that died may not have arrived (R6A-2, R7A-2)
    function ackEcho(message) {
      if (message.seat_id !== mySeatId || (message.type !== 'action' && message.type !== 'end_turn')) return;
      for (var i = 0; i < unacked.length; i++) if (unacked[i].kind === message.type) { unacked.splice(i, 1); return; }
    }
    function maybeResend() {
      if (resendAt === null || lastSeq < resendAt) return;
      resendAt = null;
      unacked.forEach(function (entry) { if (entry.resend) { entry.resend = false; entry.written = send(entry.message) === true; } });
    }
    function isOpen(candidate) { return !!candidate && typeof candidate.send === 'function' && (candidate.readyState === undefined || candidate.readyState === 1); }
    function isBootstrap(message) { return message.type === 'create_room' || message.type === 'join'; }
    function send(message) {
      if (deliberateClose || match.status === 'closed') throw new Error('relay socket is not open');
      if (!seatToken && isBootstrap(message)) bootstrapMsg = message;
      if (isOpen(socket)) { socket.send(JSON.stringify(message)); return true; }
      if (!socket && match.status !== 'reconnecting') throw new Error('relay socket is not open');
      if (message === bootstrapMsg) return false;   // written first when a socket opens
      outbox.push(JSON.stringify(message));
      if (outbox.length > MAX_OUTBOX) outbox.shift();
      return false;
    }
    function flushOutbox(openSocket) {
      while (outbox.length) {
        var text = outbox[0];
        openSocket.send(text);   // a throw leaves the rest queued; the socket is broken and its close handler schedules the next attempt
        outbox.shift();
      }
    }

    function updateFromRoomState(message) {
      if (typeof message.seat === 'string') match.seat = message.seat;
      if (typeof message.team === 'string') match.seat = message.team;
      if (typeof message.seed === 'number') match.seed = message.seed;
      if (typeof message.scene === 'string') match.scene = message.scene;
      // The relay writes team_size only for team matches; its absence means one unit per side.
      match.teamSize = validTeamSize(message.team_size) ? message.team_size : 1;
      // A snapshot that is ahead of the ordered log (resume: the room state arrives first, the missed messages follow) must not move the round on,
      // or the replayed actions of the missed round would be dropped as old and the page would wait for them for ever. The replayed end_turns move it.
      if (typeof message.last_seq === 'number') replayUntil = Math.max(replayUntil, message.last_seq);
      var catchingUp = match.round !== null && message.started && (awaitingAnswer || replayUntil > lastSeq);
      if (!catchingUp) {
        if (typeof message.round === 'number') match.round = message.round;
        if (typeof message.phase === 'string') match.phase = message.phase;
      }
      if (match.status === 'out_of_sync' && message.started) return;   // a snapshot does not clear a detected desync (external review); a reset (started false) does
      if (message.started || typeof message.seed === 'number') setStatus('playing');
      else setStatus('waiting');   // a room_state also ends 'reconnecting' (R5A-3)
    }

    function isOldRound(message) {
      return typeof message.round === 'number' && typeof match.round === 'number' &&
        message.round < match.round;
    }

    // start.heroes and start.owners are world frame (left is red). The snapshot keeps them in the page's frame: `left` is always the local team.
    function applyTeams(message) {
      match.heroes = null;
      match.owners = null;
      if (match.teamSize < 2) return;
      if (message.heroes && typeof message.heroes === 'object') {
        match.heroes = { left: [], right: [] };
        ['left', 'right'].forEach(function (worldSide) {
          var localSide = perspective ? perspective.side(worldSide) : worldSide;
          match.heroes[localSide] = Array.isArray(message.heroes[worldSide]) ? message.heroes[worldSide].slice() : [];
        });
      }
      if (message.owners && typeof message.owners === 'object') {
        match.owners = {};
        Object.keys(message.owners).forEach(function (worldUnit) {
          match.owners[perspective ? perspective.unitId(worldUnit) : worldUnit] = message.owners[worldUnit];
        });
      }
    }

    function checkUnit(unit, required) {
      if (match.teamSize < 2) return;
      if (unit === undefined && !required) return;
      if (!isTeamUnitId(unit, match.teamSize)) throw new TypeError('unit must be left_0..left_' + (match.teamSize - 1) + ' or right_0..right_' + (match.teamSize - 1));
    }

    function applyMessage(message) {
      match.log.push(message);
      if (message.type !== 'start' && isOldRound(message)) return;
      if (message.type === 'room_state') {
        updateFromRoomState(message);
      } else if (message.type === 'start') {
        match.seed = message.seed;
        match.scene = message.scene;
        match.round = message.round;
        match.phase = message.phase;
        match.teamSize = validTeamSize(message.team_size) ? message.team_size : 1;
        applyTeams(message);
        setStatus('playing');
      } else if (message.type === 'seat_left' && message.ai && message.owners && match.owners) {   // ROOM-FLOW R9: a lost AI seat's units have new owners (world frame, like `start`)
        match.owners = {};
        Object.keys(message.owners).forEach(function (worldUnit) {
          match.owners[perspective ? perspective.unitId(worldUnit) : worldUnit] = message.owners[worldUnit];
        });
      } else if (message.type === 'end_turn') {
        if (typeof message.next_round === 'number') match.round = message.next_round;
        if (typeof message.next_phase === 'string') match.phase = message.next_phase;
      } else if (message.type === 'round_hash' && typeof message.round === 'number' && typeof message.hash === 'string') {
        var hashes = hashesByRound[message.round] || (hashesByRound[message.round] = Object.create(null));
        hashes[message.seat_id || String(Object.keys(hashes).length)] = message.hash;
        var values = Object.keys(hashes).map(function (key) { return hashes[key]; });
        if (values.some(function (hash) { return hash !== values[0]; })) setStatus('out_of_sync');
      } else if (message.type === 'out_of_sync') {
        setStatus('out_of_sync');
      } else if (message.type === 'lobby_reset') {   // R6b: back to the lobby of the same room: the match is over, the next `start` begins a new one
        match.round = null; match.phase = null; match.seed = null; match.heroes = null; match.owners = null; match.log = [];
        hashesByRound = Object.create(null); unacked = []; resendAt = null; replayUntil = lastSeq;
        setStatus('waiting');
      }
      notifyMessage(message);
    }

    function receive(raw) {
      var data = raw && raw.data !== undefined ? raw.data : raw;
      var message;
      try { message = typeof data === 'string' ? JSON.parse(data) : data; } catch (error) { return; }
      if (!message || typeof message !== 'object') return;
      message = mapRelayMessage(message, perspective, false);
      if (typeof message.seat_token === 'string' && message.seat_token) { seatToken = message.seat_token; }   // with a token the bootstrap message is never replayed again (a reconnect resumes instead)
      if (message.type === 'kicked') {   // cross-check: the relay removed this seat and closes the socket; reconnecting would only resume a dead token
        deliberateClose = true; outbox = []; bootstrapMsg = null; unacked = []; resendAt = null;
        notifyMessage(message);
        try { if (socket && typeof socket.close === 'function') socket.close(); } catch (e) { /* closing already */ }
        setStatus('closed');
        return;
      }
      if (message.type === 'room_state' && typeof message.seq !== 'number') {
        if (Number.isInteger(message.first_seq) && message.first_seq > expectedSeq) {
          expectedSeq = message.first_seq; lastSeq = message.first_seq - 1;
          Object.keys(buffered).forEach(function (k) { if (+k < expectedSeq) delete buffered[k]; });
          match.round = null; match.phase = null; match.seed = null; match.heroes = null; match.owners = null; match.log = [];
          hashesByRound = Object.create(null);
        }   // R6b, red team A2: the room went back to the lobby and its log starts here; what came before is gone (a joiner, or a resume across the reset)
        if (typeof message.seat_id === 'string') mySeatId = message.seat_id;
        if (awaitingAnswer && seatToken && typeof message.last_seq !== 'number' && typeof message.seat_token !== 'string') { notifyMessage(message); updateFromRoomState(message); return; }   // a broadcast that overtook the resume answer (no token, no last_seq): not the answer (external review)
        if (awaitingAnswer && seatToken) resendAt = typeof message.last_seq === 'number' ? message.last_seq : lastSeq;   // resend what is still unacknowledged once the replay up to here is applied
        awaitingAnswer = false;
      }
      if (message.type === 'room_state' && typeof message.seq !== 'number') {
        updateFromRoomState(message);
        notifyMessage(message);
        maybeResend();
        return;
      }
      if (message.type === 'error' && message.code && awaitingAnswer) {
        awaitingAnswer = false;
        var failed = socket; socket = null; try { if (failed) failed.close(); } catch (e) { /* already closing */ }
        markDropped();   // this socket is abandoned without a close event for the client: what was written to it counts as lost too
        if (TRANSIENT_ERRORS.indexOf(message.code) >= 0) scheduleReconnect();   // the relay has not noticed the old socket yet / is busy: try again with the backoff (red-team R6A-1)
        else setStatus('closed');                                                  // the relay refused this seat for good (unknown_token, resume_expired, unknown_code, room_full ...)
        notifyMessage(message);
        return;
      }
      // action_ack names an already ordered action sequence. It is a private
      // receipt, not another entry in the global ordered log.
      if (message.type === 'action_ack') {
        notifyMessage(message);
        return;
      }
      if (typeof message.seq !== 'number' || message.seq < 1 || Math.floor(message.seq) !== message.seq) {
        notifyMessage(message);
        return;
      }
      if (message.seq < expectedSeq || buffered[message.seq]) return;
      buffered[message.seq] = message;
      while (buffered[expectedSeq]) {
        var next = buffered[expectedSeq];
        delete buffered[expectedSeq];
        lastSeq = expectedSeq;
        expectedSeq += 1;
        ackEcho(next);
        applyMessage(next);
      }
      maybeResend();
    }

    function reconnect() {
      if (match.status === 'closed' || deliberateClose) return;
      try {
        socket = socketFactory();
        attachSocket(socket, true);
      } catch (error) {
        scheduleReconnect();
      }
    }

    function scheduleReconnect() {
      if (deliberateClose || match.status === 'closed') return;
      if (reconnectStartedAt === null) reconnectStartedAt = now();
      if (now() - reconnectStartedAt >= RECONNECT_LIMIT_MS) {
        setStatus('closed');
        return;
      }
      setStatus('reconnecting');
      var delay = RECONNECT_DELAYS_MS[Math.min(reconnectAttempt, RECONNECT_DELAYS_MS.length - 1)];
      reconnectAttempt += 1;
      setTimeoutFn(function () {
        if (now() - reconnectStartedAt >= RECONNECT_LIMIT_MS) {
          setStatus('closed');
          return;
        }
        reconnect();
      }, delay);
    }

    function attachSocket(nextSocket, isReconnect) {
      nextSocket.onopen = function () {
        if (socket !== nextSocket) return;
        try {
          if (seatToken && (isReconnect || !bootstrapMsg)) {   // seated: resume FIRST, the outbox follows (also a page that reloaded with its stored seat token, red team B4)
            awaitingAnswer = true;
            nextSocket.send(JSON.stringify({ type: 'resume', seat_token: seatToken, last_seq: lastSeq }));
          } else if (bootstrapMsg) {                 // not seated yet: the first message again (initial or reconnect socket)
            awaitingAnswer = true;   // the first socket too: an error answer to create/join is handled (transient: reconnect, permanent: closed) (external review)
            nextSocket.send(JSON.stringify(bootstrapMsg));
          }
          flushOutbox(nextSocket);
          unacked.forEach(function (entry) { entry.written = true; });   // the messages that waited in the outbox are on this socket now
        } catch (error) { awaitingAnswer = false; /* the socket is broken; its close event schedules the next attempt */ }
      };
      nextSocket.onmessage = receive;
      nextSocket.onerror = function () {};
      nextSocket.onclose = function () {
        if (socket !== nextSocket || deliberateClose) return;
        socket = null;
        awaitingAnswer = false;
        markDropped();
        scheduleReconnect();
      };
    }

    function openInitialSocket() {
      try {
        socket = socketFactory();
        attachSocket(socket, false);
      } catch (error) {
        scheduleReconnect();
      }
    }

    openInitialSocket();

    return {
      // options (all optional): teamSize 1..3, units [hero ids of this seat], scene, solo, hostSideChoice. Without options the wire is the one-versus-one wire of relay-v0.
      createRoom: function (options) { send(addRoomOptions({ type: 'create_room', seat: 'red' }, options)); },
      join: function (code, seat, options) {
        if (typeof code !== 'string' || !code.trim()) throw new TypeError('code is required');
        if (typeof seat !== 'string' || !seat) throw new TypeError('seat is required');
        match.seat = seat;
        var message = { type: 'join', code: code.trim().toUpperCase(), seat: seat };
        if (options && options.units !== undefined) addRoomOptions(message, { units: options.units });
        if (options && options.name !== undefined) addRoomOptions(message, { name: options.name });
        if (options && options.claim !== undefined) addRoomOptions(message, { claim: options.claim });
        if (options && typeof options.invite === 'string') message.invite = options.invite;
        if (options && options.aiHostToken) message.ai_host_token = String(options.aiHostToken);   // ROOM-FLOW R9: the host's own AI filler proves itself with the host's seat token
        send(message);
      },
      // Marks this seat ready. options: units (replace this seat's hero list), teamSize and hostSideChoice (the room creator only; others are ignored by the relay).
      sendReady: function (options) { send(addRoomOptions({ type: 'ready' }, options && { teamSize: options.teamSize, units: options.units, hostSideChoice: options.hostSideChoice, name: options.name })); },
      setName: function (name) { send({ type: 'set_name', name: cleanName(name) }); },
      // ROOM-FLOW lobby calls (R3, R4, R6, R11, R12, R13); the relay answers with room_state, or an error for a call that is not allowed
      unready: function () { send({ type: 'unready' }); },
      move: function (options) { var m = { type: 'move' }; if (options && options.team) m.team = options.team; if (options && options.claim !== undefined) m.claim = options.claim; send(m); },
      begin: function (on) { send({ type: 'begin', on: on !== false }); },
      roomOptions: function (options) { var m = { type: 'room_options' }; ['allow_ai', 'allow_mcp'].forEach(function (k) { if (options && typeof options[k] === 'boolean') m[k] = options[k]; }); send(m); },
      invite: function (note) { send(note ? { type: 'invite', note: String(note) } : { type: 'invite' }); },
      inviteCancel: function (by) { send(by ? { type: 'invite_cancel', by: by } : { type: 'invite_cancel' }); },
      kick: function (seatId) { send({ type: 'kick', seat_id: seatId }); },
      resetLobby: function () { send({ type: 'reset_lobby' }); },
      ping: function () { try { send({ type: 'ping' }); } catch (e) { /* not open */ } },
      leave: function () { try { if (isOpen(socket)) socket.send(JSON.stringify({ type: 'leave' })); } catch (e) { /* already gone */ } this.close(); },   // the seat is released at once (close alone keeps it for the grace period)
      sendAction: function (action) {
        if (!action || typeof action !== 'object') throw new TypeError('action is required');
        checkUnit(action.unit, false);
        track('action', Object.assign({ type: 'action' }, mapRelayMessage(action, perspective, true)));
      },
      sendJudge: function (judge) {
        if (!judge || typeof judge !== 'object') throw new TypeError('judge is required');
        checkUnit(judge.unit, judge.hit === true);
        send(Object.assign({ type: 'judge' }, mapRelayMessage(judge, perspective, true)));
      },
      endTurn: function (round, phase) { track('end_turn', { type: 'end_turn', round: round, phase: phase }); },
      sendRoundHash: function (round, hash) {
        if (match.teamSize > 1 && !HASH_FORMAT.test(String(hash))) throw new TypeError('hash must be 8 lowercase hex characters');
        send({ type: 'round_hash', round: round, hash: hash });
      },
      onMessage: function (fn) {
        if (typeof fn !== 'function') throw new TypeError('message listener must be a function');
        listeners.push(fn);
        return function () { listeners = listeners.filter(function (item) { return item !== fn; }); };
      },
      onStatus: function (fn) {
        if (typeof fn !== 'function') throw new TypeError('status listener must be a function');
        statusListeners.push(fn);
        return function () { statusListeners = statusListeners.filter(function (item) { return item !== fn; }); };
      },
      state: snapshot,
      seatToken: function () { return seatToken; },
      setPerspective: function (nextPerspective) { perspective = nextPerspective || null; },
      close: function () {
        deliberateClose = true; outbox = []; bootstrapMsg = null; unacked = []; resendAt = null;
        if (socket && typeof socket.close === 'function') socket.close();
        setStatus('closed');
      }
    };
  }

  return { cleanName: cleanName, MAX_TEAM_SIZE: MAX_TEAM_SIZE, createClient: createClient, relaySocketUrl: relaySocketUrl, isTeamUnitId: isTeamUnitId };
});

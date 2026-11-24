#!/usr/bin/env node
'use strict';
var assert = require('assert');
var fs = require('fs');
var path = require('path');
var RelayClient = require('../js/relay_client.js');
var page = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');
assert.match(page, /id="room-create"/);
assert.match(page, /id="room-join"/);
assert.match(page, /id="room-qr"/);
assert.match(page, /new URLSearchParams\(location\.search\)\.get\("relay"\)/);
assert.match(page, /new URLSearchParams\(location\.search\)\.get\("room"\)/);
assert.match(page, /client\.join\(joinRoomCode, relayJoinSeat\)/);   // unit slot fill: the joiner takes relayJoinSeat
assert.match(page, /relayJoinSeat = "white"/, 'a joiner still takes white by default');
assert.match(page, /QrCode\.draw\(qr, url/);
function Socket() { this.sent = []; }
Socket.prototype.send = function (text) { this.sent.push(JSON.parse(text)); };
var socket = new Socket();
var client = RelayClient.createClient({ socketFactory: function () { return socket; }, now: Date.now, setTimeoutFn: function () {} });
socket.onopen();
client.createRoom();
assert.deepStrictEqual(socket.sent[0], { type: 'create_room', seat: 'red' });
socket.onmessage({ data: JSON.stringify({ type: 'room_state', code: 'CANDLE', seat: 'red', started: false }) });
client.join('CANDLE', 'white');
assert.deepStrictEqual(socket.sent[1], { type: 'join', code: 'CANDLE', seat: 'white' });
console.log('join flow fake socket and QR wiring: ok');

#!/usr/bin/env python3
"""Room-code and anonymous join-boundary checks."""
import asyncio
import unittest
from unittest.mock import patch

import pk_relay as relay


class Socket:
    def __init__(self): self.messages = []
    async def send(self, value): self.messages.append(relay.json.loads(value))


class RoomCodeTests(unittest.TestCase):
    def test_alphabet_length_and_100000_unique_draws(self):
        server = relay.RelayServer()
        for _ in range(100000):
            code = server._new_code()
            self.assertEqual(len(code), 6)
            self.assertTrue(set(code) <= set(relay.CODE_ALPHABET))
            self.assertNotIn(code, server.rooms)
            server.rooms[code] = relay.Room(code)

    def test_new_code_redraws_on_collision(self):
        server = relay.RelayServer()
        server.rooms['ABC234'] = relay.Room('ABC234')
        with patch.object(relay, 'make_code', side_effect=['ABC234', 'DEF567']):
            self.assertEqual(server._new_code(), 'DEF567')

    def test_unknown_code_is_trimmed_uppercased_and_rate_limited_per_socket(self):
        async def check():
            server, socket, guesses = relay.RelayServer(), Socket(), []
            room = relay.Room('ABC234')
            server.rooms[room.code] = room
            joined_room, entry = await server._dispatch(socket, None, None, {'type': 'join', 'code': ' abc234 ', 'seat': 'white'}, guesses)
            self.assertIs(joined_room, room)
            self.assertIsNotNone(entry)
            other, _ = await server._dispatch(socket, None, None, {'type': 'join', 'code': ' bad999 '}, [])
            self.assertIsNone(other)
            self.assertEqual(socket.messages[-1]['code'], 'unknown_code')
            socket.messages.clear()
            for _ in range(relay.MAX_WRONG_CODES_PER_MINUTE + 1):
                await server._dispatch(socket, None, None, {'type': 'join', 'code': 'BAD999'}, guesses)
            self.assertEqual(socket.messages[-1]['code'], 'rate_limited')
        asyncio.run(check())

    def test_code_is_not_derived_from_match_seed(self):
        self.assertNotIn('seed', relay.make_code.__code__.co_varnames)


if __name__ == '__main__':
    unittest.main()

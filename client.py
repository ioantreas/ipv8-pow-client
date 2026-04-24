import asyncio

from ipv8.community import Community
from ipv8.lazy_community import lazy_wrapper
from ipv8.messaging.payload import Payload
from ipv8.peer import Peer
from ipv8.configuration import (
    ConfigBuilder,
    WalkerDefinition,
    Strategy,
    default_bootstrap_defs,
)
from ipv8_service import IPv8


COMMUNITY_ID = bytes.fromhex("2c1cc6e35ff484f99ebdfb6108477783c0102881")

SERVER_PUBLIC_KEY = bytes.fromhex(
    "4c69624e61434c504b3a86b23934a28d669c390e2d1fc0b0870706c4591cc0cb178bc5a811da6d87d27ef319b2638ef60cc8d119724f4c53a1ebfad919c3ac4136c501ce5c09364e0ebb"
)

EMAIL = "aioannou@student.tudelft.nl"
GITHUB_URL = "https://github.com/ioantreas/ipv8-pow-client"
NONCE = 249808264


class Submission(Payload):
    msg_id = 1
    format_list = ["varlenHutf8", "varlenHutf8", "q"]

    def __init__(self, email, github_url, nonce):
        self.email = email
        self.github_url = github_url
        self.nonce = nonce

    def to_pack_list(self):
        return [
            ("varlenHutf8", self.email),
            ("varlenHutf8", self.github_url),
            ("q", self.nonce),
        ]

    @classmethod
    def from_unpack_list(cls, email, github_url, nonce):
        return cls(email, github_url, nonce)


class Response(Payload):
    msg_id = 2
    format_list = ["?", "varlenHutf8"]

    def __init__(self, success, message):
        self.success = success
        self.message = message

    def to_pack_list(self):
        return [
            ("?", self.success),
            ("varlenHutf8", self.message),
        ]

    @classmethod
    def from_unpack_list(cls, success, message):
        return cls(success, message)


class PowCommunity(Community):
    community_id = COMMUNITY_ID

    def __init__(self, settings):
        super().__init__(settings)
        self.add_message_handler(Response, self.on_response)
        self.register_task("submit_when_server_found", self.submit_when_server_found)

    async def submit_when_server_found(self):
        print("Searching for server...")

        sent = False

        while not sent:
            await asyncio.sleep(3)

            peers = self.get_peers()
            print(f"Discovered {len(peers)} peers")

            for peer in peers:
                if peer.public_key.key_to_bin() == SERVER_PUBLIC_KEY:
                    print("Found server. Sending submission...")
                    self.ez_send(peer, Submission(EMAIL, GITHUB_URL, NONCE))
                    sent = True
                    break

    @lazy_wrapper(Response)
    def on_response(self, peer: Peer, payload: Response):
        if peer.public_key.key_to_bin() != SERVER_PUBLIC_KEY:
            print("Ignoring response from non-server peer")
            return

        print("\n=== SERVER RESPONSE ===")
        print("Success:", payload.success)
        print("Message:", payload.message)


async def main():
    builder = ConfigBuilder().clear_keys().clear_overlays()

    builder.add_key("my peer", "curve25519", "mykey.pem")

    builder.add_overlay(
        "PowCommunity",
        "my peer",
        [
            WalkerDefinition(
                Strategy.RandomWalk,
                20,
                {"timeout": 3.0},
            )
        ],
        default_bootstrap_defs,
        {},
        [],
    )

    ipv8 = IPv8(
        builder.finalize(),
        extra_communities={"PowCommunity": PowCommunity},
    )

    await ipv8.start()

    try:
        while True:
            await asyncio.sleep(1)
    finally:
        await ipv8.stop()


if __name__ == "__main__":
    asyncio.run(main())
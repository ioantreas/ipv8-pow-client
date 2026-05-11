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


COMMUNITY_ID = bytes.fromhex("4c61623247726f75705369676e696e6732303236")

SERVER_PUBLIC_KEY = bytes.fromhex(
    "4c69624e61434c504b3a82e33614a342774e084af80835838d6dbdb64a537d3ddb6c1d82011a7f101553cda40cf5fa0e0fc23abd0a9c4f81322282c5b34566f6b8401f5f683031e60c96"
)

MEMBER1_KEY = bytes.fromhex("4c69624e61434c504b3a6ddc887fd7a98d41126d24eb4d3349f27683c555698c94b80b0a11bb43c2f6765645e827f4c331c3eb653f1f52d38683423e6b013c25f3157ed8adbf86aa997a")
MEMBER2_KEY = bytes.fromhex("4c69624e61434c504b3ae9a6f3ee192bcb9833fe647728a19e74d6b7fe2e42efe96f4de40d4922aa7a3dcb7c47a5f1776db9902548aab9fb4ef06dd1dc39b12f99f5e8326334ebe7fcd3")
MEMBER3_KEY = bytes.fromhex("4c69624e61434c504b3a87ca1dee80e128d6ad389fb7b2fd1f99bfa86377fdf3815e97b734d767c48840dc818b5467b27b8fad1e434e07005e05eac40a726334a5b3a83b289a51ca097c")


class RegisterGroup(Payload):
    msg_id = 1

    def __init__(self, member1_key, member2_key, member3_key):
        self.member1_key = member1_key
        self.member2_key = member2_key
        self.member3_key = member3_key

    def to_pack_list(self):
        return [
            ("varlenH", self.member1_key),
            ("varlenH", self.member2_key),
            ("varlenH", self.member3_key),
        ]

    @classmethod
    def from_unpack_list(cls, member1_key, member2_key, member3_key):
        return cls(member1_key, member2_key, member3_key)


class RegisterResponse(Payload):
    msg_id = 2
    format_list = ["?", "varlenHutf8", "varlenHutf8"]

    def __init__(self, success, group_id, message):
        self.success = success
        self.group_id = group_id
        self.message = message

    def to_pack_list(self):
        return [
            ("?", self.success),
            ("varlenHutf8", self.group_id),
            ("varlenHutf8", self.message),
        ]

    @classmethod
    def from_unpack_list(cls, success, group_id, message):
        return cls(success, group_id, message)


class Lab2Community(Community):
    community_id = COMMUNITY_ID

    def __init__(self, settings):
        super().__init__(settings)
        self.add_message_handler(RegisterResponse, self.on_register_response)
        self.register_task("register_when_server_found", self.register_when_server_found)

    async def register_when_server_found(self):
        print("Searching for Lab 2 server...")

        while True:
            await asyncio.sleep(3)

            peers = self.get_peers()
            print(f"Discovered {len(peers)} peers")

            for peer in peers:
                if peer.public_key.key_to_bin() == SERVER_PUBLIC_KEY:
                    print("Found server. Registering group...")

                    self.ez_send(
                        peer,
                        RegisterGroup(
                            MEMBER1_KEY,
                            MEMBER2_KEY,
                            MEMBER3_KEY,
                        ),
                    )
                    return

    @lazy_wrapper(RegisterResponse)
    def on_register_response(self, peer: Peer, payload: RegisterResponse):
        if peer.public_key.key_to_bin() != SERVER_PUBLIC_KEY:
            print("Ignoring response from non-server peer")
            return

        print("\n=== GROUP REGISTRATION RESPONSE ===")
        print("Success:", payload.success)
        print("Group ID:", payload.group_id)
        print("Message:", payload.message)


async def main():
    builder = ConfigBuilder().clear_keys().clear_overlays()

    # Must be the SAME key from Lab 1
    builder.add_key("my peer", "curve25519", "mykey.pem")

    builder.add_overlay(
        "Lab2Community",
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
        extra_communities={"Lab2Community": Lab2Community},
    )

    await ipv8.start()

    try:
        while True:
            await asyncio.sleep(1)
    finally:
        await ipv8.stop()


if __name__ == "__main__":
    asyncio.run(main())
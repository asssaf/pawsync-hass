import argparse
import asyncio
import hashlib
import logging
import random
import uuid
from copy import deepcopy

import aiohttp

logger = logging.getLogger(__name__)


class PawsyncClient:
    def __init__(self, session: aiohttp.ClientSession, terminal_id: str | None = None):
        self.session = session
        if terminal_id is None:
            terminal_id = str(uuid.uuid1()).replace("-", "")[-33:]

        self.terminalId = terminal_id
        trace_uuid = str(uuid.uuid4()).replace("-", "")
        self.traceId = "PET" + trace_uuid[-16:] + "-" + f"{random.randint(0, 99999):05}"

        self.context = {
            "acceptLanguage": "en",
            "appID": "psybfyca",
            "clientInfo": "API",
            "clientType": "pawsync",
            "clientVersion": "Pawsync 1.0.85",
            "debugMode": "false",
            "method": "",
            "osInfo": "Android 15",
            "terminalId": self.terminalId,
            "timeZone": "America/Los_Angeles",  # TODO
            "traceId": self.traceId,
            "userCountryCode": "US",
        }

    def request_json(self, data: dict):
        return {"context": self.context, "data": data}

    async def request_post(self, type: str, method: str, data: dict):
        json_payload = deepcopy(self.request_json(data))
        json_payload["context"]["method"] = method

        return await self.session.post(
            f"https://smartapi.pawsync.com/pet/api/{type}/v1/{method}",
            json=json_payload,
        )

    async def login(self, email: str, password: str):
        r = await self.request_post(
            "userManaged",
            "login",
            {
                "email": email,
                "password": hashlib.sha256(password.encode("utf-8")).hexdigest(),
            },
        )

        loginJson = await r.json()
        if loginJson.get("code") != 0 or loginJson.get("result") is None:
            logger.error("login failed: %s", loginJson)
            return False

        self.context["accountID"] = loginJson["result"]["accountId"]
        self.context["token"] = loginJson["result"]["token"]
        return True

    async def get_device_list(self):
        r = await self.request_post("deviceManaged", "deviceList4Pet", {})
        devicesJson = await r.json()
        if devicesJson.get("code") != 0 or devicesJson.get("result") is None:
            logger.error("get_device_list failed: %s", devicesJson)
            return None
        devices = devicesJson["result"]["list"]
        return [Device(self, d) for d in devices]


class Device:
    def __init__(self, client: PawsyncClient, d: dict):
        self.client = client
        self.deviceName = d["deviceName"]
        self.deviceImg = d["deviceImg"]
        self.deviceDefaultImg = d["deviceDefaultImg"]
        self.deviceId = d["deviceId"]
        self.connectionType = d["connectionType"]
        self.secondaryCategory = d["secondaryCategory"]
        self.deviceModel = d["deviceModel"]
        self.configModel = d["configModel"]
        self.bizId = d["bizId"]
        self.petId = d["petId"]
        self.deviceProp = d["deviceProp"]
        self.terminalId = client.terminalId

    async def requestFeed(self, amount: int):
        # Note: the original code had a slightly different JSON structure for bypassV2
        # but used context values. I'll maintain that.
        json_payload = {
            "acceptLanguage": "en",
            "accountID": self.client.context.get("accountID"),
            "appID": self.client.context.get("appID"),
            "appVersion": self.client.context.get("clientVersion"),
            "debugMode": self.client.context.get("debugMode"),
            "method": "bypassV2",
            "phoneBrand": "",
            "phoneOS": self.client.context.get("osInfo"),
            "timeZone": self.client.context.get("timeZone"),
            "token": self.client.context.get("token"),
            "traceId": self.client.context.get("traceId"),
            "userCountryCode": "US",
            "cid": self.deviceId,
            "configModule": self.configModel,
            "payload": {
                "data": {
                    "serving1": amount,
                    "cid": self.deviceId,
                    "configModule": self.configModel,
                },
                "method": "manualFeeding",
                "source": "APP",
            },
        }

        return await self.client.session.post(
            "https://smartapi.pawsync.com/pet/api/deviceManaged/v1/bypassV2",
            json=json_payload,
        )


async def login(
    session: aiohttp.ClientSession,
    email: str,
    password: str,
    terminal_id: str | None = None,
):
    """Deprecated legacy login function for compatibility."""
    client = PawsyncClient(session, terminal_id)
    if await client.login(email, password):
        # We need to set the global context for legacy functions to work
        # But we want to move away from this.
        # For now, let's just return the client.
        return client
    return None


async def getDeviceList(session: aiohttp.ClientSession, logger: logging.Logger):
    """Deprecated legacy getDeviceList function. This will NOT work without a client."""
    raise NotImplementedError("Use PawsyncClient.get_device_list() instead")


if __name__ == "__main__":
    parser = argparse.ArgumentParser("pawsync")
    parser.add_argument("email", type=str)
    parser.add_argument("password", type=str)
    parser.add_argument("--feed", action="store_true")
    parser.add_argument("--amount", type=int, default=12)
    args = parser.parse_args()

    async def impl():
        async with aiohttp.ClientSession() as session:
            client = PawsyncClient(session)
            if not await client.login(args.email, args.password):
                print("Login failed")
                return

            devices = await client.get_device_list()
            if devices is None:
                return

            for d in devices:
                print(vars(d))

            if args.feed and devices:
                f = await devices[0].requestFeed(args.amount)
                print(await f.json())

    asyncio.run(impl())

"""
Mounting daemon.
"""
import hmac
import os
import shutil
from asyncio import StreamReader
from asyncio import StreamWriter

import hashlib

import asyncio
import msgpack

# Define logging stuff.
import sys
from logbook.compat import redirect_logging
from logbook import StreamHandler, Logger

redirect_logging()

StreamHandler(sys.stderr).push_application()

logger = Logger("Mounter")

if not os.getuid() == 0:
    logger.critical("Mounter must be run as root.")
    sys.exit(1)


async def cb(reader: StreamReader, writer: StreamWriter):
    """
    Callback for mounting things.
    """
    # Read 1024 bytes off of the stream.
    data = await reader.read(1024)
    unpacked = msgpack.unpackb(data, use_bin_type=True)
    action = unpacked["action"]
    check = unpacked["check"]
    name = unpacked["name"]
    # Check the HMAC.
    hm = hmac.new(os.environ["MOUNT_PSK"], digestmod="sha256")
    hm.update(name.encode())
    if not hmac.compare_digest(hm.hexdigest(), check):
        # Don't mount it.
        writer.close()
        logger.critical("Bad HMAC recieved! Ending connection")
        return

    # Hash the name with sha256.
    hs = hashlib.sha256(name.encode()).hexdigest()
    if action == "mount":
        sub = await asyncio.create_subprocess_exec(
            "mount", "-v", os.path.join("images", hs + '.img'), os.path.join("volumes", hs)
        )
        rc = await sub.wait()
        if rc:
            logger.critical("Mount returned code {}!".format(rc))
            result = {"success": False, "rc": rc}
        else:
            result = {"success": True, "rc": rc}

    elif action == "unmount":
        sub = await asyncio.create_subprocess_exec(
            "umount", "-v", os.path.join("volumes", hs)
        )
        rc = await sub.wait()
        if rc:
            logger.critical("Umount returned code {}!".format(rc))
            result = {"success": False, "rc": rc}
        else:
            result = {"success": True, "rc": rc}
    else:
        result = {"success": False}

    cc = msgpack.packb(result, use_bin_type=True)

    await writer.write(cc)
    writer.close()

async def main():
    ud = int(sys.argv[2])
    try:
        serv = await asyncio.start_unix_server(cb, path="mounter.sock")
    except OSError as e:
        if e.errno == 98:
            os.remove("mounter.sock")
            serv = await asyncio.start_unix_server(cb, path="mounter.sock")
        else:
            raise
    os.chown("mounter.sock", ud, 0)
    logger.info("Switched Mounter owner to {}.".format(ud))
    logger.info("Started Mounter server.")

loop = asyncio.get_event_loop()
loop.run_until_complete(main())
try:
    loop.run_forever()
except Exception:
    # Remove the socket.
    os.remove("mounter.sock")
    logger.info("Shutting down Mounter.")

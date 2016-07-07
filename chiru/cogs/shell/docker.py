import asyncio
import hashlib
import hmac
import os
import pty

from asyncio.subprocess import STDOUT, PIPE, Process

import msgpack
from logbook import Logger


class DockerInterface:
    """
    A DockerInterface is Chiru's way of interfacing with a Docker container.

    It can input things into stdin on a docker process, and emit stdout.

    Each interface manages a new interface.
    """

    def __init__(self, name: str):
        """
        Create a new shell.

        Name should be the user ID of the user spawning a shell.
        """
        if not os.path.exists("images"):
            os.makedirs("images")

        if not os.path.exists("volumes"):
            os.makedirs("volumes")

        self.subprocess = None
        self.name = name

        hsh = hashlib.sha1()
        hsh.update(self.name.encode())

        self.hashed_name = hsh.hexdigest()

        self.logger = Logger("Chiru::Shell::{}".format(self.name))

    async def open_container(self, *args, image="sundwarf/chiru_shell", memory_limit=32, cpu_quota=1000,
                             autodelete: bool = True, exc: str = "bash"):
        """
        Opens a new container to run things inside.

        You probably don't want to use this method - use `create_shell` instead, which will set up the container and
        the volumes as appropriate.
        """
        # Basic command is docker run.
        command = "run "
        # Add manual arguments.
        command += ' '.join(args)
        # Use `-i` by default. No `-t` otherwise subprocess doesn't like me.
        command += "-i "
        # Give it a name.
        command += "--name {} ".format(self.name)
        # Should it be automatically deleted?
        if autodelete:
            command += "--rm "
        # Set the memory limit and the CPU quota.
        command += "--memory {}M --cpu-quota {} ".format(memory_limit, cpu_quota)
        # Add the image.
        command += "{} ".format(image)
        # Append the command.
        command += exc

        self.logger.info("Creating new container with command: `{}`".format(command))
        self.subprocess = await asyncio.create_subprocess_exec("docker", *command.split(" "),
                                                               stdin=PIPE, stdout=PIPE,
                                                               stderr=STDOUT)

    async def create_shell(self) -> Process:
        """
        Creates a new shell for usage with a channel.

        Returns the subprocess.
        """
        vol_name = self.hashed_name + ".img"
        fp = os.path.join("images", vol_name)
        vp = os.path.join(os.path.abspath("./volumes"), self.hashed_name)
        if not os.path.exists(fp):
            # Make the new loopback image.
            self.logger.info("Creating new loop device for name {}.".format(self.name))
            with open(fp, 'wb') as f:
                # 10MB
                for x in range(0, 10 * 1024):
                    # Write 1024-byte chunks.
                    f.write(bytearray(1024))

            # mkfs.ext4 it
            sub = await asyncio.create_subprocess_exec("mkfs.ext4", fp, stdout=PIPE, stderr=PIPE)
            stdout, stderr = await sub.communicate()
            self.logger.info("Result from mkfs.ext4:\n{}\n{}".format(stdout, stderr))

        if not os.path.exists(vp):
            self.logger.info("Asking Mounter to mount our volume.")
            reader, writer = await asyncio.open_unix_connection("mounter.sock")
            # Send the payload.
            # Compute the hmac.
            hm = hmac.new(os.environ["MOUNTER_PSK"].encode(), digestmod="sha256")
            hm.update(self.name.encode())
            check = hm.hexdigest()

            payload = {"action": "mount", "name": self.name, "check": check}
            writer.write(msgpack.packb(payload, use_bin_type=True))

            response = await reader.read(1024)
            response = msgpack.unpackb(response, encoding="utf-8")
            if not response["success"]:
                self.logger.info("Mounting failed! Mount returned error code {}.".format(response["rc"]))
                # Return None.
                return

        # Create the new container, using the recently mounted volume.
        await self.open_container("--read-only=true", "-v", "{}:/docker ".format(vp))
        # Return the subprocess.
        return self.subprocess

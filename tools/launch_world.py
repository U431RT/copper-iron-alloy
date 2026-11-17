"""Loads a throwaway copy of a world so the server-side data (recipes, tags,
advancements) is actually parsed by the game, then exits."""

import os
import shutil
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import launch  # noqa: E402  (reuses the argument builder)

WORLD_SRC = r"D:/GAME/MC1.26.2/1.26.2/.minecraft/saves/新的世界"
WORLD_DST = os.path.join(launch.GAME_DIR, "saves", "testworld")


def main():
    os.makedirs(os.path.dirname(WORLD_DST), exist_ok=True)
    if os.path.exists(WORLD_DST):
        shutil.rmtree(WORLD_DST)
    shutil.copytree(WORLD_SRC, WORLD_DST)
    print("world copied", flush=True)

    import json

    data = json.load(open(launch.VERSION_JSON, encoding="utf-8"))
    classpath = []
    for lib in data["libraries"]:
        dl = (lib.get("downloads") or {}).get("artifact")
        if dl and dl.get("path"):
            classpath.append(os.path.join(launch.LIBDIR, dl["path"].replace("/", os.sep)))
    classpath.append(os.path.join(launch.MC, "versions", launch.VER, launch.VER + ".jar"))

    subs = {
        "natives_directory": launch.NATIVES,
        "library_directory": launch.LIBDIR,
        "launcher_name": "dsh",
        "launcher_version": "1.0",
        "classpath": ";".join(classpath),
        "classpath_separator": ";",
        "auth_player_name": "DevTest",
        "version_name": launch.VER,
        "game_directory": launch.GAME_DIR,
        "assets_root": os.path.join(launch.MC, "assets"),
        "assets_index_name": data["assetIndex"]["id"],
        "auth_uuid": "00000000000000000000000000000000",
        "auth_access_token": "0",
        "clientid": "0",
        "auth_xuid": "0",
        "version_type": "release",
        "user_properties": "{}",
    }
    jvm = launch.flatten(data["arguments"]["jvm"]) + ["-Xmx4G", "-Xms1G"]
    game = launch.flatten(data["arguments"]["game"])
    game += ["--width", "1280", "--height", "720", "--quickPlaySingleplayer", "testworld"]
    cmd = [launch._sub(c, subs) for c in [launch.JAVA, *jvm, data["mainClass"], *game]]

    log_path = r"D:/dshworkshop/copper_iron_alloy/build/world.log"
    with open(log_path, "wb") as log:
        log.write((" ".join(cmd) + "\n\n").encode("utf-8", "replace"))
        log.flush()
        proc = subprocess.Popen(cmd, cwd=launch.GAME_DIR, stdout=log, stderr=subprocess.STDOUT,
                                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
        print("pid", proc.pid, flush=True)
        started = time.time()
        joined = None
        while time.time() - started < 480:
            if proc.poll() is not None:
                print("exited", proc.returncode, flush=True)
                return
            if joined is None and os.path.exists(launch.GAME_LOG):
                try:
                    text = open(launch.GAME_LOG, "r", encoding="utf-8", errors="replace").read()
                except OSError:
                    text = ""
                if "Starting integrated minecraft server" in text:
                    joined = time.time()
                    print("integrated server started", flush=True)
            if joined and time.time() - joined > 60:
                proc.kill()
                print("closed after world load", flush=True)
                return
            time.sleep(2)
        proc.kill()
        print("timeout", flush=True)


if __name__ == "__main__":
    main()

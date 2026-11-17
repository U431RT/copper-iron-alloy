"""Launches the 1.26.2 NeoForge client against a writable test game dir.

The sandbox lets the shell write to D:\\GAME but not child JVMs, so the game runs with
--gameDir pointing at D:/dshworkshop/_mctest (mods/assets are junctions or passed
explicitly).  The script stops the game once the main menu has finished loading.
"""

import json
import os
import subprocess
import sys
import time

MC = r"D:/GAME/MC1.26.2/1.26.2/.minecraft"
GAME_DIR = r"D:/dshworkshop/_mctest"
VER = "26.1.2-NeoForge_26.1.2.78"
JAVA = r"D:/dshworkshop/_cia/jdk25x/jdk-25.0.5+8/bin/java.exe"
VERSION_JSON = os.path.join(MC, "versions", VER, VER + ".json")
NATIVES = os.path.join(MC, "versions", VER, VER + "-natives")
LIBDIR = os.path.join(MC, "libraries")
LOG_PATH = r"D:/dshworkshop/copper_iron_alloy/build/launch.log"
GAME_LOG = os.path.join(GAME_DIR, "logs", "latest.log")


def rules_allow(entry):
    rules = entry.get("rules")
    if not rules:
        return True
    allowed = False
    for rule in rules:
        os_rule = rule.get("os")
        ok = True
        if os_rule:
            if "name" in os_rule and os_rule["name"] != "windows":
                ok = False
            if "arch" in os_rule and os_rule["arch"] != "x86_64":
                ok = False
        features = rule.get("features")
        if features and any(features.values()):
            ok = False
        if ok:
            allowed = rule.get("action") == "allow"
    return allowed


def flatten(values):
    out = []
    for v in values:
        if isinstance(v, str):
            out.append(v)
        elif isinstance(v, list):
            out.extend(v)
        elif isinstance(v, dict) and "value" in v:
            if rules_allow(v):
                out.extend(v["value"] if isinstance(v["value"], list) else [v["value"]])
    return out


def _sub(text, subs):
    for k, v in subs.items():
        text = text.replace("${" + k + "}", v)
    return text


def main():
    data = json.load(open(VERSION_JSON, encoding="utf-8"))
    classpath = []
    for lib in data["libraries"]:
        dl = (lib.get("downloads") or {}).get("artifact")
        if dl and dl.get("path"):
            classpath.append(os.path.join(LIBDIR, dl["path"].replace("/", os.sep)))
    classpath.append(os.path.join(MC, "versions", VER, VER + ".jar"))

    subs = {
        "natives_directory": NATIVES,
        "library_directory": LIBDIR,
        "launcher_name": "dsh",
        "launcher_version": "1.0",
        "classpath": ";".join(classpath),
        "classpath_separator": ";",
        "auth_player_name": "DevTest",
        "version_name": VER,
        "game_directory": GAME_DIR,
        "assets_root": os.path.join(MC, "assets"),
        "assets_index_name": data["assetIndex"]["id"],
        "auth_uuid": "00000000000000000000000000000000",
        "auth_access_token": "0",
        "clientid": "0",
        "auth_xuid": "0",
        "version_type": "release",
        "user_properties": "{}",
    }

    jvm = flatten(data["arguments"]["jvm"]) + ["-Xmx4G", "-Xms1G"]
    game = flatten(data["arguments"]["game"]) + ["--width", "1280", "--height", "720"]

    cmd = [_sub(c, subs) for c in [JAVA, *jvm, data["mainClass"], *game]]

    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    with open(LOG_PATH, "wb") as log:
        log.write((" ".join(cmd) + "\n\n").encode("utf-8", "replace"))
        log.flush()
        proc = subprocess.Popen(cmd, cwd=GAME_DIR, stdout=log, stderr=subprocess.STDOUT,
                                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
        print("pid", proc.pid, flush=True)

        started = time.time()
        menu_at = None
        while time.time() - started < 600:
            if proc.poll() is not None:
                print("exited", proc.returncode, flush=True)
                return
            if menu_at is None and os.path.exists(GAME_LOG):
                try:
                    text = open(GAME_LOG, "r", encoding="utf-8", errors="replace").read()
                except OSError:
                    text = ""
                if "Sound engine started" in text:
                    menu_at = time.time()
                    print("main menu reached", flush=True)
            if menu_at and time.time() - menu_at > 25:
                proc.kill()
                print("closed after main menu", flush=True)
                return
            time.sleep(2)
        proc.kill()
        print("killed after timeout", flush=True)


if __name__ == "__main__":
    main()

#!/usr/bin/env bash
# Builds copper_iron_alloy and drops the jar into the 1.26.2 mods folder.
set -euo pipefail

JDK="${JDK:-D:/dshworkshop/_cia/jdk25x/jdk-25.0.5+8}"
MC="D:/GAME/MC1.26.2/1.26.2/.minecraft"
ROOT="$(cd "$(dirname "$0")" && pwd)"
VERSION="1.0.0"
JAR_NAME="copper_iron_alloy-${VERSION}.jar"

cd "$ROOT"

echo "==> collecting classpath"
( cd "$MC" && find libraries -name "*.jar" | sed 's#^#D:/GAME/MC1.26.2/1.26.2/.minecraft/#' > "$ROOT/build/jars.txt" )
mkdir -p build
awk '{printf "%s;", $0}' build/jars.txt > build/cp.txt
printf -- '-cp "%s"\n-d build/classes\n--release 25\n-nowarn\n-proc:none\n' "$(cat build/cp.txt)" > build/javac.args

echo "==> compiling"
rm -rf build/classes
mkdir -p build/classes
find src/main/java -name "*.java" > build/srcs.txt
"$JDK/bin/javac" @build/javac.args @build/srcs.txt

echo "==> packing resources"
cp -r src/main/resources/. build/classes/

echo "==> building jar"
rm -f "build/${JAR_NAME}"
"$JDK/bin/jar" cf "build/${JAR_NAME}" -C build/classes .

echo "==> installing"
mkdir -p "$MC/mods"
cp "build/${JAR_NAME}" "$MC/mods/${JAR_NAME}"
ls -la "$MC/mods/${JAR_NAME}"
echo "done"

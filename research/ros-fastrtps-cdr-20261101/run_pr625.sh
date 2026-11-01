#!/usr/bin/env bash
# Compare Cyclone DDS RMW Jazzy baseline against exact CDR constructor change
# from ros2/rmw_cyclonedds PR #625, without shifting any other source or ABI.
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y -qq git cmake g++ ninja-build python3-colcon-common-extensions \
    ros-jazzy-rmw-cyclonedds-cpp ros-jazzy-rmw-fastrtps-cpp ros-jazzy-test-msgs
set +u
source /opt/ros/jazzy/setup.bash
set -u
dpkg-query -W ros-jazzy-rmw-cyclonedds-cpp ros-jazzy-rmw-fastrtps-cpp \
    ros-jazzy-cyclonedds ros-jazzy-rclpy ros-jazzy-test-msgs \
    > /evidence/package-versions.txt
PR_HEAD="73c2fb62b2be3b752b098f44cc6c41b9c4bbe85a"
SRC=/tmp/rmw_cyclonedds
git clone --quiet --branch jazzy https://github.com/ros2/rmw_cyclonedds.git "$SRC"
BASE=$(git -C "$SRC" rev-parse HEAD)
printf "%s\n" "$BASE" > /evidence/jazzy-source-sha.txt
git -C "$SRC" fetch --quiet origin pull/625/head:refs/heads/pr625
test "$(git -C "$SRC" rev-parse pr625)" = "$PR_HEAD"
git -C "$SRC" show --format= "$PR_HEAD" -- rmw_cyclonedds_cpp/src/serdes.cpp \
    > /evidence/pr625-serdes.patch
test -s /evidence/pr625-serdes.patch
sha256sum /evidence/pr625-serdes.patch > /evidence/pr625-patch.sha256
# Confirm the exact target source file is byte-for-byte identical between
# the current Jazzy baseline and the PR's Kilted parent.
PR_PARENT=$(git -C "$SRC" rev-parse pr625^)
test "$(git -C "$SRC" rev-parse "$BASE:rmw_cyclonedds_cpp/src/serdes.cpp")" = \
     "$(git -C "$SRC" rev-parse "$PR_PARENT:rmw_cyclonedds_cpp/src/serdes.cpp")"
printf "%s\n" "$PR_PARENT" > /evidence/pr625-parent-sha.txt

build_arm() {
  local arm="$1"
  local prefix="/tmp/cyclone-arm-$arm"
  colcon build --merge-install --base-paths "$SRC/rmw_cyclonedds_cpp" \
      --packages-select rmw_cyclonedds_cpp \
      --build-base "/tmp/cyclone-build-$arm" \
      --install-base "$prefix" \
      --log-base "/tmp/cyclone-logs-$arm" \
      --event-handlers console_cohesion+ \
      --cmake-args -DBUILD_TESTING=OFF \
      > "/evidence/$arm-build.log" 2>&1
  test -f "$prefix/lib/librmw_cyclonedds_cpp.so"
  sha256sum "$prefix/lib/librmw_cyclonedds_cpp.so" > "/evidence/$arm-library.sha256"
  readelf -d "$prefix/lib/librmw_cyclonedds_cpp.so" | grep SONAME \
      > "/evidence/$arm-soname.txt"
}
build_arm baseline
git -C "$SRC" apply --check /evidence/pr625-serdes.patch
git -C "$SRC" apply /evidence/pr625-serdes.patch
git -C "$SRC" diff --check
test "$(git -C "$SRC" diff --numstat -- rmw_cyclonedds_cpp/src/serdes.cpp | awk '{print $1 " " $2}')" = "6 0"
build_arm patched

ros_library_path="$LD_LIBRARY_PATH"
for arm in baseline patched; do
    prefix="/tmp/cyclone-arm-$arm"
    export LD_LIBRARY_PATH="$prefix/lib:$ros_library_path"
    export EXPECTED_LIB_DIR="$prefix/lib"
    export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
    /usr/bin/python3 -c '
import os
from rclpy.serialization import serialize_message, deserialize_message
from test_msgs.msg import Arrays
deserialize_message(serialize_message(Arrays()), Arrays)
paths = sorted(set(line.split()[-1] for line in open("/proc/self/maps")
                   if "/librmw_cyclonedds_cpp.so" in line and "/" in line))
print("\n".join(paths))
assert paths and all(p.startswith(os.environ["EXPECTED_LIB_DIR"]) for p in paths), paths
' > "/evidence/$arm-mapped-library.txt"
    # Preserve complete results, not just the native pass/fail summary.
    /usr/bin/python3 /study/probe.py > "/evidence/$arm-matrix.jsonl" \
       2> "/evidence/$arm-stderr.txt"
    cp /evidence/results.json "/evidence/$arm-results.json"
done
/usr/bin/python3 /study/check_pr625.py | tee /evidence/comparison.txt

#!/usr/bin/env bash
# Memory-bounded exploration of valid-header / dishonest-length inputs
# using pinned fork Jazzy source and exact PR #625's six-line guard.
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y -qq git cmake g++ ninja-build python3-colcon-common-extensions \
  ros-jazzy-rmw-cyclonedds-cpp ros-jazzy-rmw-fastrtps-cpp ros-jazzy-test-msgs
set +u
source /opt/ros/jazzy/setup.bash
set -u
dpkg-query -W ros-jazzy-rmw-cyclonedds-cpp ros-jazzy-cyclonedds \
  ros-jazzy-rclpy ros-jazzy-test-msgs > /evidence/packages.txt
SRC=/tmp/cyclone-oom
BASE=20b192ae744f2fe56767e68081a46ad0d7f7a0ec
PR_HEAD=73c2fb62b2be3b752b098f44cc6c41b9c4bbe85a
git clone -q --branch jazzy https://github.com/metalogiclabs/rmw_cyclonedds.git "$SRC"
test "$(git -C "$SRC" rev-parse HEAD)" = "$BASE"
git -C "$SRC" fetch --quiet https://github.com/ros2/rmw_cyclonedds.git \
  pull/625/head:refs/heads/pr625
test "$(git -C "$SRC" rev-parse pr625)" = "$PR_HEAD"
test "$(git -C "$SRC" rev-parse "HEAD:rmw_cyclonedds_cpp/src/serdes.cpp")" = \
     "$(git -C "$SRC" rev-parse "pr625^:rmw_cyclonedds_cpp/src/serdes.cpp")"
git -C "$SRC" show --format= "$PR_HEAD" -- rmw_cyclonedds_cpp/src/serdes.cpp \
  > /evidence/pr625.patch
sha256sum /evidence/pr625.patch > /evidence/pr625-patch.sha256
printf '%s\n' "$BASE" > /evidence/fork-jazzy-base.txt
printf '%s\n' "$PR_HEAD" > /evidence/pr625-source.txt

build_arm() {
  local arm="$1"
  local prefix="/tmp/cyclone-oom-$arm"
  colcon --log-base "/tmp/cyclone-oom-log-$arm" build \
    --merge-install --base-paths "$SRC/rmw_cyclonedds_cpp" \
    --packages-select rmw_cyclonedds_cpp \
    --build-base "/tmp/cyclone-oom-build-$arm" \
    --install-base "$prefix" \
    --event-handlers console_cohesion+ --cmake-args -DBUILD_TESTING=OFF \
    > "/evidence/build-$arm.log" 2>&1
  test -f "$prefix/lib/librmw_cyclonedds_cpp.so"
  sha256sum "$prefix/lib/librmw_cyclonedds_cpp.so" > "/evidence/lib-$arm.sha256"
}
build_arm baseline
git -C "$SRC" apply --check /evidence/pr625.patch
git -C "$SRC" apply /evidence/pr625.patch
test "$(git -C "$SRC" diff --numstat -- rmw_cyclonedds_cpp/src/serdes.cpp | awk '{print $1 " " $2}')" = "6 0"
build_arm patched

# Apply only the independent additional sequence-count preflight, sourced
# from the dedicated clean Metalogic Labs fork contribution branch.
NEW_SHA=aa3aba9982264b1c56e484e48e1d3e5f51c88393
git -C "$SRC" fetch --quiet origin \
  fix/jazzy-cdr-sequence-length-preflight:refs/heads/length-preflight
test "$(git -C "$SRC" rev-parse length-preflight)" = "$NEW_SHA"
git -C "$SRC" show --format= "$NEW_SHA" -- \
  rmw_cyclonedds_cpp/src/TypeSupport_impl.hpp > /evidence/sequence-preflight.patch
test -s /evidence/sequence-preflight.patch
sha256sum /evidence/sequence-preflight.patch > /evidence/sequence-preflight-patch.sha256
git -C "$SRC" apply --check /evidence/sequence-preflight.patch
git -C "$SRC" apply /evidence/sequence-preflight.patch
git -C "$SRC" diff --check
printf '%s\n' "$NEW_SHA" > /evidence/sequence-preflight-source.txt
build_arm preflight

ros_library_path="$LD_LIBRARY_PATH"
for arm in baseline patched preflight; do
  prefix="/tmp/cyclone-oom-$arm"
  export LD_LIBRARY_PATH="$prefix/lib:$ros_library_path"
  export EXPECTED_LIB_DIR="$prefix/lib"
  export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
  /usr/bin/python3 -c '
import os
from rclpy.serialization import serialize_message, deserialize_message
from test_msgs.msg import WStrings
deserialize_message(serialize_message(WStrings()), WStrings)
paths=sorted(set(x.split()[-1] for x in open("/proc/self/maps")
                 if "/librmw_cyclonedds_cpp.so" in x and "/" in x))
print("\n".join(paths))
assert paths and all(x.startswith(os.environ["EXPECTED_LIB_DIR"]) for x in paths),paths
' > "/evidence/mapped-$arm.txt"
  /usr/bin/python3 /study/oom_probe.py > "/evidence/census-$arm.jsonl" \
    2> "/evidence/census-$arm.stderr"
  cp /evidence/residual-results.json "/evidence/results-$arm.json"
done

/usr/bin/python3 /study/oom_compare.py | tee /evidence/comparison.txt

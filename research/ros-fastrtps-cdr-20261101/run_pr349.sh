#!/usr/bin/env bash
# Independent, source-pinned verification of eProsima/Fast-CDR#349 against
# ROS Jazzy's Fast-CDR ABI. No changes to an upstream repository.
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y -qq git cmake ninja-build g++ ros-jazzy-test-msgs \
  ros-jazzy-rmw-fastrtps-cpp ros-jazzy-rmw-cyclonedds-cpp ros-jazzy-fastcdr
set +u
source /opt/ros/jazzy/setup.bash
set -u
dpkg-query -W ros-jazzy-fastcdr ros-jazzy-rmw-fastrtps-cpp \
  ros-jazzy-rmw-cyclonedds-cpp ros-jazzy-rclpy ros-jazzy-test-msgs \
  > /evidence/package-versions.txt

BASE_TAG="v2.2.8"
PR_HEAD="1eaa6c809d464fb5d1c1b9be03ffcc4adc29c2ed"
PR_BASE="e92fa060825c21572f56a44656c02cbe2b06069c"
SRC=/tmp/fastcdr-source
git clone --quiet --branch "$BASE_TAG" https://github.com/eProsima/Fast-CDR.git "$SRC"
git -C "$SRC" fetch --quiet origin pull/349/head:refs/heads/source-pr349
test "$(git -C "$SRC" rev-parse source-pr349)" = "$PR_HEAD"
test "$(git -C "$SRC" rev-parse source-pr349^)" = "$PR_BASE"
git -C "$SRC" show --format= "$PR_HEAD" -- src/cpp/Cdr.cpp > /evidence/pr349-core.patch
test -s /evidence/pr349-core.patch
sha256sum /evidence/pr349-core.patch > /evidence/pr349-patch.sha256
git -C "$SRC" rev-parse HEAD > /evidence/fastcdr-base-source-sha.txt

build_arm() {
  arm="$1"
  prefix="/tmp/fastcdr-arm-$arm"
  cmake -S "$SRC" -B "/tmp/fastcdr-build-$arm" -G Ninja \
    -DCMAKE_INSTALL_PREFIX="$prefix" -DCMAKE_BUILD_TYPE=Release \
    -DBUILD_TESTING=OFF -DBUILD_SHARED_LIBS=ON \
    > "/evidence/build-$arm-configure.log"
  cmake --build "/tmp/fastcdr-build-$arm" --parallel 2 \
    > "/evidence/build-$arm.log"
  cmake --install "/tmp/fastcdr-build-$arm" \
    > "/evidence/build-$arm-install.log"
  test -f "$prefix/lib/libfastcdr.so"
  readelf -d "$prefix/lib/libfastcdr.so" | grep SONAME \
    > "/evidence/$arm-soname.txt"
  sha256sum "$prefix/lib/libfastcdr.so" > "/evidence/$arm-library.sha256"
}
build_arm baseline

# Apply precisely the PR author's one-commit core fix onto the ABI-compatible
# v2.2.8 release, rather than silently using a newer library build.
git -C "$SRC" apply --check /evidence/pr349-core.patch
git -C "$SRC" apply /evidence/pr349-core.patch
git -C "$SRC" diff --check
git -C "$SRC" diff -- src/cpp/Cdr.cpp > /evidence/applied-v2.2.8.patch
test "$(git -C "$SRC" diff --numstat -- src/cpp/Cdr.cpp | awk '{print $1 " " $2}')" = "11 0"
build_arm patched
# Independently compile the exact upstream PR head (Fast-CDR 2.4.0).
# Do not inject this ABI into ROS Jazzy: the comparative ROS test must
# change only the 2.2.8 implementation, not the ABI.
git -C "$SRC" reset --quiet --hard HEAD
git -C "$SRC" checkout --quiet --detach "$PR_HEAD"
git -C "$SRC" rev-parse HEAD > /evidence/pr349-head-source-sha.txt
build_arm prhead

# Retain the ROS environment library paths, including Cyclone DDS dependencies.
ros_library_path="$LD_LIBRARY_PATH"
# Verify mapped library selection in a native Python ROS process.
for arm in baseline patched; do
  prefix="/tmp/fastcdr-arm-$arm"
  export LD_LIBRARY_PATH="$prefix/lib:$ros_library_path"
  export EXPECTED_LIB_DIR="$prefix/lib"
  export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
  python3 -c '
import os
from rclpy.serialization import serialize_message
from test_msgs.msg import Arrays
serialize_message(Arrays())
paths=sorted(set(line.split()[-1] for line in open("/proc/self/maps")
                 if "/libfastcdr.so" in line and "/" in line))
print("\n".join(paths))
assert paths and all(p.startswith(os.environ["EXPECTED_LIB_DIR"]) for p in paths), paths
' > "/evidence/$arm-mapped-library.txt"
  python3 /study/probe.py > "/evidence/$arm-matrix.jsonl" 2> "/evidence/$arm-stderr.txt"
  cp /evidence/results.json "/evidence/$arm-results.json"
done
python3 /study/check_pr349.py | tee /evidence/comparison.txt

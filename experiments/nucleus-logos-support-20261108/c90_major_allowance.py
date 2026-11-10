"""One-factor experimental change: local source recursor-major exposure cap.

Both branch-local min(512) caps become min(4096). The shared owner fuel,
certified recursor interface, checking rules, and total Arena budget stay
unchanged. No ACCEPT is asserted by this source patch alone.
"""
from pathlib import Path


def apply_c90(source=Path("metatron-kernel/src/machine.rs")):
    text=source.read_text()
    begin="let major_result=if self.replay_projection_major {"
    end="let Some(value)=major_result.proven_value() else {"
    assert text.count(begin)==1 and text.count(end)==1, "C90 major-exposure anchors drifted"
    start=text.index(begin)
    stop=text.index(end,start)
    fragment=text[start:stop]
    assert fragment.count(".min(512)")==2 and ".min(4096)" not in fragment, "C90 baseline caps drifted"
    source.write_text(text[:start]+fragment.replace(".min(512)",".min(4096)")+text[stop:])


if __name__=="__main__":
    apply_c90()
    print("C90_MAJOR_EXPOSURE_CAP_512_TO_4096_APPLIED")

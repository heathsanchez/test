# V47b supersedes the first V47 protocol

The first V47 freeze was scientifically useful but its post-freeze hidden probe exposed two protocol assumptions that were too strong:

1. prefix depth 2 was insufficient to certify the intended four-state future-dependent floor because one behavioral state first appeared at the transition-check boundary;
2. the protocol incorrectly predicted that every closure certificate in the entire bounded table would be necessary, even for histories deeper than the horizon actually used to certify a depth-0 floor.

No frozen V47 scientific file was patched.

V47b restarts from the prior verified V46 head, freezes the same generic version-space kernel under a corrected prefix depth 3 / future depth 2 protocol, and replaces the hand-stated closure-necessity claim with a discovered closure-criticality map.

V47b is the authoritative final-boss experiment.

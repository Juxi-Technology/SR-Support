/* Host-side test harness: reads float32 observation vectors from stdin,
 * runs the exported policy, and writes float32 actions to stdout. */
#include <stdio.h>

#ifndef POLICY_INCLUDE
#define POLICY_INCLUDE "policy.h"
#endif
#include POLICY_INCLUDE

int main(void) {
    float obs[POLICY_OBS_DIM];
    float act[POLICY_ACT_DIM];
    while (fread(obs, sizeof(float), POLICY_OBS_DIM, stdin) == POLICY_OBS_DIM) {
        policy_forward(obs, act);
        fwrite(act, sizeof(float), POLICY_ACT_DIM, stdout);
    }
    return 0;
}

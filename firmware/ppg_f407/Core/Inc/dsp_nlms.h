#ifndef DSP_NLMS_H
#define DSP_NLMS_H

#include <stdint.h>

#define NLMS_FS      100.0f
#define NLMS_TAPS    32
#define NLMS_K       3
#define NLMS_W_LEN   (NLMS_TAPS * NLMS_K)
#define NLMS_MU      0.02f
#define NLMS_EPS_REL 1.0f

typedef struct {
    float z1[2];
    float z2[2];
} BiquadBP;

typedef struct {
    BiquadBP bp_ppg;
    BiquadBP bp_acc[NLMS_K];
    float ppg_dc;
    float acc_var[NLMS_K];
    float buf[NLMS_K][NLMS_TAPS];
    float w[NLMS_W_LEN];
    float pw_avg;

    /* Phat hien dinh don gian de tinh HR tuc thoi (bpm) */
    uint32_t sample_cnt;
    uint32_t last_peak;
    float prev2;
    float prev1;
    float env_rms;
    float hr_bpm;
} PPG_NLMS;

void ppg_nlms_init(PPG_NLMS *st);
float ppg_nlms_step(PPG_NLMS *st, float ir_raw, int16_t ax, int16_t ay, int16_t az, float *d_out);

#endif /* DSP_NLMS_H */

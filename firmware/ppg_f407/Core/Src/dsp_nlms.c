#include "dsp_nlms.h"

#include <math.h>
#include <string.h>

/* He so butter(2, [0.5, 5.0], btype='bandpass', fs=100.0, output='sos') */
static float biquad_bp_step(BiquadBP *f, float x)
{
    static const float b[2][3] = {
        { 0.01658193f,  0.03316386f, 0.01658193f },
        { 1.00000000f, -2.00000000f, 1.00000000f }
    };
    static const float a[2][2] = {
        { -1.62885077f, 0.69946348f },
        { -1.95738904f, 0.95853169f }
    };

    float y = x;
    for (int s = 0; s < 2; s++) {
        float w = y - a[s][0] * f->z1[s] - a[s][1] * f->z2[s];
        y = b[s][0] * w + b[s][1] * f->z1[s] + b[s][2] * f->z2[s];
        f->z2[s] = f->z1[s];
        f->z1[s] = w;
    }
    return y;
}

void ppg_nlms_init(PPG_NLMS *st)
{
    memset(st, 0, sizeof(*st));
    for (int k = 0; k < NLMS_K; k++) {
        st->acc_var[k] = 1.0f;
    }
    st->pw_avg = 1.0f;
}

float ppg_nlms_step(PPG_NLMS *st, float ir_raw, int16_t ax, int16_t ay, int16_t az, float *d_out)
{
    /* 1. Khu DC cham bang EMA de tranh soc khi bat dau do */
    if (st->ppg_dc == 0.0f) {
        st->ppg_dc = ir_raw;
    }
    st->ppg_dc = 0.995f * st->ppg_dc + 0.005f * ir_raw;
    float d = biquad_bp_step(&st->bp_ppg, ir_raw - st->ppg_dc);
    if (d_out) {
        *d_out = d;
    }

    /* 2. Loc thong dai gia toc 3 truc va chuan hoa tung truc */
    float raw_acc[NLMS_K] = {
        (float)ax / 8192.0f,
        (float)ay / 8192.0f,
        (float)az / 8192.0f
    };
    float u[NLMS_W_LEN];
    float pw = 0.0f;

    for (int k = 0; k < NLMS_K; k++) {
        float ak = biquad_bp_step(&st->bp_acc[k], raw_acc[k]);
        st->acc_var[k] = 0.995f * st->acc_var[k] + 0.005f * (ak * ak);
        float ak_norm = ak / sqrtf(st->acc_var[k] + 1e-6f);

        for (int m = NLMS_TAPS - 1; m > 0; m--) {
            st->buf[k][m] = st->buf[k][m - 1];
        }
        st->buf[k][0] = ak_norm;

        for (int m = 0; m < NLMS_TAPS; m++) {
            float val = st->buf[k][m];
            u[k * NLMS_TAPS + m] = val;
            pw += val * val;
        }
    }

    /* 3. Loc thich nghi NLMS (chuan hoa mem) */
    st->pw_avg = 0.995f * st->pw_avg + 0.005f * pw;
    float y = 0.0f;
    for (int i = 0; i < NLMS_W_LEN; i++) {
        y += st->w[i] * u[i];
    }

    float e = d - y;
    float step = NLMS_MU * e / (NLMS_EPS_REL * st->pw_avg + pw + 1e-6f);
    for (int i = 0; i < NLMS_W_LEN; i++) {
        st->w[i] += step * u[i];
    }

    /* 4. Uoc luong HR don gian tu dinh cuc bo tren e (sau 10s khoi dong) */
    st->env_rms = 0.99f * st->env_rms + 0.01f * (e * e);
    float thr = 0.5f * sqrtf(st->env_rms + 1e-6f);
    uint32_t idx = st->sample_cnt++;
    if (idx > 1000 && st->prev1 > st->prev2 && st->prev1 >= e && st->prev1 > thr) {
        uint32_t dist = (idx - 1) - st->last_peak;
        if (dist >= 33 && dist <= 150) {  /* 40 - 180 bpm o 100 Hz */
            float inst_hr = 60.0f * NLMS_FS / (float)dist;
            st->hr_bpm = (st->hr_bpm == 0.0f) ? inst_hr : (0.8f * st->hr_bpm + 0.2f * inst_hr);
            st->last_peak = idx - 1;
        } else if (dist > 150) {
            st->last_peak = idx - 1;
        }
    }
    st->prev2 = st->prev1;
    st->prev1 = e;

    return e;
}

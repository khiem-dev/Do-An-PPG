#include "sqi_model.h"
#include "sqi_trees.h"
#include <math.h>
#include <string.h>

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

#define SQI_FS         100.0f
#define SQI_MIN_DIST   33     /* int(100 * 60 / 180) */
#define SQI_SPEC_BINS  57     /* 0.70 Hz -> 3.50 Hz, buoc 0.05 Hz (3 bpm) */
#define SQI_MAX_PEAKS  64

void sqi_init(SQI_State *st)
{
    memset(st, 0, sizeof(*st));
    st->label = 0;
    st->prob_good = 0.0f;
}

/* Scratch buffers dat o BSS de tranh tran stack tren STM32 */
static float s_xe[SQI_WIN_LEN];
static int s_cand_idx[SQI_WIN_LEN / 2];
static float s_cand_val[SQI_WIN_LEN / 2];
static uint8_t s_used[SQI_WIN_LEN / 2];

static void compute_features_and_predict(SQI_State *st)
{
    /* Sap lai theo thu tu thoi gian tu cu nhat -> moi nhat */
    float *x_e = s_xe;
    float ir_sum = 0.0f;
    float d_sum = 0.0f, d_sq = 0.0f;
    float e_sum = 0.0f, e_sq = 0.0f;
    float ax_sum = 0.0f, ay_sum = 0.0f, az_sum = 0.0f;

    uint16_t start = (st->total_samples >= SQI_WIN_LEN) ? st->wr_idx : 0;
    for (int i = 0; i < SQI_WIN_LEN; i++) {
        uint16_t idx = (uint16_t)((start + i) % SQI_WIN_LEN);
        float ir = st->ir_raw[idx];
        float d  = st->d_bp[idx];
        float e  = st->e_nlms[idx];

        x_e[i] = e;
        ir_sum += ir;
        d_sum  += d;
        d_sq   += d * d;
        e_sum  += e;
        e_sq   += e * e;
        ax_sum += (float)st->ax[idx] / 8192.0f;
        ay_sum += (float)st->ay[idx] / 8192.0f;
        az_sum += (float)st->az[idx] / 8192.0f;
    }

    float n_f = (float)SQI_WIN_LEN;
    float ir_mean = ir_sum / n_f;
    float d_mean = d_sum / n_f;
    float d_var = (d_sq / n_f) - (d_mean * d_mean);
    float d_std = (d_var > 0.0f) ? sqrtf(d_var) : 0.0f;

    float e_mean = e_sum / n_f;
    float e_var = (e_sq / n_f) - (e_mean * e_mean);
    float e_std = (e_var > 0.0f) ? sqrtf(e_var) : 0.0f;

    /* 1. pi_pct & 2. ppg_std */
    float pi_pct = 100.0f * (2.0f * 1.41421356f * d_std) / (ir_mean + 1e-9f);
    float ppg_std = e_std;

    /* 3. ibi_std & 4. valid_ibi_ratio (tim dinh co prominence >= 0.3 * std, dist >= 33) */
    int *cand_idx = s_cand_idx;
    float *cand_val = s_cand_val;
    int n_cand = 0;
    float min_prom = 0.3f * e_std;

    for (int i = 1; i < SQI_WIN_LEN - 1; i++) {
        if (x_e[i] > x_e[i - 1] && x_e[i] >= x_e[i + 1]) {
            float lmin = x_e[i];
            for (int j = i - 1; j >= 0; j--) {
                if (x_e[j] < lmin) lmin = x_e[j];
                if (x_e[j] > x_e[i]) break;
            }
            float rmin = x_e[i];
            for (int j = i + 1; j < SQI_WIN_LEN; j++) {
                if (x_e[j] < rmin) rmin = x_e[j];
                if (x_e[j] > x_e[i]) break;
            }
            float base = (lmin > rmin) ? lmin : rmin;
            if ((x_e[i] - base) >= min_prom) {
                cand_idx[n_cand] = i;
                cand_val[n_cand] = x_e[i];
                n_cand++;
            }
        }
    }

    /* Chon dinh theo thu tu cao nhat, cach nhau toi thieu SQI_MIN_DIST */
    uint8_t *used = s_used;
    memset(used, 0, (size_t)n_cand);
    int peaks[SQI_MAX_PEAKS];
    int n_peaks = 0;

    while (n_peaks < SQI_MAX_PEAKS) {
        int best = -1;
        float best_v = -1e30f;
        for (int k = 0; k < n_cand; k++) {
            if (!used[k] && cand_val[k] > best_v) {
                best_v = cand_val[k];
                best = k;
            }
        }
        if (best < 0) break;
        used[best] = 1;
        int p = cand_idx[best];
        peaks[n_peaks++] = p;
        for (int k = 0; k < n_cand; k++) {
            if (!used[k]) {
                int diff = cand_idx[k] - p;
                if (diff < 0) diff = -diff;
                if (diff < SQI_MIN_DIST) used[k] = 1;
            }
        }
    }

    /* Sap xep peaks tang dan theo thoi gian */
    for (int i = 0; i < n_peaks - 1; i++) {
        for (int j = i + 1; j < n_peaks; j++) {
            if (peaks[j] < peaks[i]) {
                int tmp = peaks[i];
                peaks[i] = peaks[j];
                peaks[j] = tmp;
            }
        }
    }

    float ibi_vals[SQI_MAX_PEAKS];
    int n_valid_ibi = 0;
    float ibi_sum = 0.0f;
    for (int i = 1; i < n_peaks; i++) {
        float ibi = (float)(peaks[i] - peaks[i - 1]) / SQI_FS;
        if (ibi >= (60.0f / 180.0f) && ibi <= (60.0f / 40.0f)) {
            ibi_vals[n_valid_ibi++] = ibi;
            ibi_sum += ibi;
        }
    }
    int n_intervals = (n_peaks > 1) ? (n_peaks - 1) : 1;
    float valid_ibi_ratio = (float)n_valid_ibi / (float)n_intervals;
    float ibi_std = 1.0f;
    if (n_valid_ibi >= 2) {
        float m = ibi_sum / (float)n_valid_ibi;
        float v = 0.0f;
        for (int i = 0; i < n_valid_ibi; i++) {
            float d = ibi_vals[i] - m;
            v += d * d;
        }
        ibi_std = sqrtf(v / (float)n_valid_ibi);
    }

    /* 5. spec_purity bang Goertzel (0.70 -> 3.50 Hz, buoc 0.05 Hz) */
    for (int i = 0; i < SQI_WIN_LEN; i++) {
        float w = 0.5f * (1.0f - cosf((float)(2.0 * M_PI * i / (SQI_WIN_LEN - 1))));
        x_e[i] = (x_e[i] - e_mean) * w;
    }

    float p2[SQI_SPEC_BINS];
    float p2_sum = 0.0f;
    int dom_k = 0;
    float dom_p = -1.0f;
    for (int k = 0; k < SQI_SPEC_BINS; k++) {
        float freq = 0.70f + 0.05f * (float)k;
        float omega = (float)(2.0 * M_PI * freq / SQI_FS);
        float coeff = 2.0f * cosf(omega);
        float s1 = 0.0f, s2 = 0.0f;
        for (int i = 0; i < SQI_WIN_LEN; i++) {
            float s0 = x_e[i] + coeff * s1 - s2;
            s2 = s1;
            s1 = s0;
        }
        float mag2 = s1 * s1 + s2 * s2 - coeff * s1 * s2;
        if (mag2 < 0.0f) mag2 = 0.0f;
        p2[k] = mag2;
        p2_sum += mag2;
        if (mag2 > dom_p) {
            dom_p = mag2;
            dom_k = k;
        }
    }
    float dom_bpm = 42.0f + 3.0f * (float)dom_k;
    float p2_peak = 0.0f;
    for (int k = 0; k < SQI_SPEC_BINS; k++) {
        float bpm = 42.0f + 3.0f * (float)k;
        if (fabsf(bpm - dom_bpm) <= 12.0f) p2_peak += p2[k];
    }
    float spec_purity = p2_peak / (p2_sum + 1e-12f);

    /* 6. acc_mean_g & 7. acc_max_g */
    float ax_m = ax_sum / n_f;
    float ay_m = ay_sum / n_f;
    float az_m = az_sum / n_f;
    float acc_sum = 0.0f, acc_max = 0.0f;
    for (int i = 0; i < SQI_WIN_LEN; i++) {
        uint16_t idx = (uint16_t)((start + i) % SQI_WIN_LEN);
        float gx = (float)st->ax[idx] / 8192.0f - ax_m;
        float gy = (float)st->ay[idx] / 8192.0f - ay_m;
        float gz = (float)st->az[idx] / 8192.0f - az_m;
        float mag = sqrtf(gx * gx + gy * gy + gz * gz);
        acc_sum += mag;
        if (mag > acc_max) acc_max = mag;
    }
    float acc_mean_g = acc_sum / n_f;
    float acc_max_g = acc_max;

    st->features[0] = pi_pct;
    st->features[1] = ppg_std;
    st->features[2] = ibi_std;
    st->features[3] = valid_ibi_ratio;
    st->features[4] = spec_purity;
    st->features[5] = acc_mean_g;
    st->features[6] = acc_max_g;

    st->label = sqi_rf_predict(st->features, &st->prob_good);
    st->ready = 1;
}

int sqi_push_sample(SQI_State *st, float ir_raw, float d_bp, float e_nlms,
                    int16_t ax, int16_t ay, int16_t az)
{
    st->ir_raw[st->wr_idx] = ir_raw;
    st->d_bp[st->wr_idx]   = d_bp;
    st->e_nlms[st->wr_idx] = e_nlms;
    st->ax[st->wr_idx]     = ax;
    st->ay[st->wr_idx]     = ay;
    st->az[st->wr_idx]     = az;

    st->wr_idx = (uint16_t)((st->wr_idx + 1) % SQI_WIN_LEN);
    st->total_samples++;
    st->hop_cnt++;

    if (st->total_samples >= SQI_WIN_LEN && st->hop_cnt >= SQI_SHIFT_LEN) {
        st->hop_cnt = 0;
        compute_features_and_predict(st);
        return 1;
    }
    return 0;
}

#ifndef SQI_MODEL_H
#define SQI_MODEL_H

#include <stdint.h>

#define SQI_WIN_LEN   1000  /* 10 s o 100 Hz */
#define SQI_SHIFT_LEN 200   /* cap nhat moi 2 s */

typedef struct {
    float ir_raw[SQI_WIN_LEN];
    float d_bp[SQI_WIN_LEN];
    float e_nlms[SQI_WIN_LEN];
    int16_t ax[SQI_WIN_LEN];
    int16_t ay[SQI_WIN_LEN];
    int16_t az[SQI_WIN_LEN];

    uint32_t total_samples;
    uint16_t wr_idx;
    uint16_t hop_cnt;

    int ready;       /* 1 sau khi du 10 s dau tien */
    int label;       /* 1 = GOOD, 0 = BAD */
    float prob_good; /* xac suat lop GOOD [0..1] */
    float features[7];
} SQI_State;

void sqi_init(SQI_State *st);

/* Day 1 mau vao bo dem truot 10 s. Tra ve 1 neu vua cap nhat SQI moi, 0 neu chua. */
int sqi_push_sample(SQI_State *st, float ir_raw, float d_bp, float e_nlms,
                    int16_t ax, int16_t ay, int16_t az);

#endif /* SQI_MODEL_H */

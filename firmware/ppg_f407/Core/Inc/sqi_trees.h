/* Tu dong sinh boi python/export_sqi_c.py - KHONG SUA TAY */
#ifndef SQI_TREES_H
#define SQI_TREES_H

/* Thu tu dac trung f[0..6]:
 * f[0] = pi_pct
 * f[1] = ppg_std
 * f[2] = ibi_std
 * f[3] = valid_ibi_ratio
 * f[4] = spec_purity
 * f[5] = acc_mean_g
 * f[6] = acc_max_g
 */

static float sqi_tree_0(const float f[7]) {
    if (f[6] <= 1.063700f) {
        if (f[4] <= 0.504040f) {
            if (f[1] <= 568.587646f) {
                if (f[6] <= 0.820005f) {
                    return 0.009615f;
                } else {
                    return 0.333333f;
                }
            } else {
                if (f[4] <= 0.309558f) {
                    return 0.000000f;
                } else {
                    return 0.446809f;
                }
            }
        } else {
            if (f[0] <= 0.233456f) {
                return 0.000000f;
            } else {
                if (f[3] <= 0.795139f) {
                    return 0.000000f;
                } else {
                    return 0.754050f;
                }
            }
        }
    } else {
        if (f[6] <= 1.157069f) {
            if (f[1] <= 470.889816f) {
                return 1.000000f;
            } else {
                return 0.000000f;
            }
        } else {
            return 0.000000f;
        }
    }
}

static float sqi_tree_1(const float f[7]) {
    if (f[5] <= 0.226370f) {
        if (f[6] <= 0.043836f) {
            if (f[5] <= 0.017298f) {
                if (f[5] <= 0.008939f) {
                    return 1.000000f;
                } else {
                    return 0.903226f;
                }
            } else {
                return 0.000000f;
            }
        } else {
            if (f[0] <= 0.239223f) {
                return 0.000000f;
            } else {
                if (f[0] <= 4.675740f) {
                    return 0.670530f;
                } else {
                    return 0.000000f;
                }
            }
        }
    } else {
        if (f[0] <= 0.765047f) {
            if (f[1] <= 284.293076f) {
                return 0.000000f;
            } else {
                return 1.000000f;
            }
        } else {
            return 0.000000f;
        }
    }
}

static float sqi_tree_2(const float f[7]) {
    if (f[4] <= 0.660065f) {
        if (f[4] <= 0.515802f) {
            if (f[5] <= 0.182692f) {
                if (f[4] <= 0.331441f) {
                    return 0.016949f;
                } else {
                    return 0.330097f;
                }
            } else {
                return 0.000000f;
            }
        } else {
            if (f[0] <= 2.110124f) {
                if (f[5] <= 0.016137f) {
                    return 0.933333f;
                } else {
                    return 0.254386f;
                }
            } else {
                if (f[0] <= 2.446773f) {
                    return 0.843137f;
                } else {
                    return 0.333333f;
                }
            }
        }
    } else {
        if (f[1] <= 364.585098f) {
            if (f[3] <= 0.904545f) {
                return 0.000000f;
            } else {
                if (f[6] <= 1.991419f) {
                    return 0.907407f;
                } else {
                    return 0.000000f;
                }
            }
        } else {
            if (f[4] <= 0.787725f) {
                if (f[6] <= 0.672281f) {
                    return 0.718593f;
                } else {
                    return 0.066667f;
                }
            } else {
                if (f[3] <= 0.916084f) {
                    return 1.000000f;
                } else {
                    return 0.779817f;
                }
            }
        }
    }
}

static float sqi_tree_3(const float f[7]) {
    if (f[6] <= 0.888544f) {
        if (f[6] <= 0.056320f) {
            if (f[1] <= 129.128391f) {
                return 0.000000f;
            } else {
                if (f[1] <= 1140.641174f) {
                    return 0.962963f;
                } else {
                    return 0.710526f;
                }
            }
        } else {
            if (f[4] <= 0.550818f) {
                if (f[0] <= 0.861153f) {
                    return 0.085366f;
                } else {
                    return 0.383838f;
                }
            } else {
                if (f[6] <= 0.067622f) {
                    return 0.263158f;
                } else {
                    return 0.778313f;
                }
            }
        }
    } else {
        if (f[5] <= 0.159401f) {
            if (f[0] <= 2.442278f) {
                return 0.000000f;
            } else {
                return 1.000000f;
            }
        } else {
            if (f[5] <= 0.226370f) {
                if (f[1] <= 412.376427f) {
                    return 1.000000f;
                } else {
                    return 0.000000f;
                }
            } else {
                return 0.000000f;
            }
        }
    }
}

static float sqi_tree_4(const float f[7]) {
    if (f[6] <= 0.838756f) {
        if (f[1] <= 112.274754f) {
            if (f[1] <= 104.754379f) {
                return 0.000000f;
            } else {
                if (f[6] <= 0.173229f) {
                    return 0.000000f;
                } else {
                    return 1.000000f;
                }
            }
        } else {
            if (f[1] <= 1792.533386f) {
                if (f[4] <= 0.505314f) {
                    return 0.355769f;
                } else {
                    return 0.774803f;
                }
            } else {
                return 0.000000f;
            }
        }
    } else {
        if (f[0] <= 3.181000f) {
            if (f[5] <= 0.261502f) {
                if (f[0] <= 0.730549f) {
                    return 0.500000f;
                } else {
                    return 0.000000f;
                }
            } else {
                return 0.000000f;
            }
        } else {
            if (f[4] <= 0.608021f) {
                return 0.000000f;
            } else {
                if (f[0] <= 4.100405f) {
                    return 1.000000f;
                } else {
                    return 0.000000f;
                }
            }
        }
    }
}

static float sqi_tree_5(const float f[7]) {
    if (f[0] <= 0.238173f) {
        return 0.000000f;
    } else {
        if (f[5] <= 0.226370f) {
            if (f[0] <= 4.519640f) {
                if (f[3] <= 0.757353f) {
                    return 0.000000f;
                } else {
                    return 0.708752f;
                }
            } else {
                if (f[4] <= 0.451326f) {
                    return 0.000000f;
                } else {
                    return 0.666667f;
                }
            }
        } else {
            if (f[6] <= 0.841931f) {
                if (f[1] <= 380.109482f) {
                    return 1.000000f;
                } else {
                    return 0.000000f;
                }
            } else {
                if (f[1] <= 324.486389f) {
                    return 0.250000f;
                } else {
                    return 0.000000f;
                }
            }
        }
    }
}

static float sqi_tree_6(const float f[7]) {
    if (f[5] <= 0.174457f) {
        if (f[4] <= 0.559230f) {
            if (f[5] <= 0.055624f) {
                if (f[0] <= 2.212038f) {
                    return 0.059829f;
                } else {
                    return 0.800000f;
                }
            } else {
                if (f[0] <= 3.393320f) {
                    return 0.558824f;
                } else {
                    return 0.066667f;
                }
            }
        } else {
            if (f[0] <= 0.243206f) {
                return 0.000000f;
            } else {
                if (f[6] <= 0.060837f) {
                    return 0.917160f;
                } else {
                    return 0.695980f;
                }
            }
        }
    } else {
        if (f[2] <= 0.176096f) {
            if (f[1] <= 338.850174f) {
                if (f[2] <= 0.148268f) {
                    return 0.285714f;
                } else {
                    return 1.000000f;
                }
            } else {
                if (f[2] <= 0.159759f) {
                    return 0.000000f;
                } else {
                    return 0.076923f;
                }
            }
        } else {
            if (f[1] <= 309.931671f) {
                return 1.000000f;
            } else {
                return 0.000000f;
            }
        }
    }
}

static float sqi_tree_7(const float f[7]) {
    if (f[4] <= 0.660065f) {
        if (f[6] <= 0.818956f) {
            if (f[4] <= 0.503456f) {
                if (f[5] <= 0.084813f) {
                    return 0.069565f;
                } else {
                    return 0.511111f;
                }
            } else {
                if (f[0] <= 2.186147f) {
                    return 0.389381f;
                } else {
                    return 0.814815f;
                }
            }
        } else {
            return 0.000000f;
        }
    } else {
        if (f[1] <= 283.596893f) {
            if (f[4] <= 0.745026f) {
                if (f[1] <= 114.743244f) {
                    return 0.333333f;
                } else {
                    return 0.903846f;
                }
            } else {
                return 1.000000f;
            }
        } else {
            if (f[5] <= 0.155946f) {
                if (f[5] <= 0.008615f) {
                    return 1.000000f;
                } else {
                    return 0.656934f;
                }
            } else {
                if (f[0] <= 0.864922f) {
                    return 0.714286f;
                } else {
                    return 0.000000f;
                }
            }
        }
    }
}

static float sqi_tree_8(const float f[7]) {
    if (f[0] <= 0.240714f) {
        return 0.000000f;
    } else {
        if (f[5] <= 0.156498f) {
            if (f[1] <= 1887.557983f) {
                if (f[6] <= 0.060837f) {
                    return 0.879397f;
                } else {
                    return 0.661417f;
                }
            } else {
                return 0.000000f;
            }
        } else {
            if (f[1] <= 253.640106f) {
                return 1.000000f;
            } else {
                if (f[5] <= 0.242925f) {
                    return 0.212766f;
                } else {
                    return 0.005464f;
                }
            }
        }
    }
}

static float sqi_tree_9(const float f[7]) {
    if (f[4] <= 0.548329f) {
        if (f[4] <= 0.415391f) {
            if (f[3] <= 0.799020f) {
                if (f[2] <= 0.112272f) {
                    return 0.000000f;
                } else {
                    return 1.000000f;
                }
            } else {
                if (f[4] <= 0.287194f) {
                    return 0.000000f;
                } else {
                    return 0.062500f;
                }
            }
        } else {
            if (f[4] <= 0.532271f) {
                if (f[5] <= 0.169266f) {
                    return 0.537313f;
                } else {
                    return 0.000000f;
                }
            } else {
                return 0.000000f;
            }
        }
    } else {
        if (f[6] <= 0.838756f) {
            if (f[4] <= 0.805507f) {
                if (f[6] <= 0.043416f) {
                    return 0.895833f;
                } else {
                    return 0.648241f;
                }
            } else {
                if (f[6] <= 0.509755f) {
                    return 0.940789f;
                } else {
                    return 0.300000f;
                }
            }
        } else {
            if (f[1] <= 232.710030f) {
                return 1.000000f;
            } else {
                if (f[5] <= 0.163501f) {
                    return 0.272727f;
                } else {
                    return 0.011494f;
                }
            }
        }
    }
}

static float sqi_tree_10(const float f[7]) {
    if (f[0] <= 0.294528f) {
        if (f[3] <= 0.930952f) {
            if (f[6] <= 0.074439f) {
                return 0.000000f;
            } else {
                if (f[3] <= 0.919872f) {
                    return 0.000000f;
                } else {
                    return 1.000000f;
                }
            }
        } else {
            if (f[6] <= 0.241955f) {
                return 0.000000f;
            } else {
                return 1.000000f;
            }
        }
    } else {
        if (f[5] <= 0.169120f) {
            if (f[0] <= 4.998734f) {
                if (f[6] <= 0.383628f) {
                    return 0.849899f;
                } else {
                    return 0.564516f;
                }
            } else {
                return 0.000000f;
            }
        } else {
            if (f[1] <= 322.697159f) {
                if (f[6] <= 1.432520f) {
                    return 1.000000f;
                } else {
                    return 0.000000f;
                }
            } else {
                if (f[2] <= 0.288317f) {
                    return 0.012987f;
                } else {
                    return 1.000000f;
                }
            }
        }
    }
}

static float sqi_tree_11(const float f[7]) {
    if (f[4] <= 0.570581f) {
        if (f[5] <= 0.181191f) {
            if (f[4] <= 0.412103f) {
                if (f[5] <= 0.177554f) {
                    return 0.055556f;
                } else {
                    return 1.000000f;
                }
            } else {
                if (f[5] <= 0.058597f) {
                    return 0.278481f;
                } else {
                    return 0.784314f;
                }
            }
        } else {
            return 0.000000f;
        }
    } else {
        if (f[0] <= 0.239223f) {
            return 0.000000f;
        } else {
            if (f[0] <= 1.040191f) {
                if (f[3] <= 0.904545f) {
                    return 0.000000f;
                } else {
                    return 0.820833f;
                }
            } else {
                if (f[6] <= 0.881298f) {
                    return 0.740113f;
                } else {
                    return 0.047170f;
                }
            }
        }
    }
}

static float sqi_tree_12(const float f[7]) {
    if (f[6] <= 0.838756f) {
        if (f[0] <= 0.233491f) {
            return 0.000000f;
        } else {
            if (f[0] <= 4.295220f) {
                if (f[3] <= 0.757353f) {
                    return 0.000000f;
                } else {
                    return 0.686969f;
                }
            } else {
                return 0.000000f;
            }
        }
    } else {
        if (f[5] <= 0.163427f) {
            if (f[6] <= 1.029514f) {
                return 0.000000f;
            } else {
                if (f[4] <= 0.743092f) {
                    return 1.000000f;
                } else {
                    return 0.000000f;
                }
            }
        } else {
            if (f[0] <= 0.765047f) {
                if (f[4] <= 0.740951f) {
                    return 1.000000f;
                } else {
                    return 0.000000f;
                }
            } else {
                return 0.000000f;
            }
        }
    }
}

static float sqi_tree_13(const float f[7]) {
    if (f[4] <= 0.580253f) {
        if (f[6] <= 0.817310f) {
            if (f[5] <= 0.042504f) {
                if (f[4] <= 0.504674f) {
                    return 0.024096f;
                } else {
                    return 0.419355f;
                }
            } else {
                if (f[4] <= 0.328655f) {
                    return 0.000000f;
                } else {
                    return 0.579710f;
                }
            }
        } else {
            return 0.000000f;
        }
    } else {
        if (f[6] <= 1.056262f) {
            if (f[1] <= 229.551323f) {
                if (f[1] <= 104.064590f) {
                    return 0.000000f;
                } else {
                    return 0.901408f;
                }
            } else {
                if (f[1] <= 244.803879f) {
                    return 0.250000f;
                } else {
                    return 0.700855f;
                }
            }
        } else {
            if (f[0] <= 0.689321f) {
                if (f[1] <= 289.801239f) {
                    return 0.000000f;
                } else {
                    return 1.000000f;
                }
            } else {
                if (f[6] <= 1.073050f) {
                    return 0.250000f;
                } else {
                    return 0.000000f;
                }
            }
        }
    }
}

static float sqi_tree_14(const float f[7]) {
    if (f[5] <= 0.172507f) {
        if (f[3] <= 0.878676f) {
            if (f[4] <= 0.697096f) {
                if (f[6] <= 0.373016f) {
                    return 0.000000f;
                } else {
                    return 0.600000f;
                }
            } else {
                return 1.000000f;
            }
        } else {
            if (f[5] <= 0.012424f) {
                if (f[3] <= 0.975000f) {
                    return 0.545455f;
                } else {
                    return 0.913043f;
                }
            } else {
                if (f[0] <= 0.239664f) {
                    return 0.000000f;
                } else {
                    return 0.616601f;
                }
            }
        }
    } else {
        if (f[1] <= 295.621872f) {
            if (f[5] <= 0.630925f) {
                return 1.000000f;
            } else {
                return 0.000000f;
            }
        } else {
            if (f[1] <= 316.403488f) {
                if (f[2] <= 0.174702f) {
                    return 1.000000f;
                } else {
                    return 0.000000f;
                }
            } else {
                if (f[5] <= 0.179086f) {
                    return 0.187500f;
                } else {
                    return 0.000000f;
                }
            }
        }
    }
}

static inline int sqi_rf_predict(const float f[7], float *prob_good_out)
{
    float sum = 0.0f;
    sum += sqi_tree_0(f);
    sum += sqi_tree_1(f);
    sum += sqi_tree_2(f);
    sum += sqi_tree_3(f);
    sum += sqi_tree_4(f);
    sum += sqi_tree_5(f);
    sum += sqi_tree_6(f);
    sum += sqi_tree_7(f);
    sum += sqi_tree_8(f);
    sum += sqi_tree_9(f);
    sum += sqi_tree_10(f);
    sum += sqi_tree_11(f);
    sum += sqi_tree_12(f);
    sum += sqi_tree_13(f);
    sum += sqi_tree_14(f);
    float p = sum * 0.06666667f;
    if (prob_good_out) *prob_good_out = p;
    return (p >= 0.5f) ? 1 : 0;
}

#endif /* SQI_TREES_H */
